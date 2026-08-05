"""task-discovery 스테이지 6: 해석 — Layer 2 서사화 (상사 요구 "10년 로드맵"의 2층 구조 중 해석층).

Layer 1(aggregates+assignments+extracted, 전부 실명 인용 근거)을 재료로 LLM이 산문
총평 + 카테고리별 서사를 쓴다. **Layer 1과 절대 안 섞는다** — 별도 디렉터리
(interpretation/)에 "AI 해석" 라벨을 달아 출력한다.

grounding 방식은 extract/assign과 다르다: 여기선 원문 대조(quote_in_source)가 아니라
**근거 풀(evidence pool)을 id로 미리 못박고, LLM은 id로만 인용**하게 한다 — LLM이 인용을
다시 타이핑하다 살짝 바꿔써도 여기선 원본을 우리가 그대로 렌더링하므로 변형 여지가 없다.
citation_ids가 근거 풀 범위를 벗어나면 그 항목(citation) 자체를 버리고, 근거가 하나도
안 남은 문장(trend/특이점/카테고리 서사)은 통째로 버린다 — 근거 없는 주장을 하지 않는다.

10년·전략·"꿈"을 만들어내지 않는다 — Layer 1이 이미 보여주는 흐름을 산문으로 정리할 뿐.
LLM은 call(prompt)->str 주입.
"""
import json
import sys
from pathlib import Path

from pipeline_log import get_logger
from td_common import load_json, oneline, retry_json

ROOT = Path(__file__).parent.parent
log = get_logger("td_narrate")

MAX_CAT_EVIDENCE = 12    # 카테고리 페이지에 실을 근거 상한
TEAM_PER_CAT = 3         # 총평 프롬프트에 카테고리당 실을 근거 수

_TEAM_INSTRUCT = """너는 반도체 후공정 테스트 팀의 역량 카테고리 집계를 읽고 총평을 쓴다.
아래 카테고리 요약과 실명 인용 근거(evidence, 각 항목에 id)가 전부다 — 이 안에 없는 내용은
절대 만들지 마라("10년 뒤...", "우리의 꿈은..." 같은 데이터에 없는 단정 금지).
"큰 흐름"(2~4개)과 "소수 의견·특이점"(1~3개)을 산문 문장으로 써라. 각 문장은 그 근거가 된
evidence id 배열(citation_ids)을 반드시 붙인다.
JSON 객체로만 답하라: {"trends": [{"text": "...", "citation_ids": [0, 2]}],
"minority_notes": [{"text": "...", "citation_ids": [1]}]}"""

_CATEGORY_INSTRUCT = """너는 반도체 후공정 테스트 팀의 역량 카테고리 하나를 종합 서술한다.
아래 카테고리 정보와 실명 인용 근거(evidence, 각 항목에 id)가 전부다 — 이 안에 없는 내용은
절대 만들지 마라. 팀이 왜 이 주제를 언급했는지 2~4문장으로 써라. 근거로 쓴 evidence id
배열(citation_ids)을 반드시 붙인다.
JSON 객체로만 답하라: {"narrative": "...", "citation_ids": [0, 1]}"""


def _evidence_by_category(assignments, persons, *, anonymize=False, cap=MAX_CAT_EVIDENCE):
    """카테고리별 (실명, 인용) 근거 목록, 항목당 cap개로 절단(대표 샘플)."""
    assignments, persons = load_json(assignments), load_json(persons)
    name_by_id = {p["person_id"]: p.get("name") for p in persons}
    out = {}
    for a in assignments:
        name = f"P{a['person_id']}" if anonymize else name_by_id.get(a["person_id"], f"P{a['person_id']}")
        out.setdefault(a["category"], []).append({"name": name, "quote": a["quote"]})
    return {cat: items[:cap] for cat, items in out.items()}


def _fmt_evidence(items, *, with_category=False):
    def line(i, it):
        cat = f"({it['category']}) " if with_category else ""
        return f"[{i}] {cat}{it['name']}: {it['quote']}"
    return "\n".join(line(i, it) for i, it in enumerate(items))


def _valid_ids(ids, n):
    return sorted({i for i in (ids or []) if isinstance(i, int) and 0 <= i < n})


def _clean_bullets(bullets, evidence):
    """text+citation_ids 목록 중 근거가 하나도 안 남는 항목은 버린다."""
    out = []
    for b in bullets or []:
        text = (b.get("text") or "").strip()
        ids = _valid_ids(b.get("citation_ids"), len(evidence))
        if text and ids:
            out.append({"text": text, "citations": [evidence[i] for i in ids]})
    return out


def _team_evidence(categories, evidence_by_cat, *, per_cat=TEAM_PER_CAT):
    flat = []
    for c in categories:
        for it in evidence_by_cat.get(c["name"], [])[:per_cat]:
            flat.append({**it, "category": c["name"]})
    return flat


def _team_prompt(categories, flat_evidence):
    cat_summary = "\n".join(
        f"- {c['name']} — {c['people']}명, {c['readiness']}, 보유{c['have']}/갭{c['gap']}"
        for c in categories)
    return (_TEAM_INSTRUCT + "\n\n카테고리 요약:\n" + cat_summary +
            "\n\n근거:\n" + _fmt_evidence(flat_evidence, with_category=True))


def _category_prompt(cat, evidence):
    info = (f"{cat['name']} — {cat['people']}명, {cat['readiness']}, "
            f"보유{cat['have']}/갭{cat['gap']}, 정의: {cat.get('definition', '')}")
    return _CATEGORY_INSTRUCT + "\n\n카테고리:\n" + info + "\n\n근거:\n" + _fmt_evidence(evidence)


def narrate_team(categories, flat_evidence, call, *, tries=2, attempts=4, sleep=None):
    """근거 없는 총평은 안 쓴다 — 재시도 소진 시 빈 결과."""
    kw = {"attempts": attempts} | ({"sleep": sleep} if sleep else {})
    prompt = _team_prompt(categories, flat_evidence)
    for attempt in range(tries):
        parsed = retry_json(call, prompt, stage="narrate", call_id="team", **kw)
        trends = _clean_bullets(parsed.get("trends"), flat_evidence)
        notes = _clean_bullets(parsed.get("minority_notes"), flat_evidence)
        if trends or notes or attempt == tries - 1:
            return {"trends": trends, "minority_notes": notes}
    return {"trends": [], "minority_notes": []}


def narrate_category(cat, evidence, call, *, call_id=0, tries=2, attempts=4, sleep=None):
    """근거 없는 서사는 페이지를 만들지 않는다(None)."""
    kw = {"attempts": attempts} | ({"sleep": sleep} if sleep else {})
    prompt = _category_prompt(cat, evidence)
    for attempt in range(tries):
        parsed = retry_json(call, prompt, stage="narrate", call_id=call_id, **kw)
        ids = _valid_ids(parsed.get("citation_ids"), len(evidence))
        text = (parsed.get("narrative") or "").strip()
        if text and ids:
            return {"narrative": text, "citations": [evidence[i] for i in ids]}
        if attempt == tries - 1:
            return None
    return None


def _cites_line(citations):
    return " / ".join(f'{c["name"]}: "{oneline(c["quote"])}"' for c in citations)


def _render_team(team):
    out = ["# 미래 역량 지도 — 해석  `AI 해석 — 사실 아님, 종합 추론`", "",
           "> 이 페이지는 Layer 1(역량 테마 카드·실명 인용)을 근거로 LLM이 종합한 해석이다. "
           "확정 사실이 아니라 논의 촉발용이며, 모든 문장은 실제 인용으로 역추적된다.", ""]
    out.append("## 큰 흐름\n")
    for t in team["trends"]:
        out.append(f"- {t['text']} — 근거: {_cites_line(t['citations'])}")
    if not team["trends"]:
        out.append("- (근거 부족으로 생성 안 됨)")
    out.append("")
    out.append("## 소수 의견·특이점\n")
    for n in team["minority_notes"]:
        out.append(f"- {n['text']} — 근거: {_cites_line(n['citations'])}")
    if not team["minority_notes"]:
        out.append("- (근거 부족으로 생성 안 됨)")
    out.append("")
    return out


def _render_index(team, pages):
    out = _render_team(team)
    out.append("## 카테고리별 해석\n")
    for p in pages:
        out.append(f"- [{p['category']['name']}](category-{p['idx']:02d}.md) — "
                   f"{p['category']['people']}명 · {p['narrative']}")
    return "\n".join(out) + "\n"


def _render_category_page(p, rel_by_name):
    c = p["category"]
    out = [f"# {c['name']}  `AI 해석`", "",
           f"{c['people']}명 · 확산도 pjt {c['pjt_spread']}/cl {c['cl_spread']} · "
           f"보유 {c['have']} / 갭 {c['gap']} · {c['readiness']}", "",
           p["narrative"], "", "**근거 인용**", ""]
    for cite in p["citations"]:
        out.append(f'> {oneline(cite["quote"])} — {cite["name"]}')
    relations = rel_by_name.get(c["name"], [])
    if relations:
        out += ["", "**관련 카테고리** (taxonomy에서 그대로, LLM 재검증 없음)", ""]
        for r in relations:
            out.append(f"- {r['type']}: {r['to']}")
    return "\n".join(out) + "\n"


def narrate(aggregates, assignments, persons, taxonomy, out_dir, call, *,
            anonymize=False, tries=2, attempts=4, sleep=None):
    """Layer 2 전체: 총평 + 카테고리별 페이지. 반환: {team, pages}."""
    aggregates = load_json(aggregates)
    taxonomy = load_json(taxonomy) if taxonomy is not None else []
    rel_by_name = {c["name"]: c.get("relations", []) for c in taxonomy}
    evidence_by_cat = _evidence_by_category(assignments, persons, anonymize=anonymize)

    categories = aggregates["categories"]
    flat = _team_evidence(categories, evidence_by_cat)
    team = narrate_team(categories, flat, call, tries=tries, attempts=attempts, sleep=sleep)

    pages = []
    for idx, c in enumerate(categories):
        ev = evidence_by_cat.get(c["name"], [])
        if not ev:
            continue
        res = narrate_category(c, ev, call, call_id=idx, tries=tries, attempts=attempts, sleep=sleep)
        if res is None:
            continue
        pages.append({"idx": idx, "category": c, **res})

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.md").write_text(_render_index(team, pages), encoding="utf-8")
    for p in pages:
        (out_dir / f"category-{p['idx']:02d}.md").write_text(
            _render_category_page(p, rel_by_name), encoding="utf-8")
    return {"team": team, "pages": pages}


def main(data_dir=ROOT / "data" / "task_discovery"):
    import llm
    llm.init()
    d = Path(data_dir)
    out_dir = d / "interpretation"
    res = narrate(d / "aggregates.json", d / "assignments.json", d / "extracted.json",
                 d / "taxonomy.json", out_dir, llm.text_call())
    log.info(f"해석 총평 + 카테고리 {len(res['pages'])}개 → {out_dir}")


if __name__ == "__main__":
    main(*sys.argv[1:])
