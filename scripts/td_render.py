"""task-discovery 스테이지 5: 렌더 + 커버리지 리포트 (S1-6, #21).

aggregates + extracted + assignments → 워크숍 입력물(정적 md). 완성 로드맵이 아님을 명시.
카테고리 카드(준비도·확산도·실명 인용) + pjt×cl_level 교차표 + 소수의견 + 커버리지 리포트
+ 미결 질문. 이름은 구조상 분리 — anonymize=True면 렌더 단계 교체만으로 익명화.
dist/(배포 추적)가 아니라 data/(gitignore)에 출력 — 합성 산출물이 배포물에 안 섞이게.
"""
import json
import sys
from collections import Counter
from pathlib import Path

from td_common import load_json, oneline

ROOT = Path(__file__).parent.parent


def coverage(persons, assignments, *, failed=None, extract_dropped=0, assign_dropped=0):
    """결과 신뢰도의 방어선. 순수 함수 — 폐기·무신호·Other·인용실패 비율."""
    persons, assignments = load_json(persons), load_json(assignments)
    total = len(persons)
    no_signal = sum(1 for p in persons if not p.get("signal_present"))
    other = sum(1 for a in assignments if a["category"] == "Other")
    n_assign = len(assignments)
    dropped = (extract_dropped or 0) + (assign_dropped or 0)
    return {
        "total_people": total,
        "no_signal": no_signal,
        "no_signal_rate": no_signal / total if total else 0.0,
        "other": other,
        "other_rate": other / n_assign if n_assign else 0.0,
        "failed_count": len(failed or []),
        "dropped_count": dropped,
        "assignments": n_assign,
    }


def _name(pid, name_by_id, anonymize):
    return f"P{pid}" if anonymize else name_by_id.get(pid, f"P{pid}")


def _crosstab(assignments, persons):
    """pjt × cl_level 인원 교차표 (중복 인원 제외)."""
    meta = {p["person_id"]: p for p in persons}
    seen = {}  # (pjt, cl) -> set(person_id)
    for a in assignments:
        m = meta.get(a["person_id"], {})
        key = (m.get("pjt", "?"), m.get("cl_level", "?"))
        seen.setdefault(key, set()).add(a["person_id"])
    pjts = sorted({k[0] for k in seen})
    cls = sorted({k[1] for k in seen})
    lines = ["| pjt \\ cl | " + " | ".join(cls) + " |",
             "|---|" + "---|" * len(cls)]
    for pj in pjts:
        row = [str(len(seen.get((pj, cl), ()))) for cl in cls]
        lines.append(f"| {pj} | " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_markdown(aggregates, persons, assignments, *, anonymize=False,
                    failed=None, extract_dropped=0, assign_dropped=0):
    aggregates, persons, assignments = load_json(aggregates), load_json(persons), load_json(assignments)
    name_by_id = {p["person_id"]: p.get("name") for p in persons}
    ev_by_cat = {}  # category -> [(pid, quote)]
    for a in assignments:
        ev_by_cat.setdefault(a["category"], []).append((a["person_id"], a["quote"]))

    out = ["# 미래 역량 지도 — 리더십 워크숍 입력물", "",
           "> 이 문서는 **확정된 10년 로드맵이 아니라** 리더십 워크숍의 입력물이다. "
           "시간축·시퀀싱·전략(\"꿈\")은 데이터에 없으며 워크숍에서 사람이 채운다.", ""]

    out.append("## 역량 테마 카드\n")
    for c in aggregates["categories"]:
        out.append(f"### {c['name']}  `{c['readiness']}`")
        out.append(f"- 기여 {c['people']}명 · 확산도 pjt {c['pjt_spread']}/cl {c['cl_spread']} "
                   f"· 보유 {c['have']} / 갭 {c['gap']}")
        for pid, quote in ev_by_cat.get(c["name"], [])[:3]:
            out.append(f"  > {oneline(quote)} — {_name(pid, name_by_id, anonymize)}")
        out.append("")

    out += ["## pjt × cl_level 교차표", "", _crosstab(assignments, persons), ""]

    out.append("## 소수 의견 (별도 트랙)\n")
    if aggregates.get("minority"):
        for m in aggregates["minority"]:
            out.append(f"- {m['name']} ({m['people']}명) `{m['readiness']}`")
    else:
        out.append("- (없음)")
    out.append("")

    cov = coverage(persons, assignments, failed=failed,
                   extract_dropped=extract_dropped, assign_dropped=assign_dropped)
    out += ["## 커버리지 리포트", "",
            f"- 대상 {cov['total_people']}명 · 무신호 {cov['no_signal']}명 "
            f"({cov['no_signal_rate']:.0%})",
            f"- 배정 {cov['assignments']}건 · Other {cov['other']}건 ({cov['other_rate']:.0%})",
            f"- 추출 폐기 인원 {cov['failed_count']} · 인용검증 폐기 항목 {cov['dropped_count']}",
            "", "커버리지가 낮으면 결과 신뢰도를 이 숫자로 방어한다.", ""]

    out.append("## 워크숍 미결 질문 (데이터가 답하지 못한 것)\n")
    gaps = [c["name"] for c in aggregates["categories"] if c["readiness"] == "갭만 있음"]
    for g in gaps:
        out.append(f"- '{g}' 갭을 언제·어떻게 메울 것인가? (준비도만 있고 시점은 데이터에 없음)")
    out += ["- 이 역량들이 향하는 팀의 10년 \"꿈\"은 무엇인가? (know-why 공백)",
            "- 소수 의견 중 팀의 미래 씨앗으로 키울 것은?"]
    return "\n".join(out) + "\n"


def write(aggregates, persons, assignments, out_path, **kw):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_markdown(aggregates, persons, assignments, **kw), encoding="utf-8")
    return out_path


def main(data_dir=ROOT / "data" / "task_discovery"):
    d = Path(data_dir)
    out = write(d / "aggregates.json", d / "extracted.json", d / "assignments.json",
                d / "workshop-input.md")
    print(f"렌더 → {out}", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
