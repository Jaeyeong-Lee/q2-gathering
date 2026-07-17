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

EXTRACT_PROMPT = """다음은 {name}({cl_level})의 근원경쟁력 회고 원문이다.
본인이 하고 싶다고 쓴 미래 과제(tasks)와 확보했다고 쓴 역량(capabilities)을 항목화해
JSON 객체로만 답하라. 요약하지 말고 문장 단위로 쪼개라. quote는 반드시 원문에서
글자 그대로 발췌하라. horizon은 단기/장기/불명 중 하나. 해당 내용이 없으면 빈 배열.

{{"tasks": [{{"text": "...", "horizon": "단기", "quote": "..."}}],
  "capabilities": [{{"text": "...", "quote": "..."}}]}}

원문:
{text}"""

PAGE_PROMPT = """다음은 팀원들이 근원경쟁력 회고에 직접 쓴 미래 과제 문장 묶음(한 군집)이다.
이 군집의 제목(10자 내외 명사구)과 요지(1~2문장)를 JSON 객체로만 답하라.
{{"title": "...", "summary": "..."}}

과제 문장:
{tasks}"""


def _parse_json(response):
    start, end = response.find("{"), response.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"JSON 없음: {response[:80]!r}")
    return json.loads(response[start : end + 1])


def extract_person(doc, call):
    """1인 추출 + 검증. quote가 원문 발췌가 아니면 ValueError(재시도용)."""
    parsed = _parse_json(call(EXTRACT_PROMPT.format(**doc)))
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


def run_embed(extracted_path, out_path, embed, delay=0.0):
    """과제 문장별 임베딩 (사람당 1개 아님) → task_vectors.json."""
    import time
    persons = json.loads(Path(extracted_path).read_text())
    vectors = []
    for p in persons:
        for t in p["tasks"]:
            vectors.append({"person_id": p["person_id"], "name": p["name"],
                            "text": t["text"], "horizon": t["horizon"], "quote": t["quote"],
                            "vec": embed(t["text"])})
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
    k = min(k, len(items))
    X = normalize(np.array([it["vec"] for it in items]))
    labels = KMeans(n_clusters=k, random_state=seed, n_init=10).fit_predict(X)
    clusters = []
    for cid in range(k):
        members = [{key: it[key] for key in ("person_id", "name", "text", "horizon", "quote")}
                   for it, lb in zip(items, labels) if lb == cid]
        clusters.append({"cluster_id": cid, "items": members})
    Path(out_path).write_text(json.dumps(clusters, ensure_ascii=False, indent=1))
    return clusters


def run_pages(clusters_path, out_dir, call):
    """군집당 LLM 1회(제목·요지) + 결정적 본문(실명·인용·horizon 배지) → md 파일들."""
    clusters = json.loads(Path(clusters_path).read_text())
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for c in clusters:
        if not c["items"]:
            continue
        task_lines = "\n".join(f"- {it['text']} ({it['name']})" for it in c["items"])
        meta = _parse_json(call(PAGE_PROMPT.format(tasks=task_lines)))
        lines = [f"# {meta['title']}", "", meta["summary"], ""]
        for it in c["items"]:
            lines += [f"## {it['text']} — {it['name']} `{it['horizon']}`",
                      f"> {it['quote']}", ""]
        path = out_dir / f"cluster-{c['cluster_id']:02d}.md"
        path.write_text("\n".join(lines))
        pages.append(path)
    return pages


def main(sources_path=ROOT / "data" / "task_discovery" / "sources.json", k=8):
    """실 LLM으로 전 스테이지 실행. 산출물은 sources 옆에."""
    import llm
    llm.init()
    k = int(k)  # CLI 인자는 문자열로 들어온다
    out = Path(sources_path).parent
    run_extract(sources_path, out / "extracted.json", call=llm.call_gemini, delay=2.0)
    run_embed(out / "extracted.json", out / "task_vectors.json", embed=llm.embed_text, delay=0.5)
    run_cluster(out / "task_vectors.json", out / "clusters.json", k=k)
    pages = run_pages(out / "clusters.json", out / "pages", call=llm.call_gemini)
    log.info(f"페이지 {len(pages)}개 생성: {out / 'pages'}")


if __name__ == "__main__":
    main(*sys.argv[1:])
