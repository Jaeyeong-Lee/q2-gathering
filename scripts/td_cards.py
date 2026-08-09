"""task-discovery 산출물 조인 (S6-1, #39).

assignments(어느 카테고리냐) + extracted(누가·어느 조직이냐)를 이어 붙여 **항목 단위
레코드**를 만든다. 렌더링을 전혀 모른다 — td_inspect(탐색기)와 td_roadmap(워크숍)이
이 위에 각자 화면을 얹는다. 조인을 두 번 구현하면 언젠가 갈라진다.

**horizon을 여기서 함께 싣는다.** 어차피 assignments↔extracted를 잇고 있고 원 항목에
horizon이 붙어 있으므로 같이 들고 오면 된다. aggregates.json에 넣어봐야 소비자가 없고
(render·narrate 둘 다 안 씀) 같은 값을 두 곳에서 계산할 이유가 없다 — td_aggregate는
건드리지 않는다.
"""
import json
import sys
from pathlib import Path

from td_common import AXES, iter_facets, load_json

ROOT = Path(__file__).parent.parent

HORIZONS = ("단기", "장기", "불명")


def _origin_index(persons):
    """(person_id, axis, text) -> [원 항목, ...]. 같은 키에 항목이 둘일 수 있어 리스트다
    (같은 사람·같은 축에 텍스트가 우연히 같은 facet). iter_facets를 쓰므로 무신호 인원은
    애초에 들어오지 않는다."""
    index = {}
    for person, axis, item in iter_facets(persons):
        index.setdefault((person["person_id"], axis, item["text"]), []).append(item)
    return index


def build(assignments, persons, *, anonymize=False):
    """배정 하나 = 카드 하나. 반환: list[dict].

    무신호 인원의 항목은 카드가 되지 않는다 — 배정 자체가 없어야 정상이지만, 상류가
    어긋나도 여기서 막힌다. 반대로 extracted에 대응 항목이 없는 배정은 **버리지 않고**
    horizon만 빈 채로 남긴다 — 배정 정보(카테고리·인용)는 그 자체로 유효하다.
    """
    assignments, persons = load_json(assignments), load_json(persons)
    meta = {p["person_id"]: p for p in persons}
    origins = _origin_index(persons)
    # 아는 사람인데 무신호인 경우만 거른다 — 모르는 사람(상류 어긋남)은 카드로 남긴다.
    no_signal = {p["person_id"] for p in persons if not p.get("signal_present")}

    cards = []
    used = {}   # 같은 키의 원 항목을 순서대로 하나씩 소진 — 중복 텍스트를 접지 않기 위해
    for a in assignments:
        pid = a["person_id"]
        if pid in no_signal:
            continue
        key = (pid, a["axis"], a["text"])
        pool = origins.get(key, ())
        i = used.get(key, 0)
        origin = pool[i] if i < len(pool) else (pool[-1] if pool else None)
        used[key] = i + 1

        person = meta.get(pid)
        cards.append({
            "person_id": pid,
            "name": (f"P{pid}" if anonymize else person.get("name")) if person else None,
            "pjt": person.get("pjt") if person else None,
            "cl_level": person.get("cl_level") if person else None,
            "category": a["category"],
            "axis": a["axis"],
            "text": a["text"],
            "quote": a.get("quote", ""),
            "horizon": (origin or {}).get("horizon"),
        })
    return cards


def horizon_distribution(cards):
    """카테고리 -> {단기, 장기, 불명} 건수. **과제 카드만 센다** — 시간은 과제의 속성이지
    역량의 속성이 아니라서 horizon이 future_task에만 있다. 과제가 하나도 없는 카테고리는
    키 자체가 없다(0으로 채운 항목을 만들면 '초안이 있다'로 오해된다)."""
    dist = {}
    for c in cards:
        if c["axis"] != "future_task":
            continue
        d = dist.setdefault(c["category"], dict.fromkeys(HORIZONS, 0))
        d[c["horizon"] if c["horizon"] in HORIZONS else "불명"] += 1
    return dist


def by_category(cards):
    """카테고리 -> [카드, ...]. 순서는 cards 그대로(=assignments 순)."""
    out = {}
    for c in cards:
        out.setdefault(c["category"], []).append(c)
    return out


def by_person(cards):
    """person_id -> [카드, ...]."""
    out = {}
    for c in cards:
        out.setdefault(c["person_id"], []).append(c)
    return out


def main(data_dir=ROOT / "data" / "task_discovery"):
    """카드 통계만 콘솔에 — 카테고리명·실명은 찍지 않는다(인덱스로만)."""
    d = Path(data_dir)
    cards = build(d / "assignments.json", d / "extracted.json")
    dist = horizon_distribution(cards)
    axes = {ax: sum(1 for c in cards if c["axis"] == ax) for ax in AXES}
    print(f"카드 {len(cards)}개 · 카테고리 {len(by_category(cards))}개 · "
          f"과제 시간분포 있는 카테고리 {len(dist)}개", file=sys.stderr)
    print("  " + " · ".join(f"{ax} {n}" for ax, n in axes.items()), file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
