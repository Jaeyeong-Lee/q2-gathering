import sqlite3

import normalize_person_text as norm

COLUMNS = ["seq", "name", "pjt", "part", "cl_level", "source_file", "page_start",
           "page_end", "status", "split_filename", "normalized_filename"]


def _seed_roster(path, rows):
    conn = sqlite3.connect(path)
    conn.execute(f"CREATE TABLE roster ({', '.join(COLUMNS)}, PRIMARY KEY (seq))")
    conn.executemany(
        f"INSERT INTO roster ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * len(COLUMNS))})",
        [[r.get(c) for c in COLUMNS] for r in rows],
    )
    conn.commit()
    conn.close()


def test_normalize_all_skips_abnormal_and_already_done(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.md").write_text("A 원문", encoding="utf-8")
    (raw_dir / "b.md").write_text("B 원문", encoding="utf-8")
    rows = [
        {"seq": 1, "name": "A", "cl_level": "CL3", "status": "정상", "split_filename": "a.md", "normalized_filename": ""},
        {"seq": 2, "name": "B", "cl_level": "CL3", "status": "이상", "split_filename": "b.md", "normalized_filename": ""},
        {"seq": 3, "name": "C", "cl_level": "CL3", "status": "정상", "split_filename": "c.md", "normalized_filename": "c.normalized.md"},
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
        {"seq": 1, "name": "A", "cl_level": "CL3", "status": "정상", "split_filename": "a.md", "normalized_filename": ""},
        {"seq": 2, "name": "B", "cl_level": "CL3", "status": "정상", "split_filename": "b.md", "normalized_filename": ""},
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
        {"seq": 1, "name": "bad", "cl_level": "CL3", "status": "정상", "split_filename": "bad.md", "normalized_filename": ""},
        {"seq": 2, "name": "ok", "cl_level": "CL3", "status": "정상", "split_filename": "ok.md", "normalized_filename": ""},
    ]

    def call(prompt):
        if "불량" in prompt:
            raise RuntimeError("실패")
        return "정리된 결과"

    failed = norm.normalize_all(rows, raw_dir, call, retries=1)
    assert failed == [1]          # 실명이 아니라 seq — 로그·반환값에 이름을 안 싣는다
    assert rows[0]["normalized_filename"] == ""
    assert rows[1]["normalized_filename"] == "ok.normalized.md"


def test_normalize_all_picks_prompt_by_cl_level(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.md").write_text("A 원문", encoding="utf-8")
    (raw_dir / "b.md").write_text("B 원문", encoding="utf-8")
    monkeypatch.setattr(norm, "PROMPTS", {"CL2": "주니어용: {raw}", "CL4": "시니어용: {raw}"})
    rows = [
        {"seq": 1, "name": "A", "cl_level": "CL2", "status": "정상", "split_filename": "a.md", "normalized_filename": ""},
        {"seq": 2, "name": "B", "cl_level": "CL4", "status": "정상", "split_filename": "b.md", "normalized_filename": ""},
    ]
    prompts = []

    def call(prompt):
        prompts.append(prompt)
        return "정리된 결과"

    failed = norm.normalize_all(rows, raw_dir, call, retries=0, delay=0)
    assert failed == []
    assert prompts == ["주니어용: A 원문", "시니어용: B 원문"]


def test_normalize_all_unknown_cl_level_raises(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.md").write_text("A 원문", encoding="utf-8")
    monkeypatch.setattr(norm, "PROMPTS", {"CL2": "주니어용: {raw}"})
    rows = [
        {"seq": 1, "name": "A", "cl_level": "CL9", "status": "정상", "split_filename": "a.md", "normalized_filename": ""},
    ]
    try:
        norm.normalize_all(rows, raw_dir, lambda p: "결과", retries=0, delay=0)
        assert False, "미등록 cl_level이면 즉시 KeyError가 나야 함"
    except KeyError:
        pass


def test_main_commits_progress_even_if_crashed_midway(tmp_path, monkeypatch):
    # 2번째 사람에서 미등록 cl_level(KeyError)로 죽어도, 1번째 사람의 정제 기록은 DB에 남아야 함
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.md").write_text("A 원문", encoding="utf-8")
    (raw_dir / "b.md").write_text("B 원문", encoding="utf-8")
    monkeypatch.setattr(norm, "PROMPTS", {"CL2": "{raw}"})
    db_path = tmp_path / "roster.db"
    _seed_roster(db_path, [
        {"seq": 1, "name": "A", "cl_level": "CL2", "status": "정상",
         "split_filename": "a.md", "normalized_filename": ""},
        {"seq": 2, "name": "B", "cl_level": "CL9", "status": "정상",
         "split_filename": "b.md", "normalized_filename": ""},
    ])

    try:
        norm.main(db_path=db_path, raw_dir=raw_dir, call=lambda p: "정리된 결과", retries=0, delay=0)
        assert False, "미등록 cl_level이면 KeyError가 전파되어야 함"
    except KeyError:
        pass

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = {r["name"]: dict(r) for r in conn.execute("SELECT * FROM roster")}
    conn.close()
    assert rows["A"]["normalized_filename"] == "a.normalized.md"  # 죽기 전 진행분 보존
    assert not rows["B"]["normalized_filename"]  # 재실행 시 B만 다시 대상


def test_main_updates_manifest_in_place(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.md").write_text("A 원문", encoding="utf-8")
    db_path = tmp_path / "roster.db"
    _seed_roster(db_path, [
        {"seq": 1, "name": "A", "pjt": "P", "part": "품질", "cl_level": "CL4", "source_file": "x.md",
         "page_start": 1, "page_end": 2, "status": "정상", "split_filename": "a.md",
         "normalized_filename": ""},
    ])

    def call(prompt):
        return "정리된 결과"

    failed = norm.main(db_path=db_path, raw_dir=raw_dir, call=call, retries=0)
    assert failed == []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM roster")]
    conn.close()
    assert rows[0]["normalized_filename"] == "a.normalized.md"
    assert rows[0]["pjt"] == "P"  # 다른 필드는 그대로 유지
