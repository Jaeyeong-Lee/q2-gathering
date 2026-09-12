"""3Q 발표용 합성 픽스처를 만든다 — persons.json, neighbors.json, showcase.json.

전부 합성이다. 문장은 nebula.demo.FakeClient가 추출하는 모양을 따르므로
`python3 -m nebula demo --input persons.json --network neighbors.json`으로 LLM 없이 완주한다.
같은 코드면 몇 번을 돌려도 바이트 단위로 같은 파일이 나온다.
"""

import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))

from nebula.demo import TEAM_TOPICS, network  # noqa: E402

# PJT 이름은 demo와 같다. 주제만 늘려 PJT마다 과제군이 5~6개 나오게 한다.
EXTRA_TOPICS = {
    "테스트 개발": ["멀티사이트 조건 정리", "테스트 커버리지 측정"],
    "양산 분석": ["공정 편차 추적", "분석 리포트 자동화"],
    "신뢰성 평가": ["가속 시험 모델링"],
    "설비 기술": ["핸들러 가동률 개선", "소모품 수명 관리"],
    "데이터 플랫폼": ["STDF 통합 적재", "분석 권한 체계"],
    "품질 기술": ["고객 불량 회신 단축", "출하 판정 기준 정비", "품질 지표 표준화"],
    "제품 전개": ["신제품 램프업 체크리스트", "고객 요구 사양 추적"],
    "기술 기획": ["외부 기술 동향 정리", "로드맵 토론 준비"],
}
# 합 320. PJT 크기를 고르지 않게 해 가장 큰 PJT(70명)로 성운 성능을 본다.
COUNTS = dict(zip(TEAM_TOPICS, [18, 24, 30, 36, 40, 46, 56, 70]))
SHOWCASE_PJT = "데이터 플랫폼"
MARKERS = ["단기적으로 ", "중기적으로 ", "장기적으로 ", ""]
IDLE = "앞으로도 맡은 일을 성실히 수행하겠습니다."
DOC = "별도로 문서 작성 경험을 갖고 있다."
# FakeClient는 "기타 "로 시작하는 과제를 분류하지 않는다 → 미분류 경로를 재현한다.
OTHER = "기타 개인 관심 과제를 추진하고 싶다."


def paragraph(marker, topic, have, need):
    lines = [f"{marker}{topic} 과제를 추진하고 싶다."]
    if have:
        lines.append(f"이 과제에는 기존의 {topic} 관련 분석 경험을 활용하려 한다.")
    if need:
        lines.append(f"이를 위해 {topic} 검증 설계 역량이 더 필요하다.")
    return "\n".join(lines)


def showcase_text(topics):
    """1부 분열 장면의 자리표시. Jay 예시가 오면 이 원문만 바뀐다(plan §5.3)."""
    return "\n\n".join(paragraph(m, t, True, True) for m, t in zip(MARKERS, topics))


def person_text(rng, topics):
    if rng.random() < 0.05:
        return IDLE if rng.random() < 0.7 else IDLE + "\n\n" + DOC
    count = rng.choices([1, 2, 3, 4], weights=[25, 35, 25, 10])[0]
    parts = [
        paragraph(rng.choice(MARKERS), t, rng.random() < 0.6, rng.random() < 0.6)
        for t in rng.sample(topics, count)
    ]
    if rng.random() < 0.04:
        parts.append(OTHER)
    if rng.random() < 0.09:
        parts.append(DOC)
    return "\n\n".join(parts)


def build():
    rng = random.Random(20260915)
    topics = {pjt: TEAM_TOPICS[pjt] + EXTRA_TOPICS[pjt] for pjt in TEAM_TOPICS}
    for names in topics.values():
        # FakeClient가 인용을 부분 문자열로 찾으므로 한 주제가 다른 주제의 꼬리면 연결이 섞인다.
        assert not any(a != b and b.endswith(a) for a in names for b in names), names
    persons, serial = [], 1
    for pjt, count in COUNTS.items():
        for i in range(count):
            if pjt == SHOWCASE_PJT and i == 0:
                persons.append(
                    {"id": "P000", "name": "예시 인물", "pjt": pjt, "text": showcase_text(topics[pjt])}
                )
                continue
            persons.append(
                {
                    "id": f"P{serial:03}",
                    "name": f"합성 인물 {serial:03}",
                    "pjt": pjt,
                    "text": person_text(rng, topics[pjt]),
                }
            )
            serial += 1
    return persons


def write(name, text):
    (HERE / name).write_text(text + "\n", encoding="utf-8")


def main():
    persons = build()
    idle = sum("과제를 추진하고 싶다." not in p["text"] for p in persons)
    other = sum(OTHER in p["text"] for p in persons)
    assert len(persons) == 320 and idle and other, (len(persons), idle, other)
    write("persons.json", json.dumps(persons, ensure_ascii=False, indent=1))
    write(
        "neighbors.json",
        json.dumps(network(persons, k=30), ensure_ascii=False, separators=(",", ":")),
    )
    write(
        "showcase.json",
        json.dumps(
            {"person_id": "P000", "pjt": SHOWCASE_PJT, "task_index": 0},
            ensure_ascii=False,
            indent=1,
        ),
    )
    print(f"persons={len(persons)} idle={idle} other={other} -> {HERE}")


if __name__ == "__main__":
    main()
