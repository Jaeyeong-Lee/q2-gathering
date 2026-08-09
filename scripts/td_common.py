"""task-discovery 공유 헬퍼 (S1-2, #16).

인용 정규화 대조와 단일 계층 재시도 — td_extract·td_taxonomy·td_assign이 재사용.
"""
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from pipeline_log import OUT_DIR, get_logger

# facet 4축 (consumer 공용). 추출은 direction을 단수로 별도 처리하므로 td_extract는 자체 상수 사용.
AXES = ("future_task", "capability_gap", "capability_have", "direction")

# 콜 덤프엔 프롬프트 원문이 통째로 들어간다 — TD_OUT_DIR로 리포 밖에 두면 에이전트
# 작업 디렉터리에 실데이터가 남지 않는다(pipeline_log.OUT_DIR과 같은 뿌리를 쓴다).
CALLS_DIR = OUT_DIR / "task_discovery" / "calls"


def reject_public_path(out_path):
    """dist/ 아래로는 산출물을 쓰지 못하게 막는다 — 그 디렉터리는 GitHub Pages로 배포
    추적되므로 실명·인용·카테고리명이 박힌 파일이 들어가면 즉시 공개된다. 규칙을 주석으로만
    두면 오타 한 번에 깨지므로 코드로 막는다."""
    if "dist" in Path(out_path).resolve().parts:
        raise ValueError("dist/ 아래에는 쓸 수 없다 — 배포 추적 경로다. TD_OUT_DIR을 써라")


class Nonretryable(Exception):
    """4xx류 — 재시도해도 소용없는 오류. retry_call이 즉시 던진다."""


def load_json(x):
    """리스트면 그대로, 경로면 읽어서 파싱 — 스테이지 in/out 공용."""
    return x if not isinstance(x, (str, Path)) else json.loads(Path(x).read_text(encoding="utf-8"))


def parse_json(response):
    """LLM 응답에서 첫 { ~ 마지막 } 슬라이스 후 파싱. strict=False로 quote 내 raw 개행 허용.

    예외 메시지에 응답 원문을 넣지 않는다 — 이 메시지는 콘솔로 나가고 사람이 그대로
    복사해 옮기기 쉬운데, 응답엔 실명·인용·카테고리명이 들어 있다. 원문이 필요하면
    콜 덤프(calls/<stage>/ABNORMAL/)와 ECS 로그를 봐라(둘 다 TD_OUT_DIR 안).
    """
    start, end = response.find("{"), response.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"JSON 객체 없음 (응답 {len(response)}자)")
    return json.loads(response[start:end + 1], strict=False)


def iter_facets(persons):
    """무신호 제외, 4축의 비어있지 않은 항목을 (person, axis, item)으로 산출.
    td_taxonomy·td_assign·td_index 공용 순회 — 축 추가 시 여기 한 곳만."""
    for p in persons:
        if not p.get("signal_present"):
            continue
        for axis in AXES:
            val = p.get(axis)
            if val is None:
                continue
            for it in (val if isinstance(val, list) else [val]):
                if it and it.get("text"):
                    yield p, axis, it


def norm(s):
    """공백·개행·들여쓰기 제거. 원문 줄바꿈 차이로 진짜 인용을 떨구지 않기 위함(대조용)."""
    return "".join(s.split())


def oneline(s):
    """개행·중복 공백을 한 칸으로 접음(표시용). 인용 속 원문 개행이 blockquote를 깨지 않게."""
    return " ".join(s.split())


def quote_in_source(quote, source):
    """인용이 원문에서 발췌된 것인지 (공백 무시) 대조."""
    return norm(quote) in norm(source)


def text_is_copy_of_quotes(text, quotes):
    """text가 인용 중 하나를 그대로 베낀 것인지 (공백 무시). 서술 없는 복붙 차단."""
    return any(norm(text) == norm(q) for q in quotes)


def retry_call(call, prompt, *, attempts=4, base=0.5, jitter=True, sleep=time.sleep):
    """주입된 call을 단일 계층에서 재시도. 지수 백오프+jitter, Nonretryable(4xx)은 즉시 포기.

    SDK·프레임워크 재시도와 중첩하지 말 것 — 재시도 계층은 여기 하나로 유지한다.
    """
    for attempt in range(attempts):
        try:
            return call(prompt)
        except Nonretryable:
            raise
        except Exception:
            if attempt == attempts - 1:
                raise
            delay = base * (2 ** attempt) + (random.random() * base if jitter else 0)
            sleep(delay)


def _dump_call(stage, call_id, prompt, response, *, success):
    """콜 하나의 입출력을 파일로 남긴다 — 순수 감사·재현용, 재개 판정(#35, #36)엔 안 쓴다.
    모든 콜(성공 포함)을 calls/{stage}/에, 최종 실패는 ABNORMAL/에도 중복 저장해
    디렉토리만 보고 실패 개수를 알 수 있게 한다."""
    dirs = [CALLS_DIR / str(stage)]
    if not success:
        dirs.append(CALLS_DIR / str(stage) / "ABNORMAL")
    input_doc = {"stage": stage, "call_id": call_id, "prompt": prompt,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    output_doc = {"response": response, "success": success}
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{call_id}_input.json").write_text(
            json.dumps(input_doc, ensure_ascii=False, indent=1), encoding="utf-8")
        (d / f"{call_id}_output.json").write_text(
            json.dumps(output_doc, ensure_ascii=False, indent=1), encoding="utf-8")


def retry_json(call, prompt, *, stage, call_id, **kw):
    """retry_call과 동일하지만 JSON 파싱까지 재시도 범위 안에 넣는다 — 모델이 JSON이
    아닌 걸 뱉어도(서문·reasoning 등) 재시도 대상이 된다. 이전엔 parse_json(retry_call(...))
    순서라 파싱 실패가 즉시 위로 터졌다.

    stage/call_id(예: "taxonomy"/배치 순번)로 ECS 로그(data/pipeline.ecs.jsonl)를 남긴다:
    성공·시도별 실패는 바이트 수만, 재시도 소진 뒤 최종 실패는 프롬프트·응답 원문 전체를
    별도 WARNING으로 — 내부망 페이로드 한도(요청/응답, 정확한 값)를 다음 실행 한 번으로
    판명하기 위함(#30). 성공 로그에 원문을 안 싣는 건 호출 수백 건에 로그가 부풀지 않게.

    콜마다 입출력을 data/task_discovery/calls/{stage}/{call_id}_*.json으로도 남긴다
    (_dump_call, #34) — 순수 감사·재현용이라 재개 판정엔 안 쓴다.
    """
    log = get_logger(stage)
    prompt_bytes = len(prompt.encode("utf-8"))
    last_response = {"text": None}

    def attempt(p):
        try:
            response = call(p)
        except Exception as e:
            log.warning(f"[{call_id}] 호출 실패: {e}", extra={"ecs": {
                "error.type": type(e).__name__, "error.message": str(e),
                "http.request.body.bytes": prompt_bytes}})
            raise
        last_response["text"] = response
        response_bytes = len(response.encode("utf-8"))
        try:
            parsed = parse_json(response)
        except Exception as e:
            log.warning(f"[{call_id}] JSON 파싱 실패: {e}", extra={"ecs": {
                "error.type": type(e).__name__, "error.message": str(e),
                "http.request.body.bytes": prompt_bytes,
                "http.response.body.bytes": response_bytes}})
            raise
        log.info(f"[{call_id}] 성공", extra={"ecs": {
            "http.request.body.bytes": prompt_bytes,
            "http.response.body.bytes": response_bytes}})
        return parsed

    try:
        result = retry_call(attempt, prompt, **kw)
    except Exception as e:
        log.warning(f"[{call_id}] 최종 실패(재시도 종료): {e}", extra={"ecs": {
            "error.type": type(e).__name__, "error.message": str(e),
            "http.request.body": prompt, "http.response.body": last_response["text"]}})
        _dump_call(stage, call_id, prompt, last_response["text"], success=False)
        raise
    _dump_call(stage, call_id, prompt, last_response["text"], success=True)
    return result
