"""task-discovery 트레이서 테스트 (#2) — 추출→임베딩→군집→md 세로 관통, LLM 전부 mock."""
import json

import pytest

import task_discovery as td

SOURCES = [
    {
        "id": 1, "name": "김민준", "cl_level": "CL3",
        "text": "상반기에는 용접 라인 자동화를 진행했다. 하반기에는 용접 비전검사 고도화를 하고 싶다. 확보 역량은 PLC 제어 경험이다.",
    },
    {
        "id": 2, "name": "이서연", "cl_level": "CL2",
        "text": "커리어 회고: 품질 데이터 분석 업무를 해왔다. 장기적으로 공정 데이터 기반 예지보전 체계를 만들고 싶다.",
    },
    {
        "id": 3, "name": "박도윤", "cl_level": "CL4",
        "text": "미래에는 딥러닝 기반 외관검사 표준 플랫폼을 구축하려 한다. 데이터 파이프라인 설계 역량을 확보했다.",
    },
    {
        "id": 4, "name": "최하은", "cl_level": "CL3",
        "text": "그동안 열심히 일했습니다. 앞으로도 잘 부탁드립니다.",  # 템플릿 미준수
    },
]

# 사람별 mock 추출 응답 — quotes[] 각각이 원문 부분 문자열 (#8 복수화)
EXTRACT_RESPONSES = {
    "김민준": {
        "tasks": [{"text": "용접 비전검사 고도화", "horizon": "단기",
                   "quotes": ["하반기에는 용접 비전검사 고도화를 하고 싶다"]}],
        "capabilities": [{"text": "PLC 제어", "quotes": ["확보 역량은 PLC 제어 경험이다"]}],
    },
    "이서연": {
        "tasks": [{"text": "공정 데이터 기반 예지보전", "horizon": "장기",
                   "quotes": ["장기적으로 공정 데이터 기반 예지보전 체계를 만들고 싶다"]}],
        "capabilities": [{"text": "품질 데이터 분석", "quotes": ["품질 데이터 분석 업무를 해왔다"]}],
    },
    "박도윤": {
        "tasks": [{"text": "딥러닝 외관검사 플랫폼", "horizon": "이상한값",
                   "quotes": ["딥러닝 기반 외관검사 표준 플랫폼을 구축하려 한다"]}],
        "capabilities": [{"text": "데이터 파이프라인 설계", "quotes": ["데이터 파이프라인 설계 역량을 확보했다"]}],
    },
    "최하은": {"tasks": [], "capabilities": []},
}


PAGE_RESPONSE = {
    "title": "테스트 군집", "summary": "요지.",
    "derived": [
        {"text": "비전검사 데이터 표준화", "evidence": [
            {"person_id": 1, "quote": "용접 비전검사 고도화"}]},          # 인용 일치 → 채택
        {"text": "근거 없는 제안", "evidence": [
            {"person_id": 1, "quote": "원문에 없는 문장"}]},              # 인용 불일치 → 폐기
    ],
}


# 총평 mock (#9) — 근거 있는 항목만 살아남아야 한다
OVERVIEW_RESPONSE = {
    "trends": [
        {"text": "검사·데이터 계열로 수렴 중", "evidence": [
            {"person_id": 1, "quote": "용접 비전검사 고도화"}]},        # 대조 성공 → 채택
        {"text": "근거 없는 흐름", "evidence": [
            {"person_id": 2, "quote": "원문에 없는 문장"}]},            # 대조 실패 → 폐기
    ],
    "outliers": [
        {"text": "예지보전은 한 명만 언급", "evidence": [
            {"person_id": 2, "quote": "공정 데이터 기반 예지보전"}]},
    ],
}


def mock_call(prompt):
    if "원문:" in prompt:  # 추출 프롬프트
        for name, resp in EXTRACT_RESPONSES.items():
            if name in prompt:
                return json.dumps(resp, ensure_ascii=False)
    if "군집 요약:" in prompt:  # 총평 프롬프트
        return json.dumps(OVERVIEW_RESPONSE, ensure_ascii=False)
    return json.dumps(PAGE_RESPONSE, ensure_ascii=False)


def mock_embed(text):
    # "용접"/"검사" 계열과 "데이터" 계열이 분리되는 결정적 2차원 벡터
    return [1.0 if ("용접" in text or "검사" in text) else 0.0,
            1.0 if "데이터" in text else 0.0]


@pytest.fixture
def artifacts(tmp_path):
    src = tmp_path / "sources.json"
    src.write_text(json.dumps(SOURCES, ensure_ascii=False))
    extracted = td.run_extract(src, tmp_path / "extracted.json", call=mock_call, delay=0)
    vectors = td.run_embed(tmp_path / "extracted.json", tmp_path / "task_vectors.json", embed=mock_embed)
    clusters = td.run_cluster(tmp_path / "task_vectors.json", tmp_path / "clusters.json", k=2, seed=0)
    pages = td.run_pages(tmp_path / "clusters.json", tmp_path / "pages", call=mock_call)
    return tmp_path, extracted, vectors, clusters, pages


def test_stage_files_created(artifacts):
    tmp_path = artifacts[0]
    for f in ["extracted.json", "task_vectors.json", "clusters.json"]:
        assert (tmp_path / f).exists()
    assert list((tmp_path / "pages").glob("*.md"))


def test_quotes_are_substrings_of_source(artifacts):
    _, extracted, *_ = artifacts
    text_by_id = {s["id"]: s["text"] for s in SOURCES}
    n_quotes = 0
    for person in extracted:
        for item in person["tasks"] + person["capabilities"]:
            for q in item["quotes"]:
                assert q in text_by_id[person["person_id"]]
                n_quotes += 1
    assert n_quotes > 0


def test_quote_matches_across_linebreaks(tmp_path):
    # 원문이 문장 중간에 줄바꿈돼도 줄바꿈 없는 인용은 유효 (실 LLM에서 실제 발생)
    src = tmp_path / "s.json"
    doc = {"id": 9, "name": "김민준", "cl_level": "CL3",
           "text": "확보 역량은 PLC\n제어 경험이다."}
    src.write_text(json.dumps([doc], ensure_ascii=False))

    def call(prompt):
        return json.dumps({"tasks": [], "capabilities": [
            {"text": "PLC 제어", "quotes": ["확보 역량은 PLC 제어 경험이다."]}]}, ensure_ascii=False)

    extracted = td.run_extract(src, tmp_path / "e.json", call=call, retries=0, delay=0)
    assert extracted and extracted[0]["capabilities"]


def test_bad_quote_fails_person(tmp_path):
    src = tmp_path / "sources.json"
    src.write_text(json.dumps(SOURCES[:1], ensure_ascii=False))

    def bad_call(prompt):
        return json.dumps({"tasks": [{"text": "x", "horizon": "단기", "quotes": ["원문에 없는 문장"]}],
                           "capabilities": []}, ensure_ascii=False)

    extracted = td.run_extract(src, tmp_path / "e.json", call=bad_call, retries=0, delay=0)
    assert extracted == []  # 인용 검증 실패 → 그 사람 결과 폐기


def test_scattered_mentions_become_multiple_quotes(tmp_path):
    # verbose 원문: 한 과제의 언급이 흩어져 있으면 quotes 여러 개 — 각각 개별 대조 (#8)
    src = tmp_path / "s.json"
    doc = {"id": 9, "name": "김민준", "cl_level": "CL3",
           "text": "하반기에는 용접 비전검사 개선을 이어가려 한다. 확보 역량은 PLC 제어다.\n"
                   "3. 미래 업무\n장기적으로 용접 비전검사 결과를 표준 플랫폼으로 묶고 싶다."}
    src.write_text(json.dumps([doc], ensure_ascii=False))

    def call(prompt):
        return json.dumps({"tasks": [{
            "text": "용접 비전검사 개선을 이어가고, 장기적으로 결과를 표준 플랫폼으로 통합",
            "horizon": "장기",
            "quotes": ["하반기에는 용접 비전검사 개선을 이어가려 한다",
                       "장기적으로 용접 비전검사 결과를 표준 플랫폼으로 묶고 싶다"]}],
            "capabilities": []}, ensure_ascii=False)

    extracted = td.run_extract(src, tmp_path / "e.json", call=call, retries=0, delay=0)
    assert len(extracted[0]["tasks"][0]["quotes"]) == 2

    def bad_call(prompt):  # 복수 인용 중 하나만 불일치해도 폐기
        return json.dumps({"tasks": [{"text": "x", "horizon": "단기",
                                      "quotes": ["하반기에는 용접 비전검사 개선을 이어가려 한다",
                                                 "원문에 없는 문장"]}],
                           "capabilities": []}, ensure_ascii=False)

    assert td.run_extract(src, tmp_path / "e2.json", call=bad_call, retries=0, delay=0) == []


def test_horizon_normalized(artifacts):
    _, extracted, *_ = artifacts
    horizons = {t["horizon"] for p in extracted for t in p["tasks"]}
    assert horizons <= {"단기", "장기", "불명"}  # "이상한값"은 불명으로


def test_noncompliant_person_yields_empty(artifacts):
    _, extracted, *_ = artifacts
    by_id = {p["person_id"]: p for p in extracted}
    assert by_id[4]["tasks"] == []


def test_cluster_deterministic_and_separates(artifacts):
    tmp_path, _, vectors, clusters, _ = artifacts
    again = td.run_cluster(tmp_path / "task_vectors.json", tmp_path / "clusters2.json", k=2, seed=0)
    assert clusters == again
    # 용접/검사 계열(1,3)과 데이터 계열(2)이 다른 군집
    cid = {item["person_id"]: c["cluster_id"] for c in clusters for item in c["items"]}
    assert cid[1] == cid[3] != cid[2]


def test_cl_split_prompts(tmp_path):
    src = tmp_path / "s.json"
    src.write_text(json.dumps([SOURCES[0], SOURCES[2]], ensure_ascii=False))  # CL3 + CL4
    prompts = []

    def spy_call(prompt):
        prompts.append(prompt)
        return json.dumps({"tasks": [], "capabilities": []})

    td.run_extract(src, tmp_path / "e.json", call=spy_call, delay=0)
    cl3_prompt, cl4_prompt = prompts
    assert cl3_prompt != cl4_prompt
    assert "3단" in cl3_prompt          # CL2/3: 3단 구성 안내
    assert "미래 위주" in cl4_prompt     # CL4: 별도 템플릿 안내


def test_capability_plane_clustered(artifacts):
    tmp_path = artifacts[0]
    vectors = td.run_embed(tmp_path / "extracted.json", tmp_path / "cap_vectors.json",
                           embed=mock_embed, field="capabilities")
    assert vectors and all("person_id" in v and "quotes" in v for v in vectors)
    clusters = td.run_cluster(tmp_path / "cap_vectors.json", tmp_path / "cap_clusters.json", k=2, seed=0)
    assert sum(len(c["items"]) for c in clusters) == len(vectors)


def test_clusters_mix_horizons(artifacts):
    clusters = artifacts[3]
    mixed = [c for c in clusters if len({it["horizon"] for it in c["items"]}) > 1]
    assert mixed  # 단기/불명이 같은 군집에 공존 (지평선으로 쪼개지 않음)


def test_vectors_traceable_to_source(artifacts):
    _, _, vectors, _, _ = artifacts
    text_by_id = {s["id"]: s["text"] for s in SOURCES}
    for v in vectors:
        assert v["quotes"] and all(q in text_by_id[v["person_id"]] for q in v["quotes"])
        assert v["cl_level"] in ("CL2", "CL3", "CL4")  # 그래프 뷰 인용 카드 재료 (#10)


def test_generate_sources_schema_and_templates(tmp_path):
    docs = td.generate_sources(20, seed=1, out_path=tmp_path / "sources.json")
    assert len(docs) == 20 and (tmp_path / "sources.json").exists()
    assert all({"id", "name", "cl_level", "text"} <= set(d) for d in docs)
    cl4 = [d for d in docs if d["cl_level"] == "CL4"]
    cl23 = [d for d in docs if d["cl_level"] in ("CL2", "CL3")]
    assert cl4 and cl23
    # CL2/3은 3단 템플릿, CL4는 별도 템플릿(단 미준수자 제외)
    compliant23 = [d for d in cl23 if "미래 업무" in d["text"]]
    assert compliant23 and all("커리어 회고" in d["text"] for d in compliant23)
    assert any("앞으로의 방향" in d["text"] for d in cl4)
    # 일부 미준수자 존재
    assert any("미래 업무" not in d["text"] and "앞으로의 방향" not in d["text"] for d in docs)


def test_generate_sources_verbose_with_scattered_mentions(tmp_path):
    # 실 pptx 대응 (#8): 문단 단위 verbose 서술 + 한 과제의 언급이 원문 여러 곳에 흩어짐
    docs = td.generate_sources(20, seed=1)
    compliant = [d for d in docs if "미래 업무" in d["text"] or "앞으로의 방향" in d["text"]]
    assert all(len(d["text"]) > 200 for d in compliant)  # 한 줄짜리가 아니다
    for d in compliant:  # 어떤 도메인은 서로 다른 문단에서 두 번 이상 언급된다
        paras = d["text"].split("\n")
        assert any(sum(dom in p for p in paras) >= 2 for dom in td._DOMAINS)


def test_generate_sources_deterministic_and_feeds_extract(tmp_path):
    a = td.generate_sources(238, seed=7, out_path=tmp_path / "a.json")
    b = td.generate_sources(238, seed=7, out_path=tmp_path / "b.json")
    assert a == b
    empty = json.dumps({"tasks": [], "capabilities": []})
    extracted = td.run_extract(tmp_path / "a.json", tmp_path / "e.json", call=lambda p: empty, delay=0)
    assert len(extracted) == 238


def test_derived_suggestions_grounded_or_dropped(artifacts):
    *_, pages = artifacts
    text = "".join(p.read_text() for p in pages)
    assert "비전검사 데이터 표준화" in text      # 근거 있는 제안 채택
    assert "AI 제안" in text                     # 팀원 작성 과제와 구분 표기
    assert "근거 없는 제안" not in text          # 인용 불일치 폐기
    # 채택된 제안에는 근거 실명·인용이 붙는다
    page = next(p.read_text() for p in pages if "비전검사 데이터 표준화" in p.read_text())
    idx = page.index("비전검사 데이터 표준화")
    assert "김민준" in page[idx:] and "용접 비전검사 고도화" in page[idx:]


def test_index_overview_grounded_or_dropped(artifacts):
    # 총평 (#9): index 상단에 큰 흐름 + 소수 의견, 인용 대조 실패 항목은 폐기
    tmp_path = artifacts[0]
    index = (tmp_path / "pages" / "index.md").read_text()
    assert "총평" in index and index.index("총평") < index.index("cluster-")
    assert "검사·데이터 계열로 수렴 중" in index          # 큰 흐름 채택
    assert "예지보전은 한 명만 언급" in index              # 소수 의견 채택
    assert "근거 없는 흐름" not in index                   # 인용 불일치 폐기
    idx = index.index("검사·데이터 계열로 수렴 중")
    assert "김민준" in index[idx:]                          # 근거 실명·인용 표기


def test_overview_is_single_extra_call(artifacts):
    tmp_path, _, _, clusters, _ = artifacts
    prompts = []

    def spy_call(prompt):
        prompts.append(prompt)
        return mock_call(prompt)

    td.run_pages(tmp_path / "clusters.json", tmp_path / "pages2", call=spy_call)
    n_clusters = len([c for c in clusters if c["items"]])
    assert len(prompts) == n_clusters + 1  # 군집당 1콜 + 총평 1콜


def test_index_links_all_cluster_pages(artifacts):
    tmp_path, *_, pages = artifacts
    index = (tmp_path / "pages" / "index.md").read_text()
    cluster_pages = [p for p in pages if p.name != "index.md"]
    assert cluster_pages
    for p in cluster_pages:
        assert p.name in index  # 각 군집 페이지로 링크
    assert "명" in index  # 군집 규모 표기


def generic_call(prompt):
    """임의 원문에서 첫 줄을 인용하는 범용 mock (238명 스케일용)."""
    if "원문:" in prompt:
        first_line = prompt.split("원문:\n", 1)[1].strip().splitlines()[0]
        return json.dumps({"tasks": [{"text": first_line[:20], "horizon": "단기",
                                      "quotes": [first_line]}], "capabilities": []},
                          ensure_ascii=False)
    return json.dumps({"title": "군집", "summary": "요지."}, ensure_ascii=False)


def test_run_all_238_and_cache(tmp_path):
    src = tmp_path / "sources.json"
    td.generate_sources(238, seed=3, out_path=src)
    calls = {"extract": 0, "embed": 0}

    def counting_call(prompt):
        if "원문:" in prompt:
            calls["extract"] += 1
        return generic_call(prompt)

    def counting_embed(text):
        calls["embed"] += 1
        return [hash(text) % 97, hash(text[::-1]) % 97]

    pages = td.run_all(src, tmp_path, tmp_path / "wiki", call=counting_call,
                       embed=counting_embed, k=8, delay=0)
    assert calls["extract"] == 238 and calls["embed"] > 0
    assert (tmp_path / "wiki" / "index.md").exists() and len(pages) > 1

    calls["extract"] = calls["embed"] = 0
    td.run_all(src, tmp_path, tmp_path / "wiki", call=counting_call,
               embed=counting_embed, k=5, delay=0)  # k 변경 → 군집·페이지만 재실행
    assert calls["extract"] == 0 and calls["embed"] == 0  # 추출·임베딩은 캐시


def test_pages_have_name_and_quote(artifacts):
    *_, pages = artifacts
    text = "".join(p.read_text() for p in pages)
    assert "김민준" in text and "이서연" in text
    assert "하반기에는 용접 비전검사 고도화를 하고 싶다" in text
    assert "단기" in text and "장기" in text  # horizon 배지
