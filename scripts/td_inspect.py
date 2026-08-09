"""task-discovery 산출물 역추적 탐색기 (S6-1, #39).

산출물 넷(extracted·taxonomy·assignments·aggregates)을 자립형 HTML 한 장으로 만든다.
목적은 파일을 예쁘게 보여주는 게 아니라 **파일 사이를 건너뛰는 것**이다 — 회의에서 나오는
질문("17명이 누구야", "그 사람 원문 띄워봐")은 대부분 파일 하나 안에서 답이 안 나온다.

조인은 td_cards가 한다. 여기는 그 위에 카테고리 정의(taxonomy)를 얹어 화면 데이터를
만들고 렌더할 뿐이다. 회고 원문은 아직 안 싣는다 — 원문 펼치기는 #40.

**생성물은 민감하다** — 카테고리명(레벨 2)과 실명·인용(레벨 3)이 한 파일에 인라인된다.
출력은 TD_OUT_DIR 아래로만. dist/는 GitHub Pages로 공개되므로 _reject_public_path가
그쪽 경로를 아예 거부한다(docstring만으로는 지켜지지 않아서).
"""
import json
import sys
from pathlib import Path

import td_cards
import td_render
from pipeline_log import OUT_DIR
from td_common import load_json



def build_payload(aggregates, persons, assignments, taxonomy=None, *, anonymize=False):
    """화면이 필요한 것 전부를 하나의 dict로. 순수 함수 — 파일을 쓰지 않는다.

    aggregates에는 카테고리 정의가 없고(집계는 이름만 들고 온다) taxonomy에만 있다.
    Other처럼 taxonomy에 없는 카테고리도 목록에서 빠지면 안 되므로 빈 정의로 채운다.
    """
    aggregates = load_json(aggregates)
    persons = load_json(persons)
    assignments = load_json(assignments)
    taxonomy = load_json(taxonomy) if taxonomy is not None else []

    taxo = {c["name"]: c for c in taxonomy}
    categories = []
    for c in aggregates["categories"]:
        t = taxo.get(c["name"], {})
        categories.append({**c,
                           "definition": t.get("definition", ""),
                           "inclusion_criteria": t.get("inclusion_criteria", ""),
                           "relations": t.get("relations", [])})

    cards = td_cards.build(assignments, persons, anonymize=anonymize)

    # 회고 원문은 싣지 않는다 — 이 화면이 쓰지 않고(원문 펼치기는 #40), 미리 넣으면
    # 파일만 무거워지는데다 원문 안의 실명은 익명화로 지울 수 없어 구멍이 된다.
    people = [{"person_id": p["person_id"],
               "name": f"P{p['person_id']}" if anonymize else p.get("name"),
               "pjt": p.get("pjt"), "cl_level": p.get("cl_level"),
               "signal_present": bool(p.get("signal_present"))} for p in persons]

    return {
        "categories": categories,
        "cards": cards,
        "persons": people,
        "horizon": td_cards.horizon_distribution(cards),
        "coverage": td_render.coverage(persons, assignments),
        "anonymized": anonymize,
    }


def _embed(payload):
    """</script>가 데이터에 있어도 HTML이 깨지지 않게 이스케이프. JSON 문자열 안에서
    \\u003c는 <와 같으므로 파서에는 영향이 없고, HTML 파서만 태그로 오인하지 않게 된다."""
    return (json.dumps(payload, ensure_ascii=False)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def render_html(payload):
    return _TEMPLATE.replace("__PAYLOAD__", _embed(payload))


def _reject_public_path(out_path):
    """dist/ 아래로는 쓰지 못하게 막는다 — 그 디렉터리는 GitHub Pages로 배포 추적되므로
    실명·인용이 박힌 파일이 들어가면 공개된다. 규칙을 주석으로만 두면 오타 한 번에 깨진다."""
    if "dist" in Path(out_path).resolve().parts:
        raise ValueError("dist/ 아래에는 쓸 수 없다 — 배포 추적 경로다. TD_OUT_DIR을 써라")


def write(aggregates, persons, assignments, taxonomy=None, *, out_path, anonymize=False):
    _reject_public_path(out_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload(aggregates, persons, assignments, taxonomy, anonymize=anonymize)
    out_path.write_text(render_html(payload), encoding="utf-8")
    return out_path


# ponytail: HTML을 파이썬 문자열 상수로 들고 있다. build.py는 archive/template.html을
# 읽어 토큰 치환하는데, 여기선 파일 하나로 끝나는 쪽을 택했다(스테이지 스크립트가
# 별도 asset 디렉터리에 의존하지 않게). 화면이 두 번째로 늘거나 이 상수가 400줄을
# 넘으면 build.py 방식으로 옮길 것.
_TEMPLATE = """<!doctype html>
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

  header{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;
         padding:12px 20px;border-bottom:1px solid var(--line);background:var(--panel)}
  header h1{font-size:15px;margin:0;font-weight:650}
  .cov{margin-left:auto;display:flex;gap:14px;font-size:12px;color:var(--dim);flex-wrap:wrap}
  .cov b{color:var(--ink);font-weight:650}

  main{display:flex;align-items:stretch;min-height:calc(100vh - 46px)}
  #list{width:330px;flex:none;border-right:1px solid var(--line);background:var(--panel);
        overflow-y:auto;max-height:calc(100vh - 46px)}
  #detail{flex:1;min-width:0;padding:22px 26px;overflow-y:auto;max-height:calc(100vh - 46px)}

  .row{padding:10px 16px;border-bottom:1px solid var(--line);cursor:pointer}
  .row:hover{background:var(--soft)}
  .row.on{background:var(--soft);box-shadow:inset 3px 0 0 var(--ink)}
  .row .nm{font-weight:600;font-size:13.5px;display:flex;gap:8px;align-items:baseline}
  .row .nm .cnt{margin-left:auto;color:var(--dim);font-weight:400;font-size:12px}
  .row .meta{font-size:11.5px;color:var(--dim);margin-top:3px}

  .dot{width:7px;height:7px;border-radius:99px;flex:none;display:inline-block}
  .r0{background:var(--ready)} .r1{background:var(--gapc)} .r2{background:var(--seed)}

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

  .ax-future_task{color:var(--gapc)} .ax-capability_gap{color:var(--warn)}
  .ax-capability_have{color:var(--ready)} .ax-direction{color:var(--seed)}

  .rel{font-size:13px;margin:4px 0;color:var(--dim)}
  .rel b{color:var(--ink);font-weight:600}
  .empty{color:var(--dim);padding:60px 0;text-align:center;font-size:13.5px}
  .note{font-size:11.5px;color:var(--warn);margin-top:2px}
</style>
</head>
<body>

<header>
  <h1>산출물 탐색기</h1>
  <span id="anon" style="font-size:12px;color:var(--dim)"></span>
  <div class="cov" id="cov"></div>
</header>

<main>
  <div id="list"></div>
  <div id="detail"><div class="empty">왼쪽에서 카테고리를 고르세요</div></div>
</main>

<script>
const DATA = __PAYLOAD__;

const AX_LABEL = {future_task:"과제", capability_gap:"갭", capability_have:"보유", direction:"방향"};
const READINESS = {"이미 함":{cls:"r0", color:"--ready"},
                   "갭만 있음":{cls:"r1", color:"--gapc"},
                   "선행 신호":{cls:"r2", color:"--seed"}};
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const esc = s => String(s == null ? "" : s)
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");

// 카드를 카테고리별로 미리 묶어둔다
const BY_CAT = {};
for (const c of DATA.cards) (BY_CAT[c.category] = BY_CAT[c.category] || []).push(c);

// 커버리지 배지
const cv = DATA.coverage;
// flex gap은 텍스트 노드엔 안 먹는다 — 항목마다 span으로 감싸야 간격이 생긴다
document.getElementById("cov").innerHTML = [
  `대상 <b>${cv.total_people}</b>명`,
  `무신호 <b>${cv.no_signal}</b> (${Math.round(cv.no_signal_rate*100)}%)`,
  `배정 <b>${cv.assignments}</b>건`,
  `Other <b>${cv.other}</b> (${Math.round(cv.other_rate*100)}%)`,
].map(s => `<span>${s}</span>`).join("");
if (DATA.anonymized) document.getElementById("anon").textContent = "익명 표기";

let sel = null;

function renderList(){
  document.getElementById("list").innerHTML = DATA.categories.map((c,i) => `
    <div class="row ${sel===c.name?"on":""}" data-i="${i}">
      <div class="nm">
        <span class="dot ${(READINESS[c.readiness]||{}).cls||""}"></span>
        <span>${esc(c.name)}</span>
        <span class="cnt">${c.people}명</span>
      </div>
      <div class="meta">pjt ${c.pjt_spread} · cl ${c.cl_spread} · 보유 ${c.have} / 갭 ${c.gap}</div>
    </div>`).join("");
  for (const el of document.querySelectorAll(".row"))
    el.addEventListener("click", () => select(DATA.categories[+el.dataset.i].name));
}

function select(name){
  sel = name;
  const c = DATA.categories.find(x => x.name === name);
  const cards = BY_CAT[name] || [];
  const h = DATA.horizon[name];

  const groups = ["future_task","capability_gap","capability_have","direction"]
    .map(ax => [ax, cards.filter(k => k.axis === ax)])
    .filter(([,ks]) => ks.length);

  document.getElementById("detail").innerHTML = `
    <h2>${esc(c.name)}<span class="badge" style="background:${css((READINESS[c.readiness]||{}).color||"--dim")}"
      >${esc(c.readiness)}</span></h2>
    ${c.definition ? `<p class="def">${esc(c.definition)}</p>` : ``}
    ${c.inclusion_criteria ? `<p class="def">포함 기준 — ${esc(c.inclusion_criteria)}</p>` : ``}
    <div class="nums">
      <div><b>${c.people}</b>기여 인원</div>
      <div><b>${c.pjt_spread} / ${c.cl_spread}</b>확산도 pjt / cl</div>
      <div><b>${c.have}</b>보유 언급</div>
      <div><b>${c.gap}</b>갭 언급</div>
      ${h ? `<div><b>${h["단기"]} / ${h["장기"]} / ${h["불명"]}</b>과제 시간 단기 / 장기 / 불명</div>` : ``}
    </div>
    ${(c.pjts||[]).length ? `<div class="def">${esc((c.pjts||[]).join(" · "))} — ${esc((c.cls||[]).join(" · "))}</div>` : ``}
    ${groups.map(([ax,ks]) => `
      <div class="lbl">${AX_LABEL[ax]} ${ks.length}건</div>
      ${ks.map(k => `
        <div class="card">
          <div class="ax ax-${ax}">${AX_LABEL[ax]}${k.horizon ? " · " + esc(k.horizon) : ""}</div>
          <p class="tx">${esc(k.text)}</p>
          ${k.quote ? `<blockquote>${esc(k.quote)}</blockquote>` : ``}
          <div class="who">${esc(k.name || "(알 수 없음)")}${
            k.pjt ? " · " + esc(k.pjt) : ""}${k.cl_level ? " · " + esc(k.cl_level) : ""}</div>
        </div>`).join("")}`).join("")}
    ${(c.relations||[]).length ? `
      <div class="lbl">관련 카테고리</div>
      ${c.relations.map(r => `<div class="rel"><b>${esc(r.type)}</b> ${esc(r.to)}</div>`).join("")}
      <div class="note">taxonomy에서 그대로 — LLM 재검증 없음</div>` : ``}
    ${cards.length ? `` : `<div class="empty">이 카테고리에 배정된 항목이 없습니다</div>`}
  `;
  renderList();
  document.getElementById("detail").scrollTop = 0;
}

renderList();
</script>
</body>
</html>
"""


def main(*argv):
    """산출물 디렉터리 → 탐색기 HTML. 출력 기본값은 TD_OUT_DIR 안 — 리포에 쓰지 않는다.

      td_inspect.py [데이터디렉터리] [출력경로] [--anonymize]
    """
    args = [a for a in argv if a != "--anonymize"]
    anonymize = "--anonymize" in argv
    d = Path(args[0]) if len(args) > 0 else OUT_DIR / "task_discovery"
    out = Path(args[1]) if len(args) > 1 else d / "inspect.html"
    taxonomy = d / "taxonomy.json"
    res = write(d / "aggregates.json", d / "extracted.json", d / "assignments.json",
                taxonomy if taxonomy.exists() else None, out_path=out, anonymize=anonymize)
    # 카테고리명·실명은 찍지 않는다 — 건수만.
    print(f"탐색기 → {res} ({res.stat().st_size // 1024}kb)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
