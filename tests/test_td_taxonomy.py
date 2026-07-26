import json

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
