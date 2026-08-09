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


def test_payload_omits_source_text():
    """원문은 이 화면이 안 쓴다(#40의 원문 펼치기 몫). 미리 실으면 파일만 무거워지고,
    원문 안의 실명은 익명화로 지울 수 없어 구멍이 된다."""
    payload = td_inspect.build_payload(*_fixture())
    assert "회고 원문" not in json.dumps(payload, ensure_ascii=False)
    assert all("text" not in p for p in payload["persons"])


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
    # 외부 네트워크 참조가 없어야 file://로 열린다
    for bad in ("http://", "https://", "//cdn", "src=\"/"):
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
