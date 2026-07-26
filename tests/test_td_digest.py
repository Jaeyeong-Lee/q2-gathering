import td_digest
import td_index


def _embed(text):
    return [sum(ord(c) for c in text) % 5, 1.0]


def _persons():
    return [
        {"person_id": 1, "name": "김철수", "cl_level": "CL3", "pjt": "공정기술", "part": "FA",
         "signal_present": True, "capability_have": [], "direction": None,
         "future_task": [{"text": "STDF FA 자동화", "horizon": "단기", "quotes": ["STDF"]}],
         "capability_gap": [{"text": "데이터 분석 역량", "quotes": ["데이터 분석"]}]},
        {"person_id": 2, "name": "이영희", "cl_level": "CL2", "pjt": "양산기술", "part": "ATE",
         "signal_present": False, "future_task": [], "capability_have": [],
         "capability_gap": [], "direction": None},
    ]


def _idx():
    return td_index.build(_persons(), _embed)


def test_digest_renders_all_preset_query_titles():
    md = td_digest.render_markdown(_idx(), _embed, _persons())
    for qdef in td_digest.default_queries():
        assert qdef["title"] in md


def test_zero_hit_query_recorded_as_none_not_silently_dropped():
    # capability_have 항목이 하나도 없음 → 해당 섹션은 "없음"으로 명시
    md = td_digest.render_markdown(_idx(), _embed, _persons(),
                                   queries=[{"title": "보유역량", "axis": "capability_have"}])
    assert "보유역량" in md and "없음" in md


def test_coverage_counts_indexed_and_contributing_and_no_signal():
    cov = td_digest.coverage(_idx(), _persons())
    assert cov["total_people"] == 2
    assert cov["no_signal"] == 1
    assert cov["indexed_docs"] == 2          # 1번의 future_task 1 + gap 1
    assert cov["contributing_people"] == 1   # 무신호 2번 제외


def test_coverage_section_present_in_markdown():
    md = td_digest.render_markdown(_idx(), _embed, _persons())
    assert "커버리지" in md


def test_anonymize_hides_real_names():
    md = td_digest.render_markdown(_idx(), _embed, _persons(), anonymize=True)
    assert "김철수" not in md


def test_write_targets_non_dist(tmp_path):
    out = tmp_path / "digest.md"
    td_digest.write(_idx(), _embed, _persons(), out)
    assert out.exists() and "/dist/" not in str(out)  # 배포 디렉터리 미타깃
