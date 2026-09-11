import td_index
import td_query

# 테스트용 주입 embed: 사전으로 벡터를 강제 지정(의미 근접을 통제)
VECS = {
    "STDF 기반 FA 자동화": [1.0, 0.0],
    "표준 테스트 데이터 포맷 상관분석": [0.0, 1.0],   # 질의와 벡터상 가장 가까움(동의 표현)
    "STDF": [0.0, 1.0],                              # 질의 벡터
    "ATE 장비 운영": [1.0, 1.0],
}
def _embed(text):
    return VECS.get(text, [sum(ord(c) for c in text) % 5, 1.0])


def _persons():
    return [
        {"person_id": 1, "name": "김", "cl_level": "CL3", "pjt": "공정기술", "part": "FA",
         "signal_present": True, "capability_have": [], "capability_gap": [], "direction": None,
         "future_task": [{"text": "STDF 기반 FA 자동화", "horizon": "단기", "quotes": ["STDF"]}]},
        {"person_id": 2, "name": "이", "cl_level": "CL2", "pjt": "양산기술", "part": "ATE",
         "signal_present": True, "capability_have": [], "capability_gap": [], "direction": None,
         "future_task": [{"text": "표준 테스트 데이터 포맷 상관분석", "horizon": "장기", "quotes": ["표준"]}]},
        {"person_id": 3, "name": "박", "cl_level": "CL3", "pjt": "양산기술", "part": "ATE",
         "signal_present": True, "capability_have": [], "capability_gap": [], "direction": None,
         "future_task": [{"text": "ATE 장비 운영", "horizon": "단기", "quotes": ["ATE"]}]},
    ]


def _idx():
    return td_index.build(_persons(), _embed)


def test_exact_acronym_not_outranked_by_semantic_neighbor():
    # 질의 "STDF": 벡터상으론 2번(표준…)이 더 가깝지만, 키워드 채널이 1번(STDF 보유)을 끌어올려야
    out = td_query.query(_idx(), _embed, "STDF", top_k=5)
    assert out["results"][0]["person_id"] == 1


def test_semantic_neighbor_still_appears_via_vector_channel():
    out = td_query.query(_idx(), _embed, "STDF", top_k=5)
    pids = [r["person_id"] for r in out["results"]]
    assert 2 in pids  # 표현이 달라도 벡터 채널로 함께 나옴


def test_returns_results_even_when_keyword_channel_empty():
    # 색인 어디에도 없는 토큰 → 키워드 0, 벡터 채널만으로 결과 반환
    out = td_query.query(_idx(), _embed, "존재하지않는용어XYZ", top_k=5)
    assert out["results"]


def test_filters_narrow_results():
    out = td_query.query(_idx(), _embed, None, pjt="양산기술", top_k=10)
    assert {r["person_id"] for r in out["results"]} == {2, 3}


def test_horizon_filter():
    out = td_query.query(_idx(), _embed, None, horizon="장기", top_k=10)
    assert {r["person_id"] for r in out["results"]} == {2}


def test_filter_only_query_without_text():
    out = td_query.query(_idx(), _embed, None, cl_level="CL3", top_k=10)
    assert {r["person_id"] for r in out["results"]} == {1, 3}


def test_distribution_counts_distinct_people():
    out = td_query.query(_idx(), _embed, None, pjt="양산기술", top_k=10)
    assert out["distribution"]["people"] == 2
    assert out["distribution"]["by_cl"].get("CL3") == 1
    assert out["distribution"]["by_cl"].get("CL2") == 1
