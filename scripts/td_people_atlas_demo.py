"""Build a self-contained, synthetic-only person atlas. No API or real-data reads.

python3 scripts/td_people_atlas_demo.py
Uses character TF-IDF + the existing cosine neighbor function, not model embeddings.
Taxonomy and facets are authored fixtures; their quotes occur in the generated sources.
"""
import json
import math
import random
import re
from collections import Counter
from pathlib import Path

import numpy as np

from similarity import top_k_neighbors
from td_render_common import render, write_html

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "td_sample" / "people-atlas"
COLORS = ["#7dcfff", "#a7a4ff", "#f0afce", "#eeb78c", "#e5d688", "#9bd4bd", "#9fb8f0", "#cebcf4"]
PJTS = ["테스트 개발", "양산 분석", "신뢰성 평가", "설비 기술", "데이터 플랫폼", "품질 기술", "제품 전개", "기술 기획"]
COUNTS = [12, 16, 20, 20, 28, 28, 36, 40]
TOPICS = [
    ("diagnosis", "이상 징후를 더 일찍", "불량이 된 뒤 분석하는 일에서, 징후를 먼저 발견하는 일로.",
     "테스트·설비·품질 데이터의 이상 징후와 원인 분석", [
         "테스트 로그의 이상 패턴을 자동으로 찾아 원인 후보를 좁히는 진단 도구를 만들고 싶다.",
         "설비 센서의 미세한 변화를 모아 고장 전에 알림을 주는 체계를 만들고 싶다.",
         "품질 이력을 연결해 반복 불량의 전조를 먼저 발견하는 분석을 해보고 싶다.",
         "AI를 활용해 이상 징후의 원인 후보와 확인할 항목을 함께 제시하고 싶다."], [
         "테스트 로그를 파이썬으로 분석해 이상 패턴과 실제 불량의 관계를 확인했다.",
         "설비 센서 이력과 정비 기록을 비교하며 이상 징후를 분류한 경험이 있다.",
         "품질 이력에서 반복 불량을 묶고 원인을 추적하는 분석을 수행했다."]),
    ("data", "흩어진 데이터를 하나로", "서로 다른 기록을 연결하면, 서로의 일을 이해할 수 있다.",
     "데이터 수집·정합성·공통 식별자·표준화", [
         "테스트 결과와 설비 이력을 공통 식별자로 연결하는 데이터 기반을 만들고 싶다.",
         "각자 관리하는 분석 파일을 같은 형식으로 모아 재사용 가능한 데이터셋을 만들고 싶다.",
         "품질 데이터의 단위와 시각 기준을 통일해 조직 간 비교가 가능하게 하고 싶다."], [
         "테스트 결과 파일을 파싱하고 누락된 필드를 검증하는 수집기를 만들었다.",
         "서로 다른 시스템의 식별자를 매핑하고 데이터 정합성을 점검했다.",
         "분석 파일의 스키마를 정리하고 공통 데이터 사전을 작성했다."]),
    ("automation", "반복 작업에서 벗어나기", "사람의 시간을, 확인과 복사에서 판단과 개선으로.",
     "반복 작업 자동화와 운영 절차 개선", [
         "수작업으로 반복하는 결과 취합과 보고서 생성을 자동화하고 싶다.",
         "장비 설정 확인과 테스트 실행을 연결해 반복 조작을 줄이고 싶다.",
         "담당자마다 다른 점검 절차를 자동 실행 가능한 흐름으로 정리하고 싶다."], [
         "파이썬 스크립트로 반복 보고서의 데이터 취합을 자동화했다.",
         "장비 설정을 검사하는 스크립트를 작성해 반복 확인에 활용했다.",
         "운영 점검 절차를 정리하고 자동 실행 도구에 적용했다."]),
    ("knowledge", "경험이 다음 사람에게", "개인의 해결 경험을, 다시 꺼내 쓸 수 있는 팀의 자산으로.",
     "문제 해결 경험의 기록·검색·전수", [
         "문제 해결 과정과 실패 이유를 검색 가능한 사례집으로 남기고 싶다.",
         "새 담당자가 과거 조치의 배경까지 이해할 수 있는 인수인계 체계를 만들고 싶다.",
         "자주 묻는 기술 질문과 검증된 답변을 연결하는 지식 기반을 만들고 싶다."], [
         "반복 문의와 과거 조치 내용을 정리해 기술 사례 문서를 작성했다.",
         "신규 담당자 교육을 맡으며 문제 해결 과정을 단계별로 설명했다.",
         "팀의 기술 문서를 분류하고 사례를 찾을 수 있는 색인을 만들었다."]),
    ("efficiency", "테스트 시간을 줄이기", "같은 품질을 확인하면서, 더 적은 시간을 쓰는 방법.",
     "테스트 프로그램 최적화·병렬화·중복 제거", [
         "중복 테스트 항목을 찾아 품질을 유지하면서 전체 테스트 시간을 줄이고 싶다.",
         "테스트 프로그램의 병목을 분석해 병렬 실행 범위를 확대하고 싶다.",
         "제품별 테스트 조건을 비교해 불필요한 대기 시간을 줄이고 싶다."], [
         "테스트 프로그램의 실행 시간을 측정하고 병목 구간을 개선했다.",
         "병렬 테스트 조건을 바꿔가며 품질과 시간의 차이를 검증했다.",
         "테스트 항목의 중복 여부를 분석하고 조건을 조정했다."]),
    ("reliability", "오래 써도 믿을 수 있게", "눈앞의 통과를 넘어, 사용 조건 속의 신뢰성을 살피다.",
     "신뢰성 시험·열화·수명 검증", [
         "사용 환경을 반영한 신뢰성 시험 조건을 설계하고 싶다.",
         "온도와 전압 변화에 따른 열화 패턴을 분석해 수명 예측의 근거를 만들고 싶다.",
         "장시간 시험에서 나타나는 불량을 재현하고 검증 절차를 정교화하고 싶다."], [
         "온도 조건별 신뢰성 시험을 수행하고 열화 패턴을 비교했다.",
         "장시간 시험의 불량을 재현하며 수명 검증 자료를 정리했다.",
         "시험 조건과 실제 사용 환경의 차이를 검토했다."]),
    ("ramp", "새 제품의 첫걸음을 빠르게", "초기 시행착오를 줄이고, 검증한 방법을 다음 제품으로.",
     "신제품 초기 검증·전개·변경 관리", [
         "신제품 초기 검증 항목을 표준화해 전개 과정의 누락을 줄이고 싶다.",
         "제품 변경 이력과 검증 결과를 연결해 초기 문제 대응을 빠르게 하고 싶다.",
         "이전 제품의 검증 경험을 다음 제품 전개에 재사용하고 싶다."], [
         "신제품 초기 검증을 맡아 변경 사항과 확인 결과를 기록했다.",
         "제품 전개 과정에서 발생한 문제를 조율하고 검증 일정을 관리했다.",
         "제품 변경 이력을 정리해 초기 대응 체크리스트를 만들었다."]),
    ("control", "공정을 더 정밀하게", "변동을 이해하고, 조건을 조정하는 근거를 쌓다.",
     "공정 변동 분석과 조건 제어", [
         "공정 조건의 변동과 결과의 관계를 분석해 관리 기준을 정교화하고 싶다.",
         "실험 설계를 활용해 영향을 주는 조건을 구분하고 최적 범위를 찾고 싶다.",
         "장비별 편차를 비교해 일관된 공정 조건을 유지하는 체계를 만들고 싶다."], [
         "통계적 공정관리로 변동을 추적하고 관리 기준을 점검했다.",
         "실험 설계를 통해 주요 조건이 결과에 미치는 영향을 비교했다.",
         "장비별 공정 편차를 분석하고 조건 조정안을 검증했다."]),
]


def corpus():
    rng = random.Random(910)
    surnames = "김이박최정강조윤장임한오서신권황안송류전"
    givens = ["서윤", "도현", "지우", "민재", "하린", "예준", "수빈", "서진", "유진", "지호"]
    people = []
    primary = [4, 0, 5, 7, 1, 0, 6, 3]
    for team, count in enumerate(COUNTS):
        for j in range(count):
            i = len(people)
            pid = i + 1
            past = primary[team] if rng.random() < .66 else rng.randrange(8)
            future = 0 if rng.random() < .22 else (past if rng.random() < .46 else rng.randrange(8))
            future_ids = list(dict.fromkeys([future] + ([rng.randrange(8)] if rng.random() < .3 else [])))
            have_ids = list(dict.fromkeys([past] + ([rng.randrange(8)] if rng.random() < .35 else [])))
            facets = []
            for axis, indices in [("capability_have", have_ids), ("future_task", future_ids)]:
                for k, tid in enumerate(indices):
                    topic = TOPICS[tid]
                    quote = rng.choice(topic[5 if axis == "capability_have" else 4])
                    facets.append({"id": f"p{pid}:{axis}:{k}", "axis": axis, "category": topic[0],
                                   "local": f"PJT-{team+1}/{topic[0]}", "quote": quote,
                                   "ax_mentioned": axis == "future_task" and "AI" in quote})
            # Realistically empty future signal, without inventing absence of interest.
            if pid % 17 == 0:
                facets = [f for f in facets if f["axis"] != "future_task"]
            if pid % 43 == 0:
                facets = []
            have = "\n".join(f["quote"] for f in facets if f["axis"] == "capability_have")
            tasks = "\n".join(f["quote"] for f in facets if f["axis"] == "future_task")
            context = ["재현 조건을 남기는 것이 중요했다.", "다른 담당자와 결과를 비교하면서 기준의 차이를 알게 됐다.",
                       "실제 적용 전에는 작은 범위에서 검증하는 과정이 필요했다.", "수치만으로 설명되지 않는 현장 조건도 함께 기록했다."][j % 4]
            source = f"상반기 업무와 확보 역량\n{have}\n{context}\n\n앞으로 해보고 싶은 일\n{tasks or '앞으로도 맡은 일에 충실하며 팀에 보탬이 되고 싶다.'}"
            if not facets:
                source = "그동안 여러 업무를 두루 경험했습니다. 앞으로도 팀에 보탬이 되도록 열심히 하겠습니다."
            people.append({"id": pid, "name": surnames[i % 20] + givens[i // 20], "pjt": team,
                           "cl": rng.choices(["CL2", "CL3", "CL4"], [3, 4, 3])[0], "text": source,
                           "facets": facets, "signal": bool(facets)})
    return people


def text_vectors(people):
    """Corpus-derived char 2/3-gram TF-IDF; transparent, deterministic demo substitute."""
    bags = []
    for p in people:
        text = re.sub(r"\s+", "", p["text"])
        bags.append(Counter(text[i:i+n] for n in (2, 3) for i in range(len(text)-n+1)))
    df = Counter(term for bag in bags for term in bag)
    vocabulary = sorted(t for t, count in df.items() if count >= 2)
    vectors = {}
    for p, bag in zip(people, bags):
        vectors[p["id"]] = [(1 + math.log(bag[t])) * (math.log((1+len(people))/(1+df[t]))+1)
                             if bag[t] else 0.0 for t in vocabulary]
    return vectors


def layout(people, neighbors):
    """Seeded force layout of cosine top-4 edges. No taxonomy or PJT anchors."""
    n = len(people)
    pairs = {}
    for pid, nbs in neighbors.items():
        for nb in nbs[:4]:
            a, b = sorted((int(pid)-1, nb["id"]-1))
            pairs[a, b] = nb["similarity"]
    a = np.array([p[0] for p in pairs])
    b = np.array([p[1] for p in pairs])
    weights = np.array(list(pairs.values()))
    xy = np.random.default_rng(910).normal(0, .5, (n, 2))
    for step in range(550):
        diff = xy[:, None, :] - xy[None, :, :]
        d2 = np.sum(diff*diff, axis=2) + .015
        force = np.sum(diff / d2[:, :, None], axis=1) * .0009
        edge = xy[b] - xy[a]
        distance = np.sqrt(np.sum(edge*edge, axis=1)) + .0001
        pull = edge * ((distance - (.16 + (1-weights)*.55)) * .035 / distance)[:, None]
        np.add.at(force, a, pull)
        np.add.at(force, b, -pull)
        force -= xy * .008
        xy += np.clip(force, -.045, .045) * (1-step/650)
    xy -= xy.min(axis=0)
    xy /= xy.max(axis=0)
    for p, pos in zip(people, xy):
        p["x"], p["y"] = [round(float(v), 6) for v in pos]
    return [{"a": x+1, "b": y+1, "w": w} for (x, y), w in pairs.items()]


def build_payload():
    people = corpus()
    neighbors = top_k_neighbors(text_vectors(people), k=8)
    edges = layout(people, neighbors)
    topics = []
    for tid, name, subtitle, definition, _, _ in TOPICS:
        future = [p for p in people if any(f["category"] == tid and f["axis"] == "future_task" for f in p["facets"])]
        have = [p for p in people if any(f["category"] == tid and f["axis"] == "capability_have" for f in p["facets"])]
        topics.append({"id": tid, "name": name, "subtitle": subtitle, "definition": definition,
                       "future": [p["id"] for p in future], "have": [p["id"] for p in have],
                       "spread": len({p["pjt"] for p in future})})
    return {"synthetic": True, "people": people, "neighbors": neighbors, "edges": edges,
            "topics": topics, "pjts": [{"name": n, "color": c, "count": k} for n,c,k in zip(PJTS,COLORS,COUNTS)],
            "method": "합성 회고 전체 · 문자 2/3-gram TF-IDF · 코사인 유사도 · 상위 4명 연결",
            "taxonomy_method": "합성 원문과 함께 작성한 분류 fixture · 실제 LLM 추출·검토 결과 아님"}


def main():
    payload = build_payload()
    template = (ROOT / "templates" / "td_people_atlas.html").read_text()
    out = write_html(render(template, payload), OUT / "index.html")
    (OUT / "synthetic-input.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Synthetic atlas: {len(payload['people'])} people / {len(payload['edges'])} edges → {out}")


if __name__ == "__main__":
    main()
