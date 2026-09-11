import json

import pytest

import td_codebook


def _write(tmp_path, data):
    p = tmp_path / "codebook.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def test_loads_valid_codebook(tmp_path):
    p = _write(tmp_path, [
        {"name": "Burn-in 신뢰성", "definition": "d", "inclusion": "i", "exclusion": "x"},
        {"name": "ATE 운영", "definition": "d", "inclusion": "i"},
    ])
    cb = td_codebook.load(p)
    assert [c["name"] for c in cb] == ["Burn-in 신뢰성", "ATE 운영"]


def test_exclusion_is_optional(tmp_path):
    p = _write(tmp_path, [{"name": "X", "definition": "d", "inclusion": "i"}])
    cb = td_codebook.load(p)
    assert cb[0]["name"] == "X"  # exclusion 없어도 로드


def test_missing_required_field_raises(tmp_path):
    p = _write(tmp_path, [{"name": "X", "definition": "d"}])  # inclusion 누락
    with pytest.raises(ValueError):
        td_codebook.load(p)


def test_duplicate_name_raises(tmp_path):
    p = _write(tmp_path, [
        {"name": "X", "definition": "d", "inclusion": "i"},
        {"name": "X", "definition": "d2", "inclusion": "i2"},
    ])
    with pytest.raises(ValueError):
        td_codebook.load(p)


def test_propose_draft_reuses_taxonomy_and_writes_editable_codebook(tmp_path):
    persons = [{"person_id": 1, "signal_present": True,
                "future_task": [{"text": "MBT 신뢰성 강화", "horizon": "장기", "quotes": ["a"]}],
                "capability_have": [], "capability_gap": [], "direction": None}]
    call = lambda _: json.dumps(
        {"taxonomy": [{"name": "Burn-in 신뢰성", "definition": "d", "inclusion_criteria": "i"}]},
        ensure_ascii=False)
    out = tmp_path / "codebook_draft.json"
    td_codebook.propose_draft(persons, out, call, sleep=lambda _: None)
    draft = td_codebook.load(out)  # 초안이 코드북 스키마로 로드 가능(사람이 편집할 형태)
    assert draft[0]["name"] == "Burn-in 신뢰성"
    assert "inclusion" in draft[0]  # taxonomy의 inclusion_criteria → 코드북 inclusion
