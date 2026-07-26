from collections import Counter

import td_sources


def test_schema_has_required_fields():
    docs = td_sources.generate(n=60, seed=0)
    assert docs
    for d in docs:
        assert {"name", "cl_level", "pjt", "part", "text"} <= set(d)


def test_all_four_doc_cases_present():
    # 3단준수 / 3단미준수 / 무내용 / CL4서술형 이 모두 나와야 실데이터 이질성을 대변한다
    docs = td_sources.generate(n=200, seed=0)
    cases = {d["case"] for d in docs}
    assert {td_sources.CASE_STD, td_sources.CASE_MESSY,
            td_sources.CASE_EMPTY, td_sources.CASE_CL4} <= cases


def test_pjt_distribution_with_planning_minority():
    docs = td_sources.generate(n=200, seed=0)
    c = Counter(d["pjt"] for d in docs)
    assert set(c) == {"양산기술", "공정기술", "기획운영"}
    # 기획운영은 소수 — 확산도 집계가 조직신호/국소로 갈리도록 일부러 편중
    assert c["기획운영"] < c["양산기술"]
    assert c["기획운영"] < c["공정기술"]


def test_part_is_consistent_with_pjt():
    docs = td_sources.generate(n=200, seed=1)
    for d in docs:
        assert d["part"] in td_sources.PJT_PARTS[d["pjt"]]


def test_cl_levels_spread_over_cl2_3_4():
    docs = td_sources.generate(n=200, seed=0)
    assert {"CL2", "CL3", "CL4"} <= {d["cl_level"] for d in docs}


def test_domain_keywords_appear_in_corpus():
    docs = td_sources.generate(n=100, seed=0)
    blob = " ".join(d["text"] for d in docs)
    assert any(k in blob for k in ("Burn-in", "ATE", "Yield", "STDF", "MBT", "DPPM"))


def test_empty_case_carries_no_domain_signal():
    docs = td_sources.generate(n=300, seed=0)
    empty = [d for d in docs if d["case"] == td_sources.CASE_EMPTY]
    assert empty
    # 무내용은 도메인 과제 서술 없이 선언적("열심히"류)이라 추출이 no-signal로 격리해야 한다
    assert all("열심히" in d["text"] for d in empty)


def test_seed_is_reproducible():
    assert td_sources.generate(n=40, seed=7) == td_sources.generate(n=40, seed=7)


def test_to_sources_strips_introspection_case_field():
    docs = td_sources.generate(n=10, seed=0)
    written = td_sources.to_sources(docs)
    assert all("case" not in d for d in written)  # introspection 필드는 sources.json에 안 나감
    assert all({"name", "cl_level", "pjt", "part", "text"} <= set(d) for d in written)
