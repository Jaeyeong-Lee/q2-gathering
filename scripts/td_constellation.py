"""성좌 지도 — 별 하나가 과제(facet) 하나 (#012, #013, #014, #015).

기존 은하수(archive/)는 별이 **사람**이고 색이 팀이라 조직도를 반복한다. 여기서는 별이
**과제**고 묶음이 카테고리다 — 팀을 가로질러 같은 말을 한 과제들이 한 성좌에 모인다.

한 화면에 네 티켓이 들어간다. 좌표계를 한 번 만들면 나머지는 같은 좌표 위의 모드/필터라
화면을 넷으로 나눌 이유가 없다:
  #012 앞면 — 성좌(카테고리별 별자리), 크기=확산도
  #013 뒷면 — 빈 하늘(희박한 영역 부각). 해석층이라 화면에 그렇게 적는다
  #014 렌즈 — AX를 **언급한** 별만 점등 (판정 아님)
  #015 계보 — 별 클릭 시 원문→인용→과제→카테고리 사슬

**레이아웃은 결정적이다.** UMAP·t-SNE는 의존성이 늘고 실행마다 결과가 흔들려 "왜 저 별이
저기 있냐"에 답할 수 없다. 카테고리 앵커를 원주에 고정 배치하고, 카테고리 안에서는 카드
내용의 해시로 위치를 정한다 — 같은 산출물이면 항상 같은 그림이 나온다.

usage: python3 scripts/td_constellation.py [데이터디렉터리] [출력경로] [--anonymize]
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import td_cards
import td_render_common
from td_common import load_json

ROOT = Path(__file__).parent.parent

# 확산도가 이 값 이하인 카테고리를 "희박"으로 본다(td_aggregate.WEAK와 같은 기준).
WEAK = 2


def _unit(text):
    """카드 내용 → 단위원 안의 결정적 좌표. hashlib을 쓴다 — 파이썬 hash()는 실행마다
    솔트가 달라져 '같은 입력이면 같은 그림'이 깨진다."""
    h = hashlib.md5(text.encode("utf-8")).digest()
    angle = int.from_bytes(h[:4], "big") / 2**32 * 2 * math.pi
    radius = math.sqrt(int.from_bytes(h[4:8], "big") / 2**32)   # sqrt로 면적 균일
    return math.cos(angle) * radius, math.sin(angle) * radius


def _anchors(names, *, spread=310):
    """카테고리 앵커를 원주에 균등 배치. 이름 정렬 순서라 카테고리가 늘어도 자리가 안 흔들린다."""
    out = {}
    for i, name in enumerate(sorted(names)):
        a = 2 * math.pi * i / max(len(names), 1) - math.pi / 2
        out[name] = (math.cos(a) * spread, math.sin(a) * spread)
    return out


def build_payload(cards, categories, agg, sources=None, *, anonymize=False):
    """화면이 먹는 페이로드. 파일을 읽지 않는 순수 함수."""
    by_name = {c["name"]: c for c in categories}
    stats = {c["name"]: c for c in agg.get("categories", [])}
    names = sorted({c["category"] for c in cards} | set(by_name))
    anchors = _anchors(names)

    # 원문은 계보 뷰(#015)에서만 쓴다. 사람당 한 벌만 실어 페이로드 중복을 막는다.
    src_text = {}
    for doc in (sources or []):
        pid = doc.get("id", doc.get("person_id"))
        if pid is not None:
            src_text[str(pid)] = doc.get("text", "")

    stars = []
    for card in cards:
        cat = card["category"]
        ax, ay = anchors.get(cat, (0.0, 0.0))
        dx, dy = _unit(card["id"] + card["text"])
        stars.append({
            "id": card["id"], "cat": cat, "axis": card["axis"],
            "text": card["text"], "quote": card["quote"],
            "person": card["name"], "pid": str(card["person_id"]),
            "pjt": card["pjt"], "cl": card["cl_level"],
            "horizon": card["horizon"], "ax": card["ax_mentioned"],
            "x": round(ax + dx * 118, 1), "y": round(ay + dy * 118, 1),
            # #023이 채울 자리 — 데이터에서 온 것(크기)과 사람이 정한 것(고리)을 구별한다.
            "consensus": None,
        })

    cats = []
    for name in names:
        st = stats.get(name, {})
        people = st.get("people", 0)
        cats.append({
            "name": name,
            "definition": by_name.get(name, {}).get("definition", ""),
            "x": round(anchors[name][0], 1), "y": round(anchors[name][1], 1),
            "people": people,
            "pjt_spread": st.get("pjt_spread", 0), "cl_spread": st.get("cl_spread", 0),
            "have": st.get("have", 0), "gap": st.get("gap", 0),
            "readiness": st.get("readiness", ""),
            "stars": sum(1 for s in stars if s["cat"] == name),
            # 빈 하늘(#013): 한 조직에서만 나왔거나 보유 없이 갭만 있는 영역
            "sparse": st.get("pjt_spread", 0) <= 1 or st.get("readiness") == "갭만 있음",
        })

    return {
        "stars": stars, "cats": cats, "sources": src_text,
        "anonymize": anonymize,
        "totals": {"stars": len(stars), "cats": len(cats),
                   "ax": sum(1 for s in stars if s["ax"]),
                   "sparse": sum(1 for c in cats if c["sparse"])},
    }


def write(cards, categories, agg, sources=None, *, out_path, anonymize=False):
    payload = build_payload(cards, categories, agg, sources, anonymize=anonymize)
    return td_render_common.write_html(td_render_common.render(_TEMPLATE, payload), out_path)


def main(*argv):
    d, out, anonymize = td_render_common.parse_args(argv, "constellation.html")
    cards = td_cards.build(d / "assignments.json", d / "extracted.json", anonymize=anonymize)
    taxonomy = load_json(d / "taxonomy.json") if (d / "taxonomy.json").exists() else []
    agg = load_json(d / "aggregates.json")
    src_path = next((p for p in (d / "sources.json", d.parent / "persons.json") if p.exists()), None)
    sources = load_json(src_path) if (src_path and not anonymize) else None
    res = write(cards, taxonomy, agg, sources, out_path=out, anonymize=anonymize)
    # 카테고리명·실명은 찍지 않는다 — 건수만.
    print(f"성좌 지도 → {res} (별 {len(cards)}개 · {res.stat().st_size // 1024}kb)",
          file=sys.stderr)


_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>성좌 지도 — 무엇을 말했나</title>
<style>
  :root { --bg:#070912; --ink:#e8ecf8; --dim:#5b6480; --line:#1b2136; --gold:#f0c674; --teal:#5ad2c4; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); overflow:hidden;
         font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif; }
  canvas { display:block; cursor:crosshair; }
  .panel { position:fixed; background:rgba(10,13,25,.93); border:1px solid var(--line);
           border-radius:8px; backdrop-filter:blur(8px); }
  #hud { top:16px; left:16px; padding:14px 16px; max-width:340px; }
  h1 { margin:0 0 4px; font-size:15px; letter-spacing:.02em; font-weight:600; }
  .sub { font-size:11px; color:var(--dim); line-height:1.6; }
  .modes { margin-top:12px; display:flex; gap:6px; flex-wrap:wrap; }
  button { background:#141a2e; color:var(--ink); border:1px solid var(--line); border-radius:5px;
           padding:6px 10px; font-size:11px; cursor:pointer; font-family:inherit; }
  button.on { background:var(--gold); color:#12151f; border-color:var(--gold); font-weight:600; }
  button:hover:not(.on) { border-color:var(--dim); }
  #note { margin-top:10px; font-size:11px; line-height:1.6; padding:8px 10px; border-radius:5px;
          display:none; }
  #note.show { display:block; }
  .warn { background:rgba(240,198,116,.1); border:1px solid rgba(240,198,116,.35); color:#f5d99a; }
  #legend { bottom:16px; left:16px; padding:12px 14px; font-size:11px; color:var(--dim); line-height:1.9; }
  .sw { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:6px; vertical-align:-1px; }
  #detail { top:16px; right:16px; width:390px; max-height:calc(100vh - 32px); overflow-y:auto;
            padding:16px 18px; display:none; }
  #detail.show { display:block; }
  .lbl { font-size:9px; letter-spacing:.14em; text-transform:uppercase; color:var(--dim);
         margin:14px 0 5px; }
  .lbl:first-child { margin-top:0; }
  .chain { border-left:2px solid var(--line); padding-left:12px; margin-left:3px; }
  .chain .step { margin-bottom:12px; font-size:12.5px; line-height:1.65; }
  .src { font-size:11.5px; line-height:1.75; color:#aab3cc; max-height:190px; overflow-y:auto;
         white-space:pre-wrap; background:#0b0f1c; padding:10px; border-radius:5px; }
  mark { background:rgba(240,198,116,.28); color:#fbe6b4; border-radius:2px; padding:0 2px; }
  .tag { display:inline-block; font-size:10px; padding:2px 7px; border-radius:99px;
         border:1px solid var(--line); color:var(--dim); margin:0 4px 4px 0; }
  .tag.ax { border-color:var(--teal); color:var(--teal); }
  .close { float:right; background:none; border:none; color:var(--dim); font-size:16px; padding:0 4px; }
  #tip { position:fixed; pointer-events:none; background:rgba(8,11,20,.95); border:1px solid var(--line);
         padding:7px 10px; border-radius:5px; font-size:11.5px; display:none; max-width:290px; line-height:1.5; }
</style>
</head>
<body>
<canvas id="sky"></canvas>

<div id="hud" class="panel">
  <h1>성좌 지도</h1>
  <div class="sub">별 하나 = 과제 하나. 같은 카테고리가 한 별자리.<br>
    크기 = 확산도(몇 조직이 말했나) · 위치는 결정적이라 매번 같다.</div>
  <div class="modes">
    <button id="m-front" class="on">성좌</button>
    <button id="m-empty">빈 하늘</button>
    <button id="m-ax">AX 렌즈</button>
  </div>
  <div id="note" class="warn"></div>
</div>

<div id="legend" class="panel">
  <div><span class="sw" style="background:#e8ecf8"></span>과제 (별)</div>
  <div><span class="sw" style="background:#5ad2c4"></span>AX를 <b>언급한</b> 과제 — 판정 아님</div>
  <div><span class="sw" style="background:#f0c674"></span>희박한 영역 (한 조직만 / 갭만 있음)</div>
  <div style="margin-top:6px;color:#39405a">별을 클릭하면 원문까지의 계보가 열린다</div>
</div>

<div id="detail" class="panel"></div>
<div id="tip"></div>

<script>
const DATA = __PAYLOAD__;
const cv = document.getElementById("sky"), cx = cv.getContext("2d");
let W, H, mode = "front", sel = null, hover = null;
let view = { x: 0, y: 0, k: 1 };

function resize() {
  W = cv.width = innerWidth * devicePixelRatio;
  H = cv.height = innerHeight * devicePixelRatio;
  cv.style.width = innerWidth + "px"; cv.style.height = innerHeight + "px";
  draw();
}
addEventListener("resize", resize);

// 확산도 → 반지름. 조직 수가 1~3이라 폭이 좁으니 별 개수도 섞어 시각 대비를 준다.
const catByName = Object.fromEntries(DATA.cats.map(c => [c.name, c]));
function radius(s) {
  const c = catByName[s.cat] || {};
  return 1.6 + (c.pjt_spread || 1) * 0.9 + Math.min((c.cl_spread || 1), 3) * 0.35;
}
function toScreen(p) {
  return [W / 2 + (p.x + view.x) * view.k * devicePixelRatio,
          H / 2 + (p.y + view.y) * view.k * devicePixelRatio];
}

function starVisible(s) {
  if (mode === "ax") return s.ax;
  if (mode === "empty") return (catByName[s.cat] || {}).sparse;
  return true;
}

function draw() {
  cx.fillStyle = "#070912"; cx.fillRect(0, 0, W, H);

  // 별자리 선 — 같은 카테고리 별들을 앵커에 잇는다(성좌의 뼈대)
  for (const c of DATA.cats) {
    const dimmed = (mode === "empty" && !c.sparse) || mode === "ax";
    cx.strokeStyle = dimmed ? "rgba(27,33,54,.35)" : "rgba(70,82,120,.30)";
    cx.lineWidth = devicePixelRatio * 0.6;
    const [ax, ay] = toScreen(c);
    for (const s of DATA.stars) {
      if (s.cat !== c.name) continue;
      const [sx, sy] = toScreen(s);
      cx.beginPath(); cx.moveTo(ax, ay); cx.lineTo(sx, sy); cx.stroke();
    }
  }

  // 희박 영역 표시 (빈 하늘)
  if (mode === "empty") {
    for (const c of DATA.cats) {
      if (!c.sparse) continue;
      const [x, y] = toScreen(c);
      cx.strokeStyle = "rgba(240,198,116,.6)"; cx.lineWidth = devicePixelRatio * 1.3;
      cx.setLineDash([6 * devicePixelRatio, 5 * devicePixelRatio]);
      cx.beginPath(); cx.arc(x, y, 135 * view.k * devicePixelRatio, 0, 7); cx.stroke();
      cx.setLineDash([]);
    }
  }

  for (const s of DATA.stars) {
    const [x, y] = toScreen(s);
    const on = starVisible(s), r = radius(s) * view.k * devicePixelRatio;
    if (on && s.ax) { cx.fillStyle = "#5ad2c4"; }
    else if (on && mode === "empty") { cx.fillStyle = "#f0c674"; }
    else if (on) { cx.fillStyle = "#e8ecf8"; }
    else { cx.fillStyle = "rgba(91,100,128,.22)"; }
    if (on && (mode === "ax" || mode === "empty")) {
      cx.shadowColor = cx.fillStyle; cx.shadowBlur = 9 * devicePixelRatio;
    }
    cx.beginPath(); cx.arc(x, y, sel && sel.id === s.id ? r * 2.1 : r, 0, 7); cx.fill();
    cx.shadowBlur = 0;
    if (sel && sel.id === s.id) {
      cx.strokeStyle = "#f0c674"; cx.lineWidth = devicePixelRatio * 1.5;
      cx.beginPath(); cx.arc(x, y, r * 3.4, 0, 7); cx.stroke();
    }
  }

  // 카테고리 이름
  cx.textAlign = "center";
  for (const c of DATA.cats) {
    const [x, y] = toScreen(c);
    const faded = (mode === "empty" && !c.sparse) || (mode === "ax");
    cx.fillStyle = faded ? "#39405a" : (mode === "empty" && c.sparse ? "#f0c674" : "#8b95b4");
    cx.font = `${11.5 * devicePixelRatio}px -apple-system, sans-serif`;
    cx.fillText(c.name, x, y - 148 * view.k * devicePixelRatio);
    cx.fillStyle = "#39405a";
    cx.font = `${9.5 * devicePixelRatio}px ui-monospace, monospace`;
    cx.fillText(`${c.stars}과제 · ${c.people}명 · ${c.pjt_spread}조직`,
                x, y - 134 * view.k * devicePixelRatio);
  }
}

function hit(mx, my) {
  let best = null, bd = 16;
  for (const s of DATA.stars) {
    if (!starVisible(s)) continue;
    const [x, y] = toScreen(s);
    const d = Math.hypot(x / devicePixelRatio - mx, y / devicePixelRatio - my);
    if (d < bd) { bd = d; best = s; }
  }
  return best;
}

const AXIS_KO = { future_task: "미래 과제", capability_have: "보유 역량",
                  capability_gap: "역량 갭", direction: "지향 방향" };

function esc(t) { return (t || "").replace(/[&<>]/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m])); }

function openDetail(s) {
  sel = s;
  const c = catByName[s.cat] || {};
  const raw = DATA.sources[s.pid] || "";
  let src = esc(raw);
  if (raw && s.quote) {                     // 인용 구간을 원문 안에서 강조 (#015)
    const i = raw.indexOf(s.quote);
    if (i >= 0) src = esc(raw.slice(0, i)) + "<mark>" + esc(s.quote) + "</mark>" + esc(raw.slice(i + s.quote.length));
  }
  const d = document.getElementById("detail");
  d.innerHTML = `
    <button class="close" onclick="closeDetail()">×</button>
    <div class="lbl">계보 — 이 별은 어느 문장에서 왔나</div>
    <div>
      <span class="tag">${esc(AXIS_KO[s.axis] || s.axis)}</span>
      ${s.horizon ? `<span class="tag">${esc(s.horizon)}</span>` : ""}
      ${s.ax ? `<span class="tag ax">AX를 언급함</span>` : ""}
      <span class="tag">${esc(s.pjt || "")} · ${esc(s.cl || "")}</span>
    </div>
    <div class="lbl">① 회고 원문 ${s.person ? "— " + esc(s.person) : ""}</div>
    <div class="src">${src || "<i style='color:#39405a'>원문 없음 (익명 모드)</i>"}</div>
    <div class="lbl">② 인용 → ③ 뽑힌 과제 → ④ 카테고리</div>
    <div class="chain">
      <div class="step"><span style="color:var(--gold)">"${esc(s.quote)}"</span></div>
      <div class="step">${esc(s.text)}</div>
      <div class="step"><b>${esc(s.cat)}</b><br>
        <span style="color:var(--dim);font-size:11.5px">${esc(c.definition || "")}</span></div>
    </div>
    <div class="lbl">이 카테고리</div>
    <div style="font-size:11.5px;color:#aab3cc;line-height:1.8">
      ${c.people}명이 언급 · ${c.pjt_spread}개 조직 · ${c.cl_spread}개 직급<br>
      보유 ${c.have} / 갭 ${c.gap} · ${esc(c.readiness || "")}
    </div>`;
  d.classList.add("show");
  draw();
}
function closeDetail() { sel = null; document.getElementById("detail").classList.remove("show"); draw(); }

cv.addEventListener("click", e => { const s = hit(e.clientX, e.clientY); s ? openDetail(s) : closeDetail(); });
cv.addEventListener("mousemove", e => {
  const s = hit(e.clientX, e.clientY), tip = document.getElementById("tip");
  cv.style.cursor = s ? "pointer" : "crosshair";
  if (!s) { tip.style.display = "none"; hover = null; return; }
  hover = s;
  tip.innerHTML = `<b>${esc(s.text)}</b><br><span style="color:#5b6480">${esc(s.cat)}</span>`;
  tip.style.display = "block";
  tip.style.left = Math.min(e.clientX + 14, innerWidth - 300) + "px";
  tip.style.top = (e.clientY + 14) + "px";
});
cv.addEventListener("wheel", e => {
  e.preventDefault();
  view.k = Math.max(0.35, Math.min(3, view.k * (e.deltaY < 0 ? 1.1 : 0.9)));
  draw();
}, { passive: false });

const NOTES = {
  empty: "해석층 — 표시된 영역은 <b>한 조직에서만</b> 나왔거나 보유 없이 <b>갭만</b> 있는 " +
         "카테고리다. 우리가 넓게 보지 못한 방향이라는 뜻이지 안 중요하다는 뜻이 아니다. " +
         "왜 좁게 나왔는지는 데이터가 아니라 워크숍에서 사람이 답한다.",
  ax: "AX 표현이 원문 인용에 <b>실제로 적혀 있었다</b>는 관찰이다. " +
      "이게 진짜 AX 과제냐는 판정은 파이프라인이 하지 않는다.",
};
function setMode(m) {
  mode = m;
  for (const id of ["front", "empty", "ax"])
    document.getElementById("m-" + id).classList.toggle("on", id === m);
  const note = document.getElementById("note");
  note.innerHTML = NOTES[m] || "";
  note.classList.toggle("show", !!NOTES[m]);
  draw();
}
document.getElementById("m-front").onclick = () => setMode("front");
document.getElementById("m-empty").onclick = () => setMode("empty");
document.getElementById("m-ax").onclick = () => setMode("ax");

// 딥링크 — 발표 시퀀스(#021)와 헤드리스 검증 겸용. 기존 은하수의 #ego=와 같은 규약.
function applyHash() {
  const h = new URLSearchParams(location.hash.slice(1));
  if (h.get("mode")) setMode(h.get("mode"));
  const id = h.get("star");
  if (id) { const s = DATA.stars.find(s => s.id === id); if (s) openDetail(s); }
}
addEventListener("hashchange", applyHash);

resize();
applyHash();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main(*sys.argv[1:])
