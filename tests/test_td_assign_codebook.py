import json

import td_assign

NOOP = lambda _: None

CODEBOOK = [
    {"name": "Burn-in 신뢰성", "definition": "번인 신뢰성", "inclusion": "MBT/BIB 관련",
     "exclusion": "ATE 장비 운영은 제외"},
    {"name": "ATE 운영", "definition": "장비 운영", "inclusion": "Advantest/Teradyne"},
]


def _persons(item):
    return [{"person_id": 1, "signal_present": True, "future_task": [item],
             "capability_have": [], "capability_gap": [], "direction": None}]


FT = {"text": "MBT Burn-in 신뢰성을 강화한다", "horizon": "장기", "quotes": ["MBT Burn-in"]}


def test_assign_works_against_codebook():
    call = lambda _: json.dumps({"category": "Burn-in 신뢰성", "quote": "MBT Burn-in"}, ensure_ascii=False)
    out = td_assign.assign(_persons(FT), CODEBOOK, None, call, sleep=NOOP)
    assert out["assignments"][0]["category"] == "Burn-in 신뢰성"


def test_exclusion_appears_in_prompt_when_present():
    seen = []

    def call(prompt):
        seen.append(prompt)
        return json.dumps({"category": "Burn-in 신뢰성", "quote": "MBT Burn-in"}, ensure_ascii=False)

    td_assign.assign(_persons(FT), CODEBOOK, None, call, sleep=NOOP)
    assert "ATE 장비 운영은 제외" in seen[0]  # exclusion이 배정 프롬프트에 실린다


def test_no_exclusion_still_works_backward_compatible():
    # exclusion 없는 taxonomy 형태도 그대로 동작 (하위호환)
    taxo = [{"name": "ATE 운영", "definition": "d"}]
    call = lambda _: json.dumps({"category": "ATE 운영", "quote": "ATE"}, ensure_ascii=False)
    item = {"text": "ATE를 운영한다", "horizon": "단기", "quotes": ["ATE"]}
    out = td_assign.assign(_persons(item), taxo, None, call, sleep=NOOP)
    assert out["assignments"][0]["category"] == "ATE 운영"


# --- 기타 수집 ---

def _assigns(*cats):
    return [{"person_id": i, "axis": "future_task", "text": "t", "category": c, "quote": "q"}
            for i, c in enumerate(cats, 1)]


def test_collect_other_ratio_and_items():
    res = td_assign.collect_other(_assigns("A", "Other", "B", "Other"))
    assert res["count"] == 2
    assert abs(res["ratio"] - 0.5) < 1e-9
    assert all(x["category"] == "Other" for x in res["items"])


def test_collect_other_warns_when_over_threshold():
    over = td_assign.collect_other(_assigns("Other", "Other", "A"), threshold=0.2)
    under = td_assign.collect_other(_assigns("A", "B", "C"), threshold=0.2)
    assert over["warning"] is True and under["warning"] is False
