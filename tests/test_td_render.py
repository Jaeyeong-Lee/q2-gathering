import td_render


def _persons():
    return [{"person_id": 1, "name": "김철수", "pjt": "공정기술", "cl_level": "CL3", "signal_present": True},
            {"person_id": 2, "name": "이영희", "pjt": "양산기술", "cl_level": "CL2", "signal_present": True},
            {"person_id": 3, "name": "박무신", "pjt": "기획운영", "cl_level": "CL4", "signal_present": False}]


def _assignments():
    return [{"person_id": 1, "axis": "future_task", "text": "MBT 강화", "category": "Burn-in 신뢰성", "quote": "MBT Burn-in"},
            {"person_id": 2, "axis": "capability_gap", "text": "ATE 배움", "category": "ATE 운영", "quote": "ATE 필요"},
            {"person_id": 1, "axis": "future_task", "text": "잡다", "category": "Other", "quote": "기타"}]


def _aggregates():
    return {"categories": [
        {"name": "Burn-in 신뢰성", "people": 1, "pjt_spread": 1, "cl_spread": 1,
         "have": 0, "gap": 0, "readiness": "선행 신호", "pjts": ["공정기술"], "cls": ["CL3"]},
        {"name": "ATE 운영", "people": 1, "pjt_spread": 1, "cl_spread": 1,
         "have": 0, "gap": 1, "readiness": "선행 신호", "pjts": ["양산기술"], "cls": ["CL2"]}],
        "minority": [{"name": "Burn-in 신뢰성", "people": 1, "readiness": "선행 신호"}]}


# --- coverage (순수 함수) ---

def test_coverage_rates_match_inputs():
    cov = td_render.coverage(_persons(), _assignments(),
                             failed=[9], extract_dropped=2, assign_dropped=1)
    assert cov["total_people"] == 3
    assert cov["no_signal"] == 1
    assert abs(cov["no_signal_rate"] - 1 / 3) < 1e-9
    assert cov["other"] == 1
    assert abs(cov["other_rate"] - 1 / 3) < 1e-9  # Other 1 / 배정 3
    assert cov["failed_count"] == 1
    assert cov["dropped_count"] == 3               # 추출 2 + 배정 1


# --- render ---

def test_render_frames_as_workshop_input_and_lists_categories():
    md = td_render.render_markdown(_aggregates(), _persons(), _assignments())
    assert "워크숍" in md            # 확정 로드맵 아니라 워크숍 입력물임을 명시
    assert "Burn-in 신뢰성" in md and "ATE 운영" in md


def test_render_shows_real_name_evidence_by_default():
    md = td_render.render_markdown(_aggregates(), _persons(), _assignments())
    assert "김철수" in md            # 근거 인용에 실명


def test_render_anonymize_hides_real_names():
    md = td_render.render_markdown(_aggregates(), _persons(), _assignments(), anonymize=True)
    assert "김철수" not in md and "이영희" not in md


def test_render_includes_crosstab_and_minority_and_coverage():
    md = td_render.render_markdown(_aggregates(), _persons(), _assignments(),
                                   failed=[], extract_dropped=0, assign_dropped=0)
    assert "교차표" in md
    assert "소수" in md
    assert "커버리지" in md


def test_write_does_not_target_dist(tmp_path):
    out = tmp_path / "workshop-input.md"
    td_render.write(_aggregates(), _persons(), _assignments(), out)
    assert out.exists() and "dist" not in str(out)
