"""회고 텍스트 → LLM 성향/역량 태그 추출 배치 (todos/004).

Phase 1: LLM 호출부는 주입식(call 파라미터) — 실데이터 때 Jay가 실제 호출 함수만 꽂으면 된다.
동의어 정규화는 scripts/tag_synonyms.json 편집.
"""
import json
import sys
from pathlib import Path

from pipeline_log import get_logger

ROOT = Path(__file__).parent.parent
log = get_logger("tags")
SYNONYMS_PATH = Path(__file__).parent / "tag_synonyms.json"


def load_synonyms(path=SYNONYMS_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize(tag_list, synonyms=None):
    """동의어를 대표형으로 병합, 순서 유지·중복 제거."""
    if synonyms is None:
        synonyms = load_synonyms()
    out = []
    for tag in tag_list:
        tag = synonyms.get(tag, tag)
        if tag not in out:
            out.append(tag)
    return out


PROMPT = """다음은 한 구성원의 근원경쟁력 회고 텍스트다.
이 사람의 성향/역량 태그를 3~5개, 한국어 명사형으로 뽑아 JSON 배열로만 답하라.
예: ["문제해결형", "데이터드리븐", "현장밀착"]

회고:
{text}"""


def extract_all(persons, call, retries=1, synonyms=None, delay=0.5):
    """1인 1호출 배치. 실패한 인물만 retries회까지 개별 재시도.

    반환: ({id: [태그]}, [최종 실패 id])
    """
    import time
    if synonyms is None:
        synonyms = load_synonyms()
    by_id, failed = {}, []
    for i, p in enumerate(persons):
        prompt = PROMPT.format(text=p["text"])
        for attempt in range(1 + retries):
            try:
                by_id[p["id"]] = normalize(parse_tags(call(prompt)), synonyms)
                if i % 10 == 9:
                    log.info(f"처리: {i + 1}/{len(persons)}")
                break
            except Exception:
                log.exception(
                    f"태그 추출 실패 [{p.get('name', '?')}] (id={p['id']}) 시도 {attempt + 1}/{1 + retries}"
                )
                if attempt == retries:
                    failed.append(p["id"])
        if delay > 0:
            time.sleep(delay)
    return by_id, failed


POOL_PROMPT = """다음은 구성원들에게서 추출한 성향/역량 태그 풀 전체다.
표기가 다른 같은 의미의 태그를 병합해, {{"변형": "대표형"}} JSON 객체로만 답하라.
이미 일관된 태그는 포함하지 마라.

태그 풀:
{pool}"""


def consolidate_pool(by_id, call):
    """태그 풀 전체를 1회 LLM 호출로 표기 정리 → 매핑 적용한 새 by_id 반환."""
    pool = sorted({t for tag_list in by_id.values() for t in tag_list})
    response = call(POOL_PROMPT.format(pool=json.dumps(pool, ensure_ascii=False)))
    start, end = response.find("{"), response.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"매핑 객체 없음: {response[:80]!r}")
    mapping = json.loads(response[start : end + 1])
    return {pid: normalize(tag_list, mapping) for pid, tag_list in by_id.items()}


def parse_tags(response):
    """LLM 응답 → 태그 리스트. JSON 배열을 찾아 공백 정리·중복 제거, 못 찾으면 ValueError(재시도용)."""
    start = response.find("[")
    end = response.rfind("]")
    if start == -1 or end <= start:
        raise ValueError(f"태그 배열 없음: {response[:80]!r}")
    parsed = json.loads(response[start : end + 1])
    out = []
    for tag in parsed:
        tag = str(tag).strip()
        if tag and tag not in out:
            out.append(tag)
    return out


def main(persons_path=ROOT / "data" / "persons.json", call=None, retries=1, delay=0.5):
    """persons.json의 tags 필드를 LLM 추출 태그로 갱신. 실패 인물은 기존 태그 유지, id 목록 반환."""
    if call is None:
        raise SystemExit("LLM 호출 함수 미연결 — 실데이터 때 call 파라미터에 실제 호출부를 꽂아 실행")
    persons_path = Path(persons_path)
    persons = json.loads(persons_path.read_text(encoding="utf-8"))
    by_id, failed = extract_all(persons, call, retries=retries, delay=delay)
    try:
        by_id = consolidate_pool(by_id, call)
    except Exception:
        # 풀 정리 1콜 실패로 사람별 추출 결과(N콜)까지 버리지 않는다 — 병합 없이 그대로 저장
        log.exception("태그 풀 정리 실패 — 개별 태그는 병합 없이 저장")
    for p in persons:
        if p["id"] in by_id:
            p["tags"] = by_id[p["id"]]
    persons_path.write_text(json.dumps(persons, ensure_ascii=False, indent=1), encoding="utf-8")
    if failed:
        log.warning(f"추출 실패 {len(failed)}명 (기존 태그 유지): {failed}")
    return failed


if __name__ == "__main__":
    main(*sys.argv[1:])
