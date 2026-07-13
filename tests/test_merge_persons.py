import csv
import json

import merge_persons as merge


def _write_manifest(path, rows):
    fieldnames = ["name", "pjt", "part", "cl_level", "source_file", "page_start",
                  "page_end", "status", "split_filename", "normalized_filename"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def test_build_persons_skips_unnormalized_and_assigns_sequential_ids(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.normalized.md").write_text("# 근원경쟁력\nA 내용", encoding="utf-8")
    rows = [
        {"name": "A", "pjt": "P1", "part": "품질", "cl_level": "CL4",
         "normalized_filename": "a.normalized.md"},
        {"name": "B", "pjt": "P1", "part": "품질", "cl_level": "CL3",
         "normalized_filename": ""},  # 정제 미완료 → 제외
    ]
    persons, skipped = merge.build_persons(rows, raw_dir)
    assert skipped == ["B"]
    assert persons == [{
        "id": 0, "name": "A", "pjt": "P1", "part": "품질", "cl_level": "CL4",
        "text": "# 근원경쟁력\nA 내용", "tags": [],
    }]


def test_main_writes_persons_json(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.normalized.md").write_text("텍스트 A", encoding="utf-8")
    (raw_dir / "b.normalized.md").write_text("텍스트 B", encoding="utf-8")
    manifest_path = tmp_path / "manifest.csv"
    _write_manifest(manifest_path, [
        {"name": "A", "pjt": "P1", "part": "품질", "cl_level": "CL4", "source_file": "x.md",
         "page_start": "1", "page_end": "2", "status": "정상", "split_filename": "a.md",
         "normalized_filename": "a.normalized.md"},
        {"name": "B", "pjt": "P1", "part": "품질", "cl_level": "CL3", "source_file": "x.md",
         "page_start": "3", "page_end": "4", "status": "정상", "split_filename": "b.md",
         "normalized_filename": "b.normalized.md"},
    ])
    out_path = tmp_path / "persons.json"

    skipped = merge.main(manifest_path=manifest_path, raw_dir=raw_dir, out_path=out_path)
    assert skipped == []

    persons = json.loads(out_path.read_text(encoding="utf-8"))
    assert [p["id"] for p in persons] == [0, 1]
    assert [p["name"] for p in persons] == ["A", "B"]
    assert persons[0]["text"] == "텍스트 A"
    assert persons[0]["tags"] == []
