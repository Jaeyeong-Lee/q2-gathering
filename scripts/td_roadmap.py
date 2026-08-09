"""task-discovery 워크숍 로드맵 매트릭스 (S5-1, #43).

td_cards의 조인 위에 **시간축 × 준비도 매트릭스**를 그린다. 세로축(준비도)은 데이터가
말한 것이라 고정이고, 가로축(시간)만 워크숍에서 사람이 정한다 — 회고에는 시퀀싱이 없다.

투표 대상은 future_task(뭘 할 것인가)와 capability_gap(뭘 언제까지 갖춰야 하는가) 둘뿐이다.
capability_have·direction은 "언제"라는 질문 자체가 성립하지 않아 배경으로만 쓴다.

**역량은 그걸 쓰는 과제보다 먼저 확보돼야 한다.** 그래서 역량갭 카드의 초안은 같은
카테고리 과제보다 한 칸 왼쪽에서 시작하고, 그보다 오른쪽에 놓이면 위반으로 표시한다.
차단이 아니라 경고다 — 의도적으로 그렇게 둘 수 있고 그 자체가 논의거리다.

이 티켓은 읽기 전용이다. 드래그·투표는 #44/#45.
"""
import json
import sys
from pathlib import Path

import td_cards
from pipeline_log import OUT_DIR
from td_common import load_json

BANDS = ("단기", "중기", "장기")
VOTABLE_AXES = ("future_task", "capability_gap")

# horizon(추출이 뽑은 시간 인식) → 시간축 밴드. 불명은 가운데 — 근거 없이 급하다고
# 밀지 않는다.
_HORIZON_BAND = {"단기": 0, "장기": 2, "불명": 1}


def _band_of(horizon):
    return _HORIZON_BAND.get(horizon, 1)


def _category_task_band(cards):
    """카테고리 -> 과제 카드들의 대표 밴드(최빈, 동률이면 이른 쪽). 과제가 없으면 없음."""
    tally = {}
    for c in cards:
        if c["axis"] != "future_task":
            continue
        b = tally.setdefault(c["category"], [0, 0, 0])
        b[_band_of(c.get("horizon"))] += 1
    out = {}
    for cat, counts in tally.items():
        best = max(counts)
        out[cat] = counts.index(best)      # index가 앞선 것 = 이른 밴드 (동률 시 이른 쪽)
    return out


def votable(cards):
    """투표 대상 카드 + 초안 위치. 반환: list[dict] (원본을 건드리지 않는다).

    과제는 자기 horizon을 따르고, 역량갭은 **같은 카테고리 과제 대표 밴드보다 한 칸
    왼쪽**에서 시작한다. 과제가 없는 카테고리의 역량갭은 당길 기준이 없어 가운데.
    """
    task_band = _category_task_band(cards)
    out = []
    for c in cards:
        if c["axis"] not in VOTABLE_AXES:
            continue
        if c["axis"] == "future_task":
            band = _band_of(c.get("horizon"))
        else:
            base = task_band.get(c["category"])
            band = 1 if base is None else max(0, base - 1)
        out.append({**c, "draft_band": BANDS[band]})
    return out


def violations(voted, placed=None):
    """선후 제약 위반 카드들. placed는 {카드 text -> 밴드} 덮어쓰기(미지정이면 초안).

    역량갭이 **같은 카테고리에서 가장 이른 과제보다 뒤**에 있으면 위반이다 — 그 과제를
    시작할 때 역량이 아직 없다는 뜻이라 실행 불가능한 순서다. 같은 밴드는 위반이 아니다.
    한 종류만 있는 카테고리는 판정할 근거가 없어 건너뛴다.
    """
    placed = placed or {}
    band = lambda c: BANDS.index(placed.get(c["text"], c["draft_band"]))

    earliest_task = {}
    for c in voted:
        if c["axis"] == "future_task":
            b = band(c)
            cat = c["category"]
            if cat not in earliest_task or b < earliest_task[cat]:
                earliest_task[cat] = b

    return [c for c in voted
            if c["axis"] == "capability_gap"
            and c["category"] in earliest_task
            and band(c) > earliest_task[c["category"]]]


def _band(card, placed):
    return placed.get(card["text"], card["draft_band"])


def category_bands(voted, placed=None):
    """카테고리 -> 밴드. **카드 배치를 집계해서 얻는다** — 카테고리를 직접 찍지 않는다.
    매트릭스는 입력이 아니라 산출이다. 동률이면 이른 쪽 — 늦게 잡는 것보다 이르게 잡는
    편이 계획에서 안전하다."""
    placed = placed or {}
    tally = {}
    for c in voted:
        tally.setdefault(c["category"], [0, 0, 0])[BANDS.index(_band(c, placed))] += 1
    return {cat: BANDS[counts.index(max(counts))] for cat, counts in tally.items()}


def moved(voted, placed=None):
    """초안과 달라진 카드들. 워크숍이 무엇을 바꿨는지가 산출물의 절반이다."""
    placed = placed or {}
    return [{**c, "from": c["draft_band"], "to": _band(c, placed)}
            for c in voted if _band(c, placed) != c["draft_band"]]


def export(voted, placed=None):
    """워크숍 결과. 초안과 확정을 **둘 다** 남긴다 — 무엇을 바꿨는지 없으면 나중에
    그 결정을 방어할 수 없다."""
    placed = placed or {}
    return {
        "cards": [{"category": c["category"], "axis": c["axis"], "text": c["text"],
                   "person_id": c["person_id"], "name": c.get("name"), "pjt": c.get("pjt"),
                   "draft_band": c["draft_band"], "band": _band(c, placed),
                   "moved": _band(c, placed) != c["draft_band"]} for c in voted],
        "categories": category_bands(voted, placed),
        "violations": [c["text"] for c in violations(voted, placed)],
    }


def build_nodes(cards, categories):
    """카테고리 버블. 세로축(준비도)은 aggregates가 말한 것을 그대로 쓴다.

    capability_silent: 보유·갭 언급이 하나도 없는 카테고리. td_aggregate의 판정식은
    이때 '이미 함'으로 떨어지는데 실제로는 '역량 언급이 없다'이지 '보유가 우세하다'가
    아니다. 세로축을 여기서 고쳐 쓰지 않고(그건 Layer 1의 의미를 바꾸는 일이다) 사실만
    표시해 사람이 알아보게 한다.
    """
    task_band = _category_task_band(cards)
    dist = td_cards.horizon_distribution(cards)
    nodes = []
    for c in categories:
        base = task_band.get(c["name"])
        nodes.append({
            "name": c["name"],
            "definition": c.get("definition", ""),
            "readiness": c.get("readiness", ""),
            "people": c.get("people", 0),
            "pjt_spread": c.get("pjt_spread", 0),
            "cl_spread": c.get("cl_spread", 0),
            "have": c.get("have", 0), "gap": c.get("gap", 0),
            "draft_band": BANDS[1 if base is None else base],
            "horizon_known": base is not None,
            "capability_silent": not c.get("have", 0) and not c.get("gap", 0),
            "horizon": dist.get(c["name"]),
        })
    return nodes


def build_edges(categories):
    """taxonomy 관계 중 **화면에 있는 카테고리끼리**만. 없는 곳을 가리키는 선은 그리면
    끊긴 선으로 보여 오해를 만든다."""
    names = {c["name"] for c in categories}
    edges = []
    for c in categories:
        for r in c.get("relations") or []:
            if r.get("to") in names:
                edges.append({"from": c["name"], "to": r["to"], "type": r.get("type")})
    return edges


def build_payload(cards, categories):
    cards, categories = load_json(cards), load_json(categories)
    voted = votable(cards)
    return {"nodes": build_nodes(cards, categories),
            "edges": build_edges(categories),
            "cards": voted,
            "violations": [c["text"] for c in violations(voted)],
            "bands": list(BANDS)}


def _embed(payload):
    return (json.dumps(payload, ensure_ascii=False)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def render_html(payload):
    return _TEMPLATE.replace("__PAYLOAD__", _embed(payload))


def _reject_public_path(out_path):
    """td_inspect와 같은 이유 — dist/는 GitHub Pages로 공개된다."""
    if "dist" in Path(out_path).resolve().parts:
        raise ValueError("dist/ 아래에는 쓸 수 없다 — 배포 추적 경로다. TD_OUT_DIR을 써라")


def write(cards, categories, *, out_path):
    _reject_public_path(out_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_html(build_payload(cards, categories)), encoding="utf-8")
    return out_path


# ponytail: td_inspect와 같은 판단 — HTML을 파이썬 문자열로 들고 있다. 세 번째 화면이
# 생기면 build.py의 template.html 방식으로 옮길 것.
_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>부서 로드맵 매트릭스</title>
<style>
  :root{
    --bg:#fbfbfa; --panel:#fff; --ink:#1b1d20; --dim:#6b7280; --line:#e3e5e8; --soft:#f4f5f6;
    --ready:#0e9384; --gapc:#d97706; --seed:#7c5cd6; --warn:#dc2626;
  }
  @media (prefers-color-scheme: dark){
    :root{ --bg:#16181b; --panel:#1c1f23; --ink:#e8eaed; --dim:#9aa1ab; --line:#2f343a;
           --soft:#22262b; --ready:#3fb9ab; --gapc:#e8a33d; --seed:#a58ae8; --warn:#f0776b; }
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
       font:14px/1.6 -apple-system,BlinkMacSystemFont,"Pretendard","Apple SD Gothic Neo",
            "Malgun Gothic",sans-serif}
  header{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:11px 20px;
         border-bottom:1px solid var(--line);background:var(--panel)}
  header h1{font-size:15px;margin:0;font-weight:650;white-space:nowrap}
  header .sub{font-size:12px;color:var(--dim)}
  select{font:inherit;font-size:12.5px;padding:4px 8px;border:1px solid var(--line);
         border-radius:6px;background:var(--bg);color:var(--ink);max-width:200px}
  .warn{margin-left:auto;font-size:11.5px;color:var(--warn);border:1px solid var(--line);
        background:var(--panel);padding:3px 10px;border-radius:99px;font-weight:600}
  .bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:8px 20px;
       border-bottom:1px solid var(--line);background:var(--panel);font-size:12.5px}
  button{font:inherit;font-size:12.5px;padding:4px 11px;border:1px solid var(--line);
         background:var(--bg);border-radius:6px;cursor:pointer;color:var(--ink)}
  button.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
  main{display:flex;align-items:stretch}
  #plot{flex:1;min-width:0;padding:8px 4px 0 10px}
  svg{display:block;width:100%;height:auto}
  aside{width:340px;flex:none;border-left:1px solid var(--line);background:var(--panel);
        padding:16px 18px;overflow-y:auto}
  aside h2{font-size:16px;margin:0 0 4px}
  .badge{display:inline-block;font-size:11px;padding:2px 9px;border-radius:99px;color:#fff;
         font-weight:600;margin-left:6px;vertical-align:middle}
  .def{color:var(--dim);font-size:12.5px;margin:8px 0 0}
  .nums{display:grid;grid-template-columns:1fr 1fr;gap:8px 12px;margin:14px 0;font-size:12px;
        color:var(--dim)}
  .nums b{display:block;font-size:17px;color:var(--ink);font-weight:650;line-height:1.2}
  .lbl{font-size:11px;color:var(--dim);margin:20px 0 7px;font-weight:650;letter-spacing:.05em;
       text-transform:uppercase}
  .item{border:1px solid var(--line);border-radius:8px;padding:9px 12px;margin:6px 0}
  .item .ax{font-size:10.5px;font-weight:650}
  .item p{margin:4px 0 0;font-size:12.5px}
  .item .who{font-size:11px;color:var(--dim);margin-top:5px}
  .ax-future_task{color:var(--gapc)} .ax-capability_gap{color:var(--warn)}
  .bad{border-color:var(--warn)}
  .bad .flag{font-size:11px;color:var(--warn);font-weight:600;margin-top:5px}
  .rel{font-size:12.5px;color:var(--dim);margin:3px 0}
  .rel b{color:var(--ink)}
  .empty{color:var(--dim);text-align:center;padding:50px 0;font-size:13px}
  .note{font-size:11.5px;color:var(--warn);margin-top:8px}
  /* 카드 배치 보드 */
  #board{flex:1;min-width:0;padding:12px 16px;display:none}
  .cols{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;align-items:start}
  .col{background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:10px;
       min-height:220px}
  .col.over{border-color:var(--ink);background:var(--panel)}
  .col h3{margin:0 0 8px;font-size:12.5px;color:var(--dim);font-weight:650;
          display:flex;align-items:baseline;gap:6px}
  .col h3 .n{margin-left:auto;font-weight:400}
  .kard{background:var(--panel);border:1px solid var(--line);border-radius:9px;
        padding:9px 11px;margin:7px 0;cursor:grab}
  .kard:active{cursor:grabbing}
  .kard.drag{opacity:.4}
  .kard .ax{font-size:10.5px;font-weight:650}
  .kard .tx{margin:4px 0 0;font-size:13px;line-height:1.5}
  .kard .who{font-size:11px;color:var(--dim);margin-top:5px}
  .kard details{margin-top:6px}
  .kard summary{cursor:pointer;font-size:11px;color:var(--dim);list-style:none}
  .kard summary::-webkit-details-marker{display:none}
  .kard summary::before{content:"▸ 원문"}
  .kard details[open] summary::before{content:"▾ 원문"}
  .kard blockquote{margin:6px 0 0;padding:4px 0 4px 10px;border-left:2px solid var(--line);
                   font-size:12px;color:var(--dim)}
  .kard.moved{border-left:3px solid var(--seed)}
  .kard.moved .mv{font-size:10.5px;color:var(--seed);font-weight:600;margin-top:5px}
  .kard.bad{border-color:var(--warn)}
  .kard.bad .flag{font-size:10.5px;color:var(--warn);font-weight:600;margin-top:5px}
  .node{cursor:pointer}
  .node text{pointer-events:none;user-select:none}
  .node.sel circle{stroke:var(--ink);stroke-width:2.5}
</style>
</head>
<body>

<header>
  <h1>부서 로드맵 매트릭스</h1>
  <span class="sub">세로축 = 데이터가 말한 것 · 가로축 = 워크숍에서 정하는 것 (지금은 초안)</span>
  <span class="warn" id="src"></span>
</header>

<div class="bar">
  <button id="mMatrix" class="on">매트릭스</button>
  <button id="mBoard">카드 배치</button>
  <span style="width:8px"></span>
  <select id="cat"></select>
  <select id="fpjt"><option value="">전체 pjt</option></select>
  <select id="fcl"><option value="">전체 cl</option></select>
  <span style="width:8px"></span>
  <button id="bRel" class="on">관계선</button>
  <button id="bQuad" class="on">사분면</button>
  <button id="bBad" class="on">선후 위반</button>
  <span style="color:var(--dim)" id="stat"></span>
  <span style="margin-left:auto"></span>
  <button id="bReset">초안으로</button>
  <button id="bExport">로드맵 내보내기</button>
</div>

<main>
  <div id="plot"><svg id="svg" viewBox="0 0 900 560" preserveAspectRatio="xMidYMid meet"></svg></div>
  <div id="board"></div>
  <aside id="side"><div class="empty">버블을 클릭하면<br>근거가 여기 나옵니다</div></aside>
</main>

<script>
const DATA = __PAYLOAD__;
const NS = "http://www.w3.org/2000/svg";
const BANDS = DATA.bands;
const READINESS = {"이미 함":"--ready", "갭만 있음":"--gapc", "선행 신호":"--seed"};
const AX_LABEL = {future_task:"과제", capability_gap:"역량 갭"};
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const esc = s => String(s == null ? "" : s)
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const el = (t,a={}) => { const e = document.createElementNS(NS,t);
  for (const k in a) e.setAttribute(k, a[k]); return e; };

const W=900, H=560, M={t:30,r:24,b:48,l:112};
const PW=W-M.l-M.r, PH=H-M.t-M.b, bandH=PH/3;
const R_BAND = {"이미 함":0, "갭만 있음":1, "선행 신호":2};   // 아래→위
const cx = b => M.l + PW*(BANDS.indexOf(b) + 0.5)/3;
const cyOf = r => M.t + PH - ((R_BAND[r] ?? 1) + 0.5)*bandH;
const rad = p => 9 + Math.sqrt(Math.max(p,1))*3.2;
const alpha = n => 0.32 + 0.5*((n.pjt_spread/3) + (n.cl_spread/3))/2;

const BY_CAT = {};
for (const c of DATA.cards) (BY_CAT[c.category] = BY_CAT[c.category] || []).push(c);

document.getElementById("src").textContent =
  `${DATA.nodes.length}개 카테고리 · 카드 ${DATA.cards.length}장 · 초안 상태`;


let show = {rel:true, quad:true, bad:true}, sel = null;
let mode = "matrix", curCat = null;
const F = {pjt:"", cl:""};
// placed: 카드 text -> 밴드. 초안과 다른 것만 담는다(비어 있으면 전부 초안 상태).
const placed = {};
const state = DATA.nodes.map(n => ({...n, x:n.draft_band, y:cyOf(n.readiness), r:rad(n.people)}));
const byName = Object.fromEntries(state.map(s => [s.name, s]));

const bandOf = c => placed[c.text] || c.draft_band;
const orgOK = c => (!F.pjt || c.pjt === F.pjt) && (!F.cl || c.cl_level === F.cl);

// 아래 셋은 td_roadmap.py의 category_bands / violations / moved를 그대로 옮긴 것이다.
// 서버가 없는 A단계라 브라우저가 직접 계산해야 한다 — 규칙이 바뀌면 양쪽을 같이 고칠 것.
// 파이썬 쪽이 정본이고 테스트가 그쪽을 고정한다.
function categoryBands(){
  const tally = {};
  for (const c of DATA.cards) {
    const t = tally[c.category] = tally[c.category] || [0,0,0];
    t[BANDS.indexOf(bandOf(c))]++;
  }
  const out = {};
  for (const [cat,t] of Object.entries(tally)) out[cat] = BANDS[t.indexOf(Math.max(...t))];
  return out;   // 동률이면 indexOf가 이른 밴드를 집는다
}
function currentViolations(){
  const earliest = {};
  for (const c of DATA.cards) if (c.axis === "future_task") {
    const b = BANDS.indexOf(bandOf(c));
    if (!(c.category in earliest) || b < earliest[c.category]) earliest[c.category] = b;
  }
  return new Set(DATA.cards.filter(c => c.axis === "capability_gap"
    && c.category in earliest && BANDS.indexOf(bandOf(c)) > earliest[c.category])
    .map(c => c.text));
}
function movedCount(){ return DATA.cards.filter(c => bandOf(c) !== c.draft_band).length; }

function applyPlacement(){
  const bands = categoryBands();
  for (const s of state) s.x = bands[s.name] || s.draft_band;
  BADNOW = currentViolations();
}
let BADNOW = new Set(DATA.violations);

// 같은 칸에 겹친 버블을 세로로만 밀어낸다 — 가로는 시간축이라 건드리면 뜻이 바뀐다.
function relax(){
  for (const b of [0,1,2]) {
    const g = state.filter(s => (R_BAND[s.readiness] ?? 1) === b);
    const lo = M.t + PH - (b+1)*bandH + 13, hi = M.t + PH - b*bandH - 13;
    g.forEach(s => { s.y = cyOf(s.readiness); });
    for (let it=0; it<80; it++) {
      let moved = false;
      for (let i=0;i<g.length;i++) for (let j=i+1;j<g.length;j++) {
        const a=g[i], c=g[j];
        const dx = cx(c.x)-cx(a.x), dy = c.y-a.y;
        const need = a.r+c.r+4, dist = Math.hypot(dx,dy) || 0.01;
        if (dist < need) {
          const push = (need-dist)/2, sgn = dy >= 0 ? 1 : -1;
          a.y -= sgn*push*0.6; c.y += sgn*push*0.6; moved = true;
        }
      }
      g.forEach(s => { s.y = Math.min(hi, Math.max(lo, s.y)); });
      if (!moved) break;
    }
  }
}

function draw(){
  relax();
  const svg = document.getElementById("svg");
  svg.textContent = "";
  const defs = el("defs");
  defs.innerHTML = '<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" ' +
    'markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#9aa3b2"/></marker>';
  svg.appendChild(defs);

  if (show.quad) {
    svg.appendChild(el("rect",{x:M.l, y:M.t+PH-2*bandH, width:PW/3, height:bandH,
      fill:css("--warn"), "fill-opacity":.055}));
    svg.appendChild(el("rect",{x:M.l+PW*2/3, y:M.t, width:PW/3, height:bandH,
      fill:css("--seed"), "fill-opacity":.06}));
    const tag = (x,y,t,c) => { const n = el("text",{x, y, "font-size":10.5, fill:c,
      "font-weight":700}); n.textContent = t; svg.appendChild(n); };
    tag(M.l+9, M.t+PH-2*bandH+16, "위험 구역 — 급한데 역량이 없다", css("--warn"));
    tag(M.l+PW*2/3+9, M.t+16, "씨앗 — 지금 투자 결정", css("--seed"));
  }

  for (let i=0;i<=3;i++) {
    svg.appendChild(el("line",{x1:M.l+PW*i/3, y1:M.t, x2:M.l+PW*i/3, y2:M.t+PH,
      stroke:css("--line"), "stroke-width":1}));
    svg.appendChild(el("line",{x1:M.l, y1:M.t+PH*i/3, x2:M.l+PW, y2:M.t+PH*i/3,
      stroke:css("--line"), "stroke-width":1}));
  }
  BANDS.forEach((b,i) => { const n = el("text",{x:M.l+PW*(i+0.5)/3, y:M.t+PH+21,
    "text-anchor":"middle", "font-size":12, fill:css("--dim"), "font-weight":600});
    n.textContent = b; svg.appendChild(n); });
  Object.entries(R_BAND).forEach(([r,i]) => { const n = el("text",{x:M.l-12,
    y:M.t+PH-(i+0.5)*bandH+4, "text-anchor":"end", "font-size":12,
    fill:css(READINESS[r]), "font-weight":650}); n.textContent = r; svg.appendChild(n); });
  const ax = (x,y,t,rot) => { const n = el("text",{x, y, "font-size":11, fill:css("--dim"),
    "text-anchor":"middle"}); if (rot) n.setAttribute("transform", `rotate(-90 ${x} ${y})`);
    n.textContent = t; svg.appendChild(n); };
  ax(M.l+PW/2, H-10, "언제 할 것인가  —  워크숍에서 정한다");
  ax(18, M.t+PH/2, "준비도  —  데이터가 말한 것 (고정)", true);

  if (show.rel) for (const e of DATA.edges) {
    const a = byName[e.from], b = byName[e.to];
    if (!a || !b) continue;
    svg.appendChild(el("line",{x1:cx(a.x), y1:a.y, x2:cx(b.x), y2:b.y,
      stroke: e.type === "broader" ? "#f0c46a" : "#b9c0cc",
      "stroke-width": e.type === "broader" ? 2 : 1.3,
      "stroke-dasharray": e.type === "broader" ? "" : "5 4", "stroke-opacity":.8}));
  }

  for (const s of state) {
    const bad = show.bad && (BY_CAT[s.name] || []).some(c => BADNOW.has(c.text));
    const g = el("g",{class:"node" + (sel === s.name ? " sel" : "")});
    g.appendChild(el("circle",{cx:cx(s.x), cy:s.y, r:s.r,
      fill:css(READINESS[s.readiness] || "--dim"), "fill-opacity":alpha(s),
      stroke: bad ? css("--warn") : css(READINESS[s.readiness] || "--dim"),
      "stroke-width": bad ? 2.4 : 1.2,
      "stroke-dasharray": bad ? "4 2" : ""}));
    const words = s.name.split(" ");
    const lines = words.length > 2
      ? [words.slice(0, Math.ceil(words.length/2)).join(" "),
         words.slice(Math.ceil(words.length/2)).join(" ")]
      : [s.name];
    lines.forEach((ln,i) => {
      const t = el("text",{x:cx(s.x), y:s.y+4+(i-(lines.length-1)/2)*11,
        "text-anchor":"middle", "font-size":9.5, fill:"#fff", "font-weight":600});
      t.textContent = ln; g.appendChild(t);
    });
    g.addEventListener("click", () => { sel = s.name; draw(); side(s); });
    svg.appendChild(g);
  }
}

function side(s){
  const ks = BY_CAT[s.name] || [];
  const groups = ["future_task","capability_gap"].map(a => [a, ks.filter(k => k.axis === a)]);
  document.getElementById("side").innerHTML = `
    <h2>${esc(s.name)}<span class="badge" style="background:${css(READINESS[s.readiness]||"--dim")}"
      >${esc(s.readiness)}</span></h2>
    ${s.definition ? `<p class="def">${esc(s.definition)}</p>` : ``}
    <div class="nums">
      <div><b>${s.people}</b>기여 인원</div>
      <div><b>${s.pjt_spread} / ${s.cl_spread}</b>확산도 pjt / cl</div>
      <div><b>${s.have}</b>보유 언급</div>
      <div><b>${s.gap}</b>갭 언급</div>
    </div>
    ${s.capability_silent ? `<div class="note">보유·갭 언급이 하나도 없다.
      준비도 "${esc(s.readiness)}"는 보유가 우세해서가 아니라 역량 언급이 없어서 나온 값이다.</div>` : ``}
    ${s.horizon_known ? `` : `<div class="note">미래과제가 없어 시간축 초안을 계산할 근거가 없다 —
      가운데에 놓았다.</div>`}
    ${groups.map(([a,g]) => g.length ? `<div class="lbl">${AX_LABEL[a]} ${g.length}건</div>
      ${g.map(k => { const bad = BADNOW.has(k.text); return `
        <div class="item ${bad?"bad":""}">
          <div class="ax ax-${a}">${AX_LABEL[a]} · ${esc(bandOf(k))}${
            bandOf(k) !== k.draft_band ? " (초안 " + esc(k.draft_band) + ")" : ""}</div>
          <p>${esc(k.text)}</p>
          <div class="who">${esc(k.name || "?")}${k.pjt ? " · " + esc(k.pjt) : ""}</div>
          ${bad ? `<div class="flag">이 역량이 그것을 쓰는 첫 과제보다 뒤에 있다</div>` : ``}
        </div>`; }).join("")}` : ``).join("")}
    ${(DATA.edges.filter(e => e.from === s.name || e.to === s.name)).length
      ? `<div class="lbl">관련 카테고리</div>` + DATA.edges
          .filter(e => e.from === s.name || e.to === s.name)
          .map(e => `<div class="rel"><b>${esc(e.type)}</b> ${
            esc(e.from === s.name ? e.to : e.from)}</div>`).join("")
      : ``}`;
}

for (const [id,k] of [["bRel","rel"], ["bQuad","quad"], ["bBad","bad"]])
  document.getElementById(id).addEventListener("click", e => {
    show[k] = !show[k]; e.target.classList.toggle("on", show[k]); draw();
  });

// ── 카드 배치 보드 ────────────────────────────────────────────────────
function kardHTML(c){
  const bad = BADNOW.has(c.text), mv = bandOf(c) !== c.draft_band;
  return `<div class="kard ${mv?"moved":""} ${bad?"bad":""}" draggable="true" data-t="${esc(c.text)}">
    <div class="ax ax-${c.axis}">${AX_LABEL[c.axis]}</div>
    <p class="tx">${esc(c.text)}</p>
    <div class="who">${esc(c.name || "?")}${c.pjt ? " · " + esc(c.pjt) : ""}${
      c.cl_level ? " · " + esc(c.cl_level) : ""}</div>
    ${c.quote ? `<details><summary></summary><blockquote>${esc(c.quote)}</blockquote></details>` : ``}
    ${mv ? `<div class="mv">초안 ${esc(c.draft_band)} → ${esc(bandOf(c))}</div>` : ``}
    ${bad ? `<div class="flag">이 역량이 그것을 쓰는 첫 과제보다 뒤에 있다</div>` : ``}
  </div>`;
}

function renderBoard(){
  const mine = DATA.cards.filter(c => c.category === curCat && orgOK(c));
  const board = document.getElementById("board");
  board.innerHTML = `
    <div style="font-size:13px;margin:0 0 10px">
      <b>${esc(curCat || "")}</b>
      <span style="color:var(--dim)"> · 카드 ${mine.length}장 ·
        옮긴 카드 ${mine.filter(c => bandOf(c) !== c.draft_band).length}장</span>
    </div>
    <div class="cols">${BANDS.map(b => {
      const ks = mine.filter(c => bandOf(c) === b);
      return `<div class="col" data-b="${b}">
        <h3>${b}<span class="n">${ks.length}</span></h3>
        ${ks.map(kardHTML).join("")}
      </div>`; }).join("")}</div>
    ${mine.length ? `` : `<div class="empty">조건에 맞는 카드가 없습니다</div>`}`;
  wireDrag();
}

let dragging = null;
function wireDrag(){
  for (const k of document.querySelectorAll(".kard")) {
    k.addEventListener("dragstart", e => {
      dragging = k.dataset.t; k.classList.add("drag");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", dragging);   // Firefox는 이게 있어야 드래그가 시작된다
    });
    k.addEventListener("dragend", () => { dragging = null; k.classList.remove("drag"); });
  }
  for (const col of document.querySelectorAll(".col")) {
    col.addEventListener("dragover", e => { e.preventDefault(); col.classList.add("over"); });
    col.addEventListener("dragleave", () => col.classList.remove("over"));
    col.addEventListener("drop", e => {
      e.preventDefault(); col.classList.remove("over");
      const t = dragging || e.dataTransfer.getData("text/plain");
      if (t) place(t, col.dataset.b);
    });
  }
}

function place(text, band){
  const c = DATA.cards.find(x => x.text === text);
  if (!c) return;
  if (band === c.draft_band) delete placed[text]; else placed[text] = band;
  refresh();
}

function refresh(){
  applyPlacement();
  document.getElementById("stat").textContent =
    (BADNOW.size ? `선후 위반 ${BADNOW.size}건 · ` : "선후 위반 없음 · ") + `옮긴 카드 ${movedCount()}장`;
  draw();
  if (mode === "board") renderBoard();
  if (sel && byName[sel]) side(byName[sel]);
}

// ── 모드 · 필터 · 내보내기 ────────────────────────────────────────────
function setMode(m){
  mode = m;
  // CSS가 #board를 none으로 두므로 켤 땐 명시해야 한다 — ""로 되돌리면 CSS 규칙이 다시 먹는다.
  document.getElementById("plot").style.display = m === "matrix" ? "block" : "none";
  document.getElementById("board").style.display = m === "board" ? "block" : "none";
  document.querySelector("aside").style.display = m === "matrix" ? "block" : "none";
  document.getElementById("mMatrix").classList.toggle("on", m === "matrix");
  document.getElementById("mBoard").classList.toggle("on", m === "board");
  for (const id of ["bRel","bQuad","bBad"])
    document.getElementById(id).style.display = m === "matrix" ? "inline-block" : "none";
  document.getElementById("cat").style.display = m === "board" ? "inline-block" : "none";
  refresh();
}

const catSel = document.getElementById("cat");
for (const n of DATA.nodes)
  catSel.insertAdjacentHTML("beforeend", `<option value="${esc(n.name)}">${esc(n.name)}</option>`);
curCat = DATA.nodes.length ? DATA.nodes[0].name : null;
catSel.addEventListener("change", () => { curCat = catSel.value; renderBoard(); });

for (const [id,key] of [["fpjt","pjt"], ["fcl","cl_level"]]) {
  const el2 = document.getElementById(id);
  for (const v of [...new Set(DATA.cards.map(c => c[key]).filter(Boolean))].sort())
    el2.insertAdjacentHTML("beforeend", `<option value="${esc(v)}">${esc(v)}</option>`);
  el2.addEventListener("change", () => {
    F[key === "pjt" ? "pjt" : "cl"] = el2.value; refresh();
  });
}

document.getElementById("mMatrix").addEventListener("click", () => setMode("matrix"));
document.getElementById("mBoard").addEventListener("click", () => setMode("board"));
document.getElementById("bReset").addEventListener("click", () => {
  for (const k of Object.keys(placed)) delete placed[k];
  refresh();
});
document.getElementById("bExport").addEventListener("click", () => {
  // td_roadmap.export와 같은 모양 — 초안과 확정을 둘 다 남긴다.
  const out = {
    generated_at: new Date().toISOString(),
    note: "워크숍 배치 결과. band는 사람이 정한 값, readiness는 데이터에서 온 값.",
    categories: categoryBands(),
    violations: [...BADNOW],
    cards: DATA.cards.map(c => ({category:c.category, axis:c.axis, text:c.text,
      person_id:c.person_id, name:c.name, pjt:c.pjt,
      draft_band:c.draft_band, band:bandOf(c), moved:bandOf(c) !== c.draft_band})),
  };
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 1)], {type:"application/json"}));
  a.download = "roadmap.json"; a.click(); URL.revokeObjectURL(a.href);
});

setMode("matrix");
</script>
</body>
</html>
"""


def main(*argv):
    """산출물 디렉터리 → 로드맵 매트릭스 HTML.

      td_roadmap.py [데이터디렉터리] [출력경로] [--anonymize]
    """
    args = [a for a in argv if a != "--anonymize"]
    anonymize = "--anonymize" in argv
    d = Path(args[0]) if len(args) > 0 else OUT_DIR / "task_discovery"
    out = Path(args[1]) if len(args) > 1 else d / "roadmap.html"

    cards = td_cards.build(d / "assignments.json", d / "extracted.json", anonymize=anonymize)
    aggregates = load_json(d / "aggregates.json")
    taxo_path = d / "taxonomy.json"
    taxo = {c["name"]: c for c in load_json(taxo_path)} if taxo_path.exists() else {}
    categories = [{**c, "definition": taxo.get(c["name"], {}).get("definition", ""),
                   "relations": taxo.get(c["name"], {}).get("relations", [])}
                  for c in aggregates["categories"]]

    res = write(cards, categories, out_path=out)
    voted = votable(cards)
    # 카테고리명·실명은 찍지 않는다 — 건수만.
    print(f"로드맵 → {res} (카드 {len(voted)}장 · 선후 위반 {len(violations(voted))}건)",
          file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
