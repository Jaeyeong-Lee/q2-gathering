import json
import random

import build
import config
import generate_dummy
import similarity


def test_cosine_known_pairs():
    # cos([1,0],[0,1])=0, cos([1,0],[1,1])=1/√2≈0.7071 — 손으로 구한 값
    emb = {0: [1.0, 0.0], 1: [0.0, 1.0], 2: [1.0, 1.0]}
    nb = similarity.top_k_neighbors(emb)
    sims = {e["id"]: e["similarity"] for e in nb["0"]}
    assert sims[1] == 0.0
    assert sims[2] == 0.7071


def test_top_k_sorted_self_excluded():
    rng = random.Random(0)
    emb = {i: [rng.gauss(0, 1) for _ in range(8)] for i in range(40)}
    nb = similarity.top_k_neighbors(emb, k=5)
    assert set(nb) == {str(i) for i in emb}
    for id_str, entries in nb.items():
        assert len(entries) == 5
        entry_ids = [e["id"] for e in entries]
        assert int(id_str) not in entry_ids
        assert len(set(entry_ids)) == len(entry_ids)
        sims = [e["similarity"] for e in entries]
        assert sims == sorted(sims, reverse=True)
        for e in entries:
            assert set(e) == {"id", "similarity"}


def test_dummy_vectors_through_build(tmp_path):
    # 더미 벡터 → similarity.main → neighbors.json 교체 → 001 빌드 조립까지 관통
    data_dir = tmp_path / "data"
    generate_dummy.main(out_dir=data_dir)
    persons = json.loads((data_dir / "persons.json").read_text())

    rng = random.Random(1)
    emb = {str(p["id"]): [rng.gauss(0, 1) for _ in range(16)] for p in persons}
    emb_path = tmp_path / "embeddings.json"
    emb_path.write_text(json.dumps(emb))

    out = similarity.main(emb_path, out_path=data_dir / "neighbors.json")
    neighbors = json.loads(out.read_text())
    assert set(neighbors) == {str(p["id"]) for p in persons}
    valid_ids = {p["id"] for p in persons}
    for entries in neighbors.values():
        assert len(entries) == config.K
        assert {e["id"] for e in entries} <= valid_ids  # 001과 같은 int id

    html = build.build(data_dir=data_dir, out_path=tmp_path / "archive.html").read_text()
    assert "__DATA__" not in html
