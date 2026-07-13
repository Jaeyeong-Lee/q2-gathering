import sqlite3

import split_md_by_person as split_md

STATE_FIELDS = ["page_start", "page_end", "status", "split_filename", "normalized_filename"]


def _seed_roster(db_path, rows):
    """테스트용 roster 테이블 시딩. rows의 dict 키가 로스터 필드가 된다."""
    meta_fields = list(rows[0].keys())
    conn = sqlite3.connect(db_path)
    conn.execute(f"CREATE TABLE roster ({', '.join(meta_fields + STATE_FIELDS)}, PRIMARY KEY (seq))")
    conn.executemany(
        f"INSERT INTO roster ({', '.join(meta_fields)}) VALUES ({', '.join('?' * len(meta_fields))})",
        [[r[c] for c in meta_fields] for r in rows],
    )
    conn.commit()
    conn.close()


def test_split_pages_with_real_delimiter():
    md = "<!-- Page 1 --> 첫 페이지\n<!--Page 63--> 둘째 페이지\n<!--  Page  100  -->   "
    assert split_md.split_pages(md) == ["첫 페이지", "둘째 페이지"]


def test_split_pages_strips_html_comments():
    md = "<!-- Page 1 --> 내용 <!-- Image --> 계속\n<!-- Page 2 --> <!-- Image -->\n<!-- Page 3 --> 다음"
    # 주석은 제거되고, 주석만 있던 페이지는 빈 페이지로 취급되어 빠진다
    assert split_md.split_pages(md) == ["내용  계속", "다음"]


def test_split_pages_rejects_empty_delimiter():
    try:
        split_md.split_pages("아무 텍스트", delimiter="")
        assert False, "빈 delimiter로 호출하면 에러가 나야 함"
    except ValueError:
        pass


def test_assign_pages_hands_off_on_next_name_mention():
    # 안지유 구간 페이지엔 이름이 없다가 마지막 페이지에만 등장(끝부분에 이름), 그다음 김민수로 넘어감
    pages = ["역량 소개 내용", "경력 요약 ... 안지유", "김민수 파트 소개", "김민수 강점"]
    assigned = split_md.assign_pages(pages, ["안지유", "김민수"])
    assert assigned == {"안지유": [0, 1], "김민수": [2, 3]}


def test_assign_pages_handles_missing_name_without_crashing():
    pages = ["아무 내용도 없음"]
    assigned = split_md.assign_pages(pages, ["안지유", "김민수"])
    assert assigned == {"안지유": [0], "김민수": []}


def test_main_writes_per_person_files_and_manifest(tmp_path):
    md_path = tmp_path / "team1.md"
    md_path.write_text(
        "<!-- Page 1 --> 안지유 핵심역량\n"
        "<!-- Page 2 --> 안지유 주요경력\n"
        "<!-- Page 3 --> 김민수 핵심역량\n",
        encoding="utf-8",
    )
    db_path = tmp_path / "roster.db"
    _seed_roster(db_path, [
        # 로스터: 다른 파일 인원(박영희)은 필터링되고, seq 역순 입력도 source_file_seq로 정렬돼야 함
        {"seq": 3, "name": "박영희", "pjt": "AI", "part": "설비", "cl_level": "CL2",
         "source_file": "team2.md", "source_file_seq": 1},
        {"seq": 2, "name": "김민수", "pjt": "디지털트윈", "part": "품질", "cl_level": "CL3",
         "source_file": "team1.md", "source_file_seq": 2},
        {"seq": 1, "name": "안지유", "pjt": "디지털트윈", "part": "품질", "cl_level": "CL4",
         "source_file": "team1.md", "source_file_seq": 1},
    ])

    out_dir = tmp_path / "out"
    split_md.main(md_path, db_path=db_path, out_dir=out_dir)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM roster")]
    conn.close()

    team1_rows = [r for r in rows if r["source_file"] == "team1.md"]
    assert len(team1_rows) == 2  # team1.md 인원만
    by_name = {r["name"]: r for r in rows}
    assert by_name["안지유"]["page_start"] == 1  # sqlite는 타입을 보존 (문자열 아님)
    assert by_name["안지유"]["page_end"] == 2
    assert by_name["김민수"]["page_start"] == 3
    assert by_name["안지유"]["seq"] == 1  # 로스터 원본 필드가 보존됨
    assert by_name["안지유"]["source_file"] == "team1.md"
    assert (out_dir / by_name["안지유"]["split_filename"]).read_text(encoding="utf-8") == (
        "안지유 핵심역량\n\n안지유 주요경력"
    )
