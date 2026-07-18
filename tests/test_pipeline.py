import json

import build
import config
import generate_dummy


def test_persons_schema():
    data = generate_dummy.generate(n=150, seed=1)
    persons = data["persons"]
    assert len(persons) == 150
    assert len({p["id"] for p in persons}) == 150
    assert len({p["name"] for p in persons}) == 150
    for p in persons:
        assert set(p) == {"id", "name", "pjt", "cl_level", "text", "normalized_text", "tags"}
        assert p["cl_level"] in {"CL2", "CL3", "CL4"}
        assert isinstance(p["tags"], list) and p["tags"]
        assert p["text"].strip()


def test_neighbors_top_k():
    data = generate_dummy.generate(n=150, seed=1)
    neighbors = data["neighbors"]
    valid_ids = {p["id"] for p in data["persons"]}
    assert set(neighbors) == {str(i) for i in valid_ids}
    for id_str, entries in neighbors.items():
        assert len(entries) == config.K
        sims = [e["similarity"] for e in entries]
        assert sims == sorted(sims, reverse=True)
        assert all(0 < s < 1 for s in sims)
        entry_ids = [e["id"] for e in entries]
        assert int(id_str) not in entry_ids
        assert len(set(entry_ids)) == len(entry_ids)
        assert set(entry_ids) <= valid_ids


def test_freq_per_person():
    data = generate_dummy.generate(n=150, seed=1)
    freq = data["freq"]
    assert set(freq) == {str(p["id"]) for p in data["persons"]}
    for counts in freq.values():
        assert counts, "빈 빈도 딕셔너리 금지"
        for word, count in counts.items():
            assert word.strip()
            assert isinstance(count, int) and count >= 1


def test_build_inlines_data_into_single_html(tmp_path):
    data_dir = tmp_path / "data"
    generate_dummy.main(out_dir=data_dir)
    for f in ("persons.json", "neighbors.json", "freq.json"):
        assert (data_dir / f).exists()

    out = build.build(data_dir=data_dir, out_path=tmp_path / "dist" / "archive.html")
    html = out.read_text()

    persons = json.loads((data_dir / "persons.json").read_text())
    assert persons[0]["name"] in html
    assert "__DATA__" not in html and "__FREQ__" not in html
    import re
    assert not re.search(r'<(script|link)\b[^>]*?\b(src|href)\s*=\s*["\']https?://', html, re.IGNORECASE)


def test_build_injects_config_values(tmp_path):
    data_dir = generate_dummy.main(out_dir=tmp_path / "data")
    html = build.build(data_dir=data_dir, out_path=tmp_path / "archive.html").read_text()

    assert f'max="{config.TOPN_MAX}"' in html
    neighbors = json.loads((data_dir / "neighbors.json").read_text())
    assert all(len(v) == config.K for v in neighbors.values())


# ---- 과제 문장 그래프 (#10) ----

TASK_VECTORS = [
    {"person_id": 1, "name": "김민준", "cl_level": "CL3", "horizon": "단기",
     "text": "용접 비전검사 고도화", "quotes": ["용접 비전검사 고도화를 하고 싶다"], "vec": [1.0, 0.1]},
    {"person_id": 3, "name": "박도윤", "cl_level": "CL4", "horizon": "불명",
     "text": "딥러닝 외관검사 플랫폼", "quotes": ["외관검사 표준 플랫폼을 구축하려 한다"], "vec": [0.9, 0.2]},
    {"person_id": 2, "name": "이서연", "cl_level": "CL2", "horizon": "장기",
     "text": "공정 데이터 예지보전", "quotes": ["예지보전 체계를 만들고 싶다"], "vec": [0.1, 1.0]},
    {"person_id": 5, "name": "정하은", "cl_level": "CL3", "horizon": "장기",
     "text": "품질 데이터 분석 플랫폼", "quotes": ["품질 데이터 분석을 확장하고 싶다"], "vec": [-0.4, 0.7]},
    {"person_id": 4, "name": "조유나", "cl_level": "CL2", "horizon": "단기",
     "text": "설비 데이터 이상감지", "quotes": ["설비 이상감지 체계를 만들고 싶다"], "vec": [0.2, 0.95]},
]


def _strip_vec(v):
    return {k: x for k, x in v.items() if k != "vec"}


TASK_CLUSTERS = [
    {"cluster_id": 0, "items": [_strip_vec(TASK_VECTORS[0]), _strip_vec(TASK_VECTORS[1])]},
    {"cluster_id": 1, "items": [_strip_vec(TASK_VECTORS[2]), _strip_vec(TASK_VECTORS[3]),
                                _strip_vec(TASK_VECTORS[4])]},
]


def _write_task_data(data_dir, wiki_dir):
    td = data_dir / "task_discovery"
    td.mkdir(parents=True)
    (td / "task_vectors.json").write_text(json.dumps(TASK_VECTORS, ensure_ascii=False))
    (td / "clusters.json").write_text(json.dumps(TASK_CLUSTERS, ensure_ascii=False))
    wiki_dir.mkdir(parents=True)
    (wiki_dir / "cluster-00.md").write_text("# 지능형 검사 체계\n\n요지.\n")


def test_build_tasks_payload(tmp_path):
    wiki = tmp_path / "wiki"
    _write_task_data(tmp_path / "data", wiki)
    payload = build.build_tasks(TASK_VECTORS, TASK_CLUSTERS, wiki)

    assert [n["cluster"] for n in payload["nodes"]] == [0, 0, 1, 1, 1]
    for n in payload["nodes"]:
        assert {"id", "person_id", "name", "cl", "horizon", "text", "quotes", "outlier"} <= set(n)
    # 엣지 재료: 노드별 유사도 top-K, 내림차순
    assert set(payload["neighbors"]) == {str(n["id"]) for n in payload["nodes"]}
    for entries in payload["neighbors"].values():
        ws = [e["w"] for e in entries]
        assert ws == sorted(ws, reverse=True)
    # 군집 메타: 위키 제목이 있으면 그걸, 없으면 기본 제목 + 위키 링크
    titles = {c["id"]: c["title"] for c in payload["clusters"]}
    assert titles[0] == "지능형 검사 체계" and titles[1]
    assert all(c["page"].startswith("wiki/cluster-") for c in payload["clusters"])
    # 외톨이: 군집 중심에서 먼 문장 표시 — 정하은 벡터가 군집 1 중심에서 가장 멀다
    by_name = {n["name"]: n for n in payload["nodes"]}
    assert by_name["정하은"]["outlier"] and not by_name["김민준"]["outlier"]
    # 빈 평면(run_cluster가 "[]"를 쓴 세트)이면 None → 호출부가 토글을 숨긴다
    assert build.build_tasks([], [], wiki) is None


def test_build_injects_tasks_or_null(tmp_path):
    data_dir = generate_dummy.main(out_dir=tmp_path / "data")
    out = tmp_path / "dist" / "archive.html"

    html = build.build(data_dir=data_dir, out_path=out).read_text()
    assert "__TASKS__" not in html  # 데이터 없으면 null 주입 → 토글 숨김

    _write_task_data(data_dir, out.parent / "wiki")
    html = build.build(data_dir=data_dir, out_path=out).read_text()
    assert "__TASKS__" not in html
    assert "용접 비전검사 고도화" in html and "지능형 검사 체계" in html
    assert "#view=tasks" in html  # 딥링크 패턴 존재
