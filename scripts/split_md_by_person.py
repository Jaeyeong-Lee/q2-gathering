"""PPT→MD 원본을 사람 단위로 결정론적 분할 (LLM 없음).

sqlite roster 테이블(scripts/import_roster.py 산출물)을 source of truth로 삼아,
source_file로 해당 파일 인원을 필터링, source_file_seq 순서로 페이지를 사람에게 배정한다.
결과는 같은 roster 테이블의 상태 컬럼(page_start/page_end/status/split_filename)에 UPDATE된다.
"""
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

PAGE_DELIMITER = r"<!--\s*Page\s+\d+\s*-->"  # 원본 md의 페이지 구분자: <!-- Page 63 -->

MIN_PAGES, MAX_PAGES = 1, 8  # 정상 판정 여유 범위 (예상 3~6)


def load_roster(conn, source_file):
    """roster 테이블에서 source_file 해당분만 필터링, source_file_seq 순 정렬."""
    rows = conn.execute(
        "SELECT * FROM roster WHERE source_file = ? ORDER BY source_file_seq", (source_file,)
    ).fetchall()
    if not rows:
        raise ValueError(f"roster 테이블에 source_file={source_file!r} 항목이 없음 — 파일명 표기 확인")
    return [dict(r) for r in rows]


def split_pages(md_text, delimiter=None):
    """구분자 기준으로 페이지 분할. 구분자 미설정이면 즉시 에러(조용히 잘못 분할하지 않음)."""
    delimiter = delimiter if delimiter is not None else PAGE_DELIMITER
    if not delimiter:
        raise ValueError(
            "PAGE_DELIMITER 미설정 — scripts/split_md_by_person.py 상단에 실제 구분자 정규식을 채워주세요"
        )
    parts = re.split(delimiter, md_text)
    # 노이즈 제거 지점: 사람별 원문에서 지우고 싶은 패턴은 여기서 re.sub로 걸러낸다.
    # 여기서 지우면 다운스트림 전체(LLM 정제 입력 → 임베딩 → 워드클라우드 → 상세패널 원문)가 같이 깨끗해짐.
    # 현재: HTML 주석(<!-- Image --> 등) 제거. 추가로 지울 게 생기면 아래에 re.sub 한 줄씩 더하면 됨.
    parts = [re.sub(r"<!--.*?-->", "", p, flags=re.DOTALL) for p in parts]
    return [p.strip() for p in parts if p.strip()]


def assign_pages(pages, roster_names):
    """로스터 순서를 사전 정보로 사용: 담당자를 순서대로 진행하다 다음 사람 이름이 등장하면 넘긴다.

    반환: {name: [page_idx, ...]} (등장하지 않은 이름은 빈 리스트)
    """
    assigned = {name: [] for name in roster_names}
    if not roster_names:
        return assigned
    cur = 0
    for i, page in enumerate(pages):
        while cur + 1 < len(roster_names) and roster_names[cur + 1] in page:
            cur += 1
        assigned[roster_names[cur]].append(i)
    return assigned


def safe_filename(*parts):
    cleaned = ["".join(c for c in str(p) if c not in '/\\:*?"<>|') for p in parts]
    return "__".join(cleaned)


def main(md_path, db_path=ROOT / "data" / "roster.db", out_dir=ROOT / "data" / "raw_sections"):
    md_path = Path(md_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    roster = load_roster(conn, md_path.name)
    roster_names = [r["name"] for r in roster]

    md_text = md_path.read_text(encoding="utf-8")
    pages = split_pages(md_text)
    assigned = assign_pages(pages, roster_names)

    updates = []
    bad = []
    for r in roster:
        name = r["name"]
        page_idxs = assigned[name]
        split_filename = safe_filename(r["pjt"], r["part"], name) + ".md"
        (out_dir / split_filename).write_text(
            "\n\n".join(pages[i] for i in page_idxs), encoding="utf-8"
        )
        n = len(page_idxs)
        status = "정상" if (n and MIN_PAGES <= n <= MAX_PAGES) else "이상"
        if status == "이상":
            bad.append(r["seq"])       # 실명 대신 seq — 콘솔에 이름을 안 흘린다
        updates.append((
            (page_idxs[0] + 1) if page_idxs else None,
            (page_idxs[-1] + 1) if page_idxs else None,
            status,
            split_filename,
            r["seq"],
        ))

    conn.executemany(
        "UPDATE roster SET page_start=?, page_end=?, status=?, split_filename=? WHERE seq=?",
        updates,
    )
    conn.commit()

    total_assigned = sum(len(v) for v in assigned.values())
    if total_assigned != len(pages):
        print(f"경고: {md_path.name} — 전체 페이지 {len(pages)}장 중 {total_assigned}장만 배정됨", file=sys.stderr)

    if bad:
        print(f"이상 {len(bad)}명 (페이지 배정 확인 필요) seq={bad}", file=sys.stderr)

    conn.close()
    return db_path


if __name__ == "__main__":
    main(*sys.argv[1:])
