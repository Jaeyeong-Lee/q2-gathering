"""PPT→MD 원본을 사람 단위로 결정론적 분할 (LLM 없음).

마스터 메타 JSON(name,pjt,part,cl_level,source_file,source_file_seq,... 객체 배열)을 source of truth로 삼아,
source_file로 해당 파일 인원을 필터링, source_file_seq 순서로 페이지를 사람에게 배정한다.
사용자가 주는 필드는 전부 매니페스트에 보존하고, 코드가 채우는 컬럼만 뒤에 붙인다.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

PAGE_DELIMITER = r"<!--\s*Page\s+\d+\s*-->"  # 원본 md의 페이지 구분자: <!-- Page 63 -->

CODE_FIELDS = ["page_start", "page_end", "status", "split_filename", "normalized_filename"]

MIN_PAGES, MAX_PAGES = 1, 8  # 정상 판정 여유 범위 (예상 3~6)


def load_roster(meta_path, source_file):
    """마스터 JSON(객체 배열)에서 source_file 해당분만 필터링, source_file_seq 순 정렬."""
    all_rows = json.loads(Path(meta_path).read_text(encoding="utf-8"))
    rows = [r for r in all_rows if r["source_file"] == source_file]
    if not rows:
        raise ValueError(f"메타 JSON에 source_file={source_file!r} 항목이 없음 — 파일명 표기 확인")
    rows.sort(key=lambda r: int(r["source_file_seq"]))
    return rows


def split_pages(md_text, delimiter=None):
    """구분자 기준으로 페이지 분할. 구분자 미설정이면 즉시 에러(조용히 잘못 분할하지 않음)."""
    delimiter = delimiter if delimiter is not None else PAGE_DELIMITER
    if not delimiter:
        raise ValueError(
            "PAGE_DELIMITER 미설정 — scripts/split_md_by_person.py 상단에 실제 구분자 정규식을 채워주세요"
        )
    parts = re.split(delimiter, md_text)
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


def main(md_path, meta_path, out_dir=ROOT / "data" / "raw_sections",
         manifest_path=ROOT / "data" / "split_manifest.csv"):
    md_path = Path(md_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    roster = load_roster(meta_path, md_path.name)
    roster_names = [r["name"] for r in roster]

    md_text = md_path.read_text(encoding="utf-8")
    pages = split_pages(md_text)
    assigned = assign_pages(pages, roster_names)

    meta_fields = list(roster[0].keys())
    rows = []
    for r in roster:
        name = r["name"]
        page_idxs = assigned[name]
        split_filename = safe_filename(r["pjt"], r["part"], name) + ".md"
        (out_dir / split_filename).write_text(
            "\n\n".join(pages[i] for i in page_idxs), encoding="utf-8"
        )
        n = len(page_idxs)
        status = "정상" if (n and MIN_PAGES <= n <= MAX_PAGES) else "이상"
        rows.append(dict(r, **{
            "page_start": (page_idxs[0] + 1) if page_idxs else "",
            "page_end": (page_idxs[-1] + 1) if page_idxs else "",
            "status": status,
            "split_filename": split_filename,
            "normalized_filename": "",
        }))

    total_assigned = sum(len(v) for v in assigned.values())
    if total_assigned != len(pages):
        print(f"경고: {md_path.name} — 전체 페이지 {len(pages)}장 중 {total_assigned}장만 배정됨", file=sys.stderr)

    manifest_path = Path(manifest_path)
    write_header = not manifest_path.exists()
    with open(manifest_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=meta_fields + CODE_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)

    bad = [r["name"] for r in rows if r["status"] == "이상"]
    if bad:
        print(f"이상 {len(bad)}명 (페이지 배정 확인 필요): {bad}", file=sys.stderr)

    return manifest_path


if __name__ == "__main__":
    main(*sys.argv[1:])
