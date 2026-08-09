import td_cards


def _person(pid, **kw):
    """extracted.json의 사람 하나. 축은 kw로 넘긴다."""
    return {"person_id": pid, "name": f"P{pid}", "pjt": "양산기술", "cl_level": "CL3",
            "signal_present": True, "direction": None,
            "future_task": [], "capability_have": [], "capability_gap": [], **kw}


def _task(text, horizon="단기"):
    return {"text": text, "horizon": horizon, "quotes": ["원문"]}


def _item(text):
    return {"text": text, "quotes": ["원문"]}


def _a(pid, axis, text, category="X", quote="q"):
    return {"person_id": pid, "axis": axis, "text": text, "category": category, "quote": quote}


def test_card_carries_author_org_and_horizon():
    persons = [_person(1, pjt="공정기술", cl_level="CL4",
                       future_task=[_task("자동화한다", "장기")])]
    cards = td_cards.build([_a(1, "future_task", "자동화한다")], persons)
    assert len(cards) == 1
    c = cards[0]
    assert c["name"] == "P1"
    assert c["pjt"] == "공정기술" and c["cl_level"] == "CL4"
    assert c["horizon"] == "장기"
    assert c["category"] == "X" and c["axis"] == "future_task"


def test_non_task_axes_have_no_horizon():
    """horizon은 future_task에만 있다 — 나머지 축에선 None(누락 아님)."""
    persons = [_person(1, capability_gap=[_item("역량이 없다")])]
    cards = td_cards.build([_a(1, "capability_gap", "역량이 없다")], persons)
    assert cards[0]["horizon"] is None


def test_duplicate_text_in_same_person_and_axis_stays_two_cards():
    """같은 사람·같은 축에 텍스트가 같은 항목이 둘이면 카드도 둘 — 하나로 접히면 안 된다."""
    persons = [_person(1, future_task=[_task("같은말"), _task("같은말")])]
    assigns = [_a(1, "future_task", "같은말"), _a(1, "future_task", "같은말")]
    cards = td_cards.build(assigns, persons)
    assert len(cards) == 2


def test_more_assignments_than_origin_items_leaves_horizon_empty():
    """원 항목이 동나면 앞 항목의 horizon을 물려주지 않는다 — 근거 없는 시간축을 만드는 것은
    '대응 항목이 없다'는 사실을 지우는 조작이다. pool이 빈 경우와 답이 같아야 한다."""
    persons = [_person(1, future_task=[_task("겹침", "단기"), _task("겹침", "장기")])]
    assigns = [_a(1, "future_task", "겹침")] * 3
    cards = td_cards.build(assigns, persons)
    assert [c["horizon"] for c in cards] == ["단기", "장기", None]


def test_assignment_without_matching_extracted_item_still_becomes_card():
    """상류가 어긋나도 예외로 죽지 않는다 — horizon만 비고 배정 정보는 살린다."""
    persons = [_person(1, future_task=[_task("있는것")])]
    cards = td_cards.build([_a(1, "future_task", "없는것")], persons)
    assert len(cards) == 1
    assert cards[0]["horizon"] is None
    assert cards[0]["text"] == "없는것"


def test_assignment_for_unknown_person_still_becomes_card():
    cards = td_cards.build([_a(99, "future_task", "고아")], [_person(1)])
    assert len(cards) == 1
    assert cards[0]["name"] is None and cards[0]["pjt"] is None


def test_no_signal_person_items_never_leak_in():
    """무신호 인원의 항목은 애초에 배정되지 않지만, 들어와도 카드가 되지 않는다."""
    persons = [_person(1, signal_present=False, future_task=[_task("무신호인데있음")])]
    cards = td_cards.build([_a(1, "future_task", "무신호인데있음")], persons)
    assert cards == []


def test_anonymize_removes_names_everywhere():
    persons = [_person(1, name="홍길동", future_task=[_task("t")])]
    cards = td_cards.build([_a(1, "future_task", "t")], persons, anonymize=True)
    assert "홍길동" not in repr(cards)
    assert cards[0]["name"] == "P1"


def test_direction_axis_is_carried():
    """direction은 단수 객체다 — 리스트 축과 같은 방식으로 카드가 되어야 한다."""
    persons = [_person(1, direction=_item("지향한다"))]
    cards = td_cards.build([_a(1, "direction", "지향한다")], persons)
    assert len(cards) == 1 and cards[0]["axis"] == "direction"


def test_horizon_distribution_counts_future_tasks_per_category():
    persons = [
        _person(1, future_task=[_task("a", "단기"), _task("b", "장기")]),
        _person(2, future_task=[_task("c", "단기")]),
        _person(3, capability_gap=[_item("d")]),
    ]
    assigns = [_a(1, "future_task", "a"), _a(1, "future_task", "b"),
               _a(2, "future_task", "c"), _a(3, "capability_gap", "d")]
    dist = td_cards.horizon_distribution(td_cards.build(assigns, persons))
    # 갭 카드는 시간 분포에 기여하지 않는다 — 시간은 과제의 속성이다
    assert dist["X"] == {"단기": 2, "장기": 1, "불명": 0}


def test_horizon_distribution_omits_categories_without_tasks():
    persons = [_person(1, capability_gap=[_item("d")])]
    dist = td_cards.horizon_distribution(td_cards.build([_a(1, "capability_gap", "d")], persons))
    assert "X" not in dist


def test_build_accepts_paths(tmp_path):
    """load_json 규약 — 경로도 인메모리 객체도 받는다."""
    import json
    persons = [_person(1, future_task=[_task("t")])]
    p = tmp_path / "extracted.json"
    a = tmp_path / "assignments.json"
    p.write_text(json.dumps(persons, ensure_ascii=False), encoding="utf-8")
    a.write_text(json.dumps([_a(1, "future_task", "t")], ensure_ascii=False), encoding="utf-8")
    assert len(td_cards.build(a, p)) == 1
