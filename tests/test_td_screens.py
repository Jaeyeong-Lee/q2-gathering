"""신규 화면 4종 + 무LLM 스텁의 순수 함수 테스트 (#012~#020, #023).

렌더 화면 테스트 관습은 tests/test_td_inspect.py를 따른다 — 페이로드 단언 → HTML 문자열
단언 → tmp_path 쓰기 → dist/ 거부.
"""
import json

import pytest

import td_consensus
import td_gallery
import td_constellation
import td_fake_llm
import td_heatmap
import td_onepager
import td_questions
import td_render_common


def _card(pid, cat, axis="future_task", *, ax=False, horizon="단기", pjt="양산기술", text=None):
    return {"id": f"{pid}:{axis}:0", "person_id": pid, "name": f"P{pid}", "pjt": pjt,
            "cl_level": "CL3", "category": cat, "axis": axis,
            "text": text or f"{cat} 관련 과제", "quote": cat[:4],
            "horizon": horizon, "ax_mentioned": ax}


def _agg(names, **over):
    return {"categories": [
        {"name": n, "people": over.get("people", 5), "pjt_spread": over.get("pjt_spread", 3),
         "cl_spread": 2, "have": over.get("have", 2), "gap": over.get("gap", 1),
         "readiness": over.get("readiness", "이미 함")} for n in names], "minority": []}


# ─────────────── 렌더 공용 헬퍼 ───────────────

def test_embed_payload_neutralizes_script_tag():
    """</script>가 데이터에 있어도 HTML 파서가 태그로 오인하지 않아야 한다."""
    out = td_render_common.embed_payload({"q": "</script><img onerror=x>"})
    assert "<" not in out and ">" not in out and "&" not in out
    assert json.loads(out)["q"] == "</script><img onerror=x>"


def test_render_substitutes_extra_tokens():
    assert td_render_common.render("a__PAYLOAD__b__LIVE__", {}, live="true") == "a{}btrue"


def test_write_html_rejects_public_path(tmp_path):
    """dist/는 배포 추적 경로 — 실명·인용이 박힌 화면이 즉시 공개된다."""
    out = tmp_path / "dist" / "x.html"
    with pytest.raises(ValueError):
        td_render_common.write_html("<html>", out)
    assert not out.exists()


# ─────────────── 성좌 지도 (#012~#015) ───────────────

def test_constellation_layout_is_deterministic():
    """같은 산출물이면 항상 같은 그림 — '왜 저 별이 저기 있냐'에 답할 수 있어야 한다."""
    cards = [_card(1, "A"), _card(2, "B")]
    a = td_constellation.build_payload(cards, [], _agg(["A", "B"]))
    b = td_constellation.build_payload(cards, [], _agg(["A", "B"]))
    assert [s["x"] for s in a["stars"]] == [s["x"] for s in b["stars"]]


def test_constellation_stars_sit_near_their_category_anchor():
    """별은 자기 별자리 안에 있어야 한다 — 앵커에서 지터 반경을 넘지 않는다."""
    cards = [_card(i, "A") for i in range(6)]
    p = td_constellation.build_payload(cards, [], _agg(["A", "B", "C"]))
    anchor = next(c for c in p["cats"] if c["name"] == "A")
    for s in p["stars"]:
        assert (s["x"] - anchor["x"]) ** 2 + (s["y"] - anchor["y"]) ** 2 <= 120 ** 2


def test_constellation_reserves_slot_for_human_input():
    """#023이 채울 자리. 값이 비어 있어도 필드는 지금 있어야 나중이 스키마 개조가 안 된다."""
    p = td_constellation.build_payload([_card(1, "A")], [], _agg(["A"]))
    assert p["stars"][0]["consensus"] is None


def test_constellation_marks_sparse_categories():
    """빈 하늘(#013) 판정 — 한 조직만 말했거나 보유 없이 갭만 있는 영역."""
    narrow = _agg(["A"], pjt_spread=1)
    gap_only = _agg(["B"], readiness="갭만 있음")
    wide = _agg(["C"])
    agg = {"categories": narrow["categories"] + gap_only["categories"] + wide["categories"]}
    p = td_constellation.build_payload(
        [_card(1, "A"), _card(2, "B"), _card(3, "C")], [], agg)
    sparse = {c["name"]: c["sparse"] for c in p["cats"]}
    assert sparse == {"A": True, "B": True, "C": False}


def test_constellation_ax_flag_rides_from_card():
    """AX 렌즈(#014)는 카드의 관찰값을 그대로 옮길 뿐 판정하지 않는다."""
    p = td_constellation.build_payload([_card(1, "A", ax=True), _card(2, "A")], [], _agg(["A"]))
    assert [s["ax"] for s in p["stars"]] == [True, False]
    assert p["totals"]["ax"] == 1


def test_constellation_carries_source_text_for_lineage():
    """계보(#015)는 원문까지 보여준다 — 사람당 한 벌만 싣는다."""
    src = [{"id": 1, "text": "원문 문장"}]
    p = td_constellation.build_payload([_card(1, "A")], [], _agg(["A"]), src)
    assert p["sources"]["1"] == "원문 문장"


def test_constellation_write_renders_and_guards(tmp_path):
    out = td_constellation.write([_card(1, "A")], [], _agg(["A"]), out_path=tmp_path / "c.html")
    html = out.read_text(encoding="utf-8")
    assert "__PAYLOAD__" not in html and "성좌 지도" in html


# ─────────────── 부서 단면 (#018) ───────────────

def test_heatmap_marks_common_and_local_columns():
    """전 조직이 말한 열 = 공통, 한 조직만 = 국소. 이 구분이 화면의 절반이다."""
    cards = [_card(1, "A", pjt="X"), _card(2, "A", pjt="Y"),
             _card(3, "B", pjt="X")]
    p = td_heatmap.build_payload(cards)
    kinds = {c["cat"]: c["kind"] for c in p["cols"]}
    assert kinds == {"A": "공통", "B": "국소"}


def test_heatmap_counts_are_per_cell():
    cards = [_card(1, "A", pjt="X"), _card(2, "A", pjt="X"), _card(3, "A", pjt="Y")]
    p = td_heatmap.build_payload(cards)
    assert p["grid"][p["pjts"].index("X")][0] == 2
    assert p["peak"] == 2


# ─────────────── 질문 카드 (#019) ───────────────

def test_questions_are_deterministic_and_cite_evidence():
    """같은 입력이면 같은 질문. 근거 없는 질문은 아젠다가 아니라 잔소리다."""
    agg = _agg(["A", "B"])
    a, b = td_questions.build_payload(agg), td_questions.build_payload(agg)
    assert [q["q"] for q in a["questions"]] == [q["q"] for q in b["questions"]]
    assert all(q["evidence"] for q in a["questions"])


def test_questions_flag_gap_without_have():
    """보유 0 · 갭 >0 이면 '누가 이걸 하나' 질문이 나와야 한다."""
    agg = _agg(["A"], have=0, gap=4, readiness="갭만 있음")
    kinds = [q["kind"] for q in td_questions.build_payload(agg)["questions"]]
    assert "하겠다는데 할 사람이 없는 것" in kinds


def test_questions_empty_aggregate_is_normal():
    """규칙에 걸리는 카테고리가 없으면 빈 목록이 정상 상태다."""
    assert td_questions.build_payload({"categories": []})["questions"] == []


# ─────────────── 임원 한 장 (#020) ───────────────

def test_onepager_stats_come_from_data():
    cards = [_card(1, "A"), _card(2, "A"), _card(2, "B")]
    p = td_onepager.build_payload(cards, [], _agg(["A", "B"]))
    assert [s["n"] for s in p["stats"]] == [2, 2, 2]   # 사람 2, 주제 2, 공통 2


def test_onepager_shares_constellation_coordinates():
    """두 화면이 다른 그림을 보여주면 같은 데이터라는 신뢰가 깨진다."""
    cards, agg = [_card(1, "A")], _agg(["A"])
    mini = td_onepager.build_payload(cards, [], agg)["stars"][0]
    full = td_constellation.build_payload(cards, [], agg)["stars"][0]
    assert (mini["x"], mini["y"]) == (full["x"], full["y"])


# ─────────────── 합의의 무게 (#023, #024) ───────────────

def test_consensus_keeps_split_votes_as_dispute():
    """찬반이 갈리면 다수결로 뭉개지 않고 이견으로 남긴다 — 이 산출물의 존재 이유."""
    assert td_consensus.classify({"up": 5, "down": 4}) == td_consensus.DISPUTED
    assert td_consensus.classify({"up": 9, "down": 0}) == td_consensus.PICKED
    assert td_consensus.classify({"up": 1, "down": 9}) == td_consensus.DEFERRED
    assert td_consensus.classify({"up": 0, "down": 0}) == td_consensus.DEFERRED


def test_consensus_marks_stars_and_builds_record():
    cards = [_card(1, "A"), _card(2, "A")]
    votes = [{"card_id": "1:future_task:0", "up": 9, "down": 0}]
    p = td_consensus.build_payload(cards, [], _agg(["A"]), votes)
    marked = {s["id"]: s["consensus"] for s in p["stars"]}
    assert marked["1:future_task:0"] == td_consensus.PICKED
    assert marked["2:future_task:0"] is None          # 투표 없는 별은 관찰만
    assert len(p["consensus"]["record"][td_consensus.PICKED]) == 1


def test_consensus_without_votes_renders_observation_only():
    """워크숍 전 상태 — 투표가 없어도 지도는 정상이어야 한다."""
    p = td_consensus.build_payload([_card(1, "A")], [], _agg(["A"]), [])
    assert p["consensus"]["voted"] == 0
    assert all(s["consensus"] is None for s in p["stars"])


# ─────────────── 무LLM 스텁 ───────────────

def test_fake_extract_quotes_are_real_substrings():
    """인용이 원문 발췌가 아니면 grounding 검증에서 통째로 버려진다."""
    src = "앞으로 STDF 기반 고장분석(FA) 자동화를 하고 싶다. 파이썬 데이터 분석도 익혔다."
    parsed = json.loads(td_fake_llm.extract(f"머리말\n원문:\n{src}"))
    assert parsed["signal_present"]
    for axis in ("future_task", "capability_have"):
        for item in parsed[axis]:
            assert all(q in src for q in item["quotes"])
            assert item["text"] not in item["quotes"]   # 서술이지 복붙이 아니어야 한다


def test_fake_extract_marks_empty_document_as_no_signal():
    parsed = json.loads(td_fake_llm.extract("머리말\n원문:\n그동안 여러 업무를 두루 경험했습니다."))
    assert parsed["signal_present"] is False


def test_fake_taxonomy_spreads_across_categories():
    """카테고리가 하나뿐이면 성좌가 하나뿐인 허수아비가 된다 — 이걸 막으려고 만든 스텁이다."""
    taxo = json.loads(td_fake_llm.taxonomy("카테고리를 만들어라"))["taxonomy"]
    assert len(taxo) >= 8
    assert len({c["name"] for c in taxo}) == len(taxo)


def test_fake_assign_returns_quote_from_the_item():
    item = "STDF 기반 고장분석(FA) 자동화 과제를 추진하려 한다"
    parsed = json.loads(td_fake_llm.assign(f"지시\n\n항목:\n{item}"))
    assert parsed["quote"] in item
    assert parsed["category"] in {n for n, _ in td_fake_llm.CATEGORIES}


# ─────────────── 갤러리 (사용자 피드백: 5개 파일 흩어진 게 별로다) ───────────────

def test_gallery_embeds_all_five_views_intact():
    """다섯 화면을 이어붙이지 않고 iframe으로 격리한다 — 원문 그대로 이어붙이면
    top-level const 재선언·id 충돌로 깨진다는 게 이 화면의 존재 이유다."""
    cards = [_card(1, "A"), _card(2, "B")]
    payload = td_gallery.build_payload(cards, [], _agg(["A", "B"]), [])
    assert {v["id"] for v in payload["views"]} == {
        "constellation", "heatmap", "questions", "onepager", "consensus"}
    # 각 화면 렌더가 자기 자신의 제목/서명을 그대로 담고 있어야 재사용이 성립한다
    assert "성좌 지도" in payload["html"]["constellation"]
    assert "__PAYLOAD__" not in payload["html"]["constellation"]  # 내부 렌더는 이미 치환 완료


def test_gallery_shell_declares_no_view_globals():
    """다섯 화면 각각이 top-level `const D`/`const DATA`를 쓰므로, 셸 자신의 스크립트가
    같은 이름을 선언하면 원문 그대로 이어붙인 것과 같은 충돌이 재현된다. 셸은 GALLERY 하나만
    선언해야 한다 — 화면 본문은 iframe.srcdoc으로만 들어가고 셸 스코프에 섞이지 않는다."""
    assert "const D " not in td_gallery._TEMPLATE and "const DATA" not in td_gallery._TEMPLATE
    assert "const GALLERY" in td_gallery._TEMPLATE


def test_gallery_write_renders_and_guards(tmp_path):
    out = td_gallery.write([_card(1, "A")], [], _agg(["A"]), [], out_path=tmp_path / "g.html")
    html = out.read_text(encoding="utf-8")
    assert "__PAYLOAD__" not in html
    assert "task-discovery 갤러리" in html
    with pytest.raises(ValueError):
        td_gallery.write([_card(1, "A")], [], _agg(["A"]), [],
                         out_path=tmp_path / "dist" / "g.html")
