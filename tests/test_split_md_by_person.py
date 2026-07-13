import csv

import split_md_by_person as split_md


DELIM = r"<---\s*\d+\s*--->"


def test_split_pages_strips_and_drops_empty():
    md = "<--- 1 ---> 첫 페이지\n<--- 2 ---> 둘째 페이지\n<--- 3 --->   "
    assert split_md.split_pages(md, delimiter=DELIM) == ["첫 페이지", "둘째 페이지"]


def test_split_pages_requires_delimiter():
    try:
        split_md.split_pages("아무 텍스트")
        assert False, "delimiter 없이 호출하면 에러가 나야 함"
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
        "<--- 1 ---> 안지유 핵심역량\n"
        "<--- 2 ---> 안지유 주요경력\n"
        "<--- 3 ---> 김민수 핵심역량\n",
        encoding="utf-8",
    )
    meta_path = tmp_path / "meta.csv"
    fields = ["seq", "name", "pjt", "part", "cl_level", "source_file", "source_file_seq"]
    with open(meta_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows([
            # 마스터 CSV: 다른 파일 인원(박영희)은 필터링되고, seq 역순 입력도 source_file_seq로 정렬돼야 함
            {"seq": "3", "name": "박영희", "pjt": "AI", "part": "설비", "cl_level": "CL2",
             "source_file": "team2.md", "source_file_seq": "1"},
            {"seq": "2", "name": "김민수", "pjt": "디지털트윈", "part": "품질", "cl_level": "CL3",
             "source_file": "team1.md", "source_file_seq": "2"},
            {"seq": "1", "name": "안지유", "pjt": "디지털트윈", "part": "품질", "cl_level": "CL4",
             "source_file": "team1.md", "source_file_seq": "1"},
        ])

    out_dir = tmp_path / "out"
    manifest_path = tmp_path / "manifest.csv"
    split_md.PAGE_DELIMITER = DELIM
    try:
        split_md.main(md_path, meta_path, out_dir=out_dir, manifest_path=manifest_path)
    finally:
        split_md.PAGE_DELIMITER = None

    rows = list(csv.DictReader(open(manifest_path, encoding="utf-8")))
    assert len(rows) == 2  # team1.md 인원만 (박영희 제외)
    by_name = {r["name"]: r for r in rows}
    assert by_name["안지유"]["page_start"] == "1"
    assert by_name["안지유"]["page_end"] == "2"
    assert by_name["김민수"]["page_start"] == "3"
    assert by_name["안지유"]["seq"] == "1"  # 사용자 제공 컬럼(마스터 seq)이 보존됨
    assert by_name["안지유"]["source_file"] == "team1.md"
    assert (out_dir / by_name["안지유"]["split_filename"]).read_text(encoding="utf-8") == (
        "안지유 핵심역량\n\n안지유 주요경력"
    )
