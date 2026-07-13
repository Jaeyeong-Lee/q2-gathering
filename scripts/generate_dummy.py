"""더미 데이터 생성기 — Phase 1: 실데이터(PPT/임베딩) 확보 전 파이프라인 검증용.

산출: persons.json / neighbors.json / freq.json (todos/001 스키마)
"""
import json
from pathlib import Path
import random

from config import K

PJTS = ["설비지능화", "공정AI", "비전검사", "예지보전", "디지털트윈", "MES고도화", "로봇자동화", "품질분석"]
SURNAMES = "김이박최정강조윤장임한오서신권황안송류전홍"
GIVENS = [
    "민준", "서연", "도윤", "하은", "지호", "수아", "예준", "지유", "시우", "채원",
    "주원", "다은", "건우", "예린", "현우", "소율", "우진", "가은", "선우", "유나",
]
CL_LEVELS = ["CL2", "CL3", "CL4"]
KEYWORDS = [
    "용접", "PLC", "비전검사", "딥러닝", "공정최적화", "설비보전", "로봇티칭", "데이터분석",
    "품질관리", "자동화", "금형", "사출", "도장", "물류", "센서", "제어",
    "시뮬레이션", "표준화", "원가절감", "안전관리", "협업", "문제해결", "현장개선", "신뢰성",
]
TAGS = [
    "문제해결형", "데이터드리븐", "현장밀착", "자동화전문", "협업리더", "꼼꼼함",
    "빠른실행", "장비장인", "공정통", "품질집착", "멘토형", "신기술탐구",
]


def _make_freq(persons, rng):
    # 실데이터에서는 003(형태소 분석)이 text에서 집계 — 더미는 키워드 풀에서 임의 생성
    freq = {}
    for p in persons:
        words = rng.sample(KEYWORDS, rng.randint(8, 14))
        freq[str(p["id"])] = {w: rng.randint(1, 9) for w in words}
    return freq


def _make_person(i, name, rng):
    kws = rng.sample(KEYWORDS, 6)
    # text=정제 전 원문(흩어진 키워드 나열), normalized_text=LLM 정제본 형태
    raw_text = f"{kws[0]} {kws[1]} {kws[2]} {kws[3]} {kws[4]} {kws[5]} 관련 업무 다수 수행"
    normalized_text = (
        f"# 근원경쟁력\n\n"
        f"## 핵심 역량\n{kws[0]}, {kws[1]} 중심으로 현장 경험을 쌓아왔습니다.\n\n"
        f"## 주요 경력\n{kws[2]} 및 {kws[3]} 업무를 담당하며 {kws[4]} 프로젝트를 수행했습니다.\n\n"
        f"## 강점\n{kws[5]} 분야에서 팀에 기여할 수 있습니다.\n"
    )
    return {
        "id": i,
        "name": name,
        "pjt": rng.choice(PJTS),
        "cl_level": rng.choices(CL_LEVELS, weights=[0.3, 0.45, 0.25])[0],
        "text": raw_text,
        "normalized_text": normalized_text,
        "tags": rng.sample(TAGS, rng.randint(3, 5)),
    }


def _make_neighbors(persons, rng):
    # 같은 pjt/공통 태그에 보너스를 줘 실데이터처럼 클러스터가 생기게 한다
    n = len(persons)
    sim = {}
    for i in range(n):
        for j in range(i + 1, n):
            a, b = persons[i], persons[j]
            s = rng.uniform(0.25, 0.6)
            if a["pjt"] == b["pjt"]:
                s += 0.2
            s += 0.04 * len(set(a["tags"]) & set(b["tags"]))
            sim[(i, j)] = round(min(s, 0.99), 4)

    neighbors = {}
    for i in range(n):
        scored = [(sim[(min(i, j), max(i, j))], j) for j in range(n) if j != i]
        scored.sort(key=lambda t: (-t[0], t[1]))
        neighbors[str(i)] = [{"id": j, "similarity": s} for s, j in scored[:K]]
    return neighbors


def generate(n=150, seed=42):
    rng = random.Random(seed)
    all_names = [s + g for s in SURNAMES for g in GIVENS]
    names = rng.sample(all_names, n)
    persons = [_make_person(i, name, rng) for i, name in enumerate(names)]
    return {
        "persons": persons,
        "neighbors": _make_neighbors(persons, rng),
        "freq": _make_freq(persons, rng),
    }


def main(out_dir=Path(__file__).parent.parent / "data"):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = generate()
    for name in ("persons", "neighbors", "freq"):
        path = out_dir / f"{name}.json"
        path.write_text(json.dumps(data[name], ensure_ascii=False, indent=1))
    return out_dir


if __name__ == "__main__":
    print(main())
