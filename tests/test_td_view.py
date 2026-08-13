import json

import pytest

import td_view


def _person(pid, name, **kw):
    return {"person_id": pid, "name": name, "pjt": "양산기술", "part": "고장분석",
            "cl_level": "CL3", "signal_present": True, "direction": None,
            "future_task": [], "capability_have": [], "capability_gap": [], **kw}


def _task(text, horizon="단기"):
    return {"text": text, "horizon": horizon, "quotes": ["원문 발췌"]}


def _write(d, name, obj):
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def root(tmp_path):
    """pjt_a는 산출물 넷 다, pjt_b는 extracted만, pjt_c는 한 겹 안쪽에 둔다."""
    _write(tmp_path / "pjt_a", "extracted",
           [_person(0, "홍길동", future_task=[_task("자동 진단 로직 개선")]),
            _person(1, "김철수", signal_present=False)])
    _write(tmp_path / "pjt_a", "taxonomy",
           [{"name": "진단 자동화", "definition": "정의",
             "relations": [{"to": "품질", "type": "broader"}]}])
    _write(tmp_path / "pjt_a", "assignments",
           [{"person_id": 0, "axis": "future_task", "text": "자동 진단 로직 개선",
             "category": "진단 자동화", "quote": "근거 인용"}])
    _write(tmp_path / "pjt_a", "aggregates",
           {"categories": [{"name": "진단 자동화", "people": 1, "have": 0, "gap": 1,
                            "readiness": "선행 신호", "pjt_spread": 1, "cl_spread": 1,
                            "pjts": ["양산기술"], "cls": ["CL3"]}],
            "minority": [{"name": "진단 자동화", "people": 1}]})
    _write(tmp_path / "pjt_b", "extracted", [_person(0, "이영희")])
    _write(tmp_path / "pjt_c" / "task_discovery", "extracted", [_person(0, "박민수")])
    (tmp_path / "빈디렉터리").mkdir()
    return tmp_path


def test_산출물_있는_pjt만_이름순으로_찾는다(root):
    assert [n for n, _ in td_view.find_projects(root)] == ["pjt_a", "pjt_b", "pjt_c"]


def test_한겹_안쪽_산출물도_찾는다(root):
    found = dict(td_view.find_projects(root))
    assert found["pjt_c"].name == "task_discovery"
    assert found["pjt_a"].name == "pjt_a"


def test_없는_파일은_None으로_남는다(root):
    b = next(p for p in td_view.collect(root) if p["name"] == "pjt_b")
    assert b["data"]["extracted"] and b["data"]["taxonomy"] is None


def test_anonymize는_실명과_인용을_지운다(root):
    a = next(p for p in td_view.collect(root, anonymize=True) if p["name"] == "pjt_a")
    people = a["data"]["extracted"]
    assert [p["name"] for p in people] == ["P0", "P1"]
    assert people[0]["future_task"][0]["quotes"] == []
    assert a["data"]["assignments"][0]["quote"] == ""
    # 서술 자체는 남는다 — 지우는 건 실명과 원문 인용뿐이다
    assert people[0]["future_task"][0]["text"] == "자동 진단 로직 개선"


def test_html은_데이터를_인라인하고_닫는태그를_깨지_않는다(root):
    out = td_view.build_html(td_view.collect(root))
    assert "__DATA__" not in out and out.rstrip().endswith("</html>")
    assert "진단 자동화" in out
    assert "</script>" not in out.split("const DATA = ")[1].split("\n")[0]


def test_dist_아래로는_쓰지_못한다(root, tmp_path):
    with pytest.raises(ValueError, match="dist"):
        td_view.write(root, tmp_path / "dist" / "view.html")


def test_pjt가_하나도_없으면_멈춘다(tmp_path):
    with pytest.raises(SystemExit):
        td_view.write(tmp_path, tmp_path / "view.html")


def test_파일로_써진다(root, tmp_path):
    out, projects = td_view.write(root, tmp_path / "out" / "view.html")
    assert out.exists() and len(projects) == 3
