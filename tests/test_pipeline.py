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
        assert set(p) == {"id", "name", "pjt", "cl_level", "text", "tags"}
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

    assert f"var EGO_N = {config.EGO_DISPLAY_N};" in html
    assert f'max="{config.TOPN_MAX}"' in html
    neighbors = json.loads((data_dir / "neighbors.json").read_text())
    assert all(len(v) == config.K for v in neighbors.values())
