"""task-discovery 스테이지 4: 집계 (S1-5, #20).

assignments + extracted(pjt/cl_level·have/gap) → aggregates. 순수 함수(LLM 없음).
카테고리별로 기여 인원·확산도(distinct pjt·cl_level)·갭(have vs gap)·준비도 3구간.
소수의견은 별도 트랙으로 보존 — 다수 요약에 흡수(over-smoothing)되지 않게.
중요도는 추출이 아니라 여기 집계 빈도에서만 발생한다.
"""
import json
import sys
from pathlib import Path

from td_common import load_json

ROOT = Path(__file__).parent.parent

# 소수의견 문턱 — 기여 인원이 이 수 이하면 weak signal(선행 신호)로 별도 트랙
WEAK = 2


def aggregate(assignments, persons, out_path=None, *, weak=WEAK):
    """카테고리별 집계 + 소수의견 트랙. 반환: {categories, minority}."""
    assignments = load_json(assignments)
    persons = load_json(persons)
    meta = {p["person_id"]: p for p in persons}

    cats = {}
    for a in assignments:
        c = cats.setdefault(a["category"],
                            {"people": set(), "pjts": set(), "cls": set(), "have": 0, "gap": 0})
        m = meta.get(a["person_id"], {})
        c["people"].add(a["person_id"])
        if m.get("pjt"):
            c["pjts"].add(m["pjt"])
        if m.get("cl_level"):
            c["cls"].add(m["cl_level"])
        if a["axis"] == "capability_have":
            c["have"] += 1
        elif a["axis"] == "capability_gap":
            c["gap"] += 1

    categories = []
    for name, c in cats.items():
        people = len(c["people"])
        if people <= weak:
            readiness = "선행 신호"          # 소수 언급 = weak signal
        elif c["gap"] > c["have"]:
            readiness = "갭만 있음"          # 필요는 다수, 보유 희박
        else:
            readiness = "이미 함"            # 보유가 우세
        categories.append({
            "name": name, "people": people,
            "pjt_spread": len(c["pjts"]), "cl_spread": len(c["cls"]),
            "have": c["have"], "gap": c["gap"], "readiness": readiness,
            "pjts": sorted(c["pjts"]), "cls": sorted(c["cls"]),
        })
    categories.sort(key=lambda x: -x["people"])          # 중요도 = 집계 빈도
    minority = [c for c in categories if c["people"] <= weak]

    result = {"categories": categories, "minority": minority}
    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


def main(assignments_path=ROOT / "data" / "task_discovery" / "assignments.json",
         extracted_path=ROOT / "data" / "task_discovery" / "extracted.json"):
    out = Path(assignments_path).parent / "aggregates.json"
    res = aggregate(assignments_path, extracted_path, out)
    print(f"집계 카테고리 {len(res['categories'])} / 소수의견 {len(res['minority'])} → {out}",
          file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
