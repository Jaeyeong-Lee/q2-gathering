"""task-discovery 공유 헬퍼 (S1-2, #16).

인용 정규화 대조와 단일 계층 재시도 — td_extract·td_taxonomy·td_assign이 재사용.
"""
import json
import random
import time
from pathlib import Path

# facet 4축 (consumer 공용). 추출은 direction을 단수로 별도 처리하므로 td_extract는 자체 상수 사용.
AXES = ("future_task", "capability_gap", "capability_have", "direction")


class Nonretryable(Exception):
    """4xx류 — 재시도해도 소용없는 오류. retry_call이 즉시 던진다."""


def load_json(x):
    """리스트면 그대로, 경로면 읽어서 파싱 — 스테이지 in/out 공용."""
    return x if not isinstance(x, (str, Path)) else json.loads(Path(x).read_text(encoding="utf-8"))


def parse_json(response):
    """LLM 응답에서 첫 { ~ 마지막 } 슬라이스 후 파싱. strict=False로 quote 내 raw 개행 허용."""
    start, end = response.find("{"), response.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"JSON 없음: {response[:80]!r}")
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
