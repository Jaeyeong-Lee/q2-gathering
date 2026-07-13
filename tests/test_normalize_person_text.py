import csv

import normalize_person_text as norm


def _write_manifest(path, rows):
    fieldnames = ["name", "pjt", "part", "cl_level", "source_file", "page_start",
                  "page_end", "status", "split_filename", "normalized_filename"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    return fieldnames


def test_normalize_all_skips_abnormal_and_already_done(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.md").write_text("A 원문", encoding="utf-8")
    (raw_dir / "b.md").write_text("B 원문", encoding="utf-8")
    rows = [
        {"name": "A", "status": "정상", "split_filename": "a.md", "normalized_filename": ""},
        {"name": "B", "status": "이상", "split_filename": "b.md", "normalized_filename": ""},
        {"name": "C", "status": "정상", "split_filename": "c.md", "normalized_filename": "c.normalized.md"},
    ]
    calls = []

    def call(prompt):
        calls.append(prompt)
        return "# 근원경쟁력\n\n## 핵심 역량\n정리됨"

    failed = norm.normalize_all(rows, raw_dir, call, retries=0)
    assert failed == []
    assert len(calls) == 1  # 이상(B)과 이미 정제됨(C)은 스킵, A만 호출
    assert rows[0]["normalized_filename"] == "a.normalized.md"
    assert (raw_dir / "a.normalized.md").read_text(encoding="utf-8") == "# 근원경쟁력\n\n## 핵심 역량\n정리됨"


def test_normalize_all_retries_only_failed_person(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.md").write_text("A 원문", encoding="utf-8")
    (raw_dir / "b.md").write_text("B 원문", encoding="utf-8")
    rows = [
        {"name": "A", "status": "정상", "split_filename": "a.md", "normalized_filename": ""},
        {"name": "B", "status": "정상", "split_filename": "b.md", "normalized_filename": ""},
    ]
    fail_once = ["A 원문"]

    def flaky(prompt):
        for marker in fail_once:
            if marker in prompt:
                fail_once.remove(marker)
                raise RuntimeError("실패")
        return "정리된 결과"

    failed = norm.normalize_all(rows, raw_dir, flaky, retries=1)
    assert failed == []
    assert rows[0]["normalized_filename"] == "a.normalized.md"
    assert rows[1]["normalized_filename"] == "b.normalized.md"


def test_normalize_all_exhausted_retry_keeps_batch_alive(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "bad.md").write_text("불량 원문", encoding="utf-8")
    (raw_dir / "ok.md").write_text("정상 원문", encoding="utf-8")
    rows = [
        {"name": "bad", "status": "정상", "split_filename": "bad.md", "normalized_filename": ""},
        {"name": "ok", "status": "정상", "split_filename": "ok.md", "normalized_filename": ""},
    ]

    def call(prompt):
        if "불량" in prompt:
            raise RuntimeError("실패")
        return "정리된 결과"

    failed = norm.normalize_all(rows, raw_dir, call, retries=1)
    assert failed == ["bad"]
    assert rows[0]["normalized_filename"] == ""
    assert rows[1]["normalized_filename"] == "ok.normalized.md"


def test_main_updates_manifest_in_place(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.md").write_text("A 원문", encoding="utf-8")
    manifest_path = tmp_path / "manifest.csv"
    _write_manifest(manifest_path, [
        {"name": "A", "pjt": "P", "part": "품질", "cl_level": "CL4", "source_file": "x.md",
         "page_start": "1", "page_end": "2", "status": "정상", "split_filename": "a.md",
         "normalized_filename": ""},
    ])

    def call(prompt):
        return "정리된 결과"

    failed = norm.main(manifest_path=manifest_path, raw_dir=raw_dir, call=call, retries=0)
    assert failed == []

    rows = list(csv.DictReader(open(manifest_path, encoding="utf-8")))
    assert rows[0]["normalized_filename"] == "a.normalized.md"
    assert rows[0]["pjt"] == "P"  # 다른 필드는 그대로 유지
