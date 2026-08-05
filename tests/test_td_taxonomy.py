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
    # batch_size=1 → 2배치. 2번째 배치 프롬프트에 1번째 카테고리가 실려야(병합 메커니즘)
    responses = [
        json.dumps({"taxonomy": [_cat("Burn-in 신뢰성")]}, ensure_ascii=False),
        json.dumps({"taxonomy": [_cat("Burn-in 신뢰성"), _cat("ATE 운영")]}, ensure_ascii=False),
    ]
    seen = []

    def call(prompt):
        seen.append(prompt)
        return responses[len(seen) - 1]

    taxo = td_taxonomy.induce(_persons(), None, call, batch_size=1, sleep=NOOP)
    assert len(seen) == 2
    assert "Burn-in 신뢰성" in seen[1]  # 기존 taxonomy를 다음 배치에 제시
    assert {c["name"] for c in taxo} == {"Burn-in 신뢰성", "ATE 운영"}  # 중복 없이 병합


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
    taxo_resp = [_cat("AX 기반 자동화"), _cat("Yield 최적화")]
    taxo_resp[1]["relations"] = [{"to": "AX 기반 자동화", "type": "broader"}]
    call = lambda _: json.dumps({"taxonomy": taxo_resp}, ensure_ascii=False)
    taxo = td_taxonomy.induce(_persons(), None, call, sleep=NOOP)
    by_name = {c["name"]: c for c in taxo}
    assert by_name["Yield 최적화"]["relations"] == [{"to": "AX 기반 자동화", "type": "broader"}]


def test_dangling_self_and_bad_type_relations_are_dropped():
    c = _cat("Yield 최적화")
    c["relations"] = [
        {"to": "존재안함", "type": "broader"},       # 댕글링 참조
        {"to": "Yield 최적화", "type": "related"},   # 자기참조
        {"to": "Yield 최적화", "type": "unknown"},   # type 잘못됨(자기참조 아니어도 걸러짐 확인용 이름 재사용)
    ]
    call = lambda _: json.dumps({"taxonomy": [c]}, ensure_ascii=False)
    taxo = td_taxonomy.induce(_persons(), None, call, sleep=NOOP)
    assert taxo[0]["relations"] == []


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
    extracted_path = _write_extracted(tmp_path, _persons())  # 2 facets, batch_size=1 → 2배치
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
    assert progress["total_batches"] == 2
    assert not td_taxonomy.is_complete(out)

    seen = []

    def succeed(prompt):
        seen.append(prompt)
        return json.dumps({"taxonomy": [_cat("Burn-in 신뢰성"), _cat("ATE 운영")]}, ensure_ascii=False)

    taxo = td_taxonomy.induce(extracted_path, out, succeed, batch_size=1, sleep=NOOP)
    assert len(seen) == 1  # 배치 1은 재호출 안 됨(스킵), 배치 2만
    assert {c["name"] for c in taxo} == {"Burn-in 신뢰성", "ATE 운영"}
    assert td_taxonomy.is_complete(out)


def test_extracted_mtime_change_restarts_from_scratch(tmp_path):
    extracted_path = _write_extracted(tmp_path, _persons())
    out = tmp_path / "taxonomy.json"
    calls = []

    def call(prompt):
        calls.append(prompt)
        return json.dumps({"taxonomy": [_cat("Burn-in 신뢰성")]}, ensure_ascii=False)

    td_taxonomy.induce(extracted_path, out, call, batch_size=1, sleep=NOOP)
    assert len(calls) == 2  # 2배치 전부 호출됨

    os.utime(extracted_path, (extracted_path.stat().st_mtime + 10,) * 2)  # 상류 변경 시뮬레이션
    calls.clear()
    td_taxonomy.induce(extracted_path, out, call, batch_size=1, sleep=NOOP)
    assert len(calls) == 2  # 스킵 없이 처음부터 다시 호출됨


def test_is_complete_false_without_progress_sidecar(tmp_path):
    out = tmp_path / "taxonomy.json"
    out.write_text("[]", encoding="utf-8")
    assert not td_taxonomy.is_complete(out)
