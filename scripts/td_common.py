"""task-discovery 공유 헬퍼 (S1-2, #16).

인용 정규화 대조와 단일 계층 재시도 — td_extract·td_taxonomy·td_assign이 재사용.
"""
import random
import time


class Nonretryable(Exception):
    """4xx류 — 재시도해도 소용없는 오류. retry_call이 즉시 던진다."""


def norm(s):
    """공백·개행·들여쓰기 제거. 원문 줄바꿈 차이로 진짜 인용을 떨구지 않기 위함."""
    return "".join(s.split())


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
