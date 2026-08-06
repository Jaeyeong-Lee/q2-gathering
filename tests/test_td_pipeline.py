import json
from collections import Counter

import pytest

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
        if "relations" in prompt:          # 마지막 관계 도출 패스
            calls["taxo_relations"] += 1
            return json.dumps({"relations": []}, ensure_ascii=False)
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


def test_partial_taxonomy_resumes_via_run_all_instead_of_being_skipped(tmp_path):
    # n=12/batch_size=6 → facet 12개(가짜 extract는 사람당 1개), 2배치.
    calls, ex, tx, asg, nr = _fakes()
    taxo_calls = {"n": 0}

    def flaky_taxo(prompt):
        taxo_calls["n"] += 1
        if taxo_calls["n"] >= 2:  # 배치 1은 통과, 배치 2부터는 재시도해도 계속 실패
            raise RuntimeError("내부망 에러")
        return tx(prompt)

    with pytest.raises(RuntimeError):
        td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=flaky_taxo, assign_call=asg,
                            narrate_call=nr, n=12, seed=0, batch_size=6, sleep=NOOP)
    assert not (tmp_path / "assignments.json").exists()  # taxonomy에서 중단 — 뒤 스테이지 없음

    calls.clear()
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg, narrate_call=nr,
                        n=12, seed=0, batch_size=6, sleep=NOOP)
    # 배치 1은 스킵(이미 완료), 배치 2 + 관계 패스만 재호출 — 게이트가 완료율 기반
    assert calls["taxo"] == 2 and calls["taxo_relations"] == 1
    md = (tmp_path / "workshop-input.md").read_text(encoding="utf-8")
    assert "합성역량" in md


def test_partial_assign_resumes_via_run_all_instead_of_being_skipped(tmp_path):
    calls, ex, tx, asg, nr = _fakes()
    assign_calls = {"n": 0}

    def flaky_assign(prompt):
        assign_calls["n"] += 1
        if assign_calls["n"] >= 5:  # facet 4개까진 통과, 5번째부터 계속 실패
            raise RuntimeError("내부망 에러")
        return asg(prompt)

    with pytest.raises(RuntimeError):
        td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=flaky_assign,
                            narrate_call=nr, n=12, seed=0, sleep=NOOP)
    assert not (tmp_path / "workshop-input.md").exists()  # assign에서 중단 — 뒤 스테이지 없음

    calls.clear()
    td_pipeline.run_all(tmp_path, extract_call=ex, taxo_call=tx, assign_call=asg, narrate_call=nr,
                        n=12, seed=0, sleep=NOOP)
    assert calls["assign"] == 8  # 4개는 스킵(이미 완료), 나머지 8개만 재호출 — 게이트가 완료율 기반
    md = (tmp_path / "workshop-input.md").read_text(encoding="utf-8")
    assert "합성역량" in md
