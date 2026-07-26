import json
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

    def embed(text):
        calls["embed"] += 1
        return [sum(ord(c) for c in text) % 5, 1.0]

    return calls, extract, embed


def test_s4_smoke_produces_digest_without_categorization(tmp_path):
    calls, ex, emb = _fakes()
    td_pipeline.run_retrieval(tmp_path, extract_call=ex, embed=emb, n=12, sleep=NOOP)
    assert (tmp_path / "digest.md").exists()
    # 카테고리화 스테이지 없음
    assert not (tmp_path / "taxonomy.json").exists()
    assert not (tmp_path / "assignments.json").exists()
    assert calls["extract"] > 0 and calls["embed"] > 0


def test_s4_rerun_makes_zero_calls(tmp_path):
    calls, ex, emb = _fakes()
    td_pipeline.run_retrieval(tmp_path, extract_call=ex, embed=emb, n=12, sleep=NOOP)
    calls.clear()
    td_pipeline.run_retrieval(tmp_path, extract_call=ex, embed=emb, n=12, sleep=NOOP)
    assert sum(calls.values()) == 0  # extracted·digest 존재 → 전부 skip
