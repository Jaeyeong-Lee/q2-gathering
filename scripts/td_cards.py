"""task-discovery 산출물 조인 (S6-1, #39).

assignments(어느 카테고리냐) + extracted(누가·어느 조직이냐)를 이어 붙여 **항목 단위
레코드**를 만든다. 렌더링을 전혀 모른다 — td_inspect(탐색기)와 td_roadmap(워크숍)이
이 위에 각자 화면을 얹는다. 조인을 두 번 구현하면 언젠가 갈라진다.

**horizon을 여기서 함께 싣는다.** 어차피 assignments↔extracted를 잇고 있고 원 항목에
horizon이 붙어 있으므로 같이 들고 오면 된다. aggregates.json에 넣어봐야 소비자가 없고
(render·narrate 둘 다 안 씀) 같은 값을 두 곳에서 계산할 이유가 없다 — td_aggregate는
건드리지 않는다.
"""
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
    원 항목이 아예 없든 앞서 다 소진됐든 답은 같다(둘 다 "대응 항목 없음"이다).
    """
    assignments, persons = load_json(assignments), load_json(persons)
    meta = {p["person_id"]: p for p in persons}
    origins = _origin_index(persons)
    # 아는 사람인데 무신호인 경우만 거른다 — 모르는 사람(상류 어긋남)은 카드로 남긴다.
    no_signal = {p["person_id"] for p in persons if not p.get("signal_present")}

    cards = []
    consumed = {}   # 키별로 원 항목을 순서대로 하나씩 소진 — 중복 텍스트를 접지 않기 위해
    for a in assignments:
        pid = a["person_id"]
        if pid in no_signal:
            continue
        key = (pid, a["axis"], a["text"])
        pool = origins.get(key, ())
        i = consumed.get(key, 0)
        # 원 항목이 동나면 horizon은 비운다. 앞 항목 것을 물려주면 근거 없는 시간축이
        # 생기는데, 그건 "대응 항목이 없다"는 사실을 지우는 조작이다.
        origin = pool[i] if i < len(pool) else None
        consumed[key] = i + 1

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


def dropped_facets(assignments, persons, *, anonymize=False):
    """인용검증을 통과 못 해 배정에서 빠진 facet들. 반환: list[dict].

    td_assign은 dropped를 반환만 하고 파일로 남기지 않아 목록이 없다. 추가 저장 없이
    **차집합**으로 구한다 — extracted의 facet 중 assignments가 소비하지 않은 것.
    같은 키에 facet이 둘인데 배정이 하나면 하나만 폐기이므로 개수로 센다.

    한계: 추출 단계에서 통째로 실패한 사람은 extracted.json에 아예 없어 이 방법으로
    잡히지 않는다. 그건 td_render.coverage의 failed_count로만 보인다.
    """
    assignments, persons = load_json(assignments), load_json(persons)
    meta = {p["person_id"]: p for p in persons}
    assigned = {}
    for a in assignments:
        key = (a["person_id"], a["axis"], a["text"])
        assigned[key] = assigned.get(key, 0) + 1

    out = []
    for person, axis, item in iter_facets(persons):
        pid = person["person_id"]
        key = (pid, axis, item["text"])
        if assigned.get(key, 0) > 0:
            assigned[key] -= 1
            continue
        p = meta.get(pid, {})
        out.append({"person_id": pid,
                    "name": f"P{pid}" if anonymize else p.get("name"),
                    "pjt": p.get("pjt"), "cl_level": p.get("cl_level"),
                    "axis": axis, "text": item["text"],
                    "horizon": item.get("horizon")})
    return out


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
