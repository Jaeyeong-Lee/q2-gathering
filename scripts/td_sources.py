"""task-discovery 스테이지 0: 합성 근원경쟁력 코퍼스 생성 (S1-1, 이슈 #16).

실데이터는 보안상 반출 불가 → 이후 스테이지를 개발·검증할 원문 입력을 만든다.
사람마다 name·cl_level·pjt·part·text. text는 *추출 이전 원문*(facet 아님).
문서 이질성 4종을 반드시 포함: 3단 준수 / 3단 미준수 / 무내용 / CL4 서술형.

조직은 2단: pjt(상위 3조직) → part(세부). 후공정(back-end) DRAM 테스트 도메인.
참조: feat/task-discovery의 generate_sources 원문 템플릿 + gen_memtest 도메인 키워드.

usage: python scripts/td_sources.py [n] [seed]  → data/task_discovery/sources.json
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data" / "task_discovery" / "sources.json"

# 문서 케이스 (introspection용 — sources.json에는 안 나감)
CASE_STD = "3단준수"
CASE_MESSY = "3단미준수"
CASE_EMPTY = "무내용"
CASE_CL4 = "CL4서술형"

_SURNAMES = "김이박최정강조윤장임한오서신권황안송류전홍"
_GIVENS = ["민준", "서연", "도윤", "하은", "지호", "수아", "예준", "지유", "시우", "채원",
           "주원", "다은", "건우", "예린", "현우", "소율", "우진", "가은", "선우", "유나"]

# pjt(상위) → part(세부). part는 반드시 소속 pjt와 정합.
PJT_PARTS = {
    "양산기술": ["Test PGM개발", "ATE운영", "병렬테스트효율", "양산Yield"],
    "공정기술": ["Burn-in신뢰성", "고장분석(FA)", "설비·Handler", "품질보증(DPPM)"],
    "기획운영": ["데이터·AX", "기획·운영"],
}
# 기획운영은 소수 — 확산도가 조직신호/국소로 갈리도록 편중
_PJT_WEIGHTS = {"양산기술": 0.42, "공정기술": 0.42, "기획운영": 0.16}

# pjt별 미래과제 후보(도메인 키워드 내장) — 회고 원문에 녹인다. 파트 성격과 상관지어
# 다운스트림 taxonomy/확산도가 의미 있게 뭉치도록 pjt마다 어휘를 분리.
_PJT_TASKS = {
    "양산기술": ["Advantest V93000 Test PGM 디버깅 시간 단축", "Magnum 테스터 Para 병렬 테스트 효율화",
               "양산 Yield 저하 원인 분석·개선", "테스트 타임 단축을 위한 PGM 구조 최적화",
               "Teradyne 플랫폼 멀티사이트 확대", "신제품 D1b 초기 양산 Yield 안정화"],
    "공정기술": ["MBT(Monitoring Burn-in Test) 신뢰성 강화", "BIB(Burn-in Board) 설계·수명 관리",
               "CLT(Chamber형 LFT Test) 조건 정교화", "HFT(High-temp Final Test) 커버리지 확대",
               "STDF 기반 고장분석(FA) 자동화", "DPPM 품질 개선을 위한 선제 진단"],
    "기획운영": ["AX(AI Transformation) 기반 테스트 데이터 분석", "테스트 데이터(STDF) 통합 관리 체계",
               "D1b 신제품 램프업 기획", "설비 운영 지표 표준화"],
}
_SKILLS = ["파이썬 데이터 분석", "STDF 파싱 자동화", "ATE 스크립팅", "통계적 공정관리(SPC)",
           "머신러닝 이상탐지", "설비 자동화 제어"]

# 3단 준수 (헤더 있음, 미래과제가 3절에 위치)
_TPL_STD = """1. 상반기 성과 및 하반기 전략
상반기에는 {d1} 업무를 맡아 성과를 냈다. 진행 과정에서 반복 수작업이 병목임을 확인했고, 이 경험이 하반기 계획의 출발점이 됐다. 하반기에는 {d2}에 집중하려 한다.
2. 커리어 회고 및 확보 역량
현장 업무를 거치며 {s1} 역량을 확보했고, 최근에는 {s2}를 실무에 적용해 왔다.
3. 미래 업무
단기적으로는 {d2} 체계를 만들고 싶다. 장기적으로는 {d3}까지 확장해, 팀이 재사용할 수 있는 기반을 만드는 것이 목표다."""

# 3단 미준수 (번호 헤더 없이 문단이 뒤섞임 — 실데이터의 흔한 이탈)
_TPL_MESSY = """올해는 {d1} 관련 일을 많이 했습니다. {s1}도 익혔고요. 앞으로 {d2}를 해보고 싶은데 {d3}도 관심이 있습니다. 그동안 배운 {s2}를 살려서 팀에 도움이 되면 좋겠습니다. 이것저것 하다 보니 정리가 잘 안 되네요."""

# CL4 미래 위주 서술형 (헤더 없이 미래 방향 중심)
_TPL_CL4 = """앞으로의 방향
{d1}을(를) 팀 표준으로 자리잡게 하는 것이 목표다. 지금은 담당자마다 방식이 달라 결과를 한곳에서 비교하기 어렵다. 이를 위해 {s1}와(과) {s2} 역량을 확보해 왔다. 단기적으로는 {d2} 파일럿을 추진하고, 검증한 절차를 표준에 반영하는 것까지가 계획이다."""

# 무내용 (선언적, 도메인 신호 없음 — 추출이 no-signal로 격리해야 함)
_TPL_EMPTY = "그동안 여러 업무를 두루 경험했습니다. 앞으로도 팀에 보탬이 되도록 열심히 하겠습니다."


def _pick_case(cl_level, rng):
    """케이스 결정. 무내용 ~8%, CL4는 서술형, CL2/3는 대부분 준수·일부 미준수."""
    if rng.random() < 0.08:
        return CASE_EMPTY
    if cl_level == "CL4":
        return CASE_CL4
    return CASE_MESSY if rng.random() < 0.2 else CASE_STD


def _render(case, tasks, skills, rng):
    d = rng.sample(tasks, min(3, len(tasks)))
    while len(d) < 3:  # 풀이 3개 미만이면 재사용 허용
        d.append(rng.choice(tasks))
    s = rng.sample(skills, 2)
    if case == CASE_EMPTY:
        return _TPL_EMPTY
    if case == CASE_CL4:
        return _TPL_CL4.format(d1=d[0], d2=d[1], s1=s[0], s2=s[1])
    if case == CASE_MESSY:
        return _TPL_MESSY.format(d1=d[0], d2=d[1], d3=d[2], s1=s[0], s2=s[1])
    return _TPL_STD.format(d1=d[0], d2=d[1], d3=d[2], s1=s[0], s2=s[1])


def generate(n=200, seed=0):
    """합성 원문 n명 생성. 각 dict에 introspection용 case 포함. 고정 시드 재현."""
    rng = random.Random(seed)
    pjts, weights = zip(*_PJT_WEIGHTS.items())
    docs = []
    for i in range(1, n + 1):
        pjt = rng.choices(pjts, weights=weights)[0]
        part = rng.choice(PJT_PARTS[pjt])
        cl = rng.choices(["CL2", "CL3", "CL4"], weights=[0.3, 0.45, 0.25])[0]
        case = _pick_case(cl, rng)
        text = _render(case, _PJT_TASKS[pjt], _SKILLS, rng)
        docs.append({"id": i, "name": rng.choice(_SURNAMES) + rng.choice(_GIVENS),
                     "cl_level": cl, "pjt": pjt, "part": part, "text": text, "case": case})
    return docs


def to_sources(docs):
    """introspection용 case 필드를 떼고 sources.json에 쓸 형태로."""
    return [{k: v for k, v in d.items() if k != "case"} for d in docs]


def write(out_path=OUT, n=200, seed=0):
    docs = to_sources(generate(n, seed))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(docs, ensure_ascii=False, indent=1), encoding="utf-8")
    return docs


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    d = generate(n, seed)
    cases = {x["case"] for x in d}
    assert {CASE_STD, CASE_MESSY, CASE_EMPTY, CASE_CL4} <= cases, f"케이스 누락: {cases}"
    assert all(x["part"] in PJT_PARTS[x["pjt"]] for x in d), "pjt-part 불일치"
    write(n=n, seed=seed)
    print(f"생성: {OUT} ({len(d)}명, 케이스 {sorted(cases)})", file=sys.stderr)
