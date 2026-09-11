"""task-discovery S4 스테이지: 색인 적재 (S4-1, #26).

extracted.json의 facet을 **항목 단위**로 색인한다("한 문서=한 주제"). 각 색인 문서는
text·quotes·axis·horizon·person 메타(name·cl_level·pjt·part)와 임베딩 벡터.
검색 백엔드는 교체 가능(인터페이스: index·query·all). 이 모듈은 **인메모리 백엔드** —
ES 없이 개발·테스트하기 위함. 운영은 동일 인터페이스의 ES 백엔드로 교체.
임베딩은 embed(text)->vec 주입(테스트=가짜, 운영=BGE-M3). td_extract는 import 재사용.
"""
import sys
from pathlib import Path

from td_common import iter_facets, load_json

ROOT = Path(__file__).parent.parent


class InMemoryIndex:
    """순수 인메모리 색인 — 외부 의존 없음. 운영 ES 백엔드와 같은 인터페이스(all/count/query)."""

    def __init__(self):
        self._docs = []

    def add(self, doc):
        self._docs.append(doc)

    def all(self):
        return list(self._docs)

    def count(self):
        return len(self._docs)


def _doc_for(person, axis, item):
    """facet 항목 하나를 색인 문서로. person 메타 부착."""
    meta = {k: person.get(k) for k in ("person_id", "name", "cl_level", "pjt", "part")}
    return {**meta, "axis": axis, "horizon": item.get("horizon"),
            "text": item["text"], "quotes": item.get("quotes", [])}


def build(extracted, embed, backend=None):
    """extracted → 색인. facet 단위 문서(공용 iter_facets) + 주입된 embed로 벡터."""
    idx = backend if backend is not None else InMemoryIndex()
    for person, axis, item in iter_facets(load_json(extracted)):
        doc = _doc_for(person, axis, item)
        doc["vec"] = embed(doc["text"])
        idx.add(doc)
    return idx


def main(extracted_path=ROOT / "data" / "task_discovery" / "extracted.json"):
    import llm
    llm.init()
    idx = build(extracted_path, llm.embed_call())
    print(f"색인 {idx.count()}개 문서 (인메모리)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
