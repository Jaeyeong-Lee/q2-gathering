"""roster + 정제된 사람별 텍스트 → data/persons.json 최종 조립.

roster 테이블(split_md_by_person.py → normalize_person_text.py 순서로 채워짐)에서
normalized_filename이 있는 사람만 대상으로, id를 순차 부여해 최종 스키마로 작성한다.
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_roster(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM roster")]
    conn.close()
    return rows


def build_persons(rows, raw_dir):
    """정제 완료된 행만 사람 레코드로 변환. text=원문, normalized_text=LLM 정제본.

    반환: (persons, 제외된 name 목록).
    """
    raw_dir = Path(raw_dir)
    persons, skipped = [], []
    next_id = 0
    for r in rows:
        if not r.get("normalized_filename"):
            skipped.append(r["name"])
            continue
        persons.append({
            "id": next_id,
            "name": r["name"],
            "pjt": r["pjt"],
            "part": r["part"],
            "cl_level": r["cl_level"],
            "text": (raw_dir / r["split_filename"]).read_text(encoding="utf-8"),
            "normalized_text": (raw_dir / r["normalized_filename"]).read_text(encoding="utf-8"),
            "tags": [],
        })
        next_id += 1
    return persons, skipped


def main(db_path=ROOT / "data" / "roster.db", raw_dir=ROOT / "data" / "raw_sections",
         out_path=ROOT / "data" / "persons.json"):
    rows = load_roster(db_path)
    persons, skipped = build_persons(rows, raw_dir)

    out_path = Path(out_path)
    out_path.write_text(json.dumps(persons, ensure_ascii=False, indent=1), encoding="utf-8")

    if skipped:
        print(f"제외 {len(skipped)}명 (정제 미완료): {skipped}", file=sys.stderr)
    print(f"persons.json {len(persons)}명 작성: {out_path}", file=sys.stderr)
    return skipped


if __name__ == "__main__":
    main(*sys.argv[1:])
