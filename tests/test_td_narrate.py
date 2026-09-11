import json

import td_narrate

NOOP = lambda _: None


def _persons():
    return [{"person_id": 1, "name": "김철수"}, {"person_id": 2, "name": "이영희"}]


def _assignments():
    return [
        {"person_id": 1, "axis": "future_task", "text": "MBT 강화", "category": "Burn-in 신뢰성", "quote": "MBT를 강화하고 싶다"},
        {"person_id": 2, "axis": "capability_gap", "text": "ATE 배움", "category": "Burn-in 신뢰성", "quote": "ATE 지식이 부족하다"},
    ]


def _categories():
    return [{"name": "Burn-in 신뢰성", "people": 2, "pjt_spread": 1, "cl_spread": 1,
             "have": 0, "gap": 1, "readiness": "선행 신호", "definition": "정의"}]


# --- 근거 풀 구성 ---

def test_evidence_by_category_groups_by_category():
    ev = td_narrate._evidence_by_category(_assignments(), _persons())
    names = {it["name"] for it in ev["Burn-in 신뢰성"]}
    assert names == {"김철수", "이영희"}


def test_evidence_by_category_anonymize_hides_names():
    ev = td_narrate._evidence_by_category(_assignments(), _persons(), anonymize=True)
    names = {it["name"] for it in ev["Burn-in 신뢰성"]}
    assert names == {"P1", "P2"}


def test_evidence_by_category_caps_per_category():
    assignments = [{"person_id": 1, "axis": "future_task", "text": "x", "category": "c", "quote": f"q{i}"}
                   for i in range(20)]
    ev = td_narrate._evidence_by_category(assignments, [{"person_id": 1, "name": "김"}], cap=5)
    assert len(ev["c"]) == 5


# --- 팀 총평: citation grounding ---

def test_narrate_team_keeps_bullet_with_valid_citation_id():
    flat = [{"name": "김철수", "quote": "MBT를 강화하고 싶다", "category": "Burn-in 신뢰성"}]
    call = lambda _: json.dumps({"trends": [{"text": "Burn-in 신뢰성 강화 흐름", "citation_ids": [0]}],
                                 "minority_notes": []}, ensure_ascii=False)
    team = td_narrate.narrate_team(_categories(), flat, call, sleep=NOOP)
    assert len(team["trends"]) == 1
    assert team["trends"][0]["citations"][0]["name"] == "김철수"


def test_narrate_team_drops_bullet_when_citation_id_out_of_range():
    flat = [{"name": "김철수", "quote": "MBT를 강화하고 싶다", "category": "Burn-in 신뢰성"}]
    call = lambda _: json.dumps({"trends": [{"text": "지어낸 흐름", "citation_ids": [99]}],
                                 "minority_notes": []}, ensure_ascii=False)
    team = td_narrate.narrate_team(_categories(), flat, call, tries=1, sleep=NOOP)
    assert team["trends"] == []  # 근거 없는 문장은 버림


def test_narrate_team_drops_bullet_with_missing_text():
    flat = [{"name": "김철수", "quote": "q", "category": "c"}]
    call = lambda _: json.dumps({"trends": [{"text": "", "citation_ids": [0]}],
                                 "minority_notes": []}, ensure_ascii=False)
    team = td_narrate.narrate_team(_categories(), flat, call, tries=1, sleep=NOOP)
    assert team["trends"] == []


# --- 카테고리 서사: citation grounding ---

def test_narrate_category_success_resolves_citations():
    evidence = [{"name": "김철수", "quote": "MBT를 강화하고 싶다"}]
    call = lambda _: json.dumps({"narrative": "팀은 Burn-in 신뢰성에 집중한다.",
                                 "citation_ids": [0]}, ensure_ascii=False)
    res = td_narrate.narrate_category(_categories()[0], evidence, call, sleep=NOOP)
    assert res["narrative"] == "팀은 Burn-in 신뢰성에 집중한다."
    assert res["citations"] == evidence


def test_narrate_category_returns_none_when_no_valid_citation():
    evidence = [{"name": "김철수", "quote": "MBT를 강화하고 싶다"}]
    call = lambda _: json.dumps({"narrative": "지어낸 서사", "citation_ids": [7]}, ensure_ascii=False)
    res = td_narrate.narrate_category(_categories()[0], evidence, call, tries=1, sleep=NOOP)
    assert res is None


# --- 전체 통합 + 렌더 ---

def test_narrate_writes_index_and_category_page(tmp_path):
    aggregates = tmp_path / "aggregates.json"
    aggregates.write_text(json.dumps({"categories": _categories(), "minority": []}, ensure_ascii=False),
                          encoding="utf-8")
    assignments = tmp_path / "assignments.json"
    assignments.write_text(json.dumps(_assignments(), ensure_ascii=False), encoding="utf-8")
    persons = tmp_path / "extracted.json"
    persons.write_text(json.dumps(_persons(), ensure_ascii=False), encoding="utf-8")
    taxonomy = tmp_path / "taxonomy.json"
    taxonomy.write_text(json.dumps([{"name": "Burn-in 신뢰성", "definition": "d",
                                    "inclusion_criteria": "i",
                                    "relations": [{"to": "ATE 운영", "type": "related"}]}],
                                   ensure_ascii=False), encoding="utf-8")

    def call(prompt):
        if "카테고리 요약" in prompt:  # 팀 프롬프트
            return json.dumps({"trends": [{"text": "흐름", "citation_ids": [0]}],
                              "minority_notes": []}, ensure_ascii=False)
        return json.dumps({"narrative": "서사", "citation_ids": [0]}, ensure_ascii=False)

    out_dir = tmp_path / "interpretation"
    res = td_narrate.narrate(aggregates, assignments, persons, taxonomy, out_dir, call, sleep=NOOP)

    assert len(res["pages"]) == 1
    index_md = (out_dir / "index.md").read_text(encoding="utf-8")
    assert "AI 해석" in index_md and "흐름" in index_md
    page_md = (out_dir / "category-00.md").read_text(encoding="utf-8")
    assert "서사" in page_md
    assert "ATE 운영" in page_md  # taxonomy relations이 그대로 렌더됨


def test_narrate_skips_category_with_no_evidence(tmp_path):
    aggregates = tmp_path / "aggregates.json"
    cats = _categories() + [{"name": "무근거 카테고리", "people": 0, "pjt_spread": 0, "cl_spread": 0,
                             "have": 0, "gap": 0, "readiness": "선행 신호", "definition": ""}]
    aggregates.write_text(json.dumps({"categories": cats, "minority": []}, ensure_ascii=False),
                          encoding="utf-8")
    assignments = tmp_path / "assignments.json"
    assignments.write_text(json.dumps(_assignments(), ensure_ascii=False), encoding="utf-8")
    persons = tmp_path / "extracted.json"
    persons.write_text(json.dumps(_persons(), ensure_ascii=False), encoding="utf-8")

    call = lambda _: json.dumps({"narrative": "서사", "citation_ids": [0],
                                 "trends": [], "minority_notes": []}, ensure_ascii=False)
    out_dir = tmp_path / "interpretation"
    res = td_narrate.narrate(aggregates, assignments, persons, None, out_dir, call, sleep=NOOP)
    assert len(res["pages"]) == 1  # 근거 없는 카테고리는 페이지 자체가 안 생김
