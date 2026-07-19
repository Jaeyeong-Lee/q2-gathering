"""persons.json 순회 → LLM 리뷰 배치. persons.json은 건드리지 않고 별도 data/llm_review.json에
id별 결과를 쌓는다 (build 단계에서 llm_review 필드로 병합은 별도 작업).

CL별 정제 프롬프트 — 문구는 사용자가 직접 채운다 (TODO: 현재 셋 다 동일한 기본 문구).
normalize_person_text.py의 PROMPTS 패턴과 동일.
"""
import json
import time
from pathlib import Path

from pipeline_log import get_logger

ROOT = Path(__file__).parent.parent
log = get_logger("llm_review")

_BASE_PROMPT = """다음은 한 구성원의 근원경쟁력 회고다.
이 내용을 검토해 리뷰를 작성하라.

회고:
{text}"""

PROMPTS = {
    "CL2": _BASE_PROMPT,  # TODO: CL2용 문구로 교체
    "CL3": _BASE_PROMPT,  # TODO: CL3용 문구로 교체
    "CL4": _BASE_PROMPT,  # TODO: CL4용 문구로 교체
}


def review_all(persons, results, call, retries=1, delay=0.5):
    """미완료(results에 없는) 인물만 대상, 1인 1콜, 실패한 인물만 개별 재시도.

    results는 in-place로 채워진다 (str(id) 키). 반환: 실패한 id 목록.
    """
    failed = []
    targets = [p for p in persons if str(p["id"]) not in results]
    log.info(f"리뷰 대상 {len(targets)}명 (전체 {len(persons)}명 중 미완료만)")
    for i, p in enumerate(targets):
        prompt_template = PROMPTS[p["cl_level"]]  # 미등록 cl_level은 즉시 KeyError (재시도 대상 아님)
        for attempt in range(1 + retries):
            try:
                results[str(p["id"])] = call(prompt_template.format(text=p["text"]))
                log.info(f"리뷰 완료 [{p.get('name', '?')}] ({i + 1}/{len(targets)})")
                break
            except Exception:
                # 스택트레이스 포함 → data/pipeline.log에서 원인 확인
                log.exception(f"리뷰 실패 [{p.get('name', '?')}] (id={p['id']}) 시도 {attempt + 1}/{1 + retries}")
                if attempt == retries:
                    failed.append(p["id"])
        if delay > 0:
            time.sleep(delay)
    return failed


def main(persons_path=ROOT / "data" / "persons.json", out_path=ROOT / "data" / "llm_review.json",
         call=None, retries=1, delay=0.5):
    """persons.json을 순회해 리뷰를 생성, out_path에 {id: 리뷰} 형태로 누적 저장 (persons.json은 불변).

    도중에 죽어도(KeyError·Ctrl+C·네트워크 단절) 그때까지의 결과는 out_path에 남는다
    → 재실행 시 이미 완료된 사람은 스킵되어 LLM 재호출 없음.
    """
    if call is None:
        raise SystemExit("LLM 호출 함수 미연결 — call 파라미터에 실제 호출부(llm.call_gemini 등)를 꽂아 실행")
    persons_path = Path(persons_path)
    out_path = Path(out_path)
    persons = json.loads(persons_path.read_text(encoding="utf-8"))
    results = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}

    try:
        failed = review_all(persons, results, call, retries=retries, delay=delay)
    finally:
        out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        log.info(f"{out_path} 반영: {len(results)}명 누적")

    if failed:
        log.warning(f"리뷰 실패 {len(failed)}명 (다음 실행에서 재시도 대상): {failed}")
    return failed


if __name__ == "__main__":
    import llm
    llm.init()
    main(call=lambda prompt: llm.call_gemini(prompt, model="gpt-oss"))
