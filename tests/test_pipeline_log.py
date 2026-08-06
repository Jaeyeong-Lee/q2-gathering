import json
import logging

import pipeline_log as pl


def _record(name, level, msg, ecs=None):
    record = logging.LogRecord(name=name, level=level, pathname=__file__, lineno=1,
                                msg=msg, args=(), exc_info=None)
    if ecs is not None:
        record.ecs = ecs
    return record


def test_ecs_formatter_produces_valid_json_with_required_fields():
    line = pl.ECSJSONFormatter().format(_record("td_taxonomy", logging.INFO, "테스트 메시지"))
    data = json.loads(line)
    assert data["service.name"] == "td_taxonomy"
    assert data["log.level"] == "INFO"
    assert data["message"] == "테스트 메시지"
    assert "@timestamp" in data
    assert data["ecs.version"]


def test_out_dir_follows_td_out_dir_env(tmp_path, monkeypatch):
    """내부망에선 로그를 리포 밖에 둬야 한다 — 에이전트 작업 디렉터리에 실데이터가 밴
    로그가 남지 않게. 모듈 상수라 재로드로 확인."""
    import importlib

    monkeypatch.setenv("TD_OUT_DIR", str(tmp_path))
    reloaded = importlib.reload(pl)
    try:
        assert reloaded.LOG_PATH == tmp_path / "pipeline.log"
        assert reloaded.ECS_LOG_PATH == tmp_path / "pipeline.ecs.jsonl"
    finally:
        monkeypatch.delenv("TD_OUT_DIR")
        importlib.reload(pl)


def test_out_dir_defaults_into_repo_data_when_env_unset(monkeypatch):
    import importlib

    monkeypatch.delenv("TD_OUT_DIR", raising=False)
    reloaded = importlib.reload(pl)
    assert reloaded.LOG_PATH.name == "pipeline.log"
    assert reloaded.LOG_PATH.parent.name == "data"


def test_ecs_formatter_merges_extra_ecs_fields():
    record = _record("td_assign", logging.WARNING, "실패",
                     ecs={"error.type": "ValueError", "http.request.body.bytes": 123})
    data = json.loads(pl.ECSJSONFormatter().format(record))
    assert data["error.type"] == "ValueError"
    assert data["http.request.body.bytes"] == 123
