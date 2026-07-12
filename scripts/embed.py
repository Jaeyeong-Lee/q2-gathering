"""회고 텍스트 → 임베딩 벡터 변환 (todos/010).

가짜 PPT 자료를 생성하고 Gemini 임베딩으로 벡터화.
"""
import json
from pathlib import Path
import sys

import llm
from config import K

ROOT = Path(__file__).parent.parent


def embed_persons(persons_path=ROOT / "data" / "persons.json", out_path=None):
    """persons.json의 회고 텍스트를 임베딩.

    반환: {id: [768차원 임베딩]}
    """
    llm.init()
    persons_path = Path(persons_path)
    persons = json.loads(persons_path.read_text())

    embeddings = {}
    for i, p in enumerate(persons):
        text = p["text"]
        try:
            vec = llm.embed_text(text)
            embeddings[str(p["id"])] = vec
            if (i + 1) % 10 == 0:
                print(f"임베딩: {i + 1}/{len(persons)}", file=sys.stderr)
        except Exception as e:
            print(f"임베딩 실패 {p['id']}: {e}", file=sys.stderr)

    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(embeddings, ensure_ascii=False))
        print(f"저장: {out_path}", file=sys.stderr)

    return embeddings


def main(persons_path=ROOT / "data" / "persons.json"):
    out_path = Path(persons_path).parent / "embeddings.json"
    embed_persons(persons_path, out_path)
    return out_path


if __name__ == "__main__":
    main(*sys.argv[1:])
