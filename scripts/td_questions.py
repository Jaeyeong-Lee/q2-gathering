"""질문 카드 — 집계에서 워크숍 아젠다를 뽑는다 (#019).

규칙 몇 개로 논의 질문을 만든다. **LLM 0회** — 결정적이라 "왜 이 질문이 나왔나"에
집계 수치로 답할 수 있다. 그림 넷보다 질문 열 개가 회의를 굴린다.

각 질문에는 그것을 만들어낸 근거 수치가 반드시 붙는다. 근거 없는 질문은 아젠다가 아니라
잔소리다. 질문만 만들고 답은 하지 않는다 — 답은 워크숍에서 사람이 채운다.

usage: python3 scripts/td_questions.py [데이터디렉터리] [출력경로]
"""
import sys
from pathlib import Path

import td_render_common
from td_common import load_json

ROOT = Path(__file__).parent.parent

# 소수의견 판정 기준 (td_aggregate.WEAK와 같은 값)
WEAK = 2


def build_payload(agg):
    """aggregates.json → 질문 카드 목록. 파일을 읽지 않는 순수 함수."""
    cats = agg.get("categories", [])
    if not cats:
        return {"questions": [], "totals": {"n": 0, "cats": 0}}

    ordered = sorted(cats, key=lambda c: -c.get("people", 0))
    top = ordered[:3]
    questions = []

    for c in top:                                   # 규칙 1: 가장 넓게 나온 것
        questions.append({
            "kind": "가장 넓게 나온 것",
            "q": f"{c['name']} — 이렇게 많은 사람이 말했는데 왜 아직 안 되고 있나?",
            "why": "여러 조직·직급에서 반복해 나왔다. 합의가 아니라 미해결의 신호일 수 있다.",
            "evidence": [f"{c.get('people', 0)}명이 언급",
                         f"{c.get('pjt_spread', 0)}개 조직",
                         f"{c.get('cl_spread', 0)}개 직급"],
            "cat": c["name"],
        })

    for c in [x for x in cats if x.get("pjt_spread", 0) <= 1][:3]:   # 규칙 2: 한 조직만
        questions.append({
            "kind": "한 조직만 본 것",
            "q": f"{c['name']} — 한 조직에서만 나왔다. 선견인가, 그 조직의 사정인가?",
            "why": "확산도가 낮다는 것은 중요하지 않다는 뜻이 아니다. 아직 안 퍼졌다는 뜻이다.",
            "evidence": [f"{c.get('pjt_spread', 0)}개 조직", f"{c.get('people', 0)}명이 언급"],
            "cat": c["name"],
        })

    for c in [x for x in cats if x.get("gap", 0) > 0 and x.get("have", 0) == 0][:4]:
        questions.append({                          # 규칙 3: 갭만 있고 보유가 없다
            "kind": "하겠다는데 할 사람이 없는 것",
            "q": f"{c['name']} — 갭은 {c.get('gap', 0)}건인데 보유는 0건이다. 누가 이걸 하나?",
            "why": "필요하다고 말한 사람은 있는데 할 수 있다고 말한 사람이 없다. "
                   "채용·육성·외주 중 무엇으로 메울지는 데이터가 답하지 않는다.",
            "evidence": [f"갭 {c.get('gap', 0)}건", "보유 0건",
                         f"{c.get('readiness', '')}"],
            "cat": c["name"],
        })

    for c in [x for x in cats if x.get("have", 0) > 0 and x.get("gap", 0) > 0][:3]:
        questions.append({                          # 규칙 4: 보유와 갭이 공존
            "kind": "되는 사람과 안 되는 사람이 갈리는 것",
            "q": f"{c['name']} — 보유 {c.get('have', 0)}건과 갭 {c.get('gap', 0)}건이 같이 있다. "
                 "왜 누구는 되고 누구는 안 되나?",
            "why": "역량이 조직 안에 있는데 퍼지지 않았다는 신호다. 이전 가능한 격차인지 본다.",
            "evidence": [f"보유 {c.get('have', 0)}건", f"갭 {c.get('gap', 0)}건",
                         f"{c.get('people', 0)}명이 언급"],
            "cat": c["name"],
        })

    minority = agg.get("minority", [])
    if minority:                                    # 규칙 5: 소수의견 트랙
        questions.append({
            "kind": "소수의견",
            "q": f"{len(minority)}개 주제가 {WEAK}명 이하에서만 나왔다. 이 중 버릴 것과 "
                 "지켜볼 것을 어떻게 가르나?",
            "why": "다수결로 지우면 약한 신호가 먼저 사라진다. 무엇을 남길지는 사람이 정한다.",
            "evidence": [f"소수의견 {len(minority)}개"],
            "cat": None,
        })

    return {"questions": questions,
            "totals": {"n": len(questions), "cats": len(cats)}}


def write(agg, *, out_path):
    return td_render_common.write_html(
        td_render_common.render(_TEMPLATE, build_payload(agg)), out_path)


def main(*argv):
    d, out, _ = td_render_common.parse_args(argv, "questions.html")
    payload_src = load_json(d / "aggregates.json")
    res = write(payload_src, out_path=out)
    n = len(build_payload(payload_src)["questions"])
    print(f"질문 카드 → {res} ({n}개 · LLM 0회)", file=sys.stderr)


_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>질문 카드 — 그래서 뭘 논의하나</title>
<style>
  :root { --bg:#faf9f7; --ink:#16181d; --dim:#767d8c; --line:#e2e0dc; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); padding:44px 40px 72px;
         font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif; }
  .wrap { max-width:960px; margin:0 auto; }
  .lbl { font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:var(--dim); }
  h1 { font-size:27px; margin:6px 0 10px; font-weight:650; letter-spacing:-.01em; }
  .intro { font-size:13.5px; color:#454b57; line-height:1.75; max-width:640px;
           border-bottom:1px solid var(--line); padding-bottom:22px; }
  .card { background:#fff; border:1px solid var(--line); border-radius:9px; padding:20px 22px;
          margin-top:16px; }
  .kind { font-size:10px; letter-spacing:.12em; text-transform:uppercase; color:#b45309;
          font-weight:650; }
  .q { font-size:17px; line-height:1.55; margin:8px 0 10px; font-weight:600; letter-spacing:-.005em; }
  .why { font-size:12.5px; color:#5b6270; line-height:1.7; }
  .ev { margin-top:13px; display:flex; gap:7px; flex-wrap:wrap; }
  .ev span { font-size:11px; font-family:ui-monospace,SFMono-Regular,monospace; color:#3b4252;
             background:#f1efec; border:1px solid var(--line); border-radius:99px; padding:3px 10px; }
  .foot { margin-top:34px; padding-top:20px; border-top:1px solid var(--line);
          font-size:12px; color:var(--dim); line-height:1.8; }
</style>
</head>
<body>
<div class="wrap">
  <div class="lbl">task-discovery · 워크숍 아젠다</div>
  <h1>그래서 뭘 논의하나</h1>
  <div class="intro">집계에서 규칙으로 뽑은 질문이다. LLM은 쓰지 않았고, 각 질문에는 그것을
    만들어낸 수치가 붙어 있다. <b>질문만 만들고 답은 하지 않는다</b> — 답은 이 자리에 모인
    사람이 채운다.</div>
  <div id="cards"></div>
  <div class="foot" id="foot"></div>
</div>
<script>
const D = __PAYLOAD__;
document.getElementById("cards").innerHTML = D.questions.map(q => `
  <div class="card">
    <div class="kind">${q.kind}</div>
    <div class="q">${q.q}</div>
    <div class="why">${q.why}</div>
    <div class="ev">${q.evidence.filter(Boolean).map(e => `<span>${e}</span>`).join("")}</div>
  </div>`).join("") ||
  `<div class="card"><div class="q">규칙에 걸리는 카테고리가 없다</div>
   <div class="why">집계가 비었거나 모든 카테고리가 고르게 분포한 상태다. 빈 목록도 정상이다.</div></div>`;
document.getElementById("foot").textContent =
  `카테고리 ${D.totals.cats}개에서 질문 ${D.totals.n}개. 규칙: 확산도 상위 / 한 조직만 / ` +
  `갭만 있음 / 보유·갭 공존 / 소수의견.`;
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main(*sys.argv[1:])
