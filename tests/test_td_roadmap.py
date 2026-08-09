import td_roadmap


def _card(cat, axis, text, horizon=None, pid=1, name="홍길동"):
    return {"person_id": pid, "name": name, "pjt": "양산기술", "cl_level": "CL3",
            "category": cat, "axis": axis, "text": text, "quote": "근거", "horizon": horizon}


def _cat(name, **kw):
    return {"name": name, "people": 5, "pjt_spread": 2, "cl_spread": 2,
            "have": 3, "gap": 2, "readiness": "이미 함", "pjts": [], "cls": [],
            "definition": "", "inclusion_criteria": "", "relations": [], **kw}


# ── 투표 대상 축 ──────────────────────────────────────────────────────

def test_only_task_and_gap_become_cards():
    """'언제'라는 질문은 보유·방향엔 성립하지 않는다 — 배경 정보로만 쓴다."""
    cards = [_card("A", "future_task", "t", "단기"), _card("A", "capability_gap", "g"),
             _card("A", "capability_have", "h"), _card("A", "direction", "d")]
    axes = {c["axis"] for c in td_roadmap.votable(cards)}
    assert axes == {"future_task", "capability_gap"}


# ── 시간축 초안 ───────────────────────────────────────────────────────

def test_task_card_draft_band_follows_its_own_horizon():
    cards = [_card("A", "future_task", "단기것", "단기"),
             _card("A", "future_task", "장기것", "장기"),
             _card("A", "future_task", "불명것", "불명")]
    got = {c["text"]: c["draft_band"] for c in td_roadmap.votable(cards)}
    assert got == {"단기것": "단기", "장기것": "장기", "불명것": "중기"}


def test_task_without_horizon_defaults_to_middle():
    """horizon이 없는 과제(상류 어긋남)는 가운데 — 근거 없이 급하다고 밀지 않는다."""
    assert td_roadmap.votable([_card("A", "future_task", "t")])[0]["draft_band"] == "중기"


def test_gap_card_starts_one_band_left_of_its_category_tasks():
    """역량은 그걸 쓰는 과제보다 먼저 확보돼야 한다 — 제약을 초안에 미리 반영한다."""
    cards = [_card("A", "future_task", "t", "장기"), _card("A", "capability_gap", "g")]
    gap = next(c for c in td_roadmap.votable(cards) if c["axis"] == "capability_gap")
    assert gap["draft_band"] == "중기"


def test_gap_card_cannot_go_left_of_the_first_band():
    cards = [_card("A", "future_task", "t", "단기"), _card("A", "capability_gap", "g")]
    gap = next(c for c in td_roadmap.votable(cards) if c["axis"] == "capability_gap")
    assert gap["draft_band"] == "단기"


def test_gap_card_without_any_task_in_category_sits_in_middle():
    """과제가 없으면 기준이 없다 — 왼쪽으로 당길 근거가 없으므로 가운데."""
    gap = td_roadmap.votable([_card("A", "capability_gap", "g")])[0]
    assert gap["draft_band"] == "중기"


def test_category_draft_uses_the_majority_of_its_task_horizons():
    cards = [_card("A", "future_task", "1", "단기"), _card("A", "future_task", "2", "단기"),
             _card("A", "future_task", "3", "장기")]
    nodes = td_roadmap.build_nodes(cards, [_cat("A")])
    assert nodes[0]["draft_band"] == "단기"


def test_category_without_tasks_has_no_draft_and_says_so():
    nodes = td_roadmap.build_nodes([_card("A", "capability_gap", "g")], [_cat("A")])
    assert nodes[0]["draft_band"] == "중기"
    assert nodes[0]["horizon_known"] is False


# ── 선후 제약 ─────────────────────────────────────────────────────────

def test_gap_right_of_earliest_task_is_a_violation():
    """역량이 그것을 쓰는 첫 과제보다 뒤에 있으면 실행 불가능한 순서다."""
    cards = [_card("A", "future_task", "t", "단기"), _card("A", "capability_gap", "g")]
    placed = {"g": "장기"}
    v = td_roadmap.violations(td_roadmap.votable(cards), placed)
    assert [x["text"] for x in v] == ["g"]


def test_gap_at_same_band_as_earliest_task_is_not_a_violation():
    cards = [_card("A", "future_task", "t", "중기"), _card("A", "capability_gap", "g")]
    assert td_roadmap.violations(td_roadmap.votable(cards), {"g": "중기"}) == []


def test_category_with_only_one_kind_never_violates():
    """과제만 있거나 역량만 있으면 선후를 판정할 근거가 없다."""
    assert td_roadmap.violations(td_roadmap.votable([_card("A", "capability_gap", "g")]),
                                 {"g": "장기"}) == []
    assert td_roadmap.violations(td_roadmap.votable([_card("A", "future_task", "t", "단기")]),
                                 {}) == []


def test_violation_is_scoped_to_its_own_category():
    cards = [_card("A", "future_task", "ta", "단기"), _card("B", "capability_gap", "gb")]
    assert td_roadmap.violations(td_roadmap.votable(cards), {"gb": "장기"}) == []


# ── 노드(카테고리 버블) ────────────────────────────────────────────────

def test_node_carries_axes_needed_by_the_matrix():
    nodes = td_roadmap.build_nodes([_card("A", "future_task", "t", "단기")],
                                   [_cat("A", people=17, pjt_spread=3, cl_spread=2)])
    n = nodes[0]
    assert n["readiness"] == "이미 함"          # 세로축은 데이터가 말한 것 — 그대로 쓴다
    assert n["people"] == 17 and n["pjt_spread"] == 3 and n["cl_spread"] == 2


def test_node_flags_category_with_no_capability_mentions():
    """have=0·gap=0이면 td_aggregate가 '이미 함'으로 판정하는데, 실제로는 '역량 언급이
    없다'이지 '보유가 우세하다'가 아니다. 세로축을 그대로 쓰되 사실을 표시한다."""
    nodes = td_roadmap.build_nodes([_card("A", "future_task", "t", "단기")],
                                   [_cat("A", have=0, gap=0)])
    assert nodes[0]["capability_silent"] is True
    assert td_roadmap.build_nodes([_card("A", "future_task", "t")],
                                  [_cat("A", have=1, gap=0)])[0]["capability_silent"] is False


def test_edges_kept_only_between_present_categories():
    cats = [_cat("A", relations=[{"to": "B", "type": "related"}, {"to": "없음", "type": "broader"}]),
            _cat("B")]
    edges = td_roadmap.build_edges(cats)
    assert edges == [{"from": "A", "to": "B", "type": "related"}]


# ── 렌더 ──────────────────────────────────────────────────────────────

def test_render_is_self_contained_and_escapes_script():
    cards = [_card("A", "future_task", "인용에 </script> 가", "단기")]
    html = td_roadmap.render_html(td_roadmap.build_payload(cards, [_cat("A")]))
    assert html.startswith("<!doctype html>")
    # SVG 네임스페이스(http://www.w3.org/2000/svg)는 가져오는 주소가 아니라 XML 식별자다.
    # 실제로 막아야 하는 건 외부에서 무언가를 끌어오는 구문이다.
    for bad in ('<script src=', '<link ', '<img ', 'fetch(', 'XMLHttpRequest', 'url(http'):
        assert bad not in html
    assert "</script> 가" not in html


def test_write_refuses_dist_path(tmp_path):
    import pytest
    out = tmp_path / "dist" / "roadmap.html"
    with pytest.raises(ValueError):
        td_roadmap.write([_card("A", "future_task", "t", "단기")], [_cat("A")], out_path=out)
    assert not out.exists()
