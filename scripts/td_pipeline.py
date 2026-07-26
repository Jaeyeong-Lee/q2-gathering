"""task-discovery 파이프라인 배선 (S1-7, #22).

6 스테이지를 순서대로 잇는다: sources→extract→taxonomy→assign→aggregate→render.
중간 산출물이 있으면 건너뛴다(재실행 시 LLM 호출 0). 강제 재실행은 force=True.
모델 이원화는 여기 call site에서: 유도=큰 모델, 배정=작은 모델을 서로 다른 call로 주입
(스테이지 스키마는 그대로 — seam은 각 스테이지의 call 하나). 순차 루프 + 재시도 +
파일 영속화로 충분 — 오케스트레이션 프레임워크·멀티에이전트 미도입.
"""
import sys
from pathlib import Path

from pipeline_log import get_logger

import td_aggregate
import td_assign
import td_extract
import td_render
import td_sources
import td_taxonomy

ROOT = Path(__file__).parent.parent
log = get_logger("td_pipeline")


def run_all(data_dir, *, extract_call, taxo_call=None, assign_call=None,
            n=200, seed=0, batch_size=30, force=False, sleep=None):
    """전 스테이지 실행. taxo_call/assign_call 미지정 시 extract_call 재사용."""
    taxo_call = taxo_call or extract_call
    assign_call = assign_call or extract_call
    d = Path(data_dir)
    d.mkdir(parents=True, exist_ok=True)
    p = {name: d / f"{name}.json" for name in
         ("sources", "extracted", "taxonomy", "assignments", "aggregates")}
    workshop = d / "workshop-input.md"

    def need(path):
        return force or not Path(path).exists()

    if need(p["sources"]):
        td_sources.write(p["sources"], n=n, seed=seed)
    ex_summary = {"failed": [], "dropped": []}
    if need(p["extracted"]):
        ex_summary = td_extract.run_extract(p["sources"], p["extracted"], extract_call, sleep=sleep)
    if need(p["taxonomy"]):
        td_taxonomy.induce(p["extracted"], p["taxonomy"], taxo_call,
                           batch_size=batch_size, sleep=sleep)
    as_summary = {"dropped": []}
    if need(p["assignments"]):
        as_summary = td_assign.assign(p["extracted"], p["taxonomy"], p["assignments"],
                                      assign_call, sleep=sleep)
    if need(p["aggregates"]):
        td_aggregate.aggregate(p["assignments"], p["extracted"], p["aggregates"])
    if need(workshop):
        td_render.write(p["aggregates"], p["extracted"], p["assignments"], workshop,
                        failed=ex_summary["failed"],
                        extract_dropped=len(ex_summary["dropped"]),
                        assign_dropped=len(as_summary["dropped"]))
    log.info(f"파이프라인 완료 → {workshop}")
    return {**{k: str(v) for k, v in p.items()}, "workshop": str(workshop)}


def main(data_dir=ROOT / "data" / "task_discovery"):
    """실 LLM 실행. 유도=큰 모델, 배정=작은 모델(환경변수로 구성)."""
    import llm
    llm.init()
    # 모델 이원화: 필요 시 배정용 작은 모델을 별도 call로. 기본은 동일 call.
    run_all(data_dir, extract_call=llm.call_gemini, taxo_call=llm.call_gemini,
            assign_call=llm.call_gemini)


if __name__ == "__main__":
    main(*sys.argv[1:])
