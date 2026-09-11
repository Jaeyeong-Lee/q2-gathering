"""부서 단면 — 팀 × 카테고리 히트맵 (#018).

지도가 아니라 표다. 그래서 제일 빨리 만들고 제일 정확하게 읽힌다.
가로로 고르게 진한 줄 = 전 조직이 말한 것. 세로로 한 칸만 진한 것 = 그 조직만의 것.
**이 두 줄을 화면에 적는 게 이 화면의 절반이다** — 안 그러면 히트맵은 예쁜 격자로 끝난다.

usage: python3 scripts/td_heatmap.py [데이터디렉터리] [출력경로] [--anonymize]
"""
import sys
from collections import Counter
from pathlib import Path

import td_cards
import td_render_common

ROOT = Path(__file__).parent.parent


def build_payload(cards):
    """(pjt × category) 배정 건수 격자. 파일을 읽지 않는 순수 함수."""
    pjts = sorted({c["pjt"] for c in cards if c["pjt"]})
    cats = sorted({c["category"] for c in cards})
    counts = Counter((c["pjt"], c["category"]) for c in cards if c["pjt"])

    grid = [[counts.get((p, cat), 0) for cat in cats] for p in pjts]
    peak = max((n for row in grid for n in row), default=0)

    rows = []
    for i, p in enumerate(pjts):
        rows.append({"pjt": p, "cells": grid[i], "total": sum(grid[i])})

    # 열 판정: 몇 개 조직이 말했나 → 공통(전 조직) / 국소(한 조직)
    cols = []
    for j, cat in enumerate(cats):
        spoke = sum(1 for i in range(len(pjts)) if grid[i][j] > 0)
        cols.append({"cat": cat, "total": sum(grid[i][j] for i in range(len(pjts))),
                     "orgs": spoke,
                     "kind": "공통" if spoke == len(pjts) and len(pjts) > 1
                             else ("국소" if spoke <= 1 else "부분")})
    return {"pjts": pjts, "cats": cats, "grid": grid, "peak": peak,
            "rows": rows, "cols": cols,
            "totals": {"cards": len(cards), "common": sum(1 for c in cols if c["kind"] == "공통"),
                       "local": sum(1 for c in cols if c["kind"] == "국소")}}


def write(cards, *, out_path):
    return td_render_common.write_html(
        td_render_common.render(_TEMPLATE, build_payload(cards)), out_path)


def main(*argv):
    d, out, anonymize = td_render_common.parse_args(argv, "heatmap.html")
    cards = td_cards.build(d / "assignments.json", d / "extracted.json", anonymize=anonymize)
    res = write(cards, out_path=out)
    print(f"부서 단면 → {res} (카드 {len(cards)}장)", file=sys.stderr)


_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>부서 단면 — 팀 × 주제</title>
<style>
  :root { --bg:#faf9f7; --ink:#16181d; --dim:#767d8c; --line:#e2e0dc; --ink2:#0f172a; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); padding:44px 40px 60px;
         font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif; }
  .wrap { max-width:1180px; margin:0 auto; }
  h1 { font-size:26px; margin:0 0 6px; font-weight:650; letter-spacing:-.01em; }
  .lbl { font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:var(--dim); }
  .read { margin:22px 0 26px; display:grid; gap:12px; grid-template-columns:1fr 1fr;
          border-top:1px solid var(--line); border-bottom:1px solid var(--line); padding:18px 0; }
  .read div { font-size:13px; line-height:1.7; }
  .read b { font-weight:650; }
  table { border-collapse:collapse; width:100%; }
  th, td { padding:0; }
  th.cat { font-size:11px; font-weight:500; color:var(--dim); text-align:left; height:132px;
           vertical-align:bottom; padding-bottom:9px; white-space:nowrap; width:64px; }
  th.cat span { display:inline-block; transform:rotate(-90deg) translateX(4px); transform-origin:left bottom; }
  th.pjt { text-align:right; padding-right:14px; font-size:13px; font-weight:600; white-space:nowrap; }
  td.cell { width:64px; height:46px; text-align:center; border:1px solid var(--bg);
            font-size:12px; font-variant-numeric:tabular-nums; }
  td.tot, th.tot { font-size:11px; color:var(--dim); text-align:right; padding-left:12px;
                   font-variant-numeric:tabular-nums; }
  tr.kind td { font-size:10px; color:var(--dim); text-align:center; padding-top:6px; }
  .k공통 { color:#0f172a; font-weight:650; }
  .k국소 { color:#b45309; font-weight:650; }
  .foot { margin-top:28px; font-size:12px; color:var(--dim); line-height:1.8; }
</style>
</head>
<body>
<div class="wrap">
  <div class="lbl">task-discovery · 부서 단면</div>
  <h1>팀마다 무엇이 다른가</h1>
  <div class="lbl" id="scale"></div>

  <div class="read">
    <div><b>가로로 고르게 진한 줄</b> — 그 조직이 여러 주제를 폭넓게 말했다.
      한 칸만 진하면 그 조직의 관심이 한 곳에 몰려 있다는 뜻이다.</div>
    <div><b>세로로 전부 진한 열</b> — 전 조직이 말한 <b>공통 주제</b>. 한 칸만 진한 열은
      <b>그 조직만의 주제</b>다. 둘은 워크숍에서 다르게 다뤄야 한다.</div>
  </div>

  <div id="table"></div>

  <div class="foot" id="foot"></div>
</div>

<script>
const D = __PAYLOAD__;

function shade(n) {
  if (!n) return "#f1efec";
  const t = Math.pow(n / D.peak, 0.65);              // 감마 — 낮은 값도 보이게
  const c = [ [232,229,224], [15,23,42] ];
  const mix = c[0].map((v, i) => Math.round(v + (c[1][i] - v) * t));
  return `rgb(${mix.join(",")})`;
}
function ink(n) { return n / D.peak > 0.45 ? "#f8fafc" : "#3b4252"; }

let h = "<table><thead><tr><th></th>";
for (const c of D.cats) h += `<th class="cat"><span>${c}</span></th>`;
h += `<th class="tot">합</th></tr></thead><tbody>`;
D.rows.forEach(r => {
  h += `<tr><th class="pjt">${r.pjt}</th>`;
  r.cells.forEach(n => {
    h += `<td class="cell" style="background:${shade(n)};color:${ink(n)}">${n || ""}</td>`;
  });
  h += `<td class="tot">${r.total}</td></tr>`;
});
h += `<tr class="kind"><td></td>`;
D.cols.forEach(c => { h += `<td class="k${c.kind}">${c.kind}</td>`; });
h += `<td></td></tr></tbody></table>`;
document.getElementById("table").innerHTML = h;

document.getElementById("scale").textContent =
  `조직 ${D.pjts.length} × 카테고리 ${D.cats.length} · 배정 ${D.totals.cards}건 · 최대 칸 ${D.peak}건`;
document.getElementById("foot").innerHTML =
  `전 조직이 말한 공통 주제 <b>${D.totals.common}개</b>, 한 조직에서만 나온 주제 ` +
  `<b>${D.totals.local}개</b>. 숫자는 배정된 과제·역량 항목 수이며 중요도가 아니다 — ` +
  `많이 말했다는 것과 중요하다는 것은 데이터가 구별하지 못한다.`;
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main(*sys.argv[1:])
