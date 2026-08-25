"""task-discovery 스테이지 1: facet 추출 (S1-2, #16).

sources.json → extracted.json. 사람 단위로 signal_present + 4축을 뽑는다:
  future_task[] (horizon·ax_mentioned 포함) / capability_have[] / capability_gap[] / direction(단수)
각 항목은 text·quotes[]. 무내용 문서는 signal_present=false + 빈 축.

인용검증·재시도는 td_common 공유 헬퍼 재사용. 검증 실패는 재시도를 유발하고,
소진 시 사람 전체가 아니라 **항목 단위로** 폐기해 나머지를 보존한다.
LLM은 call(prompt)->str 주입 (tags.py 패턴). llm.py 프로바이더 라우팅과 함께 쓴다.
"""
import json
import re
import sys
from pathlib import Path

from pipeline_log import get_logger
from td_common import (Nonretryable, load_json, quote_in_source, retry_json,
                       text_is_copy_of_quotes)

ROOT = Path(__file__).parent.parent
log = get_logger("td_extract")

LIST_AXES = ("future_task", "capability_have", "capability_gap")

# AX 태그는 **판정이 아니라 관찰**이다 — 원문에 이 표현이 실제로 적혔을 때만 붙는다.
# "이게 진짜 AX냐"는 LLM이 방어할 수 없는 주관이라 파이프라인이 하지 않는다(confidence를
# 스키마에서 뺀 것과 같은 이유). 라틴 약어는 앞뒤가 알파벳이면 제외한다 — 그러지 않으면
# FAIL·MAIN 안의 'AI'가 걸린다.
_AX_RE = re.compile(r"(?<![A-Za-z])(?:AX|AI|ML)(?![A-Za-z])|머신러닝|딥러닝|인공지능")

_SCHEMA = """JSON 객체로만 답하라. 형식:
{"signal_present": true/false,
 "future_task": [{"text": "대상·방법·이유를 담은 서술", "horizon": "단기|장기|불명", "quotes": ["원문 발췌"]}],
 "capability_have": [{"text": "...", "quotes": ["..."]}],
 "capability_gap": [{"text": "...", "quotes": ["..."]}],
 "direction": {"text": "지향 방향 1문장", "quotes": ["..."]} 또는 null}
규칙: quotes는 반드시 원문에서 글자 그대로 발췌한다. text는 quote의 복사가 아니라 서술이어야 한다.
내용이 없으면 빈 배열. 무내용(선언적) 문서는 signal_present=false 로 하고 모든 축을 비운다."""

# 헤더만 format(중괄호 필드) — _SCHEMA의 JSON 예시 중괄호는 format에 안 태운다.
_HEADER_CL23 = ("다음은 {name}({cl_level}, {pjt}/{part})의 근원경쟁력 회고다. "
                "3단 구성(①상반기 성과·하반기 전략 ②커리어 회고·확보 역량 ③미래 업무)이 "
                "원칙이나 미준수 문서도 있다. 미래과제·보유역량·필요역량·지향방향을 추출하라.")
_HEADER_CL4 = ("다음은 {name}({cl_level}, {pjt}/{part})의 근원경쟁력 회고다. "
               "CL4는 미래 위주 서술형이다. 미래과제·보유역량·필요역량·지향방향을 추출하라.")


def _build_prompt(doc):
    tpl = _HEADER_CL4 if doc["cl_level"] == "CL4" else _HEADER_CL23
    # part는 실데이터(persons.json)에 없을 수 있으므로 .get 기본값 — .format(**doc)는 KeyError.
    header = tpl.format(name=doc["name"], cl_level=doc["cl_level"],
                        pjt=doc.get("pjt", ""), part=doc.get("part", ""))
    return f"{header}\n{_SCHEMA}\n\n원문:\n{doc['text']}"


def _valid_item(item, source):
    """항목이 채택 가능한지: 인용이 있고, 원문 발췌이며, text가 인용의 복사가 아님."""
    quotes = item.get("quotes") or []
    if not quotes:
        return False
    if not all(quote_in_source(q, source) for q in quotes):
        return False
    return not text_is_copy_of_quotes(item.get("text", ""), quotes)


def _ax_mentioned(item):
    """원문 인용에 AX 표현이 있는가. **text가 아니라 quotes만 본다** — quotes는
    quote_in_source로 원문 발췌가 보장되지만 text는 LLM이 고쳐 쓴 서술이라, 원문에 없던
    'AI'가 서술에 끼어들면 근거 없는 태그가 된다.

    한계: 인용이 AX 표현이 없는 다른 문장으로 잡히면 놓친다. 의도된 누락이다 —
    놓친 쪽은 워크숍에서 사람이 줍는다(시간축을 사람이 채우는 것과 같은 논리).
    """
    return any(_AX_RE.search(q) for q in item.get("quotes") or [])


def _filter(parsed, source):
    """축별로 유효 항목만 남기고 폐기 항목을 모은다. (clean_axes, direction, dropped)."""
    clean, dropped = {}, []
    for axis in LIST_AXES:
        kept = []
        for item in parsed.get(axis) or []:
            if not _valid_item(item, source):
                dropped.append(item)
                continue
            # 과제에만 붙인다. 역량갭의 AX 여부는 소비처가 없다.
            if axis == "future_task":
                item["ax_mentioned"] = _ax_mentioned(item)
            kept.append(item)
        clean[axis] = kept
    direction = parsed.get("direction")
    if direction is not None and not _valid_item(direction, source):
        dropped.append(direction)
        direction = None
    return clean, direction, dropped


def extract_person(doc, call, *, tries=2, attempts=4, sleep=None):
    """1인 추출 + 검증. 폐기 항목이 있으면 재프롬프트(tries), 소진 시 유효분만 보존.
    반환: (person, dropped_items)."""
    prompt = _build_prompt(doc)
    kw = {"attempts": attempts} | ({"sleep": sleep} if sleep else {})
    last = None
    for attempt in range(tries):
        parsed = retry_json(call, prompt, stage="extract", call_id=doc["id"], **kw)
        signal = bool(parsed.get("signal_present"))
        if not signal:
            clean = {axis: [] for axis in LIST_AXES}
            return _person(doc, False, clean, None), []
        clean, direction, dropped = _filter(parsed, doc["text"])
        last = (clean, direction, dropped)
        if not dropped or attempt == tries - 1:
            break
    clean, direction, dropped = last
    return _person(doc, True, clean, direction), dropped


def _person(doc, signal, clean, direction):
    return {"person_id": doc["id"], "name": doc["name"], "cl_level": doc["cl_level"],
            "pjt": doc.get("pjt"), "part": doc.get("part"), "signal_present": signal,
            "direction": direction, **clean}


def run_extract(sources, out_path, call, *, tries=2, attempts=4, sleep=None):
    """배치 추출 → extracted.json(즉시 영속화). 한 사람 실패는 배치를 멈추지 않는다.
    반환: {persons, failed, dropped}."""
    docs = load_json(sources)
    persons, failed, dropped_all = [], [], []
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for doc in docs:
        try:
            person, dropped = extract_person(doc, call, tries=tries, attempts=attempts, sleep=sleep)
            persons.append(person)
            for d in dropped:
                dropped_all.append({"person_id": doc["id"], "item": d})
        except (Nonretryable, Exception) as e:
            # 콘솔엔 id만 — 실명은 ECS 로그(TD_OUT_DIR 안)에만 남긴다.
            log.warning(f"추출 폐기 id={doc.get('id')}: {e}",
                        extra={"ecs": {"user.name": doc.get("name")}})
            failed.append(doc["id"])
        out_path.write_text(json.dumps(persons, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"persons": persons, "failed": failed, "dropped": dropped_all}


def main(sources_path=ROOT / "data" / "task_discovery" / "sources.json"):
    import llm
    llm.init()
    out = Path(sources_path).parent / "extracted.json"
    summary = run_extract(sources_path, out, llm.text_call())
    log.info(f"추출 {len(summary['persons'])}명 / 폐기 {len(summary['failed'])} / "
             f"항목폐기 {len(summary['dropped'])} → {out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
