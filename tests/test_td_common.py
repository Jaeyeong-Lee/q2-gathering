import json
import logging

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


def test_retry_json_retries_on_bad_json_then_succeeds():
    calls = {"n": 0}

    def flaky(prompt):
        calls["n"] += 1
        return "이건 JSON이 아님" if calls["n"] < 2 else '{"ok": true}'

    result = c.retry_json(flaky, "p", stage="test-json-retry", call_id=1,
                          base=0.0, sleep=lambda _: None)
    assert result == {"ok": True}
    assert calls["n"] == 2  # 파싱 실패도 재시도 대상


def test_retry_json_success_logs_bytes_only_no_full_text(caplog):
    def call(prompt):
        return '{"a": 1}'

    with caplog.at_level(logging.INFO, logger="test-json-success"):
        c.retry_json(call, "prompt", stage="test-json-success", call_id=1, sleep=lambda _: None)

    infos = [r for r in caplog.records if r.name == "test-json-success" and r.levelno == logging.INFO]
    assert len(infos) == 1
    ecs = infos[0].ecs
    assert ecs["http.request.body.bytes"] == len("prompt".encode("utf-8"))
    assert "http.response.body.bytes" in ecs
    assert "http.request.body" not in ecs
    assert "http.response.body" not in ecs


def test_retry_json_per_attempt_failure_logs_bytes_only(caplog):
    def call(prompt):
        call.n = getattr(call, "n", 0) + 1
        return "JSON 아님" if call.n < 2 else '{"ok": true}'

    with caplog.at_level(logging.WARNING, logger="test-json-attempt-fail"):
        c.retry_json(call, "p", stage="test-json-attempt-fail", call_id=1,
                     base=0.0, sleep=lambda _: None)

    warnings = [r for r in caplog.records
               if r.name == "test-json-attempt-fail" and r.levelno == logging.WARNING]
    assert len(warnings) == 1
    ecs = warnings[0].ecs
    assert ecs["error.type"] == "ValueError"
    assert "http.request.body" not in ecs  # 시도별 실패는 바이트 수만, 원문 없음


def test_parse_json_error_does_not_leak_response_text():
    """예외 메시지는 콘솔로 나가고 사람이 그대로 복사해 옮긴다 — 실명·인용·카테고리명이
    거기 실리면 안 된다(응답 길이만)."""
    response = '죄송합니다:\n{"name": "D1b Yield·Test PGM 최적화", "quote": "임소율: HFT DPPM"'
    with pytest.raises(ValueError) as exc:
        c.parse_json(response)
    msg = str(exc.value)
    assert "임소율" not in msg and "D1b" not in msg and "죄송" not in msg
    assert str(len(response)) in msg          # 길이는 알려준다(진단용)


def test_retry_json_failure_logs_keep_payload_out_of_console_message(caplog):
    """ECS extras엔 원문이 있어도(파일 전용), 콘솔에 찍히는 message엔 없어야 한다."""
    def bad(prompt):
        return '{"name": "D1b Yield·Test PGM 최적화", "quote": "임소율"'

    with caplog.at_level(logging.WARNING, logger="leak-check"):
        with pytest.raises(ValueError):
            c.retry_json(bad, "프롬프트", stage="leak-check", call_id=1,
                         attempts=1, base=0.0, sleep=lambda _: None)

    for record in caplog.records:
        assert "임소율" not in record.getMessage()
        assert "D1b" not in record.getMessage()


def test_retry_json_dumps_successful_call(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "CALLS_DIR", tmp_path)

    def call(prompt):
        return '{"ok": true}'

    c.retry_json(call, "prompt", stage="taxonomy", call_id=3, sleep=lambda _: None)

    input_doc = json.loads((tmp_path / "taxonomy" / "3_input.json").read_text())
    output_doc = json.loads((tmp_path / "taxonomy" / "3_output.json").read_text())
    assert input_doc["prompt"] == "prompt"
    assert input_doc["stage"] == "taxonomy"
    assert input_doc["call_id"] == 3
    assert output_doc == {"response": '{"ok": true}', "success": True}
    assert not (tmp_path / "taxonomy" / "ABNORMAL").exists()


def test_retry_json_dumps_final_failure_to_abnormal_too(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "CALLS_DIR", tmp_path)

    def always_bad(prompt):
        return "JSON 아님"

    with pytest.raises(ValueError):
        c.retry_json(always_bad, "prompt", stage="assign", call_id=7,
                     attempts=1, base=0.0, sleep=lambda _: None)

    for base in (tmp_path / "assign", tmp_path / "assign" / "ABNORMAL"):
        output_doc = json.loads((base / "7_output.json").read_text())
        assert output_doc == {"response": "JSON 아님", "success": False}


def test_retry_json_final_failure_logs_full_prompt_and_response(caplog):
    def always_bad(prompt):
        return "여전히 JSON 아님"

    with caplog.at_level(logging.WARNING, logger="test-json-final-fail"):
        with pytest.raises(ValueError):
            c.retry_json(always_bad, "내 프롬프트", stage="test-json-final-fail", call_id=1,
                        attempts=2, base=0.0, sleep=lambda _: None)

    warnings = [r for r in caplog.records
               if r.name == "test-json-final-fail" and r.levelno == logging.WARNING]
    final = warnings[-1]  # 시도별 실패 로그들 뒤에 최종 실패 로그가 별도로 온다
    assert final.ecs["http.request.body"] == "내 프롬프트"
    assert final.ecs["http.response.body"] == "여전히 JSON 아님"
    assert final.ecs["error.type"] == "ValueError"
