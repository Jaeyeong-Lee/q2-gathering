"""task-discovery S4 스테이지: 사전 조회 묶음 + 커버리지 (S4-3, #28).

자주 물을 질문을 미리 실행(td_query)해 정적 md로 떨군다 — ES 다운·네트워크 차단에도
워크숍이 진행되는 백업. 0건 질의도 "없음"으로 명시(조용히 누락 금지). 커버리지 리포트로
"이 검색 창구가 몇 명을 대표하는가"를 밝힌다. 실명은 anonymize로 렌더 단계 교체.
출력은 dist/(배포)가 아니라 data/(gitignore).
"""
import sys
from pathlib import Path

import td_query
from td_common import oneline

ROOT = Path(__file__).parent.parent


def default_queries():
    """워크숍에서 자주 물을 프리셋 질의(필터 기반)."""
    return [
        {"title": "미래과제 전체", "axis": "future_task"},
        {"title": "필요역량(갭)", "axis": "capability_gap"},
        {"title": "보유역량", "axis": "capability_have"},
        {"title": "지향 방향", "axis": "direction"},
        {"title": "양산기술 파트", "pjt": "양산기술"},
        {"title": "공정기술 파트", "pjt": "공정기술"},
        {"title": "기획운영 파트", "pjt": "기획운영"},
        {"title": "장기 과제", "axis": "future_task", "horizon": "장기"},
    ]


def coverage(index, persons):
    """이 검색 창구가 대표하는 범위. 순수 집계."""
    total = len(persons)
    no_signal = sum(1 for p in persons if not p.get("signal_present"))
    docs = index.all()
    return {
        "total_people": total,
        "no_signal": no_signal,
        "no_signal_rate": no_signal / total if total else 0.0,
        "indexed_docs": index.count(),
        "contributing_people": len({d["person_id"] for d in docs}),
    }


def _name(doc, anonymize):
    return f"P{doc['person_id']}" if anonymize else doc.get("name", f"P{doc['person_id']}")


def render_markdown(index, embed, persons, *, queries=None, anonymize=False, top_k=10):
    queries = queries if queries is not None else default_queries()
    out = ["# 사전 조회 묶음 — 워크숍 검색 백업", "",
           "> 카테고리화 없이 facet을 색인해 질의로 답한다. 반환은 항목+인용이며 해석은 사람이 한다. "
           "ES 다운 시에도 이 정적 결과로 워크숍을 진행한다.", ""]

    for qdef in queries:
        title = qdef["title"]
        res = td_query.query(index, embed, qdef.get("q"),
                             axis=qdef.get("axis"), pjt=qdef.get("pjt"),
                             cl_level=qdef.get("cl_level"), horizon=qdef.get("horizon"),
                             top_k=top_k)
        d = res["distribution"]
        out.append(f"## {title}")
        if not res["results"]:
            out += ["- (없음)", ""]                     # 0건도 명시 — 조용히 누락 금지
            continue
        out.append(f"_기여 {d['people']}명 · {d['count']}건 · pjt {d['by_pjt']} · cl {d['by_cl']}_")
        for r in res["results"]:
            q0 = oneline(r["quotes"][0] if r.get("quotes") else r["text"])
            out.append(f"- {oneline(r['text'])}  \n  > {q0} — {_name(r, anonymize)} ({r['pjt']}/{r['cl_level']})")
        out.append("")

    cov = coverage(index, persons)
    out += ["## 커버리지", "",
            f"- 대상 {cov['total_people']}명 · 무신호 {cov['no_signal']}명 ({cov['no_signal_rate']:.0%})",
            f"- 색인 {cov['indexed_docs']}건 · 기여 인원 {cov['contributing_people']}명",
            "", "이 검색 창구는 위 인원을 대표한다. 무신호·미색인은 답하지 못한다.", ""]
    return "\n".join(out) + "\n"


def write(index, embed, persons, out_path, **kw):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_markdown(index, embed, persons, **kw), encoding="utf-8")
    return out_path


def main(extracted_path=ROOT / "data" / "task_discovery" / "extracted.json"):
    import json
    import llm
    import td_index
    llm.init()
    persons = json.loads(Path(extracted_path).read_text(encoding="utf-8"))
    idx = td_index.build(persons, llm.embed_text)
    out = write(idx, llm.embed_text, persons, Path(extracted_path).parent / "digest.md")
    print(f"사전 조회 묶음 → {out}", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
