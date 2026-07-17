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

# 사람별 mock 추출 응답 — quote는 원문 부분 문자열
EXTRACT_RESPONSES = {
    "김민준": {
        "tasks": [{"text": "용접 비전검사 고도화", "horizon": "단기",
                   "quote": "하반기에는 용접 비전검사 고도화를 하고 싶다"}],
        "capabilities": [{"text": "PLC 제어", "quote": "확보 역량은 PLC 제어 경험이다"}],
    },
    "이서연": {
        "tasks": [{"text": "공정 데이터 기반 예지보전", "horizon": "장기",
                   "quote": "장기적으로 공정 데이터 기반 예지보전 체계를 만들고 싶다"}],
        "capabilities": [{"text": "품질 데이터 분석", "quote": "품질 데이터 분석 업무를 해왔다"}],
    },
    "박도윤": {
        "tasks": [{"text": "딥러닝 외관검사 플랫폼", "horizon": "이상한값",
                   "quote": "딥러닝 기반 외관검사 표준 플랫폼을 구축하려 한다"}],
        "capabilities": [{"text": "데이터 파이프라인 설계", "quote": "데이터 파이프라인 설계 역량을 확보했다"}],
    },
    "최하은": {"tasks": [], "capabilities": []},
}


def mock_call(prompt):
    if "원문:" in prompt:  # 추출 프롬프트
        for name, resp in EXTRACT_RESPONSES.items():
            if name in prompt:
                return json.dumps(resp, ensure_ascii=False)
    return json.dumps({"title": "테스트 군집", "summary": "요지."}, ensure_ascii=False)


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
            assert item["quote"] in text_by_id[person["person_id"]]
            n_quotes += 1
    assert n_quotes > 0


def test_bad_quote_fails_person(tmp_path):
    src = tmp_path / "sources.json"
    src.write_text(json.dumps(SOURCES[:1], ensure_ascii=False))

    def bad_call(prompt):
        return json.dumps({"tasks": [{"text": "x", "horizon": "단기", "quote": "원문에 없는 문장"}],
                           "capabilities": []}, ensure_ascii=False)

    extracted = td.run_extract(src, tmp_path / "e.json", call=bad_call, retries=0, delay=0)
    assert extracted == []  # 인용 검증 실패 → 그 사람 결과 폐기


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


def test_pages_have_name_and_quote(artifacts):
    *_, pages = artifacts
    text = "".join(p.read_text() for p in pages)
    assert "김민준" in text and "이서연" in text
    assert "하반기에는 용접 비전검사 고도화를 하고 싶다" in text
    assert "단기" in text and "장기" in text  # horizon 배지
