"""임원 한 장 — 인터랙션 없는 정물 (#020).

스크롤도 클릭도 없다. 수치 셋 + 성좌 미니 컷 + 한 문장. 인쇄해도 그대로 읽힌다.

탐색 화면은 볼 시간이 있는 사람 것이다. 로드맵을 요구한 상사의 상사는 30초를 쓴다.
그 30초용 물건이 저장소에 없었고, 인터랙티브 화면의 스크린샷은 그 답이 아니다.

usage: python3 scripts/td_onepager.py [데이터디렉터리] [출력경로]
"""
import sys
from pathlib import Path

import td_cards
import td_constellation
import td_render_common
from td_common import load_json

ROOT = Path(__file__).parent.parent


def build_payload(cards, categories, agg):
    """수치 셋 + 미니 성좌 좌표. 성좌 좌표는 td_constellation에서 그대로 가져온다 —
    두 화면이 다른 그림을 보여주면 같은 데이터라는 신뢰가 깨진다."""
    full = td_constellation.build_payload(cards, categories, agg)
    cats = full["cats"]
    people = len({c["person_id"] for c in cards})
    common = [c for c in cats if c["pjt_spread"] >= 3]
    gap_only = [c for c in cats if c["readiness"] == "갭만 있음"]
    top = max(cats, key=lambda c: c["people"]) if cats else None

    return {
        "stats": [
            {"n": people, "label": "회고를 쓴 사람"},
            {"n": len(cats), "label": "뽑힌 주제"},
            {"n": len(common), "label": "전 조직 공통 주제"},
        ],
        "stars": [{"x": s["x"], "y": s["y"], "ax": s["ax"]} for s in full["stars"]],
        "cats": [{"x": c["x"], "y": c["y"], "name": c["name"], "sparse": c["sparse"]}
                 for c in cats],
        "headline": (f"{people}명의 회고에서 {len(cats)}개 주제가 나왔고, 그중 "
                     f"{len(common)}개는 전 조직이 공통으로 말했다."
                     if cats else "집계된 주제가 없다."),
        "sub": (f"가장 넓게 나온 주제는 「{top['name']}」({top['people']}명). "
                f"할 수 있다고 말한 사람 없이 필요하다고만 말한 주제가 {len(gap_only)}개다."
                if top else ""),
        "note": "숫자는 '몇 명이 말했나'이지 중요도가 아니다. 우선순위는 워크숍에서 사람이 정한다.",
    }


def write(cards, categories, agg, *, out_path):
    return td_render_common.write_html(
        td_render_common.render(_TEMPLATE, build_payload(cards, categories, agg)), out_path)


def main(*argv):
    d, out, anonymize = td_render_common.parse_args(argv, "onepager.html")
    cards = td_cards.build(d / "assignments.json", d / "extracted.json", anonymize=anonymize)
    taxonomy = load_json(d / "taxonomy.json") if (d / "taxonomy.json").exists() else []
    res = write(cards, taxonomy, load_json(d / "aggregates.json"), out_path=out)
    print(f"임원 한 장 → {res}", file=sys.stderr)


_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>한 장 요약</title>
<style>
  :root { --bg:#faf9f7; --ink:#16181d; --dim:#767d8c; --line:#e2e0dc; }
  * { box-sizing:border-box; }
  html, body { height:100%; }
  body { margin:0; background:var(--bg); color:var(--ink); overflow:hidden;
         font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif; }
  .page { height:100%; max-width:1180px; margin:0 auto; padding:52px 48px 40px;
          display:flex; flex-direction:column; }
  .lbl { font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:var(--dim); }
  .stats { display:flex; gap:64px; margin:20px 0 6px; }
  .stat b { display:block; font-size:58px; line-height:1; font-weight:600; letter-spacing:-.02em;
            font-variant-numeric:tabular-nums; }
  .stat span { font-size:12px; color:var(--dim); }
  h1 { font-size:23px; line-height:1.5; font-weight:600; margin:26px 0 8px; letter-spacing:-.01em;
       max-width:900px; }
  .sub { font-size:14px; color:#495060; line-height:1.65; max-width:820px; }
  .art { flex:1; min-height:0; margin:18px 0 0; border-top:1px solid var(--line); position:relative; }
  canvas { position:absolute; inset:0; width:100%; height:100%; }
  .note { font-size:11.5px; color:var(--dim); padding-top:14px; border-top:1px solid var(--line); }
  @media print { body { overflow:visible; } .page { height:auto; } }
</style>
</head>
<body>
<div class="page">
  <div class="lbl">task-discovery · 한 장 요약</div>
  <div class="stats" id="stats"></div>
  <h1 id="headline"></h1>
  <div class="sub" id="sub"></div>
  <div class="art"><canvas id="mini"></canvas></div>
  <div class="note" id="note"></div>
</div>
<script>
const D = __PAYLOAD__;
document.getElementById("stats").innerHTML = D.stats.map(s =>
  `<div class="stat"><b>${s.n}</b><span>${s.label}</span></div>`).join("");
document.getElementById("headline").textContent = D.headline;
document.getElementById("sub").textContent = D.sub;
document.getElementById("note").textContent = D.note;

const cv = document.getElementById("mini"), cx = cv.getContext("2d");
function draw() {
  const r = cv.getBoundingClientRect(), dpr = devicePixelRatio;
  cv.width = r.width * dpr; cv.height = r.height * dpr;
  cx.clearRect(0, 0, cv.width, cv.height);
  const k = Math.min(r.width / 980, r.height / 980) * dpr;   // 성좌는 가로세로 같은 폭이라 같은 분모
  const ox = cv.width / 2, oy = cv.height / 2;
  const P = p => [ox + p.x * k, oy + p.y * k];
  for (const c of D.cats) {                       // 성좌 뼈대
    const [ax, ay] = P(c);
    cx.strokeStyle = "rgba(120,128,145,.16)"; cx.lineWidth = dpr * 0.5;
    for (const s of D.stars) {
      if (Math.hypot(s.x - c.x, s.y - c.y) > 125) continue;
      const [sx, sy] = P(s);
      cx.beginPath(); cx.moveTo(ax, ay); cx.lineTo(sx, sy); cx.stroke();
    }
  }
  for (const s of D.stars) {
    const [x, y] = P(s);
    cx.fillStyle = s.ax ? "#0e7c6b" : "#3b4252";
    cx.beginPath(); cx.arc(x, y, (s.ax ? 2.4 : 1.7) * dpr, 0, 7); cx.fill();
  }
  cx.textAlign = "center"; cx.font = `${10.5 * dpr}px -apple-system, sans-serif`;
  for (const c of D.cats) {
    const [x, y] = P(c);
    cx.fillStyle = c.sparse ? "#b45309" : "#767d8c";
    cx.fillText(c.name, x, y - 22 * dpr);
  }
}
draw(); addEventListener("resize", draw);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main(*sys.argv[1:])
