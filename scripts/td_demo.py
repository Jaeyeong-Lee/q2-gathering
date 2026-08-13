"""가짜 pjt 산출물 생성기 — td_view 화면을 실데이터 없이 띄워 보려고 만든 것.

파이프라인을 돌리지 않고 산출물 넷(extracted·taxonomy·assignments·aggregates)을
직접 만든다. 사람·조직·과제 어휘는 td_sources의 합성 코퍼스를 그대로 쓰고,
집계는 td_aggregate를 호출해 실제 파이프라인과 같은 규칙으로 계산한다.
따라서 화면에 뜨는 숫자는 앞뒤가 맞다 — 다만 원본이 가짜일 뿐이다.

파이프라인 검증에는 쓰지 마라. 그건 td_sources로 원문을 만들어 실제로 돌리는 쪽이다.

usage: python3 scripts/td_demo.py [출력디렉터리] [pjt수]
"""
import json
import random
import sys
from pathlib import Path

import td_sources
from td_aggregate import aggregate

FILES = ("extracted", "taxonomy", "assignments", "aggregates")

# 과제 어휘 → 카테고리. 분류 체계 단계가 내놓을 법한 묶음을 손으로 적어둔 것이다.
CATEGORY = {
    "Advantest V93000 Test PGM 디버깅 시간 단축": "Test PGM 개발 효율화",
    "테스트 타임 단축을 위한 PGM 구조 최적화": "Test PGM 개발 효율화",
    "Magnum 테스터 Para 병렬 테스트 효율화": "병렬 테스트 확대",
    "Teradyne 플랫폼 멀티사이트 확대": "병렬 테스트 확대",
    "양산 Yield 저하 원인 분석·개선": "양산 Yield 개선",
    "신제품 D1b 초기 양산 Yield 안정화": "양산 Yield 개선",
    "MBT(Monitoring Burn-in Test) 신뢰성 강화": "번인 신뢰성 확보",
    "BIB(Burn-in Board) 설계·수명 관리": "번인 신뢰성 확보",
    "CLT(Chamber형 LFT Test) 조건 정교화": "테스트 조건 정교화",
    "HFT(High-temp Final Test) 커버리지 확대": "테스트 조건 정교화",
    "STDF 기반 고장분석(FA) 자동화": "고장분석 자동화",
    "DPPM 품질 개선을 위한 선제 진단": "품질 선제 진단",
    "AX(AI Transformation) 기반 테스트 데이터 분석": "테스트 데이터 분석 체계",
    "테스트 데이터(STDF) 통합 관리 체계": "테스트 데이터 분석 체계",
    "D1b 신제품 램프업 기획": "신제품 램프업",
    "설비 운영 지표 표준화": "설비 운영 표준화",
}
RELATED = {"Test PGM 개발 효율화": "병렬 테스트 확대",
           "병렬 테스트 확대": "Test PGM 개발 효율화",
           "양산 Yield 개선": "고장분석 자동화",
           "번인 신뢰성 확보": "테스트 조건 정교화",
           "테스트 조건 정교화": "번인 신뢰성 확보",
           "고장분석 자동화": "테스트 데이터 분석 체계",
           "품질 선제 진단": "고장분석 자동화",
           "테스트 데이터 분석 체계": "설비 운영 표준화",
           "신제품 램프업": "양산 Yield 개선",
           "설비 운영 표준화": "테스트 데이터 분석 체계"}

# 인용은 원문에서 오려낸 문장이어야 한다 — 합성 원문의 문형을 그대로 쓴다.
Q_TASK = ("단기적으로는 {} 체계를 만들고 싶다.",
          "하반기에는 {}에 집중하려 한다.",
          "장기적으로는 {}까지 확장해, 팀이 재사용할 수 있는 기반을 만드는 것이 목표다.")
Q_HAVE = ("현장 업무를 거치며 {} 역량을 확보했다.", "최근에는 {}를 실무에 적용해 왔다.")
Q_GAP = ("{}는 아직 부족해 학습이 필요하다.", "{} 쪽은 경험이 얕아 보완하려 한다.")
HORIZONS = ("단기", "중기", "장기")


def _person(doc, rnd):
    """합성 원문 1건 → extracted 1건. 무내용 문서는 축을 비운다(신호 없음)."""
    base = {"person_id": doc["id"], "name": doc["name"], "pjt": doc["pjt"],
            "part": doc["part"], "cl_level": doc["cl_level"]}
    if doc["case"] == td_sources.CASE_EMPTY:
        return {**base, "signal_present": False, "direction": None,
                "future_task": [], "capability_have": [], "capability_gap": []}

    tasks = rnd.sample(td_sources._PJT_TASKS[doc["pjt"]], rnd.randint(1, 3))
    have, gap = rnd.sample(td_sources._SKILLS, 2)
    return {
        **base, "signal_present": True,
        "direction": {"text": f"{tasks[0]}을(를) 팀 표준으로 자리잡게 하는 것",
                      "quotes": [f"{tasks[0]}을(를) 팀 표준으로 자리잡게 하는 것이 목표다."]}
                     if doc["cl_level"] == "CL4" else None,
        "future_task": [{"text": t, "horizon": HORIZONS[i % 3],
                         "quotes": [Q_TASK[i % 3].format(t)]} for i, t in enumerate(tasks)],
        "capability_have": [{"text": have, "quotes": [rnd.choice(Q_HAVE).format(have)]}],
        "capability_gap": [{"text": gap, "quotes": [rnd.choice(Q_GAP).format(gap)]}],
    }


def _assignments(people, rnd):
    """추출 항목 → 카테고리 배정. 어휘에 없는 역량은 Other로 흘린다(실제로도 그렇다)."""
    rows = []
    for p in people:
        for axis in ("future_task", "capability_have", "capability_gap"):
            for item in p[axis]:
                cat = CATEGORY.get(item["text"])
                if cat is None:                       # 역량 어휘는 과제 카테고리에 얹는다
                    cat = rnd.choice(sorted(set(CATEGORY.values())) + ["Other"])
                rows.append({"person_id": p["person_id"], "axis": axis, "text": item["text"],
                             "category": cat, "quote": item["quotes"][0]})
    return rows


def build(seed=7, n_pjt=8, n_people=200):
    """pjt별 {파일명: 데이터}. pjt 하나 = 파트 하나로 잡아 8개 화면을 만든다."""
    rnd = random.Random(seed)
    docs = td_sources.generate(n=n_people, seed=seed)
    parts = [p for ps in td_sources.PJT_PARTS.values() for p in ps][:n_pjt]

    out = {}
    for k, part in enumerate(parts):
        people = [_person(d, rnd) for d in docs if d["part"] == part]
        rows = _assignments(people, rnd)
        cats = sorted({r["category"] for r in rows})
        out[f"pjt_{chr(ord('a') + k)}"] = {
            "extracted": people,
            "taxonomy": [{"name": c,
                          "definition": f"{c} 관련 과제와 역량을 묶은 카테고리",
                          "inclusion_criteria": f"{c}에 직접 기여하는 서술만 포함",
                          "relations": [{"to": RELATED[c], "type": "related"}]}
                         for c in cats if c in RELATED],
            "assignments": rows,
            "aggregates": aggregate(rows, people),
        }
    return out


def write(root, **kw):
    root = Path(root)
    for name, data in build(**kw).items():
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        for f in FILES:
            (d / f"{f}.json").write_text(json.dumps(data[f], ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    return root


if __name__ == "__main__":
    root = write(sys.argv[1] if len(sys.argv) > 1 else "data/task_discovery/demo",
                 n_pjt=int(sys.argv[2]) if len(sys.argv) > 2 else 8)
    made = sorted(p.name for p in root.iterdir() if p.is_dir())
    assert all((root / m / f"{f}.json").exists() for m in made for f in FILES)
    for m in made:
        people = json.loads((root / m / "extracted.json").read_text(encoding="utf-8"))
        assert people, f"{m}: 사람이 없다"
        # 무신호인데 항목이 남아 있으면 화면이 앞뒤가 안 맞는다
        assert all(p["signal_present"] or not (p["future_task"] or p["capability_have"]
                                               or p["capability_gap"] or p["direction"])
                   for p in people), m
    print(f"가짜 산출물 → {root} · pjt {len(made)}개: {', '.join(made)}", file=sys.stderr)
