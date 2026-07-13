"""master.json 로스터를 sqlite roster 테이블로 1회 이전한다. 이후 master.json은 폐기하고 sqlite를 직접 편집."""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

STATE_FIELDS = ["page_start", "page_end", "status", "split_filename", "normalized_filename"]


def main(json_path, db_path=ROOT / "data" / "roster.db"):
    rows = json.loads(Path(json_path).read_text(encoding="utf-8"))
    meta_fields = list(rows[0].keys())

    conn = sqlite3.connect(db_path)
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS roster "
        f"({', '.join(meta_fields + STATE_FIELDS)}, PRIMARY KEY (seq))"
    )
    conn.executemany(
        f"INSERT INTO roster ({', '.join(meta_fields)}) VALUES ({', '.join('?' * len(meta_fields))})",
        [[r[c] for c in meta_fields] for r in rows],
    )
    conn.commit()
    conn.close()
    print(f"{len(rows)}명 임포트 완료: {db_path}", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
