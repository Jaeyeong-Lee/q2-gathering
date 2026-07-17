"""미래 과제 발굴 트레이서 (issue #2) — 추출→임베딩→군집→md 세로 관통.

스테이지별 파일 in/out, LLM 호출은 주입식(call/embed 파라미터) — tags.py 패턴.
설계 정본: docs/task-discovery.md. CL별 프롬프트 분리·역량 평면 군집은 #4.
"""
import json
import sys
from pathlib import Path

from pipeline_log import get_logger

ROOT = Path(__file__).parent.parent
log = get_logger("task_discovery")

HORIZONS = ("단기", "장기", "불명")

_EXTRACT_RULES = """본인이 하고 싶다고 쓴 미래 과제(tasks)와 확보했다고 쓴 역량(capabilities)을 항목화해
JSON 객체로만 답하라. 요약하지 말고 문장 단위로 쪼개라. quote는 반드시 원문에서
글자 그대로 발췌하라. horizon은 단기/장기/불명 중 하나. 해당 내용이 없으면 빈 배열.

{{"tasks": [{{"text": "...", "horizon": "단기", "quote": "..."}}],
  "capabilities": [{{"text": "...", "quote": "..."}}]}}

원문:
{text}"""

# CL별 프롬프트 분리 (#4): CL2/3은 3단 구성, CL4는 미래 위주 별도 템플릿
EXTRACT_PROMPT_CL23 = ("다음은 {name}({cl_level})의 근원경쟁력 회고 원문이다. "
                       "3단 구성(①상반기 성과·하반기 전략 ②커리어 회고·확보 역량 ③미래 업무)이 "
                       "원칙이나 미준수 문서도 있다.\n" + _EXTRACT_RULES)
EXTRACT_PROMPT_CL4 = ("다음은 {name}({cl_level})의 근원경쟁력 회고 원문이다. "
                      "CL4는 미래 위주 서술형 템플릿이다.\n" + _EXTRACT_RULES)

PAGE_PROMPT = """다음은 팀원들이 근원경쟁력 회고에 직접 쓴 미래 과제 문장 묶음(한 군집)이다.
이 군집의 제목(10자 내외 명사구)과 요지(1~2문장), 그리고 이 과제들에서 파생 가능한
새 관점의 과제 제안(derived) 0~3개를 JSON 객체로만 답하라. 자유 브레인스토밍 금지 —
각 제안의 evidence는 아래 목록의 person_id와 그 사람의 과제 문장을 글자 그대로
인용해야 하며, 인용할 수 없는 제안은 내지 마라.
{{"title": "...", "summary": "...",
  "derived": [{{"text": "...", "evidence": [{{"person_id": 1, "quote": "..."}}]}}]}}

과제 문장:
{tasks}"""


## 더미 원문 생성 (issue #3) — 실 pptx 원문 확보 전 입력 대체. generate_dummy.py 패턴.

_SURNAMES = "김이박최정강조윤장임한오서신권황안송류전홍"
_GIVENS = ["민준", "서연", "도윤", "하은", "지호", "수아", "예준", "지유", "시우", "채원",
           "주원", "다은", "건우", "예린", "현우", "소율", "우진", "가은", "선우", "유나"]
_DOMAINS = ["용접 비전검사", "공정 데이터 예지보전", "딥러닝 외관검사", "로봇 티칭 자동화",
            "디지털트윈 시뮬레이션", "MES 데이터 표준화", "품질 데이터 분석", "설비 이상감지",
            "PLC 제어 고도화", "물류 자동화", "금형 수명 예측", "에너지 사용 최적화"]
_SKILLS = ["PLC 제어", "SQL 리포팅", "파이썬 데이터 분석", "로봇 티칭", "비전 알고리즘",
           "MLOps 운영", "현장 개선", "공정 설계", "센서 캘리브레이션", "표준화 문서화"]

_TPL_CL23 = """1. 상반기 성과 및 하반기 전략
상반기에는 {d1} 과제를 수행해 성과를 냈다. 하반기에는 {d2} 개선을 이어가려 한다.
2. 커리어 회고 및 확보 역량
그동안 {s1}와(과) {s2} 역량을 확보했다.
3. 미래 업무
단기적으로는 {d3} 체계를 만들고 싶다. 장기적으로는 {d4} 플랫폼을 구축하고 싶다."""

_TPL_CL4 = """앞으로의 방향
{d1}을(를) 표준 플랫폼으로 통합하는 것이 목표다. 이를 위해 {s1}와(과) {s2} 역량을
확보해 왔다. 단기적으로는 {d2} 파일럿을 추진하고 싶다."""

_TPL_BAD = "그동안 여러 업무를 두루 경험했습니다. 앞으로도 팀에 보탬이 되도록 열심히 하겠습니다."


def generate_sources(n=20, seed=0, out_path=None):
    """더미 원문 n명 생성 — CL2/3 3단·CL4 별도 템플릿, ~10% 미준수. 고정 시드 재현."""
    import random
    rng = random.Random(seed)
    docs = []
    for i in range(1, n + 1):
        cl = rng.choices(["CL2", "CL3", "CL4"], weights=[0.3, 0.45, 0.25])[0]
        d = rng.sample(_DOMAINS, 4)
        s = rng.sample(_SKILLS, 2)
        if rng.random() < 0.1:
            text = _TPL_BAD
        elif cl == "CL4":
            text = _TPL_CL4.format(d1=d[0], d2=d[1], s1=s[0], s2=s[1])
        else:
            text = _TPL_CL23.format(d1=d[0], d2=d[1], d3=d[2], d4=d[3], s1=s[0], s2=s[1])
        docs.append({"id": i, "name": rng.choice(_SURNAMES) + rng.choice(_GIVENS),
                     "cl_level": cl, "text": text})
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(docs, ensure_ascii=False, indent=1))
    return docs


def _parse_json(response):
    start, end = response.find("{"), response.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"JSON 없음: {response[:80]!r}")
    return json.loads(response[start : end + 1])


def extract_person(doc, call):
    """1인 추출 + 검증. quote가 원문 발췌가 아니면 ValueError(재시도용)."""
    tpl = EXTRACT_PROMPT_CL4 if doc["cl_level"] == "CL4" else EXTRACT_PROMPT_CL23
    parsed = _parse_json(call(tpl.format(**doc)))
    tasks, capabilities = parsed.get("tasks", []), parsed.get("capabilities", [])
    for item in tasks + capabilities:
        if item["quote"] not in doc["text"]:
            raise ValueError(f"인용 불일치 (id={doc['id']}): {item['quote'][:40]!r}")
    for t in tasks:
        if t.get("horizon") not in HORIZONS:
            t["horizon"] = "불명"
    return {"person_id": doc["id"], "name": doc["name"], "cl_level": doc["cl_level"],
            "tasks": tasks, "capabilities": capabilities}


def run_extract(sources_path, out_path, call, retries=1, delay=0.5):
    """인당 1콜 배치 추출 → extracted.json. 검증 실패 인물은 재시도 후 폐기."""
    import time
    docs = json.loads(Path(sources_path).read_text())
    out, failed = [], []
    for doc in docs:
        for attempt in range(1 + retries):
            try:
                out.append(extract_person(doc, call))
                break
            except Exception:
                # ponytail: 인용 1건 불일치도 사람 전체 폐기 — 238명 확장(#7) 전 항목 단위 폐기로 재고
                log.exception(f"추출 실패 [{doc.get('name', '?')}] 시도 {attempt + 1}/{1 + retries}")
                if attempt == retries:
                    failed.append(doc["id"])
        if delay > 0:
            time.sleep(delay)
    Path(out_path).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    if failed:
        log.warning(f"추출 폐기 {len(failed)}명: {failed}")
    return out


def run_embed(extracted_path, out_path, embed, delay=0.0, field="tasks"):
    """문장별 임베딩 (사람당 1개 아님) → vectors.json. field로 과제/역량 평면 선택."""
    import time
    persons = json.loads(Path(extracted_path).read_text())
    vectors = []
    for p in persons:
        for t in p[field]:
            vectors.append({"person_id": p["person_id"], "name": p["name"],
                            **{k: v for k, v in t.items()}, "vec": embed(t["text"])})
            if delay > 0:
                time.sleep(delay)
    Path(out_path).write_text(json.dumps(vectors, ensure_ascii=False))
    return vectors


def run_cluster(vectors_path, out_path, k=8, seed=0):
    """정규화 후 KMeans(유클리드=코사인) → clusters.json. 군집이 이상하면 입력 문장 품질부터 볼 것."""
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import normalize

    items = json.loads(Path(vectors_path).read_text())
    if not items:  # 예: 역량 문장이 하나도 안 뽑힌 세트
        Path(out_path).write_text("[]")
        return []
    k = min(k, len(items))
    X = normalize(np.array([it["vec"] for it in items]))
    labels = KMeans(n_clusters=k, random_state=seed, n_init=10).fit_predict(X)
    clusters = []
    for cid in range(k):
        members = [{key: v for key, v in it.items() if key != "vec"}
                   for it, lb in zip(items, labels) if lb == cid]
        clusters.append({"cluster_id": cid, "items": members})
    Path(out_path).write_text(json.dumps(clusters, ensure_ascii=False, indent=1))
    return clusters


def _grounded(suggestion, items):
    """파생 제안 검증: 모든 evidence가 군집 멤버의 실제 문장/인용과 대조돼야 채택."""
    evidence = suggestion.get("evidence")
    if not evidence:
        return False
    for ev in evidence:
        if not any(it["person_id"] == ev["person_id"]
                   and (ev["quote"] in it["quote"] or ev["quote"] in it["text"])
                   for it in items):
            log.warning(f"파생 제안 폐기 (인용 불일치): {suggestion.get('text', '?')!r}")
            return False
    return True


def run_pages(clusters_path, out_dir, call):
    """군집당 LLM 1회(제목·요지) + 결정적 본문(실명·인용·horizon 배지) → md 파일들."""
    clusters = json.loads(Path(clusters_path).read_text())
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for c in clusters:
        if not c["items"]:
            continue
        task_lines = "\n".join(f"- [person_id={it['person_id']}] {it['text']} ({it['name']})"
                               for it in c["items"])
        meta = _parse_json(call(PAGE_PROMPT.format(tasks=task_lines)))
        lines = [f"# {meta['title']}", "", meta["summary"], ""]
        for it in c["items"]:
            lines += [f"## {it['text']} — {it['name']} `{it['horizon']}`",
                      f"> {it['quote']}", ""]
        derived = [d for d in meta.get("derived", []) if _grounded(d, c["items"])]
        if derived:
            lines += ["## 파생 과제 제안 `AI 제안`", ""]
            name_by_id = {it["person_id"]: it["name"] for it in c["items"]}
            for d in derived:
                refs = " / ".join(f"{name_by_id[ev['person_id']]}: “{ev['quote']}”"
                                  for ev in d["evidence"])
                lines += [f"- **{d['text']}** — 근거: {refs}"]
            lines += [""]
        path = out_dir / f"cluster-{c['cluster_id']:02d}.md"
        path.write_text("\n".join(lines))
        pages.append((path, meta["title"], c["items"]))

    index_lines = ["# 미래 과제 지도", "", "군집당 페이지 하나. 실명·원문 인용 — 사내 한정.", ""]
    for path, title, items in pages:
        people = len({it["person_id"] for it in items})
        keywords = " · ".join(it["text"] for it in items[:3])
        index_lines.append(f"- [{title}]({path.name}) — {people}명 / {keywords}")
    (out_dir / "index.md").write_text("\n".join(index_lines) + "\n")
    return [p for p, _, _ in pages] + [out_dir / "index.md"]


def run_all(sources_path, out, pages_dir, call, embed, k=8, delay=2.0):
    """전 스테이지 실행. 추출·임베딩 산출물이 있으면 캐시로 쓰고 건너뛴다(LLM 0콜) —
    군집·페이지는 항상 재실행(k·프롬프트 변경 반영). 강제 재실행은 해당 JSON 삭제."""
    out = Path(out)
    if not (out / "extracted.json").exists():
        run_extract(sources_path, out / "extracted.json", call=call, delay=delay)
    for field, name in (("tasks", "task_vectors.json"), ("capabilities", "capability_vectors.json")):
        if not (out / name).exists():
            run_embed(out / "extracted.json", out / name, embed=embed, delay=delay / 4, field=field)
    run_cluster(out / "task_vectors.json", out / "clusters.json", k=k)
    # 역량 평면 (#4) — 빈 칸 매트릭스(옵션)·발굴층의 재료, 페이지는 과제 평면만
    run_cluster(out / "capability_vectors.json", out / "capability_clusters.json", k=k)
    pages = run_pages(out / "clusters.json", pages_dir, call=call)
    log.info(f"페이지 {len(pages)}개 생성: {pages_dir}")
    return pages


def main(sources_path=ROOT / "data" / "task_discovery" / "sources.json", k=8):
    """실 LLM으로 전 스테이지 실행(GEMINI_API_KEY 필요). 마일스톤 1 데모:
    sources 없으면 더미 20명 생성, wiki는 dist/wiki/(추적됨), 중간 산출물은 data/(무시됨)."""
    import llm
    llm.init()
    sources_path = Path(sources_path)
    if not sources_path.exists():
        generate_sources(20, out_path=sources_path)
        log.info(f"더미 20명 생성: {sources_path}")
    run_all(sources_path, sources_path.parent, ROOT / "dist" / "wiki",
            call=llm.call_gemini, embed=llm.embed_text, k=int(k))


if __name__ == "__main__":
    main(*sys.argv[1:])
