import json

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
