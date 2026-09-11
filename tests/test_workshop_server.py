import json
import urllib.error
import urllib.request

import pytest

import workshop_server as ws


def _card(cat, axis, text, draft="중기"):
    # 코드가 카드를 식별하는 키는 id다(text는 유일하지 않다). 읽기 쉽도록 같은 값을 준다.
    return {"id": text, "person_id": 1, "name": "홍길동", "pjt": "양산기술", "cl_level": "CL3",
            "category": cat, "axis": axis, "text": text, "quote": "근거",
            "horizon": None, "draft_band": draft}


# ── 집계 규칙 ─────────────────────────────────────────────────────────

def test_majority_wins():
    votes = {"t": {"단기": 3, "장기": 1}}
    assert ws.tally([_card("A", "future_task", "t")], votes)["placed"]["t"] == "단기"


def test_tie_keeps_the_draft():
    """동률이면 사람이 정하지 못한 것이다 — 데이터가 준 초안을 그대로 둔다."""
    votes = {"t": {"단기": 2, "장기": 2}}
    assert ws.tally([_card("A", "future_task", "t", draft="중기")], votes)["placed"]["t"] == "중기"


def test_no_votes_keeps_the_draft():
    out = ws.tally([_card("A", "future_task", "t", draft="장기")], {})
    assert out["placed"]["t"] == "장기"
    assert out["disputed"] == []          # 아무도 안 봤으면 이견이 아니다


def test_below_majority_is_disputed():
    """최빈값이 과반에 못 미치면 합의가 아니다 — 워크숍 아젠다로 올린다.
    단독 1위이므로 잠정 위치는 그쪽으로 정한다(동률과는 다른 경우)."""
    votes = {"t": {"단기": 2, "중기": 1, "장기": 1}}
    out = ws.tally([_card("A", "future_task", "t")], votes)
    assert out["disputed"] == ["t"]
    assert out["placed"]["t"] == "단기"


def test_clear_majority_is_not_disputed():
    votes = {"t": {"단기": 3, "장기": 1}}
    assert ws.tally([_card("A", "future_task", "t")], votes)["disputed"] == []


def test_exactly_half_is_disputed():
    """과반은 절반 초과다 — 4표 중 2표는 합의로 치지 않는다."""
    votes = {"t": {"단기": 2, "장기": 2}}
    assert ws.tally([_card("A", "future_task", "t")], votes)["disputed"] == ["t"]


def test_progress_counts_cards_with_any_vote():
    cards = [_card("A", "future_task", "a"), _card("A", "future_task", "b")]
    out = ws.tally(cards, {"a": {"단기": 1}})
    assert out["progress"] == {"voted": 1, "total": 2}


def test_tally_carries_category_bands_and_violations():
    cards = [_card("A", "future_task", "t", draft="단기"),
             _card("A", "capability_gap", "g", draft="단기")]
    out = ws.tally(cards, {"g": {"장기": 3}})
    assert out["categories"]["A"] in ("단기", "중기", "장기")
    assert out["violations"] == ["g"]      # 역량이 첫 과제보다 뒤로 갔다


# ── 투표 기록 ─────────────────────────────────────────────────────────

def test_record_vote_is_per_voter_not_cumulative():
    """같은 사람이 다시 투표하면 앞의 표를 바꾼다 — 논의 중 생각이 바뀔 수 있다."""
    votes, by_voter = {}, {}
    ws.record(votes, by_voter, voter="v1", id="t", band="단기")
    ws.record(votes, by_voter, voter="v1", id="t", band="장기")
    assert votes["t"] == {"장기": 1}


def test_record_keeps_different_voters_separate():
    votes, by_voter = {}, {}
    ws.record(votes, by_voter, voter="v1", id="t", band="단기")
    ws.record(votes, by_voter, voter="v2", id="t", band="단기")
    assert votes["t"] == {"단기": 2}


def test_record_rejects_unknown_band():
    with pytest.raises(ValueError):
        ws.record({}, {}, voter="v1", id="t", band="언젠가")


# ── 영속화 ────────────────────────────────────────────────────────────

def test_state_round_trips_through_a_file(tmp_path):
    """몇 시간짜리 세션이다 — 서버가 죽어도 재시작하면 이어져야 한다."""
    path = tmp_path / "workshop-votes.json"
    votes, by_voter = {}, {}
    ws.record(votes, by_voter, voter="v1", id="t", band="단기")
    ws.save(path, votes, by_voter)

    votes2, by_voter2 = ws.load(path)
    assert votes2 == votes and by_voter2 == by_voter


def test_load_of_missing_file_starts_empty(tmp_path):
    assert ws.load(tmp_path / "none.json") == ({}, {})


def test_save_refuses_dist_path(tmp_path):
    with pytest.raises(ValueError):
        ws.save(tmp_path / "dist" / "votes.json", {}, {})


# ── HTTP (스모크) ─────────────────────────────────────────────────────

@pytest.fixture
def server(tmp_path):
    cards = [_card("A", "future_task", "t"), _card("A", "future_task", "u")]
    page = "<!doctype html><html><body>ok</body></html>"
    srv = ws.serve(cards, page, tmp_path / "votes.json", port=0)
    yield srv, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read())


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def test_vote_shows_up_in_state(server):
    srv, base = server
    _post(base + "/vote", {"voter": "v1", "id": "t", "band": "단기"})
    state = _get(base + "/state")
    assert state["placed"]["t"] == "단기"
    assert state["progress"] == {"voted": 1, "total": 2}


def test_vote_is_written_through_to_the_file(server, tmp_path):
    srv, base = server
    _post(base + "/vote", {"voter": "v1", "id": "t", "band": "장기"})
    votes, _ = ws.load(tmp_path / "votes.json")
    assert votes == {"t": {"장기": 1}}


def test_page_is_served_at_root(server):
    srv, base = server
    with urllib.request.urlopen(base + "/", timeout=5) as r:
        assert b"ok" in r.read()


def test_bad_vote_is_rejected_without_killing_the_server(server):
    srv, base = server
    body = json.dumps({"voter": "v", "id": "t", "band": "언젠가"}).encode()
    req = urllib.request.Request(base + "/vote", data=body,
                                 headers={"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=5)
    assert e.value.code == 400
    assert _get(base + "/state")["progress"]["voted"] == 0


def test_two_cards_with_the_same_text_get_separate_votes():
    """실데이터에는 서로 다른 사람이 같은 문장을 쓴 카드가 있다 — 표가 섞이면 안 된다."""
    a = {**_card("A", "future_task", "같은말"), "id": "1:future_task:0"}
    b = {**_card("A", "future_task", "같은말"), "id": "2:future_task:0"}
    out = ws.tally([a, b], {"1:future_task:0": {"장기": 3}})
    assert out["placed"]["1:future_task:0"] == "장기"
    assert out["placed"]["2:future_task:0"] == "중기"        # 초안 그대로
    assert out["progress"] == {"voted": 1, "total": 2}
