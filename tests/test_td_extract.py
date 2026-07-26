import json

import td_extract

NOOP = lambda _: None

SRC = "앞으로\nSTDF 기반 고장분석을 자동화하고 싶다. 이를 위해 파이썬 데이터 분석 역량이 필요하다."


def _doc(text=SRC, cl="CL3"):
    return {"id": 1, "name": "김테스트", "cl_level": cl, "pjt": "공정기술",
            "part": "고장분석(FA)", "text": text}


def _resp(**kw):
    base = {"signal_present": True, "future_task": [], "capability_have": [],
            "capability_gap": [], "direction": None}
    base.update(kw)
    return lambda _: json.dumps(base, ensure_ascii=False)


def test_valid_extraction_keeps_items_and_copies_meta():
    call = _resp(future_task=[{"text": "STDF로 FA를 자동화한다", "horizon": "단기",
                              "quotes": ["STDF 기반 고장분석"]}])
    person, dropped = td_extract.extract_person(_doc(), call, sleep=NOOP)
    assert person["signal_present"] is True
    assert person["person_id"] == 1 and person["pjt"] == "공정기술" and person["part"] == "고장분석(FA)"
    assert len(person["future_task"]) == 1 and not dropped


def test_quote_not_in_source_item_dropped():
    call = _resp(future_task=[{"text": "무언가", "horizon": "단기",
                              "quotes": ["원문에 없는 인용"]}])
    person, dropped = td_extract.extract_person(_doc(), call, tries=1, sleep=NOOP)
    assert person["future_task"] == []
    assert dropped  # 폐기 기록에 남는다


def test_source_newline_quote_survives():
    # 원문에만 개행이 있는 진짜 인용은 통과 (norm 대조)
    call = _resp(capability_gap=[{"text": "데이터 분석 역량을 키운다",
                                 "quotes": ["파이썬 데이터 분석 역량이 필요"]}])
    person, dropped = td_extract.extract_person(_doc(), call, sleep=NOOP)
    assert len(person["capability_gap"]) == 1 and not dropped


def test_text_equal_to_quote_dropped():
    call = _resp(future_task=[{"text": "STDF 기반 고장분석", "horizon": "단기",
                              "quotes": ["STDF 기반 고장분석"]}])
    person, dropped = td_extract.extract_person(_doc(), call, tries=1, sleep=NOOP)
    assert person["future_task"] == [] and dropped


def test_no_signal_doc_returns_false_and_empty_axes():
    call = _resp(signal_present=False)
    person, dropped = td_extract.extract_person(_doc(text="열심히 하겠습니다"), call, sleep=NOOP)
    assert person["signal_present"] is False
    assert person["future_task"] == [] and person["capability_have"] == []
    assert person["capability_gap"] == [] and person["direction"] is None


def test_valid_items_survive_when_one_item_dropped():
    call = _resp(future_task=[
        {"text": "STDF로 FA를 자동화한다", "horizon": "단기", "quotes": ["STDF 기반 고장분석"]},
        {"text": "지어낸 과제", "horizon": "장기", "quotes": ["원문에 없음"]},
    ])
    person, dropped = td_extract.extract_person(_doc(), call, tries=1, sleep=NOOP)
    assert len(person["future_task"]) == 1 and len(dropped) == 1


def test_doc_without_part_extracts_ok():
    # persons.json 등 실데이터엔 part가 없을 수 있다 — .format(**doc)가 KeyError 나면 안 됨
    doc = {"id": 5, "name": "무파트", "cl_level": "CL3", "pjt": "공정기술", "text": SRC}
    call = _resp(future_task=[{"text": "STDF로 FA를 자동화", "horizon": "단기", "quotes": ["STDF 기반 고장분석"]}])
    person, dropped = td_extract.extract_person(doc, call, sleep=NOOP)
    assert person["part"] is None and len(person["future_task"]) == 1


def test_cl4_and_cl23_use_different_prompts():
    seen = []

    def capture(prompt):
        seen.append(prompt)
        return json.dumps({"signal_present": False, "future_task": [], "capability_have": [],
                           "capability_gap": [], "direction": None}, ensure_ascii=False)

    td_extract.extract_person(_doc(cl="CL3"), capture, sleep=NOOP)
    td_extract.extract_person(_doc(cl="CL4"), capture, sleep=NOOP)
    assert seen[0] != seen[1]  # CL2/3 와 CL4 는 서로 다른 템플릿


def test_batch_continues_when_one_person_hard_fails(tmp_path):
    docs = [_doc(), {**_doc(), "id": 2, "name": "실패자"}, {**_doc(), "id": 3, "name": "정상"}]

    def call(prompt):
        if "실패자" in prompt:
            raise RuntimeError("계속 실패")
        return json.dumps({"signal_present": True,
                           "future_task": [{"text": "STDF로 FA 자동화", "horizon": "단기",
                                            "quotes": ["STDF 기반 고장분석"]}],
                           "capability_have": [], "capability_gap": [], "direction": None},
                          ensure_ascii=False)

    out = tmp_path / "extracted.json"
    summary = td_extract.run_extract(docs, out, call, attempts=2, sleep=NOOP)
    ids = [p["person_id"] for p in summary["persons"]]
    assert ids == [1, 3]  # 2번은 폐기, 배치는 계속
    assert summary["failed"] == [2]
    assert json.loads(out.read_text(encoding="utf-8"))  # 즉시 영속화됨
