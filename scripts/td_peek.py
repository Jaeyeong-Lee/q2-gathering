"""task-discovery 상태 확인 창구 — 본문·이름을 절대 출력하지 않는다.

내부망에선 실데이터(실명·회고 원문)와 카테고리명(사내 제품 코드명)이 에이전트 컨텍스트에
들어가면 안 된다. 그래서 산출물을 직접 열어보는 대신 이 스크립트로 **건수·진행률·바이트
통계만** 본다. 카테고리는 이름 대신 인덱스(#1, #2...)로 부른다.

여기에 이름·본문을 출력하는 코드를 추가하지 마라 — 그 경로가 없다는 게 이 모듈의 목적이다.

usage: python3 scripts/td_peek.py [data_dir]     (기본: data/task_discovery)
       TD_OUT_DIR 이 설정돼 있으면 로그·콜덤프는 거기서 읽는다.
"""
import json
import sys
from collections import Counter
from pathlib import Path

from pipeline_log import ECS_LOG_PATH
from td_common import CALLS_DIR

ROOT = Path(__file__).parent.parent


def _load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def artifacts(d):
    """산출물 건수·진행률. 레벨 0 — 개인정보도 사업정보도 없다."""
    out = []
    extracted = _load(d / "extracted.json")
    if extracted is not None:
        no_signal = sum(1 for p in extracted if not p.get("signal_present"))
        out.append(f"extracted.json      {len(extracted)}건  무신호 {no_signal}건")

    taxonomy = _load(d / "taxonomy.json")
    if taxonomy is not None:
        edges = sum(len(c.get("relations") or []) for c in taxonomy)
        with_rel = sum(1 for c in taxonomy if c.get("relations"))
        out.append(f"taxonomy.json       {len(taxonomy)}건  relations {edges}엣지 / {with_rel}개 카테고리")

    assignments = _load(d / "assignments.json")
    if assignments is not None:
        other = sum(1 for a in assignments if a.get("category") == "Other")
        pct = f"{other / len(assignments):.1%}" if assignments else "0%"
        out.append(f"assignments.json    {len(assignments)}건  Other {other}건({pct})")

    for name, done_key, total_key in (("taxonomy", "batches_done", "total_batches"),
                                      ("assignments", "processed", "total_facets")):
        progress = _load(d / f"{name}.progress.json")
        if progress:
            done, total = progress.get(done_key), progress.get(total_key)
            mark = "완료" if done == total else "미완 — 재실행하면 이어감"
            out.append(f"진행률 {name:<12} {done}/{total}  {mark}")
    return out


def aggregates(d):
    """카테고리별 집계. 레벨 1 — 이름 없이 인덱스와 숫자만."""
    agg = _load(d / "aggregates.json")
    if agg is None:
        return []
    rows = [f"{'':<5}{'인원':>5}{'pjt':>5}{'cl':>4}{'보유':>5}{'갭':>5}  준비도"]
    for i, c in enumerate(agg.get("categories", []), start=1):
        rows.append(f"#{i:<4}{c['people']:>5}{c['pjt_spread']:>5}{c['cl_spread']:>4}"
                    f"{c['have']:>5}{c['gap']:>5}  {c['readiness']}")
    rows.append(f"소수의견 트랙 {len(agg.get('minority', []))}개")
    return rows


def llm_calls(ecs_path=None):
    """ECS 로그에서 스테이지별 성공/실패와 바이트 분포. 페이로드 한도 진단용 —
    바이트 수는 민감하지 않다."""
    ecs_path = Path(ecs_path) if ecs_path else ECS_LOG_PATH
    if not ecs_path.exists():
        return [f"(ECS 로그 없음: {ecs_path})"]

    stats = {}
    for line in ecs_path.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        req, resp = rec.get("http.request.body.bytes"), rec.get("http.response.body.bytes")
        if req is None and resp is None:
            continue
        s = stats.setdefault(rec.get("service.name", "?"),
                             {"ok": 0, "fail": 0, "req": 0, "resp": 0, "errors": Counter()})
        if rec.get("log.level") == "INFO":
            s["ok"] += 1
        else:
            s["fail"] += 1
            if rec.get("error.type"):
                s["errors"][rec["error.type"]] += 1
        s["req"] = max(s["req"], req or 0)
        s["resp"] = max(s["resp"], resp or 0)

    if not stats:
        return ["(호출 기록 없음)"]
    rows = [f"{'stage':<12}{'성공':>6}{'실패':>6}{'요청최대':>11}{'응답최대':>11}  에러"]
    for name, s in sorted(stats.items()):
        errs = ", ".join(f"{k}×{v}" for k, v in s["errors"].items())
        rows.append(f"{name:<12}{s['ok']:>6}{s['fail']:>6}"
                    f"{s['req'] / 1024:>10.1f}k{s['resp'] / 1024:>10.1f}k  {errs}")
        if s["resp"] >= 20 * 1024:
            rows.append(f"{'':<12}  ⚠ 응답이 20kb 이상 — 출력 한도 의심")
    return rows


def failures(calls_dir=None):
    """ABNORMAL 디렉터리에 남은 최종 실패 콜. 파일명(call_id)만 — 내용은 안 읽는다."""
    calls_dir = Path(calls_dir) if calls_dir else CALLS_DIR
    if not calls_dir.exists():
        return [f"(콜 덤프 없음: {calls_dir})"]
    rows = []
    for stage_dir in sorted(calls_dir.iterdir()):
        abnormal = stage_dir / "ABNORMAL"
        if not abnormal.is_dir():
            continue
        ids = sorted({p.name.split("_")[0] for p in abnormal.glob("*_input.json")})
        if ids:
            rows.append(f"{stage_dir.name}: {len(ids)}건 — call_id {', '.join(ids)}")
    return rows or ["실패 없음"]


def report(data_dir):
    d = Path(data_dir)
    lines = ["[산출물]", *(artifacts(d) or ["(없음)"]),
             "", "[집계]  ※ 카테고리는 인덱스로만", *(aggregates(d) or ["(없음)"]),
             "", "[LLM 호출]", *llm_calls(),
             "", "[최종 실패]", *failures()]
    return "\n".join(lines)


def main(data_dir=ROOT / "data" / "task_discovery"):
    print(report(data_dir))


if __name__ == "__main__":
    main(*sys.argv[1:])
