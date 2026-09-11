"""task-discovery 산출물 역추적 탐색기 (S6-1, #39).

산출물 넷(extracted·taxonomy·assignments·aggregates)을 자립형 HTML 한 장으로 만든다.
목적은 파일을 예쁘게 보여주는 게 아니라 **파일 사이를 건너뛰는 것**이다 — 회의에서 나오는
질문("17명이 누구야", "그 사람 원문 띄워봐")은 대부분 파일 하나 안에서 답이 안 나온다.

조인은 td_cards가 한다. 여기는 그 위에 카테고리 정의(taxonomy)·회고 원문·예외 목록을
얹어 화면 데이터를 만들고 렌더할 뿐이다. **원문은 extracted.json에 없다** — td_extract가
담지 않으므로 추출 입력(sources.json/persons.json)을 따로 읽는다.

**생성물은 민감하다** — 카테고리명(레벨 2)과 실명·인용(레벨 3)이 한 파일에 인라인된다.
출력은 TD_OUT_DIR 아래로만. dist/는 GitHub Pages로 공개되므로 td_common.reject_public_path가
그쪽 경로를 아예 거부한다(docstring만으로는 지켜지지 않아서).
"""
import json
import sys
from pathlib import Path

import td_assign
import td_cards
import td_render_common
import td_render
from pipeline_log import OUT_DIR
from td_common import load_json, reject_public_path



def build_payload(aggregates, persons, assignments, taxonomy=None, *,
                  sources=None, anonymize=False):
    """화면이 필요한 것 전부를 하나의 dict로. 순수 함수 — 파일을 쓰지 않는다.

    aggregates에는 카테고리 정의가 없고(집계는 이름만 들고 온다) taxonomy에만 있다.
    Other처럼 taxonomy에 없는 카테고리도 목록에서 빠지면 안 되므로 빈 정의로 채운다.

    회고 원문은 **extracted.json에 없다** — td_extract가 담지 않아 입력 파일(sources.json
    또는 persons.json)에서 따로 가져와야 한다. sources를 안 주면 원문 칸이 빈 채로 동작한다.
    """
    aggregates = load_json(aggregates)
    persons = load_json(persons)
    assignments = load_json(assignments)
    taxonomy = load_json(taxonomy) if taxonomy is not None else []
    src_text = {}
    if sources is not None and not anonymize:
        # id는 사람 id — extracted의 person_id와 같은 값이다(td_extract가 그대로 물려준다).
        src_text = {d["id"]: d.get("text", "") for d in load_json(sources)}

    taxo = {c["name"]: c for c in taxonomy}
    categories = []
    for c in aggregates["categories"]:
        t = taxo.get(c["name"], {})
        categories.append({**c,
                           "definition": t.get("definition", ""),
                           "inclusion_criteria": t.get("inclusion_criteria", ""),
                           "relations": t.get("relations", [])})

    cards = td_cards.build(assignments, persons, anonymize=anonymize)

    # 익명화 시 원문을 통째로 뺀다 — 원문 안의 실명은 정규식으로 지울 수 없고,
    # 지우는 척하는 게 안 지우는 것보다 위험하다.
    people = [{"person_id": p["person_id"],
               "name": f"P{p['person_id']}" if anonymize else p.get("name"),
               "pjt": p.get("pjt"), "cl_level": p.get("cl_level"),
               "signal_present": bool(p.get("signal_present")),
               "text": src_text.get(p["person_id"], "")}
              for p in persons]

    return {
        "categories": categories,
        "cards": cards,
        "persons": people,
        "horizon": td_cards.horizon_distribution(cards),
        "coverage": td_render.coverage(persons, assignments),
        "exceptions": {
            "no_signal": [p for p in people if not p["signal_present"]],
            "other": [c for c in cards if c["category"] == td_assign.OTHER],
            "dropped": td_cards.dropped_facets(assignments, persons, anonymize=anonymize),
        },
        "anonymized": anonymize,
    }


def render_html(payload):
    return td_render_common.render(_TEMPLATE, payload)


def write(aggregates, persons, assignments, taxonomy=None, *, out_path,
          sources=None, anonymize=False):
    payload = build_payload(aggregates, persons, assignments, taxonomy,
                            sources=sources, anonymize=anonymize)
    return td_render_common.write_html(render_html(payload), out_path)


# ponytail: HTML을 파이썬 문자열 상수로 들고 있다. build.py는 archive/template.html을
# 읽어 토큰 치환하는데, 여기선 파일 하나로 끝나는 쪽을 택했다(스테이지 스크립트가
# 별도 asset 디렉터리에 의존하지 않게). 화면이 두 번째로 늘거나 이 상수가 400줄을
# 넘으면 build.py 방식으로 옮길 것.
_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>산출물 탐색기</title>
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

  header{display:flex;align-items:center;gap:12px;flex-wrap:wrap;
         padding:10px 20px;border-bottom:1px solid var(--line);background:var(--panel)}
  header h1{font-size:15px;margin:0;font-weight:650;white-space:nowrap}
  #q{flex:1;min-width:190px;max-width:420px;font:inherit;font-size:13px;padding:5px 11px;
     border:1px solid var(--line);border-radius:7px;background:var(--bg);color:var(--ink)}
  select{font:inherit;font-size:12.5px;padding:4px 8px;border:1px solid var(--line);
         border-radius:6px;background:var(--bg);color:var(--ink)}
  .cov{display:flex;gap:13px;font-size:12px;color:var(--dim);flex-wrap:wrap;margin-left:auto}
  .cov b{color:var(--ink);font-weight:650}

  .tabs{display:flex;gap:2px;padding:0 20px;border-bottom:1px solid var(--line);
        background:var(--panel)}
  .tab{padding:7px 14px;font-size:13px;cursor:pointer;border-bottom:2px solid transparent;
       color:var(--dim)}
  .tab.on{color:var(--ink);border-bottom-color:var(--ink);font-weight:600}
  .tab .n{font-size:11.5px;color:var(--dim);margin-left:5px}

  #crumb{padding:7px 20px;font-size:12px;color:var(--dim);background:var(--panel);
         border-bottom:1px solid var(--line);display:none}
  #crumb a{color:var(--ink);cursor:pointer;text-decoration:underline;text-underline-offset:2px}
  #crumb span.sep{margin:0 7px;opacity:.5}

  main{display:flex;align-items:stretch}
  #list{width:330px;flex:none;border-right:1px solid var(--line);background:var(--panel);
        overflow-y:auto}
  #detail{flex:1;min-width:0;padding:22px 26px;overflow-y:auto}

  .row{padding:10px 16px;border-bottom:1px solid var(--line);cursor:pointer}
  .row:hover{background:var(--soft)}
  .row.on{background:var(--soft);box-shadow:inset 3px 0 0 var(--ink)}
  .row .nm{font-weight:600;font-size:13.5px;display:flex;gap:8px;align-items:baseline}
  .row .nm .cnt{margin-left:auto;color:var(--dim);font-weight:400;font-size:12px;flex:none}
  .row .meta{font-size:11.5px;color:var(--dim);margin-top:3px}
  .row.mute .nm{color:var(--dim);font-weight:500}

  .dot{width:7px;height:7px;border-radius:99px;flex:none;display:inline-block}
  .r0{background:var(--ready)} .r1{background:var(--gapc)} .r2{background:var(--seed)}
  .rx{background:var(--dim);opacity:.5}

  h2{font-size:19px;margin:0 0 6px;letter-spacing:-.01em}
  .badge{display:inline-block;font-size:11px;padding:2px 9px;border-radius:99px;
         color:#fff;font-weight:600;vertical-align:middle;margin-left:8px}
  .def{color:var(--dim);font-size:13.5px;margin:8px 0 0}
  .nums{display:flex;gap:22px;margin:16px 0 4px;flex-wrap:wrap}
  .nums div{font-size:12px;color:var(--dim)}
  .nums b{display:block;font-size:18px;color:var(--ink);font-weight:650;line-height:1.25}

  .lbl{font-size:11px;color:var(--dim);margin:26px 0 8px;font-weight:650;
       letter-spacing:.05em;text-transform:uppercase}
  .card{border:1px solid var(--line);border-radius:9px;padding:11px 14px;margin:8px 0;
        background:var(--panel)}
  .card .ax{font-size:11px;font-weight:650;letter-spacing:.03em}
  .card .tx{margin:5px 0 0;font-size:13.5px}
  .card blockquote{margin:8px 0 0;padding:5px 0 5px 11px;border-left:2px solid var(--line);
                   font-size:12.5px;color:var(--dim)}
  .card .who{font-size:11.5px;color:var(--dim);margin-top:7px}
  a.link{color:var(--ink);cursor:pointer;text-decoration:underline;text-underline-offset:2px}
  mark{background:#ffe9a8;color:#1b1d20;border-radius:2px;padding:0 1px}

  .ax-future_task{color:var(--gapc)} .ax-capability_gap{color:var(--warn)}
  .ax-capability_have{color:var(--ready)} .ax-direction{color:var(--seed)}

  .rel{font-size:13px;margin:4px 0;color:var(--dim)}
  .rel b{color:var(--ink);font-weight:600}
  .empty{color:var(--dim);padding:60px 0;text-align:center;font-size:13.5px}
  .note{font-size:11.5px;color:var(--warn);margin-top:6px}

  details.src{margin-top:14px;border:1px solid var(--line);border-radius:9px;
              background:var(--panel)}
  details.src summary{cursor:pointer;padding:9px 14px;font-size:12.5px;color:var(--dim);
                      font-weight:600;list-style:none}
  details.src summary::-webkit-details-marker{display:none}
  details.src summary::before{content:"▸ ";opacity:.6}
  details.src[open] summary::before{content:"▾ "}
  details.src pre{margin:0;padding:0 16px 14px;white-space:pre-wrap;word-break:break-word;
                  font:13px/1.7 inherit;color:var(--ink)}

  .subtabs{display:flex;gap:6px;margin-bottom:4px}
  .subtab{font-size:12.5px;padding:4px 11px;border:1px solid var(--line);border-radius:99px;
          cursor:pointer;color:var(--dim)}
  .subtab.on{background:var(--ink);color:var(--bg);border-color:var(--ink);font-weight:600}
</style>
</head>
<body>

<header>
  <h1>산출물 탐색기</h1>
  <input id="q" type="search" placeholder="서술·인용 전체 검색" autocomplete="off">
  <select id="fpjt"><option value="">전체 pjt</option></select>
  <select id="fcl"><option value="">전체 cl</option></select>
  <span id="anon" style="font-size:12px;color:var(--dim)"></span>
  <div class="cov" id="cov"></div>
</header>

<div class="tabs" id="tabs"></div>
<div id="crumb"></div>

<main>
  <div id="list"></div>
  <div id="detail"><div class="empty">왼쪽에서 항목을 고르세요</div></div>
</main>

<script>
const DATA = __PAYLOAD__;

const AX_LABEL = {future_task:"과제", capability_gap:"갭", capability_have:"보유", direction:"방향"};
const AX_ORDER = ["future_task","capability_gap","capability_have","direction"];
const READINESS = {"이미 함":{cls:"r0", color:"--ready"},
                   "갭만 있음":{cls:"r1", color:"--gapc"},
                   "선행 신호":{cls:"r2", color:"--seed"}};
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const esc = s => String(s == null ? "" : s)
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");

const PERSON = {};
for (const p of DATA.persons) PERSON[p.person_id] = p;

// ── 상태 ────────────────────────────────────────────────────────────
// tab: 어느 입구로 보고 있나 / sel: 그 안에서 무엇을 / trail: 왕복 경로
let tab = "cat", sel = null, exTab = "no_signal", trail = [];
const F = {q:"", pjt:"", cl:""};

// ── 필터 ────────────────────────────────────────────────────────────
// 검색은 인덱스를 안 만든다 — 수백~수천 건에선 매번 훑어도 체감 지연이 없다.
const hit = (...fields) => {
  if (!F.q) return true;
  const q = F.q.toLowerCase();
  return fields.some(f => f && String(f).toLowerCase().includes(q));
};
const orgOK = r => (!F.pjt || r.pjt === F.pjt) && (!F.cl || r.cl_level === F.cl);
const cardOK = c => orgOK(c) && hit(c.text, c.quote, c.name, c.category);
const cards = () => DATA.cards.filter(cardOK);
const persons = () => DATA.persons.filter(p => orgOK(p) && hit(p.name, p.text));

function mark(s){
  const t = esc(s);
  if (!F.q) return t;
  const q = esc(F.q).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return t.replace(new RegExp(q, "gi"), m => `<mark>${m}</mark>`);
}

// 카테고리는 필터가 걸리면 남은 카드 기준으로 다시 센다 — 화면의 숫자와 목록이
// 어긋나면 어느 쪽을 믿을지 알 수 없다.
function categories(){
  const ks = cards(), by = {};
  for (const c of ks) (by[c.category] = by[c.category] || []).push(c);
  const filtering = F.q || F.pjt || F.cl;
  return DATA.categories
    .map(c => {
      const mine = by[c.name] || [];
      if (!filtering) return {...c, shown:mine.length, hidden:false};
      const people = new Set(mine.map(k => k.person_id));
      return {...c, people:people.size, shown:mine.length, hidden:!mine.length,
              pjt_spread:new Set(mine.map(k=>k.pjt).filter(Boolean)).size,
              cl_spread:new Set(mine.map(k=>k.cl_level).filter(Boolean)).size,
              have:mine.filter(k=>k.axis==="capability_have").length,
              gap:mine.filter(k=>k.axis==="capability_gap").length};
    })
    .filter(c => !c.hidden);
}

function exRows(kind){
  const rows = DATA.exceptions[kind];
  return kind === "no_signal"
    ? rows.filter(p => orgOK(p) && hit(p.name, p.text))
    : rows.filter(r => orgOK(r) && hit(r.text, r.quote, r.name));
}

// ── 헤더 ────────────────────────────────────────────────────────────
const cv = DATA.coverage;
// 필터가 걸리면 배지도 그 범위로 다시 센다 — 목록은 걸러졌는데 숫자가 전체면
// 예외 탭의 건수와 어긋나 어느 쪽을 믿을지 알 수 없다.
function renderCoverage(){
  const filtering = F.q || F.pjt || F.cl;
  const ps = persons(), ks = cards();
  const n = filtering
    ? {total: ps.length, no_signal: ps.filter(p => !p.signal_present).length,
       assignments: ks.length, other: ks.filter(k => k.category === "Other").length}
    : {total: cv.total_people, no_signal: cv.no_signal,
       assignments: cv.assignments, other: cv.other};
  const pct = (a,b) => b ? Math.round(a/b*100) : 0;
  // flex gap은 텍스트 노드엔 안 먹는다 — 항목마다 span으로 감싸야 간격이 생긴다
  document.getElementById("cov").innerHTML = [
    (filtering ? "걸러진 " : "") + `대상 <b>${n.total}</b>명`,
    `무신호 <b>${n.no_signal}</b> (${pct(n.no_signal, n.total)}%)`,
    `배정 <b>${n.assignments}</b>건`,
    `Other <b>${n.other}</b> (${pct(n.other, n.assignments)}%)`,
  ].map(s => `<span>${s}</span>`).join("");
}
if (DATA.anonymized) document.getElementById("anon").textContent = "익명 표기";

for (const [id, key] of [["fpjt","pjt"], ["fcl","cl_level"]]) {
  const el = document.getElementById(id);
  for (const v of [...new Set(DATA.persons.map(p => p[key]).filter(Boolean))].sort())
    el.insertAdjacentHTML("beforeend", `<option value="${esc(v)}">${esc(v)}</option>`);
  el.addEventListener("change", () => {
    F[key === "pjt" ? "pjt" : "cl"] = el.value; sel = null; render();
  });
}
document.getElementById("q").addEventListener("input", e => {
  F.q = e.target.value.trim(); sel = null; render();
});

// ── 탐색 이동 ────────────────────────────────────────────────────────
function go(nextTab, nextSel, {push = true} = {}){
  if (push && sel !== null) trail.push({tab, sel, label: crumbLabel()});
  tab = nextTab; sel = nextSel; render();
}
function crumbLabel(){
  if (tab === "cat") return sel;
  if (tab === "person") return (PERSON[sel] || {}).name || `P${sel}`;
  return "예외";
}
function back(i){ const t = trail[i]; trail = trail.slice(0, i); tab = t.tab; sel = t.sel; render(); }

// ── 렌더 ────────────────────────────────────────────────────────────
function renderTabs(){
  const counts = {cat: categories().length, person: persons().length,
                  ex: exRows("no_signal").length + exRows("other").length + exRows("dropped").length};
  document.getElementById("tabs").innerHTML = [
    ["cat","카테고리",counts.cat], ["person","사람",counts.person], ["ex","예외",counts.ex],
  ].map(([k,label,n]) =>
    `<div class="tab ${tab===k?"on":""}" data-t="${k}">${label}<span class="n">${n}</span></div>`
  ).join("");
  for (const el of document.querySelectorAll(".tab"))
    el.addEventListener("click", () => { trail = []; tab = el.dataset.t; sel = null; render(); });
}

function renderCrumb(){
  const el = document.getElementById("crumb");
  if (!trail.length) { el.style.display = "none"; return; }
  el.style.display = "block";
  el.innerHTML = trail.map((t,i) => `<a data-back="${i}">${esc(t.label)}</a>`)
    .join('<span class="sep">›</span>') + `<span class="sep">›</span>${esc(crumbLabel())}`;
  for (const a of el.querySelectorAll("[data-back]"))
    a.addEventListener("click", () => back(+a.dataset.back));
}

function renderList(){
  const el = document.getElementById("list");
  if (tab === "cat") {
    const cs = categories();
    el.innerHTML = cs.length ? cs.map(c => `
      <div class="row ${sel===c.name?"on":""}" data-k="${esc(c.name)}">
        <div class="nm"><span class="dot ${(READINESS[c.readiness]||{}).cls||""}"></span>
          <span>${mark(c.name)}</span><span class="cnt">${c.people}명</span></div>
        <div class="meta">항목 ${c.shown} · pjt ${c.pjt_spread} · cl ${c.cl_spread}
          · 보유 ${c.have} / 갭 ${c.gap}</div>
      </div>`).join("") : `<div class="empty">조건에 맞는 카테고리가 없습니다</div>`;
  } else if (tab === "person") {
    const ps = persons();
    el.innerHTML = ps.length ? ps.map(p => {
      const mine = DATA.cards.filter(c => c.person_id === p.person_id);
      const ncat = new Set(mine.map(c => c.category)).size;
      return `
      <div class="row ${p.signal_present?"":"mute"} ${sel===p.person_id?"on":""}"
           data-k="${p.person_id}">
        <div class="nm"><span class="dot ${p.signal_present?"r0":"rx"}"></span>
          <span>${mark(p.name || "(이름 없음)")}</span>
          <span class="cnt">${p.signal_present ? ncat + "개 카테고리" : "무신호"}</span></div>
        <div class="meta">${esc(p.pjt || "")} ${esc(p.cl_level || "")} · 항목 ${mine.length}</div>
      </div>`; }).join("") : `<div class="empty">조건에 맞는 사람이 없습니다</div>`;
  } else {
    const kinds = [["no_signal","무신호"], ["other","Other"], ["dropped","배정 폐기"]];
    el.innerHTML = `<div style="padding:12px 16px">
      <div class="subtabs">${kinds.map(([k,label]) =>
        `<span class="subtab ${exTab===k?"on":""}" data-x="${k}">${label} ${exRows(k).length}</span>`
      ).join("")}</div>
      <div class="note">추출 단계에서 통째로 실패한 사람은 extracted.json에 아예 없어
        여기에도, 아래 어느 목록에도 잡히지 않는다. 그 수는 추출을 돌린 실행 로그에만 있다.</div>
    </div>` + renderExList();
    for (const el2 of document.querySelectorAll(".subtab"))
      el2.addEventListener("click", () => { exTab = el2.dataset.x; sel = null; render(); });
  }
  for (const row of document.querySelectorAll(".row"))
    row.addEventListener("click", () => {
      const k = row.dataset.k;
      // 사람은 숫자 id, 예외 탭의 무신호도 사람이라 숫자여야 선택이 잡힌다.
      const numeric = tab === "person" || (tab === "ex" && exTab === "no_signal");
      go(tab, numeric ? +k : k, {push:false});
    });
}

function renderExList(){
  const rows = exRows(exTab);
  if (!rows.length) return `<div class="empty">없습니다</div>`;
  if (exTab === "no_signal")
    return rows.map(p => `
      <div class="row mute ${sel===p.person_id?"on":""}" data-k="${p.person_id}">
        <div class="nm"><span class="dot rx"></span><span>${mark(p.name || "(이름 없음)")}</span></div>
        <div class="meta">${esc(p.pjt || "")} ${esc(p.cl_level || "")} · 원문 ${(p.text||"").length}자</div>
      </div>`).join("");
  return rows.map((r,i) => `
    <div class="row" data-k="${i}">
      <div class="nm"><span class="dot rx"></span>
        <span class="ax ax-${r.axis}">${AX_LABEL[r.axis]}</span></div>
      <div class="meta">${mark((r.text||"").slice(0,70))}</div>
      <div class="meta">${esc(r.name || "")} ${esc(r.pjt || "")}</div>
    </div>`).join("");
}

function cardHTML(k){
  return `<div class="card">
    <div class="ax ax-${k.axis}">${AX_LABEL[k.axis]}${k.horizon ? " · " + esc(k.horizon) : ""}</div>
    <p class="tx">${mark(k.text)}</p>
    ${k.quote ? `<blockquote>${mark(k.quote)}</blockquote>` : ``}
    <div class="who">${k.person_id != null && PERSON[k.person_id]
      ? `<a class="link" data-person="${k.person_id}">${mark(k.name || "?")}</a>`
      : esc(k.name || "(알 수 없음)")}${k.pjt ? " · " + esc(k.pjt) : ""}${
      k.cl_level ? " · " + esc(k.cl_level) : ""}</div>
  </div>`;
}

// 링크는 data 속성 + 리스너로 단다. onclick에 이름을 문자열로 끼워 넣으면 카테고리명에
// 따옴표가 하나만 있어도 깨진다 — 사내 코드명엔 뭐가 들어갈지 모른다.
function wireLinks(root){
  for (const a of root.querySelectorAll("[data-person]"))
    a.addEventListener("click", () => go("person", +a.dataset.person));
  for (const a of root.querySelectorAll("[data-cat]"))
    a.addEventListener("click", () => go("cat", a.dataset.cat));
}

function renderDetail(){
  const el = document.getElementById("detail");
  if (sel === null) { el.innerHTML = `<div class="empty">왼쪽에서 항목을 고르세요</div>`; return; }

  if (tab === "cat") {
    const c = categories().find(x => x.name === sel) || DATA.categories.find(x => x.name === sel);
    if (!c) { el.innerHTML = `<div class="empty">조건에서 벗어났습니다</div>`; return; }
    const ks = cards().filter(k => k.category === sel);
    const h = DATA.horizon[sel];
    const groups = AX_ORDER.map(ax => [ax, ks.filter(k => k.axis === ax)]).filter(([,g]) => g.length);
    el.innerHTML = `
      <h2>${esc(c.name)}<span class="badge" style="background:${
        css((READINESS[c.readiness]||{}).color||"--dim")}">${esc(c.readiness)}</span></h2>
      ${c.definition ? `<p class="def">${mark(c.definition)}</p>` : ``}
      ${c.inclusion_criteria ? `<p class="def">포함 기준 — ${mark(c.inclusion_criteria)}</p>` : ``}
      <div class="nums">
        <div><b>${c.people}</b>기여 인원</div>
        <div><b>${c.pjt_spread} / ${c.cl_spread}</b>확산도 pjt / cl</div>
        <div><b>${c.have}</b>보유 언급</div>
        <div><b>${c.gap}</b>갭 언급</div>
        ${h ? `<div><b>${h["단기"]} / ${h["장기"]} / ${h["불명"]}</b>과제 시간 단기 / 장기 / 불명</div>` : ``}
      </div>
      ${groups.map(([ax,g]) => `<div class="lbl">${AX_LABEL[ax]} ${g.length}건</div>
        ${g.map(cardHTML).join("")}`).join("")}
      ${(c.relations||[]).length ? `<div class="lbl">관련 카테고리</div>
        ${c.relations.map(r => `<div class="rel"><b>${esc(r.type)}</b>
          <a class="link" data-cat="${esc(r.to)}">${esc(r.to)}</a></div>`).join("")}
        <div class="note">taxonomy에서 그대로 — LLM 재검증 없음</div>` : ``}
      ${ks.length ? `` : `<div class="empty">조건에 맞는 항목이 없습니다</div>`}`;
    return;
  }

  if (tab === "person" || (tab === "ex" && exTab === "no_signal")) {
    const p = PERSON[sel];
    if (!p) { el.innerHTML = `<div class="empty">조건에서 벗어났습니다</div>`; return; }
    const mine = DATA.cards.filter(k => k.person_id === p.person_id);
    const byCat = {};
    for (const k of mine) (byCat[k.category] = byCat[k.category] || []).push(k);
    el.innerHTML = `
      <h2>${esc(p.name || "(이름 없음)")}${p.signal_present ? `` :
        `<span class="badge" style="background:${css("--dim")}">무신호</span>`}</h2>
      <p class="def">${esc(p.pjt || "")} ${esc(p.cl_level || "")}</p>
      <div class="nums">
        <div><b>${mine.length}</b>배정된 항목</div>
        <div><b>${Object.keys(byCat).length}</b>기여 카테고리</div>
      </div>
      ${Object.entries(byCat).map(([cat,ks]) => `
        <div class="lbl"><a class="link" data-cat="${esc(cat)}">${esc(cat)}</a> ${ks.length}건</div>
        ${ks.map(cardHTML).join("")}`).join("")}
      ${mine.length ? `` : `<div class="empty">배정된 항목이 없습니다</div>`}
      ${p.text ? `<details class="src" data-src="${p.person_id}">
        <summary>회고 원문 ${p.text.length}자</summary></details>`
       : `<div class="note">${DATA.anonymized
          ? "익명 표기라 원문을 싣지 않았다 — 원문 안의 실명은 지울 수 없다."
          : "원문이 없습니다."}</div>`}`;
    return;
  }

  // 예외 탭의 Other / 배정 폐기 — 행 자체가 상세다
  const rows = exRows(exTab);
  const r = rows[sel];
  if (!r) { el.innerHTML = `<div class="empty">조건에서 벗어났습니다</div>`; return; }
  el.innerHTML = `
    <h2>${exTab === "other" ? "Other로 배정" : "인용검증 폐기"}</h2>
    <p class="def">${exTab === "other"
      ? "맞는 카테고리가 없어 흘러간 항목이다. 비율이 높으면 카테고리 체계에 빠진 주제가 있다는 신호다."
      : "인용을 두 번 대조했으나 원문에서 확인되지 않아 버려진 항목이다."}</p>
    ${cardHTML(r)}`;
}

// 원문은 펼칠 때 만든다 — 200명분을 미리 그리면 DOM이 무거워진다.
function wireSource(root){
  for (const d of root.querySelectorAll("details.src")) d.addEventListener("toggle", () => {
    if (!d.open || d.querySelector("pre")) return;
    const p = PERSON[+d.dataset.src];
    d.insertAdjacentHTML("beforeend", `<pre>${mark((p && p.text) || "")}</pre>`);
  });
}

function render(){
  renderCoverage(); renderTabs(); renderCrumb(); renderList(); renderDetail();
  wireLinks(document.getElementById("detail"));
  wireSource(document.getElementById("detail"));
  document.getElementById("detail").scrollTop = 0;
}
render();
</script>
</body>
</html>
"""


def main(*argv):
    """산출물 디렉터리 → 탐색기 HTML. 출력 기본값은 TD_OUT_DIR 안 — 리포에 쓰지 않는다.

      td_inspect.py [데이터디렉터리] [출력경로] [--anonymize]
    """
    d, out, anonymize = td_render_common.parse_args(argv, "inspect.html")
    taxonomy = d / "taxonomy.json"
    # 원문은 추출 입력에만 있다. 합성이면 sources.json, 실데이터면 persons.json.
    sources = next((p for p in (d / "sources.json", d.parent / "persons.json") if p.exists()), None)
    res = write(d / "aggregates.json", d / "extracted.json", d / "assignments.json",
                taxonomy if taxonomy.exists() else None, out_path=out,
                sources=sources, anonymize=anonymize)
    # 카테고리명·실명은 찍지 않는다 — 건수만.
    print(f"탐색기 → {res} ({res.stat().st_size // 1024}kb)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
