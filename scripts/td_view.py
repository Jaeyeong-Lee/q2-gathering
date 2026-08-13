"""pjt별 산출물 뷰어 — 보고 자리에서 화면에 띄우는 용도 (자립형 HTML 1장).

`<루트>/pjt_a/`, `pjt_b/` … 각각에 든 산출물 넷(extracted·taxonomy·assignments·
aggregates)을 **한 파일**로 묶고, 상단 버튼으로 pjt를 갈아끼운다. 발표 중에 탭
여덟 개를 오가지 않으려고 만든 것이다.

td_inspect와 다른 물건이다 — 저쪽은 파일 사이를 건너뛰는 역추적 탐색기고, 여기는
**파일 하나하나를 그대로 보여준다**("우리가 뭘 만들었는지"). 조인하지 않으므로
td_cards를 쓰지 않는다.

**생성물은 민감하다** — 카테고리명(사내 코드명)과 실명·인용이 한 파일에 인라인된다.
td_common.reject_public_path로 dist/ 출력을 막는다. 실명을 빼려면 --anonymize.

usage: python3 scripts/td_view.py <루트> [출력경로] [--anonymize]
"""
import json
import sys
from pathlib import Path

from pipeline_log import OUT_DIR
from td_common import load_json, reject_public_path

FILES = ("extracted", "taxonomy", "assignments", "aggregates")

# 디렉터리명 → 화면에 띄울 부서명. 없는 pjt는 디렉터리명 그대로 나온다.
PJT_LABELS = {
    # "pjt_a": "",
}


def find_projects(root):
    """<루트> 아래 pjt 디렉터리들. 산출물이 한 겹 더 들어가 있어도 찾는다.

    반환: [(이름, 산출물디렉터리), ...] 이름순. 산출물이 하나도 없는 디렉터리는 건너뛴다.
    """
    root = Path(root)
    found = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        # 바로 아래에 없으면 한 겹 안쪽(task_discovery/)까지만 본다
        cand = next((c for c in (d, d / "task_discovery")
                     if any((c / f"{n}.json").exists() for n in FILES)), None)
        if cand is not None:
            found.append((d.name, cand))
    return found


def _anon_map(extracted):
    """person_id → P0, P1 …. extracted 순서를 그대로 쓴다(재현 가능해야 대조가 된다)."""
    return {p.get("person_id"): f"P{i}" for i, p in enumerate(extracted or [])}


def _apply_anon(data, names):
    """실명이 담기는 자리만 치환한다. 인용(quotes/quote)은 원문이라 통째로 뺀다."""
    for person in data.get("extracted") or []:
        person["name"] = names.get(person.get("person_id"), "P?")
        for axis in ("future_task", "capability_have", "capability_gap"):
            for item in person.get(axis) or []:
                item["quotes"] = []
        if isinstance(person.get("direction"), dict):
            person["direction"]["quotes"] = []
    for row in data.get("assignments") or []:
        row["quote"] = ""
    return data


def collect(root, *, anonymize=False):
    """pjt별 산출물을 dict로 모은다. 없는 파일은 None으로 남긴다(있는 것만 그린다)."""
    projects = []
    for name, d in find_projects(root):
        data = {}
        for n in FILES:
            path = d / f"{n}.json"
            data[n] = load_json(path) if path.exists() else None
        if anonymize:
            data = _apply_anon(data, _anon_map(data.get("extracted")))
        projects.append({"name": name, "data": data})
    return projects


def build_html(projects):
    """자립형 HTML. 데이터는 JSON으로 인라인하고 렌더는 브라우저가 한다."""
    payload = [{"name": p["name"], "label": PJT_LABELS.get(p["name"], p["name"]),
                **p["data"]} for p in projects]
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return _TEMPLATE.replace("__DATA__", blob)


def write(root, out_path, *, anonymize=False):
    reject_public_path(out_path)
    projects = collect(root, anonymize=anonymize)
    if not projects:
        raise SystemExit(f"산출물이 있는 pjt 디렉터리를 못 찾았다: {root}")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_html(projects), encoding="utf-8")
    return out_path, projects


_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>산출물 뷰어</title>
<style>
  :root{
    --bg:#fff; --ink:#1f2328; --dim:#8b949e; --mid:#57606a;
    --line:#e6e8eb; --soft:#f6f7f8; --sel:#0969da;
    /* 색은 뜻이 있는 자리에만 — horizon 셋, readiness 셋 */
    --ac:#0969da;  --acbg:#ddf4ff;  --acln:#b6e3ff;
    --wn:#9a6700;  --wnbg:#fff8c5;  --wnln:#f2e5a0;
    --ok:#1a7f37;  --okbg:#dafbe1;  --okln:#aceebb;
    --vi:#8250df;  --vibg:#fbefff;  --viln:#e6cff5;
    --mono:"SFMono-Regular",Menlo,Consolas,"D2Coding","Courier New",monospace;
    --sans:"Pretendard","Apple SD Gothic Neo","Malgun Gothic",-apple-system,"Segoe UI",sans-serif;
  }
  *{box-sizing:border-box}
  body{margin:0;background:#f4f6f8;color:var(--ink);font-family:var(--sans);font-size:14px;
       line-height:1.6}

  header{position:sticky;top:0;z-index:5;background:rgba(255,255,255,.94);
         backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
  .strip{display:flex;align-items:center;gap:6px;padding:10px 16px;flex-wrap:wrap}
  .strip+.strip{border-top:1px solid var(--line)}
  .strip .sp{margin-left:auto}

  button{font-family:var(--sans);font-size:13px;color:var(--mid);background:var(--bg);
         border:1px solid var(--line);border-radius:99px;padding:5px 13px;cursor:pointer;
         transition:background .12s,color .12s,border-color .12s}
  button:hover:not(:disabled){background:var(--soft);color:var(--ink)}
  button[aria-current="true"]{background:var(--ac);border-color:var(--ac);color:#fff}
  button:disabled{color:#c9ced4;cursor:default}
  .tab{border:0;border-radius:0;padding:5px 2px;margin-right:18px;color:var(--dim);
       border-bottom:2px solid transparent;font-weight:600}
  .tab:hover:not(:disabled){background:none;color:var(--ink)}
  .tab[aria-selected="true"]{color:var(--ac);border-bottom-color:var(--ac)}
  .tab.f-taxonomy[aria-selected="true"]{color:var(--vi);border-bottom-color:var(--vi)}
  .tab.f-assignments[aria-selected="true"]{color:var(--wn);border-bottom-color:var(--wn)}
  .tab.f-aggregates[aria-selected="true"]{color:var(--ok);border-bottom-color:var(--ok)}

  input{font-family:var(--sans);font-size:13px;padding:5px 9px;border:1px solid var(--line);
        border-radius:4px;width:240px}
  input:focus{outline:2px solid var(--sel);outline-offset:-1px;border-color:var(--sel)}

  main{max-width:1000px;margin:0 auto;padding:16px 16px 90px}

  /* 항목 카드 — 접힌 줄만 보고, 필요할 때 편다 */
  .card{background:var(--bg);border:1px solid var(--line);border-radius:7px;margin-bottom:7px;
        transition:border-color .12s}
  .card:hover{border-color:#d5dbe1}
  .card>.hd{display:flex;align-items:baseline;gap:10px;padding:10px 16px;cursor:pointer;
            list-style:none}
  .card>.hd::-webkit-details-marker{display:none}
  .card>.hd:hover{background:var(--soft)}
  .card[open]>.hd{border-bottom:1px solid var(--line)}
  .idx{flex:none;display:inline-grid;place-items:center;width:22px;height:22px;border-radius:99px;
       font-family:var(--mono);font-size:11px;color:var(--tab);background:var(--tabbg);
       align-self:center}
  .ttl{font-weight:600}
  .hd .l{color:var(--mid);font-size:12.5px}
  .hd .r{margin-left:auto;font-family:var(--mono);font-size:11.5px;color:var(--dim);
         white-space:nowrap}
  .bd{padding:4px 22px 15px 26px}   /* 제목 줄보다 한 칸 들여쓴다 */

  .sec{font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;
       color:var(--mid);margin:14px 0 5px}
  .bd>.sec:first-child{margin-top:9px}
  .it{padding:4px 0 5px}
  .it+.it{border-top:1px dashed var(--line)}
  .bdg,.pill{display:inline-block;font-size:11px;border-radius:3px;padding:0 6px;
             border:1px solid var(--line);color:var(--mid);background:var(--soft)}
  .bdg{font-family:var(--mono);font-size:10.5px;margin-right:7px;vertical-align:1px}
  .pill{border-radius:11px}
  .t-a{color:var(--wn);background:var(--wnbg);border-color:var(--wnln)}   /* 단기 · 갭만 */
  .t-b{color:var(--ac);background:var(--acbg);border-color:var(--acln)}   /* 중기 · 선행 */
  .t-c{color:var(--vi);background:var(--vibg);border-color:var(--viln)}   /* 장기 */
  .t-d{color:var(--ok);background:var(--okbg);border-color:var(--okln)}   /* 이미 함 */
  .q{color:var(--mid);font-size:12.5px;padding-left:11px;border-left:2px solid var(--tabln);
     margin:3px 0 0}
  .src{font-family:var(--mono);font-size:11px;color:var(--dim);margin-top:2px}
  .p{margin:0 0 2px}

  .sec.ok{color:var(--ok)}
  .sec.wn{color:var(--wn)}
  .card[open]{border-color:var(--tabln)}
  .card[open]>.hd{background:var(--tabbg);border-bottom-color:var(--tabln)}

  /* 지금 보고 있는 파일이 화면의 강조색을 정한다 */
  .list{--tab:var(--ac);--tabbg:var(--acbg);--tabln:var(--acln)}
  .list.f-taxonomy{--tab:var(--vi);--tabbg:var(--vibg);--tabln:var(--viln)}
  .list.f-assignments{--tab:var(--wn);--tabbg:var(--wnbg);--tabln:var(--wnln)}
  .list.f-aggregates{--tab:var(--ok);--tabbg:var(--okbg);--tabln:var(--okln)}

  .chips{display:flex;flex-wrap:wrap;gap:5px}
  .chip{font-size:12px;border:1px solid var(--tabln);border-radius:12px;padding:1px 10px;
        color:var(--mid);background:var(--tabbg)}
  .chip b{font-family:var(--mono);font-weight:600;color:var(--ink)}

  table{border-collapse:collapse;width:100%;font-size:13px;background:var(--bg);
        border:1px solid var(--line);border-radius:7px;overflow:hidden}
  th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line)}
  th{background:var(--soft);font-family:var(--mono);font-size:10.5px;
     letter-spacing:.08em;text-transform:uppercase;color:var(--mid);font-weight:600;
     border-bottom-color:var(--line)}
  td.n,th.n{text-align:right;font-family:var(--mono)}
  th[title]{text-decoration:underline dotted var(--dim);text-underline-offset:3px;cursor:help}
  tbody tr:hover{background:var(--tabbg)}
  tbody tr:last-child td{border-bottom:0}

  .empty{color:var(--dim);padding:60px 0;text-align:center}
</style>
</head>
<body>
<header>
  <div class="strip" id="pjts"></div>
  <div class="strip">
    <div id="tabs" role="tablist"></div>
    <span class="sp"></span>
    <input type="search" id="q" placeholder="검색" spellcheck="false">
    <button id="exp">전체 펼치기</button>
    <button id="col">전체 접기</button>
  </div>
</header>
<main id="view"></main>

<script>
"use strict";
const DATA = __DATA__;
const FILES = ["extracted", "taxonomy", "assignments", "aggregates"];

let pi = 0, fi = 0, query = "";
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
const el = (cls, html) => {
  const d = document.createElement("div");
  if (cls) d.className = cls;
  if (html != null) d.innerHTML = html;
  return d;
};

/* 접히는 카드. 안쪽은 펼칠 때 만든다(200명이어도 첫 화면이 가볍게). */
function card(i, title, left, right, fill) {
  const d = document.createElement("details");
  d.className = "card";
  const hd = document.createElement("summary");
  hd.className = "hd";
  hd.innerHTML = `<span class="idx">${i}</span><span class="ttl">${esc(title)}</span>` +
                 `<span class="l">${esc(left)}</span><span class="r">${esc(right)}</span>`;
  const bd = el("bd");
  let built = false;
  d.ontoggle = () => { if (d.open && !built) { fill(bd); built = true; } };
  d.append(hd, bd);
  return d;
}

/* 값 → 색. 모르는 값이면 무채색으로 둔다(잘못 물들이는 것보단 낫다). */
const TONE = {"단기": "t-a", "중기": "t-b", "장기": "t-c",
              "갭만 있음": "t-a", "선행 신호": "t-b", "이미 함": "t-d"};
const tone = v => TONE[v] || "";

const quotes = qs => (qs || []).filter(Boolean)
  .map(q => `<div class="q">${esc(q)}</div>`).join("");
const items = list => (list || []).map(it =>
  `<div class="it">` +
  (it.horizon ? `<span class="bdg ${tone(it.horizon)}">${esc(it.horizon)}</span>` : "") +
  `${esc(it.text)}${quotes(it.quotes)}</div>`).join("");

/* ── 파일별 화면 ── */
function viewExtracted(list, box) {
  box.append(...list.map((p, i) => {
    const n = k => (p[k] || []).length;
    const right = p.signal_present === false ? "신호 없음"
      : `과제 ${n("future_task")} · 보유 ${n("capability_have")} · 부족 ${n("capability_gap")}`;
    const left = [p.part, p.cl_level].filter(Boolean).join(" · ");
    return card(i + 1, p.name, left, right, bd => {
      if (p.direction) bd.append(el("sec", "방향"),
        el("", `<div class="it">${esc(p.direction.text)}${quotes(p.direction.quotes)}</div>`));
      for (const [k, label, cls] of [["future_task", "미래 과제", ""],
                                     ["capability_have", "보유 역량", "ok"],
                                     ["capability_gap", "부족 역량", "wn"]])
        if (n(k)) bd.append(el(`sec ${cls}`, label), el("", items(p[k])));
    });
  }));
}

function viewTaxonomy(list, box) {
  box.append(...list.map((c, i) => card(i + 1, c.name, "", `관계 ${(c.relations || []).length}`, bd => {
    if (c.definition) bd.append(el("sec", "정의"), el("p", esc(c.definition)));
    if (c.inclusion_criteria) bd.append(el("sec", "포함 기준"), el("p", esc(c.inclusion_criteria)));
    if ((c.relations || []).length) bd.append(el("sec", "관계"), el("chips",
      c.relations.map(r => `<span class="chip">${esc(r.type)} → ${esc(r.to)}</span>`).join("")));
  })));
}

/* 배정은 카테고리로 묶어야 읽힌다 — 건수 많은 것부터 */
function viewAssignments(list, box) {
  const groups = new Map();
  for (const a of list) {
    const k = a.category || "—";
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(a);
  }
  box.append(...[...groups].sort((a, b) => b[1].length - a[1].length)
    .map(([cat, rows], i) => card(i + 1, cat, "", `${rows.length}건`, bd =>
      bd.append(el("", rows.map(r =>
        `<div class="it">${esc(r.text)}${quotes([r.quote])}` +
        `<div class="src">${esc(r.axis)} · #${esc(r.person_id)}</div></div>`).join(""))))));
}

function viewAggregates(obj, box) {
  const cats = obj.categories || [], minor = obj.minority || [];
  if (cats.length) {
    const t = document.createElement("table");
    t.innerHTML =
      `<thead><tr><th>카테고리</th>` +
      `<th class="n" title="배정된 서로 다른 사람 수. 한 사람이 여러 건이어도 1">인원</th>` +
      `<th class="n" title="capability_have 축 배정 건수 — 사람 수가 아니라 서술 건수다">확보</th>` +
      `<th class="n" title="capability_gap 축 배정 건수 — 사람 수가 아니라 서술 건수다">미확보</th>` +
      `<th title="인원 2 이하면 선행 신호, 아니면 미확보>확보일 때 갭만 있음, 그 외 이미 함">판정</th>` +
      `<th class="n" title="이 카테고리를 언급한 서로 다른 pjt 수">pjt</th>` +
      `<th class="n" title="이 카테고리를 언급한 서로 다른 CL 수">CL</th></tr></thead>` +
      `<tbody>` + cats.map(c =>
        `<tr><td>${esc(c.name)}</td><td class="n">${esc(c.people)}</td>` +
        `<td class="n">${esc(c.have)}</td><td class="n">${esc(c.gap)}</td>` +
        `<td><span class="pill ${tone(c.readiness)}">${esc(c.readiness)}</span></td>` +
        `<td class="n">${esc(c.pjt_spread)}</td>` +
        `<td class="n">${esc(c.cl_spread)}</td></tr>`).join("") + `</tbody>`;
    box.append(el("sec", `카테고리 ${cats.length}`), t);
  }
  if (minor.length) box.append(el("sec", `소수 의견 ${minor.length}`), el("chips",
    minor.map(m => `<span class="chip">${esc(m.name)} <b>${esc(m.people)}</b></span>`).join("")));
}

const VIEWS = {extracted: viewExtracted, taxonomy: viewTaxonomy,
               assignments: viewAssignments, aggregates: viewAggregates};

/* ── 검색: 최상위 배열의 항목만 걸러낸다 ── */
function filtered(val, q) {
  if (!q) return val;
  const has = x => JSON.stringify(x).toLowerCase().includes(q);
  if (Array.isArray(val)) return val.filter(has);
  const out = {};
  for (const [k, v] of Object.entries(val)) out[k] = Array.isArray(v) ? v.filter(has) : v;
  return out;
}

/* ── 상단 ── */
function initHeader() {
  $("pjts").replaceChildren(...DATA.map((p, i) => {
    const b = document.createElement("button");
    b.textContent = p.label || p.name;
    b.onclick = () => { pi = i; render(); };
    return b;
  }));
  $("tabs").replaceChildren(...FILES.map((name, i) => {
    const b = document.createElement("button");
    b.className = `tab f-${name}`;
    b.textContent = name;
    b.setAttribute("role", "tab");
    b.onclick = () => { fi = i; render(); };
    return b;
  }));
  $("q").oninput = e => { query = e.target.value.trim().toLowerCase(); render(); };
  const all = want => $("view").querySelectorAll("details.card").forEach(d => d.open = want);
  $("exp").onclick = () => all(true);
  $("col").onclick = () => all(false);
}

function render() {
  const p = DATA[pi];
  [...$("pjts").children].forEach((b, i) => b.setAttribute("aria-current", String(i === pi)));
  if (!p[FILES[fi]]) {
    const alt = FILES.findIndex(k => p[k]);
    if (alt >= 0 && alt !== fi) { fi = alt; return render(); }
  }
  [...$("tabs").children].forEach((b, i) => {
    const empty = !p[FILES[i]];
    b.disabled = empty;
    b.setAttribute("aria-selected", String(i === fi && !empty));
  });

  const val = p[FILES[fi]];
  if (val == null) {
    $("view").replaceChildren(el("empty", `${esc(p.name)} · ${FILES[fi]}.json 없음`));
    return;
  }
  const shown = filtered(val, query);
  const box = el(`list f-${FILES[fi]}`);
  VIEWS[FILES[fi]](shown, box);
  $("view").replaceChildren(box);
  scrollTo({top: 0});
}

addEventListener("keydown", e => {
  if (e.target.matches("input")) return;
  if (e.key === "ArrowRight" && pi < DATA.length - 1) { pi++; render(); }
  if (e.key === "ArrowLeft"  && pi > 0)               { pi--; render(); }
});

initHeader();
render();
</script>
</body>
</html>
"""


def main(*argv):
    """pjt 루트 → 뷰어 HTML.

      td_view.py <루트> [출력경로] [--anonymize]
    """
    args = [a for a in argv if a != "--anonymize"]
    anonymize = "--anonymize" in argv
    if not args:
        raise SystemExit(__doc__.strip().splitlines()[-1])
    root = Path(args[0])
    out = Path(args[1]) if len(args) > 1 else OUT_DIR / "task_discovery" / "view.html"
    out, projects = write(root, out, anonymize=anonymize)
    # 카테고리명·실명은 찍지 않는다 — 이름과 건수만.
    names = ", ".join(p["name"] for p in projects)
    print(f"뷰어 → {out} ({out.stat().st_size // 1024}kb) · pjt {len(projects)}개: {names}",
          file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
