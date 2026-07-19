import json
from pathlib import Path
import subprocess

import pytest

import build
import generate_dummy

LOGIC = Path(__file__).parent.parent / "archive" / "cloud_logic.js"


def run_js(expr):
    """cloud_logic.js를 로드한 node에서 expr을 평가해 JSON으로 돌려받는다."""
    script = LOGIC.read_text(encoding="utf-8") + f"\nconsole.log(JSON.stringify({expr}));"
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_cloud_state_sums_and_returns_frequencies():
    # 합산: 용접 4+2=6, 품질 2
    freq = {"1": {"용접": 4, "품질": 2}, "2": {"용접": 2}}
    ids = [1, 2, 3, 4, 5]  # 5명 (3~5는 freq 없음도 허용)
    state = run_js(f"cloudState({json.dumps(freq, ensure_ascii=False)}, {ids})")
    assert state["ok"] is True
    words = dict(state["list"])
    assert words["용접"] == 6
    assert words["품질"] == 2


def test_fewer_than_five_people_refuses_to_render():
    freq = {str(i): {"용접": 1} for i in range(4)}
    state = run_js(f"cloudState({json.dumps(freq)}, [0, 1, 2, 3])")
    assert state["ok"] is False
    assert "list" not in state


def test_scope_ids_for_all_team_cl_ego():
    persons = json.dumps([
        {"id": 0, "pjt": "공정AI", "cl_level": "CL2"},
        {"id": 1, "pjt": "공정AI", "cl_level": "CL3"},
        {"id": 2, "pjt": "비전검사", "cl_level": "CL3"},
    ], ensure_ascii=False)
    assert run_js(f'cloudScopeIds("all", null, {persons}, null)') == [0, 1, 2]
    assert run_js(f'cloudScopeIds("team", "공정AI", {persons}, null)') == [0, 1]
    assert run_js(f'cloudScopeIds("cl", "CL3", {persons}, null)') == [1, 2]
    assert run_js(f'cloudScopeIds("ego", null, {persons}, [2, 0])') == [2, 0]
    assert run_js(f'cloudScopeIds("ego", null, {persons}, null)') == []


def test_common_tags_intersection_preserves_order():
    # 에고 엣지 라벨(006): 앞사람 태그 순서 기준 교집합, 없으면 빈 배열(라벨 생략)
    assert run_js('commonTags(["현장밀착","꼼꼼함","멘토형"], ["멘토형","현장밀착","공정통"])') == ["현장밀착", "멘토형"]
    assert run_js('commonTags(["현장밀착"], ["공정통"])') == []
    assert run_js("commonTags(null, [\"공정통\"])") == []


def test_tag_filter_lights_only_holders():
    # 활성 태그 없으면 전원 통과, 있으면 보유자만 점등(나머지 dim)
    p_with = '{"id": 0, "tags": ["멘토형", "공정통"]}'
    p_without = '{"id": 1, "tags": ["꼼꼼함"]}'
    assert run_js(f'passesTagFilter({p_with}, null)') is True
    assert run_js(f'passesTagFilter({p_without}, null)') is True
    assert run_js(f'passesTagFilter({p_with}, "멘토형")') is True
    assert run_js(f'passesTagFilter({p_without}, "멘토형")') is False
    assert run_js('passesTagFilter({"id": 2}, "멘토형")') is False  # tags 없는 인물


def test_md_to_html_headings_and_paragraphs():
    # 더미 회고 텍스트 형식(001): # 제목, ## 소제목, 빈 줄로 구분된 문단
    md = "# 근원경쟁력\n\n## 핵심 역량\n용접, PLC 중심으로 일했습니다.\n\n## 강점\n협업에 강합니다."
    html = run_js(f"mdToHtml({json.dumps(md, ensure_ascii=False)})")
    assert "<h1>근원경쟁력</h1>" in html
    assert "<h2>핵심 역량</h2>" in html
    assert "<p>용접, PLC 중심으로 일했습니다.</p>" in html
    assert "<p>협업에 강합니다.</p>" in html


def test_md_to_html_escapes_raw_html_and_renders_bullets():
    md = "## 경력\n- <script>alert(1)</script> 대응\n- **금형** 설계"
    html = run_js(f"mdToHtml({json.dumps(md, ensure_ascii=False)})")
    assert "<script>" not in html  # 원문 HTML은 이스케이프
    assert "&lt;script&gt;" in html
    assert "<ul><li>" in html
    assert "<b>금형</b> 설계" in html


def test_build_inlines_wordcloud_lib_and_logic(tmp_path):
    data_dir = generate_dummy.main(out_dir=tmp_path / "data")
    html = build.build(data_dir=data_dir, out_path=tmp_path / "a.html").read_text(encoding="utf-8")
    assert "__ECHARTS_JS__" not in html and "__ECHARTS_WORDCLOUD_JS__" not in html and "__CLOUD_LOGIC_JS__" not in html
    assert "echarts" in html
    assert "function cloudState" in html
    import re
    assert not re.search(r'<(script|link)\b[^>]*?\b(src|href)\s*=\s*["\']https?://', html, re.IGNORECASE)
