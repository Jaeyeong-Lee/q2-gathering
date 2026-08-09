"""워크숍 투표 서버 (S5-3, #45).

참석자가 각자 PC에서 카드를 시간 구간에 배치하고, 그 표가 한 곳에 모인다.
엔드포인트 셋뿐이다 — `GET /state` · `POST /vote` · 정적 페이지.

**로직은 여기 있고 HTTP는 껍데기다.** tally/record/save/load는 순수 함수라 서버 없이
테스트된다. HTTP 계층은 스모크만 건다.

**이견 카드가 이 서버의 존재 이유다.** 최빈값이 과반에 못 미치는 카드만 뽑아내면 800장이
논의할 스무 장으로 줄어든다. 합의된 것은 자동으로 통과시키고 갈린 것만 사람 시간을 쓴다 —
이 장치가 없으면 그 규모는 물리적으로 소화 불가능하다.

DB를 쓰지 않는다. 몇 시간짜리 1회성 세션에 참석자 수십 명 규모라, 투표가 들어올 때마다
JSON으로 write-through 하면 서버가 죽어도 재시작 시 복구된다. 이 저장소의 기존 철학
(순차 루프 + 재시도 + 파일 영속화)과 같다. 새 의존성도 없다 — 표준 라이브러리뿐.

인증은 없다. 사내 폐쇄망에서 진행자가 URL을 공유하는 방식이다.
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import td_cards
import td_roadmap
from pipeline_log import OUT_DIR, get_logger
from td_common import load_json

log = get_logger("workshop_server")

BANDS = td_roadmap.BANDS


def tally(cards, votes):
    """표를 세어 확정 위치·이견·집계를 낸다. 순수 함수.

    최빈값이 확정 위치이고, **동률이면 초안을 유지한다** — 사람이 정하지 못한 것을
    임의로 한쪽으로 밀지 않는다. 최빈값이 과반(절반 초과)에 못 미치면 합의가 아니므로
    이견 카드로 분류한다. 표가 하나도 없는 카드는 아무도 안 본 것이지 갈린 게 아니다.
    """
    placed, disputed, voted = {}, [], 0
    for c in cards:
        counts = votes.get(c["id"]) or {}
        total = sum(counts.values())
        if not total:
            placed[c["id"]] = c["draft_band"]
            continue
        voted += 1
        top = max(counts.values())
        winners = [b for b in BANDS if counts.get(b, 0) == top]
        placed[c["id"]] = c["draft_band"] if len(winners) > 1 else winners[0]
        if top * 2 <= total:                      # 과반 = 절반 초과
            disputed.append(c["id"])

    return {"placed": placed,
            "disputed": disputed,
            "categories": td_roadmap.category_bands(cards, placed),
            "violations": [c["id"] for c in td_roadmap.violations(cards, placed)],
            "moved": [m["id"] for m in td_roadmap.moved(cards, placed)],
            "progress": {"voted": voted, "total": len(cards)}}


def record(votes, by_voter, *, voter, id, band):
    """표 하나를 기록. **사람당 한 표**라 같은 사람이 다시 투표하면 앞의 표를 바꾼다 —
    논의 중에 생각이 바뀌는 게 이 워크숍의 목적이다.

    카드는 id로 식별한다. text는 유일하지 않아(서로 다른 사람이 같은 문장을 쓸 수 있다)
    키로 쓰면 한 표가 여러 카드에 먹힌다.
    """
    if band not in BANDS:
        raise ValueError(f"모르는 구간 (허용: {', '.join(BANDS)})")
    prev = by_voter.get(voter, {}).get(id)
    counts = votes.setdefault(id, {})
    if prev == band:
        return
    if prev:
        counts[prev] = max(0, counts.get(prev, 0) - 1)
        if not counts[prev]:
            del counts[prev]
    counts[band] = counts.get(band, 0) + 1
    by_voter.setdefault(voter, {})[id] = band


def _reject_public_path(path):
    if "dist" in Path(path).resolve().parts:
        raise ValueError("dist/ 아래에는 쓸 수 없다 — 배포 추적 경로다. TD_OUT_DIR을 써라")


def save(path, votes, by_voter):
    _reject_public_path(path)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"votes": votes, "by_voter": by_voter},
                               ensure_ascii=False, indent=1), encoding="utf-8")


def load(path):
    path = Path(path)
    if not path.exists():
        return {}, {}
    d = json.loads(path.read_text(encoding="utf-8"))
    return d.get("votes", {}), d.get("by_voter", {})


def serve(cards, page, votes_path, *, port=8000):
    """서버를 띄우고 반환한다(백그라운드 스레드). 호출자가 shutdown()을 부른다.

    상태는 프로세스 메모리에 들고, 투표마다 파일로 write-through 한다. 락 하나로 전체를
    감싼다 — 참석자 수십 명에 투표가 초당 몇 건이라 경합이 없다.
    """
    votes, by_voter = load(votes_path)
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path.startswith("/state"):
                with lock:
                    self._send(200, tally(cards, votes))
            elif self.path in ("/", "/index.html"):
                self._send(200, page.encode("utf-8"), "text/html")
            else:
                self._send(404, {"error": "없음"})

        def do_POST(self):
            if not self.path.startswith("/vote"):
                self._send(404, {"error": "없음"})
                return
            try:
                n = int(self.headers.get("Content-Length") or 0)
                p = json.loads(self.rfile.read(n) or b"{}")
                with lock:
                    record(votes, by_voter, voter=p["voter"], id=p["id"], band=p["band"])
                    save(votes_path, votes, by_voter)
                    self._send(200, tally(cards, votes))
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                # 카드 본문은 응답에 싣지 않는다 — 실명·인용이 들어 있다.
                self._send(400, {"error": str(e)})

        def log_message(self, *args):
            pass      # 기본 로거는 요청 경로를 stderr에 찍는다 — 조용히 둔다

    srv = ThreadingHTTPServer(("", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _page(d, anonymize=False):
    """#44의 배치 화면을 그대로 쓰고, 상태 소스만 폴링으로 바꾼다."""
    cards = td_cards.build(d / "assignments.json", d / "extracted.json", anonymize=anonymize)
    aggregates = load_json(d / "aggregates.json")
    taxo_path = d / "taxonomy.json"
    taxo = {c["name"]: c for c in load_json(taxo_path)} if taxo_path.exists() else {}
    categories = [{**c, "definition": taxo.get(c["name"], {}).get("definition", ""),
                   "relations": taxo.get(c["name"], {}).get("relations", [])}
                  for c in aggregates["categories"]]
    payload = td_roadmap.build_payload(cards, categories)
    return td_roadmap.render_html(payload, live=True), payload["cards"]


def main(*argv):
    """워크숍 투표 서버.

      workshop_server.py [데이터디렉터리] [포트] [--anonymize]
    """
    args = [a for a in argv if a != "--anonymize"]
    anonymize = "--anonymize" in argv
    d = Path(args[0]) if len(args) > 0 else OUT_DIR / "task_discovery"
    port = int(args[1]) if len(args) > 1 else 8000

    page, cards = _page(d, anonymize=anonymize)
    votes_path = d / "workshop-votes.json"
    srv = serve(cards, page, votes_path, port=port)
    # 카테고리명·실명은 찍지 않는다 — 건수만.
    log.info(f"워크숍 서버 :{srv.server_address[1]} · 카드 {len(cards)}장 · 표 → {votes_path}")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main(*sys.argv[1:])
