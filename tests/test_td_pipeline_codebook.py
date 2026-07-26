import json
import os
import time
from collections import Counter

import td_pipeline

NOOP = lambda _: None


def _fakes():
    calls = Counter()

    def extract(prompt):
        calls["extract"] += 1
        src = prompt.split("원문:\n", 1)[1].strip()
        q = src[:8]
        return json.dumps({"signal_present": True,
                           "future_task": [{"text": "과제 서술 " + q, "horizon": "단기", "quotes": [q]}],
                           "capability_have": [], "capability_gap": [], "direction": None},
                          ensure_ascii=False)

    def taxo(prompt):
        calls["taxo"] += 1
        return json.dumps({"taxonomy": [{"name": "합성역량", "definition": "d",
                                         "inclusion_criteria": "i"}]}, ensure_ascii=False)

    def assign(prompt):
        calls["assign"] += 1
        item = prompt.split("항목:\n", 1)[1].strip()
        return json.dumps({"category": "합성역량", "quote": item[:6]}, ensure_ascii=False)

    return calls, extract, taxo, assign


def _codebook(tmp_path):
    cb = tmp_path / "codebook.json"
    cb.write_text(json.dumps([{"name": "합성역량", "definition": "d", "inclusion": "i"}],
                             ensure_ascii=False), encoding="utf-8")
    return cb


def test_codebook_mode_skips_taxonomy(tmp_path):
    calls, ex, tx, asg = _fakes()
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg,
                        codebook=_codebook(tmp_path), n=12, sleep=NOOP)
    assert not (tmp_path / "taxonomy.json").exists()   # 유도 skip
    assert calls["taxo"] == 0
    assert (tmp_path / "workshop-input.md").exists()
    assert calls["extract"] > 0 and calls["assign"] > 0


def test_codebook_edit_reassigns_but_reuses_extraction(tmp_path):
    calls, ex, tx, asg = _fakes()
    cb = _codebook(tmp_path)
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg,
                        codebook=cb, n=12, sleep=NOOP)
    ex_before, as_before = calls["extract"], calls["assign"]
    os.utime(cb, (time.time() + 10, time.time() + 10))  # 코드북을 더 새롭게(편집 흉내)
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg,
                        codebook=cb, n=12, sleep=NOOP)
    assert calls["extract"] == ex_before   # 추출 재사용
    assert calls["assign"] > as_before     # 배정만 재실행


def test_other_report_written_in_codebook_mode(tmp_path):
    calls, ex, tx, asg = _fakes()
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg,
                        codebook=_codebook(tmp_path), n=12, sleep=NOOP)
    report = json.loads((tmp_path / "other-report.json").read_text(encoding="utf-8"))
    assert "ratio" in report and "warning" in report
