import json
import os

import pytest

import td_taxonomy

NOOP = lambda _: None


def _persons():
    return [
        {"person_id": 1, "signal_present": True,
         "future_task": [{"text": "MBT Burn-in 신뢰성을 강화한다", "horizon": "장기", "quotes": ["a"]}],
         "capability_have": [], "capability_gap": [], "direction": None},
        {"person_id": 2, "signal_present": True,
         "future_task": [{"text": "Advantest ATE Test PGM을 최적화한다", "horizon": "단기", "quotes": ["b"]}],
         "capability_have": [], "capability_gap": [], "direction": None},
    ]


def _cat(name, definition="정의", inclusion="포함기준"):
    return {"name": name, "definition": definition, "inclusion_criteria": inclusion}


def test_each_category_has_name_definition_inclusion():
    call = lambda _: json.dumps({"taxonomy": [_cat("Burn-in 신뢰성")]}, ensure_ascii=False)
    taxo = td_taxonomy.induce(_persons(), None, call, sleep=NOOP)
    assert taxo
    for c in taxo:
        assert {"name", "definition", "inclusion_criteria"} <= set(c)


def test_missing_fields_are_defaulted_not_dropped():
    call = lambda _: json.dumps({"taxonomy": [{"name": "품질(DPPM)"}]}, ensure_ascii=False)
    taxo = td_taxonomy.induce(_persons(), None, call, sleep=NOOP)
    assert taxo[0]["name"] == "품질(DPPM)"
    assert "definition" in taxo[0] and "inclusion_criteria" in taxo[0]


def test_batches_merge_and_carry_existing_taxonomy_forward():
    # batch_size=1 → facet 배치 2 + 관계 패스 1. 2번째 배치 프롬프트에 1번째 카테고리가 실려야
    responses = [
        json.dumps({"taxonomy": [_cat("Burn-in 신뢰성")]}, ensure_ascii=False),
        json.dumps({"taxonomy": [_cat("Burn-in 신뢰성"), _cat("ATE 운영")]}, ensure_ascii=False),
        json.dumps({"relations": []}, ensure_ascii=False),
    ]
    seen = []

    def call(prompt):
        seen.append(prompt)
        return responses[len(seen) - 1]

    taxo = td_taxonomy.induce(_persons(), None, call, batch_size=1, sleep=NOOP)
    assert len(seen) == 3
    assert "Burn-in 신뢰성" in seen[1]  # 기존 taxonomy를 다음 배치에 제시
    assert {c["name"] for c in taxo} == {"Burn-in 신뢰성", "ATE 운영"}  # 중복 없이 병합


def _call_seq(*responses):
    """호출 순서대로 응답을 돌려주는 가짜 call. 마지막 응답은 소진 후에도 반복 사용."""
    seen = []

    def call(prompt):
        seen.append(prompt)
        return responses[min(len(seen) - 1, len(responses) - 1)]

    return call, seen


def test_batch_prompt_does_not_ask_for_relations():
    """관계는 배치 루프의 관심사가 아니다 — 응답 크기가 부풀던 원인(#30)."""
    call, seen = _call_seq(json.dumps({"taxonomy": [_cat("Burn-in 신뢰성")]}, ensure_ascii=False),
                           json.dumps({"relations": []}, ensure_ascii=False))
    td_taxonomy.induce(_persons(), None, call, batch_size=100, sleep=NOOP)
    assert "relations" not in seen[0]      # 배치 프롬프트엔 relations 요구 없음
    assert "relations" in seen[-1]         # 마지막 관계 패스에서만 요구


def test_writes_taxonomy_file(tmp_path):
    out = tmp_path / "taxonomy.json"
    call = lambda _: json.dumps({"taxonomy": [_cat("Yield 최적화")]}, ensure_ascii=False)
    td_taxonomy.induce(_persons(), out, call, sleep=NOOP)
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written[0]["name"] == "Yield 최적화"


def test_relations_default_to_empty_list():
    call = lambda _: json.dumps({"taxonomy": [_cat("Burn-in 신뢰성")]}, ensure_ascii=False)
    taxo = td_taxonomy.induce(_persons(), None, call, sleep=NOOP)
    assert taxo[0]["relations"] == []


def test_relations_kept_when_target_exists_in_taxonomy():
    call, _ = _call_seq(
        json.dumps({"taxonomy": [_cat("AX 기반 자동화"), _cat("Yield 최적화")]}, ensure_ascii=False),
        json.dumps({"relations": [{"from": "Yield 최적화", "to": "AX 기반 자동화",
                                   "type": "broader"}]}, ensure_ascii=False))
    taxo = td_taxonomy.induce(_persons(), None, call, batch_size=100, sleep=NOOP)
    by_name = {c["name"]: c for c in taxo}
    assert by_name["Yield 최적화"]["relations"] == [{"to": "AX 기반 자동화", "type": "broader"}]
    assert by_name["AX 기반 자동화"]["relations"] == []


def test_dangling_self_and_bad_type_relations_are_dropped():
    call, _ = _call_seq(
        json.dumps({"taxonomy": [_cat("Yield 최적화")]}, ensure_ascii=False),
        json.dumps({"relations": [
            {"from": "Yield 최적화", "to": "존재안함", "type": "broader"},     # 댕글링 참조
            {"from": "Yield 최적화", "to": "Yield 최적화", "type": "related"},  # 자기참조
            {"from": "Yield 최적화", "to": "Yield 최적화", "type": "unknown"},  # 잘못된 type
            {"from": "존재안함", "to": "Yield 최적화", "type": "broader"},      # from이 댕글링
        ]}, ensure_ascii=False))
    taxo = td_taxonomy.induce(_persons(), None, call, batch_size=100, sleep=NOOP)
    assert taxo[0]["relations"] == []


def test_relations_derived_once_after_all_batches_see_full_taxonomy():
    """관계 패스는 완성된 카테고리 전체를 본다 — 배치 중간의 부분 taxonomy가 아니라."""
    call, seen = _call_seq(
        json.dumps({"taxonomy": [_cat("Burn-in 신뢰성")]}, ensure_ascii=False),
        json.dumps({"taxonomy": [_cat("Burn-in 신뢰성"), _cat("ATE 운영")]}, ensure_ascii=False),
        json.dumps({"relations": [{"from": "ATE 운영", "to": "Burn-in 신뢰성",
                                   "type": "related"}]}, ensure_ascii=False))
    taxo = td_taxonomy.induce(_persons(), None, call, batch_size=1, sleep=NOOP)
    assert "Burn-in 신뢰성" in seen[-1] and "ATE 운영" in seen[-1]  # 관계 프롬프트에 둘 다
    by_name = {c["name"]: c for c in taxo}
    assert by_name["ATE 운영"]["relations"] == [{"to": "Burn-in 신뢰성", "type": "related"}]


def test_no_signal_facets_excluded():
    persons = _persons() + [{"person_id": 3, "signal_present": False, "future_task": [],
                             "capability_have": [], "capability_gap": [], "direction": None}]
    seen = []

    def call(prompt):
        seen.append(prompt)
        return json.dumps({"taxonomy": [_cat("x")]}, ensure_ascii=False)

    td_taxonomy.induce(persons, None, call, batch_size=100, sleep=NOOP)
    # 무신호(3번)는 facet이 없으므로 프롬프트에 실릴 항목이 2개뿐
    assert seen and "MBT Burn-in" in seen[0] and "Advantest ATE" in seen[0]


def _write_extracted(tmp_path, persons):
    path = tmp_path / "extracted.json"
    path.write_text(json.dumps(persons, ensure_ascii=False), encoding="utf-8")
    return path


def test_batch_failure_persists_progress_and_resumes_without_recalling_done_batches(tmp_path):
    # 2 facets, batch_size=1 → facet 배치 2 + 관계 패스 1 = total_batches 3
    extracted_path = _write_extracted(tmp_path, _persons())
    out = tmp_path / "taxonomy.json"
    calls = []

    def fail_from_second_call(prompt):
        calls.append(prompt)
        if len(calls) >= 2:
            raise RuntimeError("내부망 에러")
        return json.dumps({"taxonomy": [_cat("Burn-in 신뢰성")]}, ensure_ascii=False)

    with pytest.raises(RuntimeError):
        td_taxonomy.induce(extracted_path, out, fail_from_second_call, batch_size=1,
                           attempts=1, sleep=NOOP)

    written = json.loads(out.read_text(encoding="utf-8"))
    assert {c["name"] for c in written} == {"Burn-in 신뢰성"}
    progress = json.loads((tmp_path / "taxonomy.progress.json").read_text(encoding="utf-8"))
    assert progress["batches_done"] == 1
    assert progress["total_batches"] == 3
    assert not td_taxonomy.is_complete(out)

    call, seen = _call_seq(
        json.dumps({"taxonomy": [_cat("Burn-in 신뢰성"), _cat("ATE 운영")]}, ensure_ascii=False),
        json.dumps({"relations": []}, ensure_ascii=False))
    taxo = td_taxonomy.induce(extracted_path, out, call, batch_size=1, sleep=NOOP)
    assert len(seen) == 2  # 배치 1은 스킵, 배치 2 + 관계 패스만
    assert {c["name"] for c in taxo} == {"Burn-in 신뢰성", "ATE 운영"}
    assert td_taxonomy.is_complete(out)


def test_relations_pass_failure_keeps_categories_and_resumes_relations_only(tmp_path):
    """facet 배치는 다 끝났는데 관계 콜에서 죽어도 카테고리는 남고, 재실행하면 관계만 다시."""
    extracted_path = _write_extracted(tmp_path, _persons())
    out = tmp_path / "taxonomy.json"
    calls = []

    def fail_on_relations(prompt):
        calls.append(prompt)
        if "relations" in prompt:
            raise RuntimeError("응답 20kb 초과")
        return json.dumps({"taxonomy": [_cat("Burn-in 신뢰성")]}, ensure_ascii=False)

    with pytest.raises(RuntimeError):
        td_taxonomy.induce(extracted_path, out, fail_on_relations, batch_size=100,
                           attempts=1, sleep=NOOP)

    written = json.loads(out.read_text(encoding="utf-8"))
    assert {c["name"] for c in written} == {"Burn-in 신뢰성"}   # 카테고리는 보존
    assert not td_taxonomy.is_complete(out)                    # 관계 패스가 남아 미완성

    call, seen = _call_seq(json.dumps({"relations": []}, ensure_ascii=False))
    taxo = td_taxonomy.induce(extracted_path, out, call, batch_size=100, sleep=NOOP)
    assert len(seen) == 1                                      # facet 배치는 재호출 안 됨
    assert {c["name"] for c in taxo} == {"Burn-in 신뢰성"}
    assert td_taxonomy.is_complete(out)


def test_extracted_mtime_change_restarts_from_scratch(tmp_path):
    extracted_path = _write_extracted(tmp_path, _persons())
    out = tmp_path / "taxonomy.json"
    calls = []

    def call(prompt):
        calls.append(prompt)
        return json.dumps({"taxonomy": [_cat("Burn-in 신뢰성")]}, ensure_ascii=False)

    td_taxonomy.induce(extracted_path, out, call, batch_size=1, sleep=NOOP)
    assert len(calls) == 3  # facet 배치 2 + 관계 패스 1

    os.utime(extracted_path, (extracted_path.stat().st_mtime + 10,) * 2)  # 상류 변경 시뮬레이션
    calls.clear()
    td_taxonomy.induce(extracted_path, out, call, batch_size=1, sleep=NOOP)
    assert len(calls) == 3  # 스킵 없이 처음부터 다시 호출됨


def test_is_complete_false_without_progress_sidecar(tmp_path):
    out = tmp_path / "taxonomy.json"
    out.write_text("[]", encoding="utf-8")
    assert not td_taxonomy.is_complete(out)
