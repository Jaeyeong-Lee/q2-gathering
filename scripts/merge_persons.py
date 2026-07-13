"""매니페스트 + 정제된 사람별 텍스트 → data/persons.json 최종 조립.

매니페스트(split_md_by_person.py → normalize_person_text.py 순서로 채워진 CSV)에서
normalized_filename이 있는 사람만 대상으로, id를 순차 부여해 최종 스키마로 작성한다.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_manifest(manifest_path):
    with open(manifest_path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_persons(rows, raw_dir):
    """정제 완료된 행만 사람 레코드로 변환. 반환: (persons, 제외된 name 목록)."""
    raw_dir = Path(raw_dir)
    persons, skipped = [], []
    next_id = 0
    for r in rows:
        if not r.get("normalized_filename"):
            skipped.append(r["name"])
            continue
        text = (raw_dir / r["normalized_filename"]).read_text(encoding="utf-8")
        persons.append({
            "id": next_id,
            "name": r["name"],
            "pjt": r["pjt"],
            "part": r["part"],
            "cl_level": r["cl_level"],
            "text": text,
            "tags": [],
        })
        next_id += 1
    return persons, skipped


def main(manifest_path=ROOT / "data" / "split_manifest.csv", raw_dir=ROOT / "data" / "raw_sections",
         out_path=ROOT / "data" / "persons.json"):
    rows = load_manifest(manifest_path)
    persons, skipped = build_persons(rows, raw_dir)

    out_path = Path(out_path)
    out_path.write_text(json.dumps(persons, ensure_ascii=False, indent=1), encoding="utf-8")

    if skipped:
        print(f"제외 {len(skipped)}명 (정제 미완료): {skipped}", file=sys.stderr)
    print(f"persons.json {len(persons)}명 작성: {out_path}", file=sys.stderr)
    return skipped


if __name__ == "__main__":
    main(*sys.argv[1:])
