import pytest

import td_common as c


def test_norm_strips_all_whitespace_including_newlines():
    assert c.norm("STDF\n 기반\t고장분석") == c.norm("STDF 기반 고장분석")


def test_quote_in_source_tolerates_source_newlines():
    # 원문에만 개행이 있어도 진짜 인용은 매칭돼야 한다 (PPT 추출 개행 대응)
    source = "앞으로\nSTDF 기반\n고장분석을 하고 싶다"
    assert c.quote_in_source("STDF 기반 고장분석", source)


def test_quote_not_in_source_is_rejected():
    assert not c.quote_in_source("존재하지 않는 인용", "실제 원문 텍스트")


def test_text_is_copy_of_quote_detected():
    # text가 인용을 그대로 베낀 것(공백만 다름)도 복사로 판정
    assert c.text_is_copy_of_quotes("STDF 기반 고장분석", ["STDF 기반  고장분석"])
    assert not c.text_is_copy_of_quotes("STDF로 FA를 자동화한다", ["STDF 기반 고장분석"])


def test_retry_call_retries_transient_then_succeeds():
    calls = {"n": 0}

    def flaky(prompt):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("일시 오류")
        return "ok"

    out = c.retry_call(flaky, "p", attempts=4, base=0.0, sleep=lambda _: None)
    assert out == "ok"
    assert calls["n"] == 3


def test_retry_call_gives_up_after_attempts():
    def always_fail(prompt):
        raise RuntimeError("계속 실패")

    with pytest.raises(RuntimeError):
        c.retry_call(always_fail, "p", attempts=3, base=0.0, sleep=lambda _: None)


def test_retry_call_does_not_retry_nonretryable():
    calls = {"n": 0}

    def bad_request(prompt):
        calls["n"] += 1
        raise c.Nonretryable("4xx")

    with pytest.raises(c.Nonretryable):
        c.retry_call(bad_request, "p", attempts=5, base=0.0, sleep=lambda _: None)
    assert calls["n"] == 1  # 4xx는 재시도하지 않는다
