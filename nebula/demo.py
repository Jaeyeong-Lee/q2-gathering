"""Deterministic fixture provider, clearly distinct from semantic LLM inference."""

from typing import Any
import re

TEAM_TOPICS = {
    "테스트 개발": ["병렬 테스트 개선", "검증 누락 줄이기", "실행 시간 단축"],
    "양산 분석": ["수율 변동 분석", "불량 패턴 진단", "분석 재현성 확보"],
    "신뢰성 평가": [
        "열화 특성 분석",
        "시험 조건 설계",
        "장기 불량 재현",
        "수명 분포 해석",
    ],
    "설비 기술": ["정비 시점 판단", "장비 편차 조정", "조작 자동화"],
    "데이터 플랫폼": ["기록 식별자 연결", "데이터 품질 검증", "분석 환경 공유"],
    "품질 기술": ["품질 전조 분석", "원인 검증"],
    "제품 전개": ["초기 검증 표준화", "변경 영향 추적", "검증 경험 재사용"],
    "기술 기획": ["기술 경험 전수", "투자 판단 기준", "파일럿 검증 설계"],
}


def source():
    result: list[dict[str, Any]] = []
    counts = [12, 16, 20, 20, 28, 28, 36, 40]
    for pi, (pjt, topics) in enumerate(TEAM_TOPICS.items()):
        for j in range(counts[pi]):
            pid = len(result) + 1
            paragraphs = []
            for k in range(1 + pid % 2):
                topic = topics[(j + k) % len(topics)]
                marker = ["단기적으로 ", "중기적으로 ", "장기적으로 ", ""][
                    (pid + k) % 4
                ]
                lines = [f"{marker}{topic} 과제를 추진하고 싶다."]
                if pid % 5:
                    lines.append(
                        f"이 과제에는 기존의 {topic} 관련 분석 경험을 활용하려 한다."
                    )
                if pid % 3:
                    lines.append(f"이를 위해 {topic} 검증 설계 역량이 더 필요하다.")
                paragraphs.append("\n".join(lines))
            if pid % 19 == 0:
                paragraphs = ["앞으로도 맡은 일을 성실히 수행하겠습니다."]
            if pid % 11 == 0:
                paragraphs.append("별도로 문서 작성 경험을 갖고 있다.")
            result.append(
                {
                    "id": str(pid),
                    "name": f"합성 인물 {pid:03}",
                    "pjt": pjt,
                    "text": "\n\n".join(paragraphs),
                }
            )
    return result


def _extract(text):
    """Split the synthetic paragraph shape into tasks and capabilities, without refs."""
    tasks: list[dict[str, Any]] = []
    caps: list[dict[str, Any]] = []
    for paragraph in text.split("\n\n"):
        lines = paragraph.splitlines()
        if "과제를 추진하고 싶다." not in lines[0]:
            if "문서 작성 경험" in paragraph:
                caps.append(
                    {
                        "kind": "have",
                        "label": "문서 작성",
                        "quote": paragraph,
                        "occurrence": 1,
                    }
                )
            continue
        quote = lines[0]
        label = re.sub(r"^(단기|중기|장기)적으로 ", "", quote).replace(
            " 과제를 추진하고 싶다.", ""
        )
        h = next(
            (
                h
                for marker, h in [("단기", "short"), ("중기", "mid"), ("장기", "long")]
                if quote.startswith(marker)
            ),
            "unknown",
        )
        tasks.append(
            {
                "label": label,
                "quote": quote,
                "occurrence": 1,
                "horizon": h,
                "time_quote": quote if h != "unknown" else None,
            }
        )
        for line in lines[1:]:
            have = line.startswith("이 과제에는")
            caps.append(
                {
                    "kind": "have" if have else "need",
                    "label": label + (" 분석 경험" if have else " 검증 설계"),
                    "quote": line,
                    "occurrence": 1,
                }
            )
    return tasks, caps


class FakeClient:
    cache_identity = {"provider": "fake", "version": 1}

    def complete(self, stage, system, payload):
        if stage in ("tasks", "capabilities"):
            tasks, caps = _extract(payload["text"])
            return {stage: tasks if stage == "tasks" else caps}
        if stage == "links":
            links: list[dict[str, Any]] = []
            for paragraph in payload["text"].split("\n\n"):
                task = next(
                    (t for t in payload["tasks"] if t["quote"] in paragraph), None
                )
                if task is None:
                    continue
                links.extend(
                    {
                        "task_ref": task["ref"],
                        "capability_ref": c["ref"],
                        "relation_quote": paragraph,
                    }
                    for c in payload["capabilities"]
                    if c["quote"] in paragraph
                )
            return {"links": links}
        if stage == "taxonomy":
            existing = {c["name"] for c in payload["existing"]}
            # "기타 "로 시작하는 합성 과제는 분류하지 않아 미분류 경로를 픽스처에서 재현한다.
            labels = {t["label"] for t in payload["tasks"] if not t["label"].startswith("기타 ")}
            names = sorted(labels - existing)
            return {
                "additions": [
                    {
                        "name": n,
                        "definition": n + "에 관한 미래 업무",
                        "includes": n + "를 대상으로 하는 개선과 검증",
                        "excludes": "대상이 다른 업무 및 일반적인 학습 의향",
                    }
                    for n in names
                ]
            }
        if stage == "consolidate":
            return {
                "additions": [
                    {k: c[k] for k in ("name", "definition", "includes", "excludes")}
                    for c in payload["drafts"]
                ]
            }
        if stage == "assign":
            ids = {c["name"]: c["id"] for c in payload["categories"]}
            return {
                "assignments": [
                    {
                        "task_id": t["id"],
                        "category_id": ids.get(t["label"]),
                        "reason": "합성 원문의 업무 대상과 카테고리 정의가 일치함",
                    }
                    for t in payload["tasks"]
                ]
            }
        raise ValueError("unknown demo stage")


def network(inputs, k=4):
    """Actual TF-IDF cosine on synthetic text, only to exercise the existing-network input."""
    import math
    from collections import Counter

    bags = [Counter(re.findall(r"[가-힣A-Za-z0-9]+", p["text"])) for p in inputs]
    df = Counter(token for bag in bags for token in bag)
    vectors = [
        {
            token: (1 + math.log(count))
            * (1 + math.log((1 + len(inputs)) / (1 + df[token])))
            for token, count in bag.items()
        }
        for bag in bags
    ]
    norms = [math.sqrt(sum(v * v for v in vector.values())) for vector in vectors]
    neighbors = {}
    for i, person in enumerate(inputs):
        scores = []
        for j, other in enumerate(inputs):
            if i == j:
                continue
            score = sum(v * vectors[j].get(k, 0) for k, v in vectors[i].items()) / (
                norms[i] * norms[j]
            )
            scores.append(
                {"id": other["id"], "similarity": round(min(1.0, max(-1.0, score)), 6)}
            )
        neighbors[person["id"]] = sorted(
            scores, key=lambda n: (-n["similarity"], n["id"])
        )[:k]
    return neighbors
