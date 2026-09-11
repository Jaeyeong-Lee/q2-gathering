"""정제 전 사람별 회고 원문 → LLM으로 스키마 마크다운 정제 (좁은 스코프, 사람 1명 = 1콜).

scripts/llm.py의 openai_compat/internal provider(사내망 로컬 모델)를 그대로 재사용.
roster 테이블(split_md_by_person.py 산출물)에서 status=정상인 사람만 대상으로 한다.
"""
import sqlite3
import time
from pathlib import Path

from pipeline_log import get_logger

ROOT = Path(__file__).parent.parent
log = get_logger("normalize")

# CL별 정제 프롬프트 — 문구는 사용자가 직접 채운다 (TODO: 현재 셋 다 동일한 기본 문구)
_BASE_PROMPT = """다음은 한 구성원의 근원경쟁력 회고 원문(PPT 발췌, 정리 안 됨)이다.
아래 마크다운 형식으로 다듬어 그 형식만 답하라:

# 근원경쟁력

## 핵심 역량
...

## 주요 경력
...

## 강점
...

원문:
{raw}"""

PROMPTS = {
    "CL2": _BASE_PROMPT,  # TODO: CL2용 문구로 교체
    "CL3": _BASE_PROMPT,  # TODO: CL3용 문구로 교체
    "CL4": _BASE_PROMPT,  # TODO: CL4용 문구로 교체
}


def normalize_all(rows, raw_dir, call, retries=1, delay=0.5):
    """status=정상 & 미정제 행만 대상, 사람별 1콜, 실패한 사람만 개별 재시도.

    rows는 in-place로 normalized_filename이 채워진다 (실패자는 빈 값 유지).
    반환: 실패한 name 목록.
    """
    raw_dir = Path(raw_dir)
    failed = []
    targets = [r for r in rows if r["status"] == "정상" and not r.get("normalized_filename")]
    log.info(f"정제 대상 {len(targets)}명 (전체 {len(rows)}행 중 정상·미정제만)")
    for i, r in enumerate(targets):
        raw_path = raw_dir / r["split_filename"]
        raw_text = raw_path.read_text(encoding="utf-8")
        prompt_template = PROMPTS[r["cl_level"]]  # 미등록 cl_level은 즉시 KeyError (재시도 대상 아님)
        for attempt in range(1 + retries):
            try:
                result = call(prompt_template.format(raw=raw_text))
                out_name = raw_path.stem + ".normalized.md"
                (raw_dir / out_name).write_text(result, encoding="utf-8")
                r["normalized_filename"] = out_name
                # 콘솔엔 seq만 — 실명은 ECS 로그(TD_OUT_DIR 안)에만 남긴다.
                log.info(f"정제 완료 seq={r['seq']} ({i + 1}/{len(targets)})",
                         extra={"ecs": {"user.name": r["name"], "file.name": out_name}})
                break
            except Exception:
                # 스택트레이스 포함 → pipeline.log에서 원인(URL 오타·모델명·타임아웃 등) 확인
                log.exception(f"정제 실패 seq={r['seq']} 시도 {attempt + 1}/{1 + retries}",
                              extra={"ecs": {"user.name": r["name"]}})
                if attempt == retries:
                    failed.append(r["seq"])
        if delay > 0:
            time.sleep(delay)
    return failed


def main(db_path=ROOT / "data" / "roster.db", raw_dir=ROOT / "data" / "raw_sections",
         call=None, retries=1, delay=0.5):
    """roster 테이블의 normalized_filename을 채운다. 실패자는 다음 실행에서 재시도 대상으로 남는다."""
    if call is None:
        raise SystemExit("LLM 호출 함수 미연결 — call 파라미터에 실제 호출부(llm.call_gemini 등)를 꽂아 실행")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM roster")]

    try:
        failed = normalize_all(rows, raw_dir, call, retries=retries, delay=delay)
    finally:
        # 도중에 죽어도(KeyError·Ctrl+C·네트워크 단절) 그때까지 채운 normalized_filename은 DB에 남긴다
        # → 재실행 시 이미 정제된 사람은 스킵되어 LLM 재호출 없음
        done = [(r["normalized_filename"], r["seq"]) for r in rows if r.get("normalized_filename")]
        conn.executemany("UPDATE roster SET normalized_filename = ? WHERE seq = ?", done)
        conn.commit()
        conn.close()
        log.info(f"DB 반영: normalized_filename {len(done)}명 기록됨 ({db_path})")

    if failed:
        log.warning(f"정제 실패 {len(failed)}명 (다음 실행에서 재시도 대상) seq={failed}")
    return failed


if __name__ == "__main__":
    import llm
    llm.init()
    main(call=lambda prompt: llm.call_gemini(prompt, model="gpt-oss"))
