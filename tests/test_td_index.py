import td_index

# 결정적 가짜 embed: 문자 코드 합 기반 2차원 벡터 (테스트용, 실제 의미 없음)
def _embed(text):
    s = sum(ord(c) for c in text)
    return [s % 7, (s // 7) % 7]


def _persons():
    return [
        {"person_id": 1, "name": "김철수", "cl_level": "CL3", "pjt": "공정기술", "part": "고장분석(FA)",
         "signal_present": True,
         "future_task": [{"text": "STDF 기반 FA 자동화", "horizon": "단기", "quotes": ["STDF 기반"]}],
         "capability_have": [], "capability_gap": [{"text": "데이터 분석 역량", "quotes": ["데이터 분석"]}],
         "direction": None},
        {"person_id": 2, "name": "이영희", "cl_level": "CL2", "pjt": "양산기술", "part": "ATE운영",
         "signal_present": False,
         "future_task": [], "capability_have": [], "capability_gap": [], "direction": None},
    ]


def test_person_fans_out_into_one_doc_per_facet():
    idx = td_index.build(_persons(), _embed)
    # 1번: future_task 1 + capability_gap 1 = 2개, 2번(무신호): 0개
    docs = idx.all()
    assert len(docs) == 2


def test_no_signal_person_not_indexed():
    idx = td_index.build(_persons(), _embed)
    assert all(d["person_id"] == 1 for d in idx.all())


def test_each_doc_carries_axis_horizon_and_person_meta():
    idx = td_index.build(_persons(), _embed)
    d = next(x for x in idx.all() if x["axis"] == "future_task")
    assert d["horizon"] == "단기"
    assert d["pjt"] == "공정기술" and d["cl_level"] == "CL3" and d["name"] == "김철수"
    assert d["part"] == "고장분석(FA)"


def test_docs_have_embeddings_from_injected_embed():
    idx = td_index.build(_persons(), _embed)
    d = idx.all()[0]
    assert d["vec"] == _embed(d["text"])


def test_inmemory_backend_holds_docs_without_es():
    idx = td_index.build(_persons(), _embed)
    # 백엔드는 순수 인메모리 — 외부 의존 없이 색인 문서를 보관·열람
    assert isinstance(idx.all(), list) and idx.count() == 2
