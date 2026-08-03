import json
from collections import Counter

import td_pipeline

NOOP = lambda _: None


def _fakes():
    """전 스테이지를 통과시키는 가짜 call 3종. 인용은 프롬프트 원문/항목에서 실제 발췌."""
    calls = Counter()

    def extract(prompt):
        calls["extract"] += 1
        src = prompt.split("원문:\n", 1)[1].strip()
        q = src[:8]  # 원문 실제 부분문자열 → grounding 통과
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

    def narrate(prompt):
        calls["narrate"] += 1
        if "카테고리 요약" in prompt:
            return json.dumps({"trends": [{"text": "흐름", "citation_ids": [0]}],
                              "minority_notes": []}, ensure_ascii=False)
        return json.dumps({"narrative": "서사", "citation_ids": [0]}, ensure_ascii=False)

    return calls, extract, taxo, assign, narrate


def test_smoke_end_to_end_produces_workshop_md(tmp_path):
    calls, ex, tx, asg, nr = _fakes()
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg, narrate_call=nr,
                        n=12, seed=0, sleep=NOOP)
    md = (tmp_path / "workshop-input.md").read_text(encoding="utf-8")
    assert "워크숍" in md and "합성역량" in md
    # 네 스테이지 모두 실행됨 (모델 이원화: 유도/배정/해석 서로 다른 call)
    assert calls["extract"] > 0 and calls["taxo"] > 0 and calls["assign"] > 0 and calls["narrate"] > 0


def test_smoke_produces_layer2_interpretation(tmp_path):
    calls, ex, tx, asg, nr = _fakes()
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg, narrate_call=nr,
                        n=12, seed=0, sleep=NOOP)
    index_md = (tmp_path / "interpretation" / "index.md").read_text(encoding="utf-8")
    assert "AI 해석" in index_md  # Layer 1과 안 섞이게 라벨 명시


def test_rerun_makes_zero_llm_calls(tmp_path):
    calls, ex, tx, asg, nr = _fakes()
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg, narrate_call=nr,
                        n=12, sleep=NOOP)
    calls.clear()
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg, narrate_call=nr,
                        n=12, sleep=NOOP)
    assert sum(calls.values()) == 0  # 중간 산출물 존재 → 전부 skip


def test_force_reruns_stages(tmp_path):
    calls, ex, tx, asg, nr = _fakes()
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg, narrate_call=nr,
                        n=12, sleep=NOOP)
    calls.clear()
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg, narrate_call=nr,
                        n=12, sleep=NOOP, force=True)
    assert calls["extract"] > 0  # force면 재실행
