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
            "html": rendered}


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
  .frame-wrap{ flex:1; min-height:0; position:relative; background:#fff; }
  iframe{ position:absolute; inset:0; width:100%; height:100%; border:0; display:none; }
  iframe.on{ display:block; }
  .loading{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
             color:var(--dim); font-size:12.5px; }
</style>
</head>
<body>
<div class="shell">
  <div class="bar" id="bar">
    <div class="brand">task-discovery 갤러리</div>
  </div>
  <div class="frame-wrap" id="frameWrap"></div>
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

var loaded = {};
function selectView(id){
  GALLERY.views.forEach(function(v){
    document.getElementById("tab-" + v.id).classList.toggle("on", v.id === id);
    frames[v.id].classList.toggle("on", v.id === id);
  });
  if (!loaded[id]){                    // 처음 여는 탭만 그때 렌더 — 5개 동시 물리 시뮬레이션 방지
    frames[id].srcdoc = GALLERY.html[id];
    loaded[id] = true;
  }
  history.replaceState(null, "", "#view=" + id);
}

var initial = (location.hash.match(/view=([a-z]+)/) || [])[1];
selectView(GALLERY.html[initial] ? initial : GALLERY.views[0].id);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main(*sys.argv[1:])
