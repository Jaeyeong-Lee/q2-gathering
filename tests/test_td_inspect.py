import json

import td_inspect


def _person(pid, name, **kw):
    return {"person_id": pid, "name": name, "pjt": "양산기술", "cl_level": "CL3",
            "signal_present": True, "direction": None, "text": f"{name}의 회고 원문",
            "future_task": [], "capability_have": [], "capability_gap": [], **kw}


def _task(text, horizon="단기"):
    return {"text": text, "horizon": horizon, "quotes": ["원문"]}


def _a(pid, text, category, axis="future_task", quote="근거"):
    return {"person_id": pid, "axis": axis, "text": text, "category": category, "quote": quote}


def _fixture():
    persons = [_person(1, "홍길동", future_task=[_task("자동화한다")]),
               _person(2, "김영희", future_task=[_task("표준화한다", "장기")])]
    assigns = [_a(1, "자동화한다", "테스트 자동화"), _a(2, "표준화한다", "테스트 자동화")]
    taxonomy = [{"name": "테스트 자동화", "definition": "정의", "inclusion_criteria": "기준",
                 "relations": [{"to": "다른것", "type": "related"}]}]
    aggregates = {"categories": [{"name": "테스트 자동화", "people": 2, "pjt_spread": 1,
                                  "cl_spread": 1, "have": 0, "gap": 0,
                                  "readiness": "선행 신호", "pjts": ["양산기술"],
                                  "cls": ["CL3"]}],
                  "minority": []}
    return aggregates, persons, assigns, taxonomy


def test_payload_joins_taxonomy_definition_into_categories():
    """정의는 taxonomy에만 있고 aggregates엔 없다 — 탐색기는 둘을 이어 붙여야 한다."""
    payload = td_inspect.build_payload(*_fixture())
    cat = payload["categories"][0]
    assert cat["definition"] == "정의"
    assert cat["inclusion_criteria"] == "기준"
    assert cat["people"] == 2


def test_payload_carries_relations():
    payload = td_inspect.build_payload(*_fixture())
    assert payload["categories"][0]["relations"] == [{"to": "다른것", "type": "related"}]


def test_payload_carries_source_text_per_person():
    """원문 펼치기(#40)의 재료. 화면은 펼칠 때만 DOM에 그린다."""
    payload = td_inspect.build_payload(*_fixture())
    by_id = {p["person_id"]: p for p in payload["persons"]}
    assert by_id[1]["text"] == "홍길동의 회고 원문"


def test_anonymize_drops_source_text_entirely():
    """원문 안의 실명은 정규식으로 지울 수 없다 — 지우는 척하면 그게 더 위험하다.
    익명화를 켜면 원문을 아예 싣지 않는 쪽이 정직하다."""
    aggregates, persons, assigns, taxonomy = _fixture()
    payload = td_inspect.build_payload(aggregates, persons, assigns, taxonomy, anonymize=True)
    assert all(p["text"] == "" for p in payload["persons"])


def test_payload_coverage_matches_td_render():
    """같은 숫자를 두 곳에서 다르게 계산하면 회의에서 신뢰를 잃는다."""
    import td_render
    aggregates, persons, assigns, taxonomy = _fixture()
    payload = td_inspect.build_payload(aggregates, persons, assigns, taxonomy)
    assert payload["coverage"] == td_render.coverage(persons, assigns)


def test_anonymize_removes_names_from_payload():
    aggregates, persons, assigns, taxonomy = _fixture()
    payload = td_inspect.build_payload(aggregates, persons, assigns, taxonomy, anonymize=True)
    assert "홍길동" not in json.dumps(payload, ensure_ascii=False)


def test_category_without_taxonomy_entry_still_appears():
    """Other는 taxonomy에 없다 — 정의가 없다고 목록에서 사라지면 안 된다."""
    aggregates, persons, assigns, taxonomy = _fixture()
    aggregates["categories"].append({"name": "Other", "people": 1, "pjt_spread": 1,
                                     "cl_spread": 1, "have": 0, "gap": 0,
                                     "readiness": "선행 신호", "pjts": [], "cls": []})
    payload = td_inspect.build_payload(aggregates, persons, assigns, taxonomy)
    other = next(c for c in payload["categories"] if c["name"] == "Other")
    assert other["definition"] == ""


def test_render_is_self_contained():
    html = td_inspect.render_html(td_inspect.build_payload(*_fixture()))
    assert "<script" in html and "</html>" in html
    # 외부에서 무언가를 끌어오는 구문이 없어야 file://로 열린다
    for bad in ('<script src=', '<link ', '<img ', 'fetch(', 'XMLHttpRequest', 'url(http'):
        assert bad not in html


def test_render_survives_script_tag_in_data():
    """인용에 </script>가 들어가도 HTML이 깨지지 않아야 한다."""
    aggregates, persons, assigns, taxonomy = _fixture()
    assigns[0]["quote"] = "인용에 </script> 가 있다"
    html = td_inspect.render_html(td_inspect.build_payload(aggregates, persons, assigns, taxonomy))
    assert "</script> 가 있다" not in html          # 그대로 새어나오면 스크립트가 닫힌다
    assert "\\u003c/script\\u003e" in html


def test_write_creates_file(tmp_path):
    out = tmp_path / "inspect.html"
    td_inspect.write(*_fixture(), out_path=out)
    assert out.exists() and out.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_write_refuses_dist_path(tmp_path):
    """dist/는 GitHub Pages로 배포 추적된다 — 실명이 박힌 파일이 들어가면 공개된다."""
    import pytest
    out = tmp_path / "dist" / "inspect.html"
    with pytest.raises(ValueError):
        td_inspect.write(*_fixture(), out_path=out)
    assert not out.exists()


def test_payload_exceptions_split_three_ways():
    """무신호 / Other / 배정 폐기 — 세 목록이 서로 겹치지 않아야 한다."""
    aggregates, persons, assigns, taxonomy = _fixture()
    persons.append(_person(3, "박무신", signal_present=False))
    persons.append(_person(4, "최폐기", future_task=[_task("폐기될것")]))
    persons.append(_person(5, "정기타", future_task=[_task("기타로감")]))
    assigns.append(_a(5, "기타로감", "Other"))
    aggregates["categories"].append({"name": "Other", "people": 1, "pjt_spread": 1,
                                     "cl_spread": 1, "have": 0, "gap": 0,
                                     "readiness": "선행 신호", "pjts": [], "cls": []})
    ex = td_inspect.build_payload(aggregates, persons, assigns, taxonomy)["exceptions"]

    assert [p["person_id"] for p in ex["no_signal"]] == [3]
    assert [d["text"] for d in ex["dropped"]] == ["폐기될것"]
    assert [o["text"] for o in ex["other"]] == ["기타로감"]

    ids = lambda rows: {(r["person_id"], r.get("text")) for r in rows}
    assert not (ids(ex["dropped"]) & ids(ex["other"]))


def test_exception_counts_match_coverage():
    """커버리지 숫자와 목록 길이가 어긋나면 회의에서 신뢰를 잃는다."""
    aggregates, persons, assigns, taxonomy = _fixture()
    persons.append(_person(3, "박무신", signal_present=False))
    payload = td_inspect.build_payload(aggregates, persons, assigns, taxonomy)
    assert len(payload["exceptions"]["no_signal"]) == payload["coverage"]["no_signal"]
    assert len(payload["exceptions"]["other"]) == payload["coverage"]["other"]


def test_extract_failed_count_surfaced_as_number_only():
    """추출 단계에서 통째로 실패한 사람은 extracted.json에 없어 목록으로 못 잡는다.
    숫자로만 표시하고 그 한계를 화면이 밝혀야 한다."""
    payload = td_inspect.build_payload(*_fixture())
    assert "failed_count" in payload["coverage"]
