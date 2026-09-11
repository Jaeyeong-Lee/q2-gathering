"""LLM 없이 파이프라인을 완주시키는 결정적 스텁 (#010 보강).

`make td-sample`은 Gemini 실호출을 쓴다. 이 모듈은 그 키가 없거나, 화면을 개발하며
산출물을 수십 번 다시 만들어야 할 때 쓰는 대체 경로다. LLM 호출 0회, 같은 seed면 같은 결과.

**왜 테스트의 가짜 call을 그대로 쓰지 않나**: tests/test_td_pipeline.py의 `_fakes()`는
스테이지가 도는지만 보므로 카테고리를 하나만 뱉는다. 그걸로 성좌 지도를 그리면 별자리가
하나뿐인 허수아비가 된다. 여기서는 합성 코퍼스(td_sources.py)가 pjt별로 분리해 둔 도메인
어휘를 키워드로 잡아 카테고리 10개로 흩어, 확산도·AX 언급·horizon이 화면에서 의미를 갖게 한다.

인용은 전부 원문에서 잘라낸 실제 부분문자열이라 grounding 검증(quote_in_source)을 그대로 탄다.
"""
import json
import re

# 카테고리 ← 합성 코퍼스 어휘. 앞의 것부터 매칭하므로 구체적인 항목을 위에 둔다.
# name은 td_taxonomy 프롬프트가 예시로 준 형태(짧은 명사구)를 따른다.
CATEGORIES = [
    ("Test PGM 디버깅·구조 최적화", ("Test PGM 디버깅", "PGM 구조 최적화", "ATE 스크립팅")),
    ("병렬 테스트·멀티사이트 효율화", ("병렬 테스트", "멀티사이트")),
    ("D1b 신제품 램프업", ("D1b 신제품", "D1b 초기", "램프업")),
    ("양산 Yield 안정화", ("Yield",)),
    ("Burn-in 신뢰성·BIB 관리", ("Burn-in", "MBT", "BIB")),
    ("고온·챔버 테스트 조건 정교화", ("CLT", "HFT", "High-temp", "Chamber")),
    ("STDF 기반 고장분석 자동화", ("고장분석", "STDF 파싱")),
    ("DPPM 품질 선제진단", ("DPPM", "통계적 공정관리")),
    ("AX 기반 테스트 데이터 분석", ("AX", "머신러닝", "데이터 분석", "테스트 데이터")),
    ("설비 운영·자동화 표준화", ("설비", "운영 지표")),
]

_RELATIONS = [
    ("병렬 테스트·멀티사이트 효율화", "Test PGM 디버깅·구조 최적화", "broader"),
    ("STDF 기반 고장분석 자동화", "AX 기반 테스트 데이터 분석", "related"),
    ("DPPM 품질 선제진단", "Burn-in 신뢰성·BIB 관리", "related"),
    ("D1b 신제품 램프업", "양산 Yield 안정화", "related"),
]

# 원문에 실제로 박혀 있는 구절들 — 인용으로 그대로 잘라 쓴다(td_sources.py의 어휘와 동기).
_TASK_PHRASES = [
    "Advantest V93000 Test PGM 디버깅 시간 단축", "Magnum 테스터 Para 병렬 테스트 효율화",
    "양산 Yield 저하 원인 분석·개선", "테스트 타임 단축을 위한 PGM 구조 최적화",
    "Teradyne 플랫폼 멀티사이트 확대", "신제품 D1b 초기 양산 Yield 안정화",
    "MBT(Monitoring Burn-in Test) 신뢰성 강화", "BIB(Burn-in Board) 설계·수명 관리",
    "CLT(Chamber형 LFT Test) 조건 정교화", "HFT(High-temp Final Test) 커버리지 확대",
    "STDF 기반 고장분석(FA) 자동화", "DPPM 품질 개선을 위한 선제 진단",
    "AX(AI Transformation) 기반 테스트 데이터 분석", "테스트 데이터(STDF) 통합 관리 체계",
    "D1b 신제품 램프업 기획", "설비 운영 지표 표준화",
]
_SKILL_PHRASES = ["파이썬 데이터 분석", "STDF 파싱 자동화", "ATE 스크립팅",
                  "통계적 공정관리(SPC)", "머신러닝 이상탐지", "설비 자동화 제어"]


def category_of(text):
    """텍스트가 어느 카테고리에 속하는지 — 키워드 우선순위 매칭. 없으면 None."""
    for name, keys in CATEGORIES:
        if any(k in text for k in keys):
            return name, next(k for k in keys if k in text)
    return None


def _found(phrases, src):
    """원문에 등장하는 구절을 등장 순서대로 (중복 제거)."""
    hits = [(src.index(p), p) for p in phrases if p in src]
    return [p for _, p in sorted(hits)]


def extract(prompt):
    src = prompt.split("원문:\n", 1)[1].strip()
    tasks, skills = _found(_TASK_PHRASES, src), _found(_SKILL_PHRASES, src)
    if not tasks and not skills:                      # 무내용 템플릿 → 신호 없음
        return json.dumps({"signal_present": False, "future_task": [],
                           "capability_have": [], "capability_gap": [], "direction": None},
                          ensure_ascii=False)

    # horizon은 원문의 단기/장기 표현을 실제로 반영한다 — 없으면 불명.
    def horizon(i):
        if "단기적으로는" in src and i == 0:
            return "단기"
        if "장기적으로는" in src and i == 1:
            return "장기"
        return "불명"

    future = [{"text": f"{p} 과제를 추진하려 한다", "horizon": horizon(i), "quotes": [p]}
              for i, p in enumerate(tasks[:2])]
    have = [{"text": f"{s} 역량을 실무에 적용해 왔다", "quotes": [s]} for s in skills[:2]]
    # 갭은 언급했으나 아직 못 하는 것 — 세 번째 과제가 있으면 그것으로.
    gap = [{"text": f"{p} 수행에 필요한 역량이 아직 부족하다", "quotes": [p]}
           for p in tasks[2:3]]
    direction = ({"text": f"{tasks[0]} 방향으로 팀 표준을 만들고 싶다", "quotes": [tasks[0]]}
                 if tasks else None)
    return json.dumps({"signal_present": True, "future_task": future,
                       "capability_have": have, "capability_gap": gap, "direction": direction},
                      ensure_ascii=False)


def taxonomy(prompt):
    """배치마다 같은 고정 taxonomy를 돌려준다 — induce가 배치 결과로 통째 교체하므로
    이것만으로 안정적인 카테고리 집합이 된다. 마지막 relations 패스만 분기."""
    if "relations" in prompt:
        return json.dumps({"relations": [{"from": f, "to": t, "type": ty}
                                         for f, t, ty in _RELATIONS]}, ensure_ascii=False)
    return json.dumps({"taxonomy": [
        {"name": name,
         "definition": f"{keys[0]} 관련 과제와 역량을 묶는다.",
         "inclusion_criteria": f"{'·'.join(keys)} 중 하나를 다루면 여기에 넣는다."}
        for name, keys in CATEGORIES]}, ensure_ascii=False)


def assign(prompt):
    item = prompt.split("항목:\n", 1)[1].strip()
    hit = category_of(item)
    if hit is None:
        return json.dumps({"category": "Other", "quote": item[:10]}, ensure_ascii=False)
    name, key = hit
    return json.dumps({"category": name, "quote": key}, ensure_ascii=False)


def narrate(prompt):
    if "카테고리 요약" in prompt:
        return json.dumps({"trends": [{"text": "여러 조직이 같은 과제를 반복해서 언급한다",
                                       "citation_ids": [0]}],
                           "minority_notes": []}, ensure_ascii=False)
    return json.dumps({"narrative": "합성 코퍼스 기반 서사 — 해석층 자리 확인용",
                       "citation_ids": [0]}, ensure_ascii=False)


def embed(text):
    """결정적 의사 임베딩. 실제 의미 벡터가 아니라 **같은 입력이면 같은 좌표**를 주는 장치다.
    문자 코드를 8차원으로 접어 넣는다 — tests/test_td_index.py의 가짜 embed와 같은 발상."""
    vec = [0.0] * 8
    for i, ch in enumerate(text):
        vec[i % 8] += (ord(ch) % 97) / 97.0
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [v / norm for v in vec]


def calls():
    """run_all이 요구하는 4종 call 묶음."""
    return {"extract_call": extract, "taxo_call": taxonomy,
            "assign_call": assign, "narrate_call": narrate}
