import json
import os

import pytest

import td_assign

NOOP = lambda _: None

TAXO = [{"name": "Burn-in 신뢰성", "definition": "d", "inclusion_criteria": "i"},
        {"name": "ATE 운영", "definition": "d", "inclusion_criteria": "i"}]


def _persons(*items):
    return [{"person_id": 1, "signal_present": True, "future_task": list(items),
             "capability_have": [], "capability_gap": [], "direction": None}]


FT = {"text": "MBT Burn-in 신뢰성을 강화한다", "horizon": "장기", "quotes": ["MBT Burn-in"]}


def _resp(category, quote):
    return lambda _: json.dumps({"category": category, "quote": quote}, ensure_ascii=False)


def test_facet_assigned_to_valid_category_with_grounded_quote():
    out = td_assign.assign(_persons(FT), TAXO, None, _resp("Burn-in 신뢰성", "MBT Burn-in"), sleep=NOOP)
    assert len(out["assignments"]) == 1
    a = out["assignments"][0]
    assert a["category"] == "Burn-in 신뢰성" and a["person_id"] == 1 and a["axis"] == "future_task"


def test_no_matching_category_goes_to_other():
    out = td_assign.assign(_persons(FT), TAXO, None, _resp("Other", "MBT Burn-in"), sleep=NOOP)
    assert out["assignments"][0]["category"] == td_assign.OTHER


def test_category_not_in_taxonomy_is_rejected_and_dropped():
    out = td_assign.assign(_persons(FT), TAXO, None, _resp("존재하지않는범주", "MBT Burn-in"),
                           tries=1, sleep=NOOP)
    assert out["assignments"] == [] and out["dropped"]


def test_ungrounded_quote_is_dropped():
    out = td_assign.assign(_persons(FT), TAXO, None, _resp("Burn-in 신뢰성", "원문에 없는 인용"),
                           tries=1, sleep=NOOP)
    assert out["assignments"] == [] and out["dropped"]


def test_valid_survives_when_sibling_dropped():
    ft2 = {"text": "ATE를 운영한다", "horizon": "단기", "quotes": ["ATE 운영"]}

    def call(prompt):
        # 첫 항목엔 유효, 둘째 항목엔 환각 범주
        if "ATE를 운영한다" in prompt:
            return json.dumps({"category": "없는범주", "quote": "ATE 운영"}, ensure_ascii=False)
        return json.dumps({"category": "Burn-in 신뢰성", "quote": "MBT Burn-in"}, ensure_ascii=False)

    out = td_assign.assign(_persons(FT, ft2), TAXO, None, call, tries=1, sleep=NOOP)
    assert len(out["assignments"]) == 1 and len(out["dropped"]) == 1


def test_writes_assignments_file(tmp_path):
    out_path = tmp_path / "assignments.json"
    td_assign.assign(_persons(FT), TAXO, out_path, _resp("Burn-in 신뢰성", "MBT Burn-in"), sleep=NOOP)
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written[0]["category"] == "Burn-in 신뢰성"


def _write(tmp_path, name, data):
    path = tmp_path / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


FT2 = {"text": "ATE를 운영한다", "horizon": "단기", "quotes": ["ATE 운영"]}


def test_crash_midway_persists_progress_and_resumes_without_recalling_done_items(tmp_path):
    extracted_path = _write(tmp_path, "extracted.json", _persons(FT, FT2))
    taxo_path = _write(tmp_path, "taxonomy.json", TAXO)
    out = tmp_path / "assignments.json"
    calls = []

    def fail_from_second_call(prompt):
        calls.append(prompt)
        if len(calls) >= 2:
            raise RuntimeError("내부망 에러")
        return json.dumps({"category": "Burn-in 신뢰성", "quote": "MBT Burn-in"}, ensure_ascii=False)

    with pytest.raises(RuntimeError):
        td_assign.assign(extracted_path, taxo_path, out, fail_from_second_call,
                         tries=1, attempts=1, sleep=NOOP)

    written = json.loads(out.read_text(encoding="utf-8"))
    assert len(written) == 1 and written[0]["category"] == "Burn-in 신뢰성"
    progress = json.loads((tmp_path / "assignments.progress.json").read_text(encoding="utf-8"))
    assert progress["processed"] == 1
    assert progress["total_facets"] == 2
    assert not td_assign.is_complete(out)

    seen = []

    def succeed(prompt):
        seen.append(prompt)
        return json.dumps({"category": "ATE 운영", "quote": "ATE 운영"}, ensure_ascii=False)

    res = td_assign.assign(extracted_path, taxo_path, out, succeed, sleep=NOOP)
    assert len(seen) == 1  # 이미 처리된 1번 항목은 재호출 안 됨, 2번만
    assert len(res["assignments"]) == 2
    assert td_assign.is_complete(out)


def test_resume_handles_duplicate_text_facets_by_position_not_content(tmp_path):
    dup = {"text": "동일 텍스트 항목", "horizon": "단기", "quotes": ["동일"]}
    extracted_path = _write(tmp_path, "extracted.json", _persons(dup, dup))  # 텍스트 완전 동일한 두 항목
    taxo_path = _write(tmp_path, "taxonomy.json", TAXO)
    out = tmp_path / "assignments.json"
    calls = []

    def fail_from_second_call(prompt):
        calls.append(prompt)
        if len(calls) >= 2:
            raise RuntimeError("실패")
        return json.dumps({"category": "Burn-in 신뢰성", "quote": "동일"}, ensure_ascii=False)

    with pytest.raises(RuntimeError):
        td_assign.assign(extracted_path, taxo_path, out, fail_from_second_call,
                         tries=1, attempts=1, sleep=NOOP)
    assert len(json.loads(out.read_text(encoding="utf-8"))) == 1

    seen = []

    def succeed(prompt):
        seen.append(prompt)
        return json.dumps({"category": "ATE 운영", "quote": "동일"}, ensure_ascii=False)

    res = td_assign.assign(extracted_path, taxo_path, out, succeed, sleep=NOOP)
    assert len(seen) == 1  # 텍스트가 같아도 위치상 두 번째 항목만 재호출됨
    assert len(res["assignments"]) == 2


def test_extracted_mtime_change_restarts_assign_from_scratch(tmp_path):
    extracted_path = _write(tmp_path, "extracted.json", _persons(FT, FT2))
    taxo_path = _write(tmp_path, "taxonomy.json", TAXO)
    out = tmp_path / "assignments.json"
    calls = []

    def call(prompt):
        calls.append(prompt)
        quote = "ATE 운영" if "ATE를 운영한다" in prompt else "MBT Burn-in"
        return json.dumps({"category": "Burn-in 신뢰성", "quote": quote}, ensure_ascii=False)

    td_assign.assign(extracted_path, taxo_path, out, call, sleep=NOOP)
    assert len(calls) == 2

    os.utime(extracted_path, (extracted_path.stat().st_mtime + 10,) * 2)  # 상류 변경 시뮬레이션
    calls.clear()
    td_assign.assign(extracted_path, taxo_path, out, call, sleep=NOOP)
    assert len(calls) == 2  # 스킵 없이 처음부터 다시


def test_taxonomy_mtime_change_restarts_assign_from_scratch(tmp_path):
    extracted_path = _write(tmp_path, "extracted.json", _persons(FT, FT2))
    taxo_path = _write(tmp_path, "taxonomy.json", TAXO)
    out = tmp_path / "assignments.json"
    calls = []

    def call(prompt):
        calls.append(prompt)
        quote = "ATE 운영" if "ATE를 운영한다" in prompt else "MBT Burn-in"
        return json.dumps({"category": "Burn-in 신뢰성", "quote": quote}, ensure_ascii=False)

    td_assign.assign(extracted_path, taxo_path, out, call, sleep=NOOP)
    assert len(calls) == 2

    os.utime(taxo_path, (taxo_path.stat().st_mtime + 10,) * 2)  # 코드북/taxonomy 편집 시뮬레이션
    calls.clear()
    td_assign.assign(extracted_path, taxo_path, out, call, sleep=NOOP)
    assert len(calls) == 2  # 스킵 없이 처음부터 다시


def test_is_complete_false_without_progress_sidecar(tmp_path):
    out = tmp_path / "assignments.json"
    out.write_text("[]", encoding="utf-8")
    assert not td_assign.is_complete(out)
