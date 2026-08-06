import json

import td_peek

# 실제 산출물에 들어갈 법한 민감 문자열 — peek 출력에 절대 나오면 안 되는 것들
SECRETS = ["임소율", "D1b Yield·Test PGM 최적화", "HFT DPPM을 FA와 연계", "사내 정의 문장"]


def _fixture(tmp_path):
    d = tmp_path / "td"
    d.mkdir()
    (d / "extracted.json").write_text(json.dumps([
        {"person_id": 1, "name": "임소율", "signal_present": True,
         "future_task": [{"text": "HFT DPPM을 FA와 연계", "quotes": ["임소율"]}]},
        {"person_id": 2, "name": "임소율", "signal_present": False, "future_task": []},
    ], ensure_ascii=False), encoding="utf-8")
    (d / "taxonomy.json").write_text(json.dumps([
        {"name": "D1b Yield·Test PGM 최적화", "definition": "사내 정의 문장",
         "inclusion_criteria": "i", "relations": [{"to": "다른범주", "type": "broader"}]},
        {"name": "다른범주", "definition": "사내 정의 문장", "inclusion_criteria": "i",
         "relations": []},
    ], ensure_ascii=False), encoding="utf-8")
    (d / "assignments.json").write_text(json.dumps([
        {"person_id": 1, "axis": "future_task", "text": "HFT DPPM을 FA와 연계",
         "category": "D1b Yield·Test PGM 최적화", "quote": "임소율"},
        {"person_id": 2, "axis": "future_task", "text": "x", "category": "Other", "quote": "y"},
    ], ensure_ascii=False), encoding="utf-8")
    (d / "aggregates.json").write_text(json.dumps({
        "categories": [{"name": "D1b Yield·Test PGM 최적화", "people": 12, "pjt_spread": 3,
                        "cl_spread": 2, "have": 8, "gap": 15, "readiness": "갭만 있음"}],
        "minority": [],
    }, ensure_ascii=False), encoding="utf-8")
    (d / "taxonomy.progress.json").write_text(json.dumps(
        {"batches_done": 1, "total_batches": 3}), encoding="utf-8")
    return d


def test_peek_never_prints_names_or_content(tmp_path):
    """이 스크립트의 존재 이유 — 산출물에 민감 문자열이 있어도 출력엔 안 나온다."""
    out = td_peek.report(_fixture(tmp_path))
    for secret in SECRETS:
        assert secret not in out, f"누출: {secret!r}"


def test_peek_reports_counts_and_progress(tmp_path):
    out = td_peek.report(_fixture(tmp_path))
    assert "2건" in out and "무신호 1건" in out          # extracted 건수
    assert "1/3" in out and "미완" in out                 # 진행률 + 미완 표시
    assert "Other 1건" in out                             # Other 비율


def test_peek_shows_categories_by_index_not_name(tmp_path):
    out = td_peek.report(_fixture(tmp_path))
    assert "#1" in out and "갭만 있음" in out             # 인덱스 + 숫자는 보여줌
    assert "D1b" not in out                               # 이름은 안 보여줌


def test_llm_calls_summarizes_bytes_and_flags_large_response(tmp_path):
    ecs = tmp_path / "pipeline.ecs.jsonl"
    ecs.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [
        {"service.name": "taxonomy", "log.level": "INFO",
         "http.request.body.bytes": 1200, "http.response.body.bytes": 8000},
        {"service.name": "taxonomy", "log.level": "WARNING", "error.type": "ValueError",
         "http.request.body.bytes": 1200, "http.response.body.bytes": 21000},
    ]), encoding="utf-8")

    rows = "\n".join(td_peek.llm_calls(ecs))
    assert "taxonomy" in rows and "ValueError" in rows
    assert "20.5k" in rows                                # 응답 최대치를 kb로
    assert "출력 한도 의심" in rows                        # 20kb 넘으면 경고


def test_failures_lists_call_ids_only(tmp_path):
    abnormal = tmp_path / "taxonomy" / "ABNORMAL"
    abnormal.mkdir(parents=True)
    (abnormal / "12_input.json").write_text('{"prompt": "임소율"}', encoding="utf-8")
    (abnormal / "12_output.json").write_text('{"response": "D1b"}', encoding="utf-8")

    rows = "\n".join(td_peek.failures(tmp_path))
    assert "taxonomy" in rows and "12" in rows
    assert "임소율" not in rows and "D1b" not in rows      # 파일 내용은 안 읽는다
