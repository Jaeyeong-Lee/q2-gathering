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


def test_ecs_formatter_merges_extra_ecs_fields():
    record = _record("td_assign", logging.WARNING, "실패",
                     ecs={"error.type": "ValueError", "http.request.body.bytes": 123})
    data = json.loads(pl.ECSJSONFormatter().format(record))
    assert data["error.type"] == "ValueError"
    assert data["http.request.body.bytes"] == 123
