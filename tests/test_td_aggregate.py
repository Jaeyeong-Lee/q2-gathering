import json

import td_aggregate


def _person(pid, pjt, cl):
    return {"person_id": pid, "pjt": pjt, "cl_level": cl}


def _a(pid, category, axis="future_task"):
    return {"person_id": pid, "axis": axis, "text": "t", "category": category, "quote": "q"}


def test_spread_counts_distinct_pjt_and_cl_not_rows():
    persons = [_person(1, "양산기술", "CL2"), _person(2, "양산기술", "CL3"), _person(3, "양산기술", "CL4")]
    # 세 명 모두 양산기술 → pjt 확산도 1, cl 확산도 3 (행 수 3이 아님)
    assigns = [_a(1, "X"), _a(2, "X"), _a(3, "X")]
    out = td_aggregate.aggregate(assigns, persons)
    cat = next(c for c in out["categories"] if c["name"] == "X")
    assert cat["people"] == 3
    assert cat["pjt_spread"] == 1
    assert cat["cl_spread"] == 3


def test_gap_dominant_category_marked_gap_only():
    persons = [_person(i, "공정기술", "CL3") for i in (1, 2, 3)]
    assigns = [_a(i, "Y", axis="capability_gap") for i in (1, 2, 3)]
    out = td_aggregate.aggregate(assigns, persons)
    cat = next(c for c in out["categories"] if c["name"] == "Y")
    assert cat["gap"] == 3 and cat["have"] == 0
    assert cat["readiness"] == "갭만 있음"


def test_have_dominant_category_marked_already_done():
    persons = [_person(i, "공정기술", "CL3") for i in (1, 2, 3)]
    assigns = [_a(i, "Z", axis="capability_have") for i in (1, 2, 3)]
    out = td_aggregate.aggregate(assigns, persons)
    cat = next(c for c in out["categories"] if c["name"] == "Z")
    assert cat["readiness"] == "이미 함"


def test_few_person_category_is_weak_signal_and_kept_in_minority():
    persons = [_person(1, "기획운영", "CL4")]
    assigns = [_a(1, "특이방향")]
    out = td_aggregate.aggregate(assigns, persons)
    cat = next(c for c in out["categories"] if c["name"] == "특이방향")
    assert cat["readiness"] == "선행 신호"
    # 소수의견은 별도 트랙에 보존돼 다수 요약에 흡수되지 않는다
    assert any(m["name"] == "특이방향" for m in out["minority"])


def test_categories_sorted_by_people_desc():
    persons = [_person(i, "양산기술", "CL3") for i in range(1, 5)]
    assigns = [_a(1, "small"), _a(2, "big"), _a(3, "big"), _a(4, "big")]
    out = td_aggregate.aggregate(assigns, persons)
    assert out["categories"][0]["name"] == "big"


def test_writes_aggregates_file(tmp_path):
    out_path = tmp_path / "aggregates.json"
    td_aggregate.aggregate([_a(1, "X")], [_person(1, "양산기술", "CL2")], out_path)
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert "categories" in written and "minority" in written
