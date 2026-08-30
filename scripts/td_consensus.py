"""합의의 무게 — 사람의 결정이 지도에 새겨진다 (#023, #024).

지금 저장소의 흐름은 전부 한 방향이다. 파이프라인이 산출물을 만들고 화면이 보여주는 데서
끝나고, 워크숍에서 사람이 정한 것을 **입력으로 되받는** 경로가 하나도 없다.
CONTEXT.md는 "전략은 사람이 채운다"고 말하는데, 사람이 채운 것을 받아 적는 산출물이 없었다.

이 모듈이 그 고리를 닫는다:
  #023 — 투표 결과를 성좌 지도의 별 속성으로. **크기는 데이터(확산도), 고리는 사람(결정).**
         둘이 시각적으로 구별돼야 관찰과 합의가 안 섞인다.
  #024 — 같은 투표에서 "고른 것 · 미룬 것 · 이견" 세 단짜리 기록 문서.
         **이견을 지우지 않는다** — 합의를 연출하는 문서가 아니라 그날의 기록이므로.

투표 파일이 없으면 지도는 관찰만 있는 상태로 정상 렌더된다(워크숍 전 상태).

usage: python3 scripts/td_consensus.py [데이터디렉터리] [출력경로] [--votes 경로]
"""
import json
import sys
from pathlib import Path

import td_cards
import td_constellation
import td_render_common
from td_common import load_json

ROOT = Path(__file__).parent.parent

# 투표 결과 → 세 갈래. workshop_server가 남기는 형태를 그대로 먹는다.
PICKED, DEFERRED, DISPUTED = "고른 것", "미룬 것", "이견"


def classify(vote, *, dispute_ratio=0.34):
    """한 카드의 투표를 세 갈래로. 찬반이 갈리면 다수결로 뭉개지 않고 이견으로 남긴다 —
    그게 이 산출물의 존재 이유다."""
    up, down = vote.get("up", 0), vote.get("down", 0)
    total = up + down
    if total == 0:
        return DEFERRED
    minority = min(up, down) / total
    if minority >= dispute_ratio:
        return DISPUTED
    return PICKED if up > down else DEFERRED


def build_payload(cards, categories, agg, votes, sources=None, *, anonymize=False):
    """성좌 페이로드에 합의 속성을 얹는다. 투표가 비면 consensus는 전부 None으로 남는다."""
    payload = td_constellation.build_payload(cards, categories, agg, sources,
                                             anonymize=anonymize)
    by_card = {v["card_id"]: v for v in votes}
    counts = {PICKED: 0, DEFERRED: 0, DISPUTED: 0}
    record = {PICKED: [], DEFERRED: [], DISPUTED: []}

    for star in payload["stars"]:
        vote = by_card.get(star["id"])
        if not vote:
            continue
        verdict = classify(vote)
        star["consensus"] = verdict
        star["votes"] = {"up": vote.get("up", 0), "down": vote.get("down", 0)}
        counts[verdict] += 1
        record[verdict].append({"id": star["id"], "text": star["text"], "cat": star["cat"],
                                "up": vote.get("up", 0), "down": vote.get("down", 0)})

    payload["consensus"] = {
        "voted": sum(counts.values()), "counts": counts,
        "record": record,
        "session": {"date": None, "voters": None},
    }
    return payload


def write(cards, categories, agg, votes, sources=None, *, out_path, anonymize=False):
    payload = build_payload(cards, categories, agg, votes, sources, anonymize=anonymize)
    return td_render_common.write_html(td_render_common.render(_TEMPLATE, payload), out_path)


def main(*argv):
    args = list(argv)
    votes_path = None
    if "--votes" in args:
        i = args.index("--votes"); votes_path = args[i + 1]; del args[i:i + 2]
    d, out, anonymize = td_render_common.parse_args(args, "consensus.html")
    votes_path = Path(votes_path) if votes_path else d / "votes.json"
    votes = load_json(votes_path) if Path(votes_path).exists() else []

    cards = td_cards.build(d / "assignments.json", d / "extracted.json", anonymize=anonymize)
    taxonomy = load_json(d / "taxonomy.json") if (d / "taxonomy.json").exists() else []
    src_path = next((p for p in (d / "sources.json", d.parent / "persons.json") if p.exists()), None)
    sources = load_json(src_path) if (src_path and not anonymize) else None
    res = write(cards, taxonomy, load_json(d / "aggregates.json"), votes, sources,
                out_path=out, anonymize=anonymize)
    print(f"합의의 무게 → {res} (투표 {len(votes)}건)", file=sys.stderr)


_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>합의의 무게 — 우리가 고른 것</title>
<style>
  :root { --bg:#070912; --ink:#e8ecf8; --dim:#5b6480; --line:#1b2136;
          --pick:#4ade80; --defer:#5b6480; --dispute:#f0c674; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); overflow:hidden;
         font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif; }
  canvas { display:block; }
  .panel { position:fixed; background:rgba(10,13,25,.94); border:1px solid var(--line);
           border-radius:8px; backdrop-filter:blur(8px); }
  #hud { top:16px; left:16px; padding:14px 16px; max-width:330px; }
  h1 { margin:0 0 4px; font-size:15px; font-weight:600; }
  .sub { font-size:11px; color:var(--dim); line-height:1.65; }
  .modes { margin-top:12px; display:flex; gap:6px; }
  button { background:#141a2e; color:var(--ink); border:1px solid var(--line); border-radius:5px;
           padding:6px 10px; font-size:11px; cursor:pointer; font-family:inherit; }
  button.on { background:#e8ecf8; color:#12151f; border-color:#e8ecf8; font-weight:600; }
  #legend { bottom:16px; left:16px; padding:12px 14px; font-size:11px; color:var(--dim); line-height:1.95; }
  .sw { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:7px; vertical-align:-1px; }
  .ring { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:7px;
          vertical-align:-1px; border:2px solid var(--pick); }
  #record { top:16px; right:16px; width:400px; max-height:calc(100vh - 32px); overflow-y:auto;
            padding:18px 20px; }
  .lbl { font-size:9px; letter-spacing:.14em; text-transform:uppercase; color:var(--dim); margin:16px 0 7px; }
  .lbl:first-child { margin-top:0; }
  .item { font-size:12px; line-height:1.6; padding:7px 0; border-bottom:1px solid #131829; }
  .item .cat { color:var(--dim); font-size:10.5px; }
  .tally { float:right; font-family:ui-monospace,monospace; font-size:10.5px; color:var(--dim); }
  .head-pick { color:var(--pick); } .head-defer { color:var(--defer); }
  .head-dispute { color:var(--dispute); }
  .empty { font-size:11.5px; color:var(--dim); font-style:italic; padding:6px 0; }
  .banner { margin-top:11px; font-size:11px; line-height:1.6; padding:8px 10px; border-radius:5px;
            background:rgba(240,198,116,.1); border:1px solid rgba(240,198,116,.3); color:#f5d99a; }
</style>
</head>
<body>
<canvas id="sky"></canvas>

<div id="hud" class="panel">
  <h1>합의의 무게</h1>
  <div class="sub">크기는 <b>데이터</b>(확산도). 고리는 <b>사람</b>(워크숍이 고른 것).<br>
    관찰과 결정이 한 그림에 있되 섞이지 않는다.</div>
  <div class="modes">
    <button id="m-after" class="on">워크숍 후</button>
    <button id="m-before">워크숍 전</button>
  </div>
  <div class="banner" id="banner"></div>
</div>

<div id="legend" class="panel">
  <div><span class="sw" style="background:#e8ecf8"></span>과제 — 크기 = 확산도(데이터)</div>
  <div><span class="ring"></span>워크숍이 <b>고른 것</b> (사람)</div>
  <div><span class="ring" style="border-color:#f0c674"></span>이견으로 남은 것</div>
  <div><span class="sw" style="background:#2a3147"></span>미룬 것</div>
</div>

<div id="record" class="panel"></div>

<script>
const D = __PAYLOAD__;
const C = D.consensus;
const cv = document.getElementById("sky"), cx = cv.getContext("2d");
let W, H, mode = "after";
const catByName = Object.fromEntries(D.cats.map(c => [c.name, c]));
const RING = { "고른 것": "#4ade80", "이견": "#f0c674" };

function resize() {
  W = cv.width = innerWidth * devicePixelRatio; H = cv.height = innerHeight * devicePixelRatio;
  cv.style.width = innerWidth + "px"; cv.style.height = innerHeight + "px"; draw();
}
addEventListener("resize", resize);
function radius(s) {
  const c = catByName[s.cat] || {};
  return 1.6 + (c.pjt_spread || 1) * 0.9 + Math.min(c.cl_spread || 1, 3) * 0.35;
}
const P = p => [W / 2 + p.x * devicePixelRatio * 0.98, H / 2 + p.y * devicePixelRatio * 0.98];

function draw() {
  cx.fillStyle = "#070912"; cx.fillRect(0, 0, W, H);
  for (const c of D.cats) {
    const [ax, ay] = P(c);
    cx.strokeStyle = "rgba(70,82,120,.22)"; cx.lineWidth = devicePixelRatio * 0.55;
    for (const s of D.stars) {
      if (s.cat !== c.name) continue;
      const [sx, sy] = P(s);
      cx.beginPath(); cx.moveTo(ax, ay); cx.lineTo(sx, sy); cx.stroke();
    }
  }
  for (const s of D.stars) {
    const [x, y] = P(s), r = radius(s) * devicePixelRatio;
    const verdict = mode === "after" ? s.consensus : null;
    cx.fillStyle = verdict === "미룬 것" ? "#2a3147" : "#e8ecf8";
    cx.beginPath(); cx.arc(x, y, r, 0, 7); cx.fill();
    if (RING[verdict]) {                       // 고리 = 사람이 정한 것
      cx.strokeStyle = RING[verdict]; cx.lineWidth = devicePixelRatio * 1.6;
      cx.shadowColor = RING[verdict]; cx.shadowBlur = 7 * devicePixelRatio;
      cx.beginPath(); cx.arc(x, y, r + 4 * devicePixelRatio, 0, 7); cx.stroke();
      cx.shadowBlur = 0;
    }
  }
  cx.textAlign = "center";
  for (const c of D.cats) {
    const [x, y] = P(c);
    cx.fillStyle = "#8b95b4"; cx.font = `${11 * devicePixelRatio}px -apple-system, sans-serif`;
    cx.fillText(c.name, x, y - 146 * devicePixelRatio);
  }
}

function esc(t) { return (t || "").replace(/[&<>]/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m])); }
function section(title, cls, items, empty) {
  return `<div class="lbl ${cls}">${title} · ${items.length}건</div>` + (items.length
    ? items.map(i => `<div class="item"><span class="tally">${i.up}↑ ${i.down}↓</span>
        ${esc(i.text)}<br><span class="cat">${esc(i.cat)}</span></div>`).join("")
    : `<div class="empty">${empty}</div>`);
}
document.getElementById("record").innerHTML =
  `<div class="lbl">결정 기록 — 그날 무엇이 정해졌나</div>
   <div style="font-size:11.5px;color:#8b95b4;line-height:1.7;margin-bottom:4px">
     투표 ${C.voted}건 / 과제 ${D.totals.stars}개. 이견은 다수결로 지우지 않고 그대로 남긴다.</div>` +
  section("고른 것", "head-pick", C.record["고른 것"], "아직 고른 것이 없다.") +
  section("이견으로 남은 것", "head-dispute", C.record["이견"], "이견 없음.") +
  section("미룬 것", "head-defer", C.record["미룬 것"], "미룬 것 없음.");

document.getElementById("banner").innerHTML = C.voted
  ? `워크숍 투표 <b>${C.voted}건</b>이 지도에 실렸다. 고리가 있는 별은 데이터가 아니라
     <b>사람이 고른 것</b>이다.`
  : `아직 투표가 없다 — 관찰만 있는 상태다. 투표 파일을 넣으면 고리가 생긴다.`;

function setMode(m) {
  mode = m;
  document.getElementById("m-after").classList.toggle("on", m === "after");
  document.getElementById("m-before").classList.toggle("on", m === "before");
  draw();
}
document.getElementById("m-after").onclick = () => setMode("after");
document.getElementById("m-before").onclick = () => setMode("before");
addEventListener("hashchange", applyHash);
function applyHash() {
  const h = new URLSearchParams(location.hash.slice(1));
  if (h.get("mode")) setMode(h.get("mode"));
}
resize(); applyHash();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main(*sys.argv[1:])
