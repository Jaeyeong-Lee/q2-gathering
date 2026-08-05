"""task-discovery 스테이지 3: 배정 (S1-4, #19).

extracted.json의 각 facet을 taxonomy.json의 카테고리 하나에 배정 → assignments.json.
맞는 카테고리가 없으면 Other. 모델이 taxonomy에 없는 범주를 지어내면 거부·재시도.
배정마다 근거 인용을 요구하고 td_common 정규화 대조로 검증(추출과 동일 규칙).
스테이지는 call 하나만 안다 — 작은 모델 사용은 호출부(td_pipeline)가 다른 call을 주입.
"""
import json
import sys
from pathlib import Path

from pipeline_log import get_logger
from td_common import iter_facets, load_json, quote_in_source, retry_json

ROOT = Path(__file__).parent.parent
log = get_logger("td_assign")

OTHER = "Other"

_INSTRUCT = """아래 카테고리에서 이 항목이 속할 카테고리 하나를 고른다. 맞는 게 없으면 "Other".
새 카테고리를 지어내지 말 것. 근거로 항목에서 인용을 하나 뽑는다.
JSON 객체로만 답하라: {"category": "카테고리명 또는 Other", "quote": "항목 근거 인용"}"""


def _cat_view(c):
    """배정 프롬프트에 실을 범주 뷰. inclusion/exclusion(있으면)까지 제시."""
    view = {"name": c["name"], "definition": c.get("definition", "")}
    inclusion = c.get("inclusion") or c.get("inclusion_criteria")  # 코드북/taxonomy 양쪽
    if inclusion:
        view["inclusion"] = inclusion
    if c.get("exclusion"):
        view["exclusion"] = c["exclusion"]
    return view


def _prompt(item, taxonomy):
    cats = json.dumps([_cat_view(c) for c in taxonomy], ensure_ascii=False)
    return f"{_INSTRUCT}\n\n카테고리:\n{cats}\n\n항목:\n{item['text']}"


def collect_other(assignments, *, threshold=0.2):
    """Other 항목 별도 수집 + 비율. 고정 코드북(S2)의 '기타 뭉갬' 약점 방어 —
    비율이 임계를 넘으면 코드북 갱신 신호."""
    assignments = load_json(assignments)
    others = [a for a in assignments if a["category"] == OTHER]
    n = len(assignments)
    ratio = len(others) / n if n else 0.0
    return {"items": others, "count": len(others), "ratio": ratio, "warning": ratio > threshold}


def _assign_one(item, taxonomy, names, call, tries, kw, call_id):
    """유효한 배정을 얻으면 (category, quote), 실패하면 None."""
    evidence = item["text"] + " " + " ".join(item.get("quotes") or [])
    for attempt in range(tries):
        parsed = retry_json(call, _prompt(item, taxonomy), stage="assign", call_id=call_id, **kw)
        cat, quote = parsed.get("category"), parsed.get("quote", "")
        ok_cat = cat == OTHER or cat in names
        ok_quote = bool(quote) and quote_in_source(quote, evidence)
        if ok_cat and ok_quote:
            return cat, quote
    return None


def assign(extracted, taxonomy, out_path, call, *, tries=2, attempts=4, sleep=None):
    """각 facet을 카테고리에 배정. 검증 실패 항목은 폐기, 나머지는 보존.
    반환: {assignments, dropped}."""
    persons = load_json(extracted)
    taxonomy = load_json(taxonomy)
    names = {c["name"] for c in taxonomy}
    kw = {"attempts": attempts} | ({"sleep": sleep} if sleep else {})
    assignments, dropped = [], []
    for call_id, (person, axis, item) in enumerate(iter_facets(persons), start=1):
        pid = person["person_id"]
        result = _assign_one(item, taxonomy, names, call, tries, kw, call_id)
        if result is None:
            dropped.append({"person_id": pid, "axis": axis, "text": item["text"]})
            continue
        cat, quote = result
        assignments.append({"person_id": pid, "axis": axis, "text": item["text"],
                            "category": cat, "quote": quote})
    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(assignments, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"assignments": assignments, "dropped": dropped}


def main(extracted_path=ROOT / "data" / "task_discovery" / "extracted.json",
         taxonomy_path=ROOT / "data" / "task_discovery" / "taxonomy.json"):
    import llm
    llm.init()
    out = Path(extracted_path).parent / "assignments.json"
    res = assign(extracted_path, taxonomy_path, out, llm.text_call())
    log.info(f"배정 {len(res['assignments'])} / 폐기 {len(res['dropped'])} → {out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
