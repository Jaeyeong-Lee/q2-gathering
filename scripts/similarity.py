"""임베딩 벡터 → 코사인 유사도 top-K 이웃 neighbors.json 변환 (todos/002).

입력: {인물id: 벡터} JSON (차원은 입력에서 유추). 실데이터 임베딩이 오면 재실행만 하면 된다.
"""
import json
import math
from pathlib import Path
import sys

from config import K

ROOT = Path(__file__).parent.parent


def top_k_neighbors(embeddings, k=K):
    """{id: 벡터} → {str(id): [{"id", "similarity"}, ...]} (유사도 내림차순, 자기 자신 제외)."""
    ids = list(embeddings)
    unit = [[x / math.hypot(*embeddings[i]) for x in embeddings[i]] for i in ids]
    out = {}
    # ponytail: 순수 파이썬 O(n²·d) — 수백 명 규모 빌드 타임엔 충분, 수천 명·고차원이면 numpy로
    for a, i in enumerate(ids):
        scored = [
            (round(math.sumprod(unit[a], unit[b]), 4), ids[b])
            for b in range(len(ids)) if b != a
        ]
        scored.sort(key=lambda t: (-t[0], t[1]))
        out[str(i)] = [{"id": j, "similarity": s} for s, j in scored[:k]]
    return out


def main(emb_path, out_path=ROOT / "data" / "neighbors.json"):
    # JSON 키는 문자열이므로 persons.json의 int id로 되돌린다
    embeddings = {int(i): v for i, v in json.loads(Path(emb_path).read_text()).items()}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(top_k_neighbors(embeddings), ensure_ascii=False, indent=1))
    return out_path


if __name__ == "__main__":
    print(main(*sys.argv[1:]))
