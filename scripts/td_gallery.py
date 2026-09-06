"""갤러리 — td 화면 5종을 한 페이지에서 탭으로 (사용자 피드백: 파일 5개 흩어진 게 별로다).

각 화면의 build_payload/_TEMPLATE은 그대로 재사용한다 — 새로 만드는 화면은 하나도 없다,
5개를 한 셸(탭 바 + iframe)에 담는 것뿐이다.

**iframe으로 격리하는 이유**: 다섯 화면 스크립트 전부 IIFE로 감싸지 않고 top-level
`const D`/`const DATA`를 쓴다(td_heatmap·td_questions·td_onepager·td_consensus는 전부
`const D`, td_constellation은 `<canvas id="sky">`를 consensus와 공유). 원문 그대로
한 페이지에 이어붙이면 변수 재선언·DOM id 충돌로 전부 깨진다. iframe은 완전히 별도
스코프라 각 화면의 코드를 한 글자도 안 고치고 그대로 넣을 수 있다.

usage: python3 scripts/td_gallery.py [데이터디렉터리] [출력경로] [--votes 경로] [--anonymize]
"""
import sys
from pathlib import Path

import td_cards
import td_consensus
import td_constellation
import td_heatmap
import td_onepager
import td_questions
import td_render_common
from td_common import load_json

ROOT = Path(__file__).parent.parent

VIEWS = [
    ("constellation", "성좌 지도", "별=과제 · 카테고리별 성좌 · 빈 하늘 · AX 렌즈 · 계보"),
    ("heatmap", "부서 단면", "팀 × 카테고리 배정 건수"),
    ("questions", "질문 카드", "집계에서 뽑은 워크숍 아젠다"),
    ("onepager", "임원 한 장", "수치 셋 + 미니 성좌, 스크롤 없음"),
    ("consensus", "합의의 무게", "워크숍 투표가 별에 고리로"),
]


def _tour_scenes(cards, agg, votes):
    """항해(#021) 장면 목록. 캡션은 전부 실측 수치 문장이다 — 지어낸 서사(가짜 narrate
    스텁이 모든 카테고리에 복붙하는 그 문장)는 절대 넣지 않는다. 통찰이 빈 것을 순서로
    가릴 수는 없으니, 최소한 보여주는 숫자만큼은 정직해야 한다."""
    cats = agg.get("categories", [])
    n_people = len({c["person_id"] for c in cards})
    n_cats = len(cats)
    top = max(cats, key=lambda c: c.get("people", 0)) if cats else None
    sparse_n = sum(1 for c in cats
                   if c.get("pjt_spread", 0) <= 1 or c.get("readiness") == "갭만 있음")
    ax_n = sum(1 for c in cards if c.get("ax_mentioned"))
    heat = td_heatmap.build_payload(cards)
    q_n = len(td_questions.build_payload(agg)["questions"])
    voted_n = len(votes)

    return [
        {"view": "constellation", "hash": None,
         "caption": f"{n_people}명의 회고에서 {n_cats}개 카테고리가 나왔다."},
        {"view": "constellation", "hash": "mode=empty",
         "caption": (f"이 중 {sparse_n}개는 한 조직에서만 나왔거나 갭만 있다 — 넓게 못 본 방향."
                     if sparse_n else "모든 카테고리가 두 조직 이상에서 나왔다 — 희박한 영역 없음.")},
        {"view": "constellation", "hash": "mode=ax",
         "caption": (f"AX를 언급한 과제는 {ax_n}개." if ax_n
                     else "AX를 언급한 과제가 아직 없다.")},
        {"view": "heatmap", "hash": None,
         "caption": (f"팀 단면 — 전 조직 공통 {heat['totals']['common']}개, "
                     f"한 조직만의 것 {heat['totals']['local']}개.")},
        {"view": "questions", "hash": None,
         "caption": f"그래서 논의할 질문 {q_n}개가 나온다."},
        {"view": "onepager", "hash": None,
         "caption": (f"한 장으로 줄이면: 가장 넓은 주제는 「{top['name']}」"
                     f"({top.get('people', 0)}명)." if top else "집계된 주제가 없다.")},
        {"view": "consensus", "hash": None,
         "caption": (f"워크숍 투표 {voted_n}건이 별에 고리로 새겨졌다." if voted_n
                     else "아직 투표 전 — 관찰만 있는 상태다.")},
    ]


def build_payload(cards, categories, agg, votes, sources=None, *, anonymize=False):
    """다섯 화면의 렌더 결과를 모아 갤러리 셸이 먹는 페이로드로 묶는다. 파일을 읽지 않는다."""
    rendered = {
        "constellation": td_render_common.render(
            td_constellation._TEMPLATE,
            td_constellation.build_payload(cards, categories, agg, sources, anonymize=anonymize)),
        "heatmap": td_render_common.render(td_heatmap._TEMPLATE, td_heatmap.build_payload(cards)),
        "questions": td_render_common.render(td_questions._TEMPLATE, td_questions.build_payload(agg)),
        "onepager": td_render_common.render(
            td_onepager._TEMPLATE, td_onepager.build_payload(cards, categories, agg)),
        "consensus": td_render_common.render(
            td_consensus._TEMPLATE,
            td_consensus.build_payload(cards, categories, agg, votes, sources, anonymize=anonymize)),
    }
    return {"views": [{"id": vid, "title": title, "desc": desc} for vid, title, desc in VIEWS],
            "html": rendered, "tour": _tour_scenes(cards, agg, votes)}


def write(cards, categories, agg, votes, sources=None, *, out_path, anonymize=False):
    payload = build_payload(cards, categories, agg, votes, sources, anonymize=anonymize)
    return td_render_common.write_html(td_render_common.render(_TEMPLATE, payload), out_path)


def main(*argv):
    args = list(argv)
    votes_path = None
    if "--votes" in args:
        i = args.index("--votes"); votes_path = args[i + 1]; del args[i:i + 2]
    d, out, anonymize = td_render_common.parse_args(args, "gallery.html")

    cards = td_cards.build(d / "assignments.json", d / "extracted.json", anonymize=anonymize)
    taxonomy = load_json(d / "taxonomy.json") if (d / "taxonomy.json").exists() else []
    agg = load_json(d / "aggregates.json")
    src_path = next((p for p in (d / "sources.json", d.parent / "persons.json") if p.exists()), None)
    sources = load_json(src_path) if (src_path and not anonymize) else None
    votes_path = Path(votes_path) if votes_path else d / "votes.json"
    votes = load_json(votes_path) if Path(votes_path).exists() else []

    res = write(cards, taxonomy, agg, votes, sources, out_path=out, anonymize=anonymize)
    print(f"갤러리 → {res} ({len(VIEWS)}개 화면 한 페이지 · {res.stat().st_size // 1024}kb)",
          file=sys.stderr)


_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>task-discovery — 산출물 갤러리</title>
<style>
  :root{ --bg:#faf8f4; --ink:#211e1a; --dim:#7a7468; --line:#e7e2d8; --amber:#a6650f; }
  *{ box-sizing:border-box; }
  html,body{ margin:0; height:100%; background:var(--bg); color:var(--ink);
             font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif; }
  .shell{ height:100%; display:flex; flex-direction:column; }
  .bar{ display:flex; align-items:center; gap:2px; padding:0 16px; border-bottom:1px solid var(--line);
        flex:none; background:#fff; overflow-x:auto; }
  .brand{ font-family:Georgia,"Noto Serif KR",serif; font-size:15px; font-weight:600; padding:14px 16px 14px 0;
          white-space:nowrap; border-right:1px solid var(--line); margin-right:6px; }
  .tab{ appearance:none; background:none; border:none; padding:13px 16px; font-size:13px; font-weight:600;
        color:var(--dim); cursor:pointer; white-space:nowrap; border-bottom:2px solid transparent;
        font-family:inherit; }
  .tab:hover{ color:var(--ink); }
  .tab.on{ color:var(--ink); border-bottom-color:var(--amber); }
  .tab .n{ display:block; font-size:10px; font-weight:500; color:var(--dim); margin-top:1px; }
  .tab.on .n{ color:#a08a5c; }
  .tour-btn{ appearance:none; margin-left:auto; background:var(--amber); color:#fff; border:none;
             border-radius:100px; padding:8px 16px; font-size:12.5px; font-weight:600; cursor:pointer;
             white-space:nowrap; font-family:inherit; }
  .tour-btn:hover{ background:#8f5609; }
  .frame-wrap{ flex:1; min-height:0; position:relative; background:#fff; }
  iframe{ position:absolute; inset:0; width:100%; height:100%; border:0; display:none; }
  iframe.on{ display:block; }

  /* ---- 항해(발표 모드) ---- */
  .tour-chrome{ position:fixed; inset:0; z-index:50; pointer-events:none; display:none; }
  .tour-chrome.on{ display:block; }
  .tour-caption{ position:absolute; left:50%; bottom:32px; transform:translateX(-50%);
                 max-width:min(720px,86vw); background:rgba(20,17,12,0.92); color:#faf8f4;
                 border-radius:12px; padding:16px 22px; font-size:15px; line-height:1.6;
                 text-align:center; pointer-events:auto; box-shadow:0 12px 34px rgba(0,0,0,0.28); }
  .tour-dots{ display:flex; gap:6px; justify-content:center; margin-top:11px; }
  .tour-dots span{ width:6px; height:6px; border-radius:50%; background:rgba(255,255,255,0.28); }
  .tour-dots span.on{ background:var(--amber); }
  .tour-nav{ position:absolute; top:50%; transform:translateY(-50%); width:44px; height:44px;
             border-radius:50%; border:none; background:rgba(20,17,12,0.55); color:#fff; font-size:18px;
             cursor:pointer; pointer-events:auto; }
  .tour-nav:hover{ background:rgba(20,17,12,0.8); }
  .tour-nav.prev{ left:20px; } .tour-nav.next{ right:20px; }
  .tour-nav[disabled]{ opacity:0.25; cursor:default; }
  .tour-exit{ position:absolute; top:20px; right:24px; background:rgba(20,17,12,0.55); color:#fff;
              border:none; border-radius:100px; padding:7px 14px; font-size:12px; cursor:pointer;
              pointer-events:auto; }
  .tour-exit:hover{ background:rgba(20,17,12,0.8); }
</style>
</head>
<body>
<div class="shell">
  <div class="bar" id="bar">
    <div class="brand">task-discovery 갤러리</div>
  </div>
  <div class="frame-wrap" id="frameWrap"></div>
</div>
<div class="tour-chrome" id="tourChrome">
  <button class="tour-nav prev" id="tourPrev">‹</button>
  <button class="tour-nav next" id="tourNext">›</button>
  <button class="tour-exit" id="tourExit">항해 종료 (Esc)</button>
  <div class="tour-caption">
    <div id="tourCaption"></div>
    <div class="tour-dots" id="tourDots"></div>
  </div>
</div>
<script>
const GALLERY = __PAYLOAD__;
const wrap = document.getElementById("frameWrap");
const bar = document.getElementById("bar");
const frames = {};

GALLERY.views.forEach(function(v){
  var tab = document.createElement("button");
  tab.className = "tab"; tab.id = "tab-" + v.id;
  tab.innerHTML = v.title + '<span class="n">' + v.desc + '</span>';
  tab.title = v.desc;
  tab.onclick = function(){ selectView(v.id); };
  bar.appendChild(tab);

  var frame = document.createElement("iframe");
  frame.id = "frame-" + v.id;
  wrap.appendChild(frame);
  frames[v.id] = frame;
});

if (GALLERY.tour && GALLERY.tour.length){
  var tourBtn = document.createElement("button");
  tourBtn.className = "tour-btn";
  tourBtn.textContent = "▶ 항해";
  tourBtn.onclick = function(){ startTour(0); };
  bar.appendChild(tourBtn);
}

var loaded = {}, ready = {};

// hash가 필요한 장면(예: mode=ax)은 iframe이 로드된 뒤에야 그 안의 딥링크를 적용할 수 있다 —
// 기존 은하수/성좌 지도의 #ego=·#mode= 관례를 그대로 타는 것뿐, 새 프로토콜을 만들지 않았다.
function openView(id, innerHash){
  GALLERY.views.forEach(function(v){
    document.getElementById("tab-" + v.id).classList.toggle("on", v.id === id);
    frames[v.id].classList.toggle("on", v.id === id);
  });
  var frame = frames[id];
  function applyHash(){ if (innerHash) frame.contentWindow.location.hash = innerHash; }
  if (ready[id]){
    applyHash();
  } else {
    frame.addEventListener("load", function once(){
      frame.removeEventListener("load", once);
      ready[id] = true;
      applyHash();
    });
    if (!loaded[id]){ frame.srcdoc = GALLERY.html[id]; loaded[id] = true; }
  }
  history.replaceState(null, "", "#view=" + id);
}
function selectView(id){ openView(id, null); }

// ---------------- 항해(#021) — 장면 순서를 코드에 박아 발표자가 키 하나로 넘긴다 ----------------
var tourChrome = document.getElementById("tourChrome");
var tourCaption = document.getElementById("tourCaption");
var tourDots = document.getElementById("tourDots");
var scene = -1;   // -1 = 항해 모드 아님

function renderTourChrome(){
  var scenes = GALLERY.tour;
  tourCaption.textContent = scenes[scene].caption;
  tourDots.innerHTML = scenes.map(function(_, i){
    return '<span class="' + (i === scene ? "on" : "") + '"></span>';
  }).join("");
  document.getElementById("tourPrev").disabled = scene === 0;
  document.getElementById("tourNext").disabled = scene === scenes.length - 1;
}
function gotoScene(i){
  var scenes = GALLERY.tour;
  scene = Math.max(0, Math.min(scenes.length - 1, i));
  openView(scenes[scene].view, scenes[scene].hash);
  renderTourChrome();
}
function startTour(i){ tourChrome.classList.add("on"); gotoScene(i); }
function exitTour(){ scene = -1; tourChrome.classList.remove("on"); }

document.getElementById("tourPrev").onclick = function(){ gotoScene(scene - 1); };
document.getElementById("tourNext").onclick = function(){ gotoScene(scene + 1); };
document.getElementById("tourExit").onclick = exitTour;
document.addEventListener("keydown", function(e){
  if (scene < 0) return;
  if (e.key === "ArrowRight" || e.key === " ") { e.preventDefault(); gotoScene(scene + 1); }
  else if (e.key === "ArrowLeft") gotoScene(scene - 1);
  else if (e.key === "Escape") exitTour();
});

var initial = (location.hash.match(/view=([a-z]+)/) || [])[1];
var tourStart = (location.hash.match(/tour=(\d+)/) || [])[1];   // #tour=<n> — 특정 장면부터, 검증·직접 링크용
if (tourStart != null && GALLERY.tour[Number(tourStart)]) startTour(Number(tourStart));
else selectView(GALLERY.html[initial] ? initial : GALLERY.views[0].id);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main(*sys.argv[1:])
