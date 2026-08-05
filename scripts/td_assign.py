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


def _progress_path(out_path):
    return out_path.parent / "assignments.progress.json"


def is_complete(out_path):
    """assignments.json이 끝까지 처리됐는지 — 진행 사이드카의 processed==total_facets로 판정
    (taxonomy.is_complete와 동일한 이유: 존재만으론 부분 저장과 구분 안 됨)."""
    out_path = Path(out_path)
    progress_path = _progress_path(out_path)
    if not out_path.exists() or not progress_path.exists():
        return False
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    return progress.get("processed") == progress.get("total_facets")


def assign(extracted, taxonomy, out_path, call, *, tries=2, attempts=4, sleep=None):
    """각 facet을 카테고리에 배정. 검증 실패 항목은 폐기, 나머지는 보존. 반환: {assignments, dropped}.

    out_path가 있으면 항목마다 즉시 저장(td_extract.run_extract와 동일 패턴) + 진행 사이드카
    (assignments.progress.json)로 중단 지점부터 재개한다. 재개 판정은 텍스트 내용이 아니라
    iter_facets 순서상의 위치(processed 카운트)로 한다 — 같은 사람·축에 우연히 텍스트가
    같은 facet이 둘 있어도 위치로 구분되므로 안전하다. extracted/taxonomy 중 하나라도
    mtime이 사이드카와 다르면(상류 변경) 처음부터 다시 배정한다.

    ponytail: dropped는 재개 시 이전 세그먼트분이 사이드카에 안 남아 최종 반환값엔 이번
    실행분만 잡힌다 — assignments.json(정답)엔 영향 없고 커버리지 리포트의 폐기 수만
    과소 집계될 수 있음. 필요해지면 dropped도 같은 방식으로 파일 영속화.
    """
    # load_json 전에 mtime을 재둔다 — extracted/taxonomy가 경로면 load_json이 그 값을
    # 리스트로 덮어써서 이후엔 경로였는지 알 수 없어진다.
    extracted_mtime = Path(extracted).stat().st_mtime if isinstance(extracted, (str, Path)) else None
    taxonomy_mtime = Path(taxonomy).stat().st_mtime if isinstance(taxonomy, (str, Path)) else None

    persons = load_json(extracted)
    taxonomy = load_json(taxonomy)
    names = {c["name"] for c in taxonomy}
    kw = {"attempts": attempts} | ({"sleep": sleep} if sleep else {})

    facets = list(iter_facets(persons))
    total_facets = len(facets)

    out_path = Path(out_path) if out_path is not None else None
    progress_path = _progress_path(out_path) if out_path is not None else None

    assignments, dropped, processed = [], [], 0
    if progress_path is not None and progress_path.exists() and out_path.exists():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        if (progress.get("extracted_mtime") == extracted_mtime
                and progress.get("taxonomy_mtime") == taxonomy_mtime):
            processed = progress.get("processed", 0)
            assignments = json.loads(out_path.read_text(encoding="utf-8"))
        # mtime이 다르면 상류가 바뀐 것 — processed=0/assignments=[] 그대로 둬 처음부터 재시작

    def save():
        if out_path is None:
            return
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(assignments, ensure_ascii=False, indent=1), encoding="utf-8")
        progress_path.write_text(json.dumps(
            {"processed": processed, "total_facets": total_facets,
             "extracted_mtime": extracted_mtime, "taxonomy_mtime": taxonomy_mtime},
            ensure_ascii=False, indent=1), encoding="utf-8")

    for call_id, (person, axis, item) in enumerate(facets, start=1):
        if call_id <= processed:
            continue
        pid = person["person_id"]
        result = _assign_one(item, taxonomy, names, call, tries, kw, call_id)
        if result is None:
            dropped.append({"person_id": pid, "axis": axis, "text": item["text"]})
        else:
            cat, quote = result
            assignments.append({"person_id": pid, "axis": axis, "text": item["text"],
                                "category": cat, "quote": quote})
        processed = call_id
        save()

    save()  # facet 0개거나 이미 완료 상태로 진입해도 항상 한 번은 저장 보장
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
