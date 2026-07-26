"""task-discovery 파이프라인 배선 (S1-7, #22).

6 스테이지를 순서대로 잇는다: sources→extract→taxonomy→assign→aggregate→render.
중간 산출물이 있으면 건너뛴다(재실행 시 LLM 호출 0). 강제 재실행은 force=True.
모델 이원화는 여기 call site에서: 유도=큰 모델, 배정=작은 모델을 서로 다른 call로 주입
(스테이지 스키마는 그대로 — seam은 각 스테이지의 call 하나). 순차 루프 + 재시도 +
파일 영속화로 충분 — 오케스트레이션 프레임워크·멀티에이전트 미도입.
"""
import json
import sys
from pathlib import Path

from pipeline_log import get_logger

import td_aggregate
import td_assign
import td_digest
import td_extract
import td_index
import td_render
import td_sources
import td_taxonomy

ROOT = Path(__file__).parent.parent
log = get_logger("td_pipeline")


def run_all(data_dir, *, extract_call, taxo_call=None, assign_call=None, codebook=None,
            n=200, seed=0, batch_size=30, force=False, sleep=None):
    """전 스테이지 실행. dirty 캐스케이드로 앞 스테이지가 돌면 뒤도 재실행.

    codebook 지정(S2): taxonomy 유도를 건너뛰고 코드북으로 배정. 코드북이 assignments
    보다 새로우면 재배정(추출 재사용). codebook=None(S1): taxonomy 유도로 카테고리 생성.
    """
    taxo_call = taxo_call or extract_call
    assign_call = assign_call or extract_call
    d = Path(data_dir)
    d.mkdir(parents=True, exist_ok=True)
    p = {name: d / f"{name}.json" for name in
         ("sources", "extracted", "taxonomy", "assignments", "aggregates")}
    workshop = d / "workshop-input.md"
    dirty = force

    if dirty or not p["sources"].exists():
        td_sources.write(p["sources"], n=n, seed=seed)
        dirty = True
    ex_summary = {"failed": [], "dropped": []}
    if dirty or not p["extracted"].exists():
        ex_summary = td_extract.run_extract(p["sources"], p["extracted"], extract_call, sleep=sleep)
        dirty = True

    if codebook is None:
        if dirty or not p["taxonomy"].exists():
            td_taxonomy.induce(p["extracted"], p["taxonomy"], taxo_call,
                               batch_size=batch_size, sleep=sleep)
            dirty = True
        assign_source = p["taxonomy"]
    else:
        assign_source = codebook  # 코드북 편집(더 새로움) → 재배정
        if not dirty and p["assignments"].exists() and \
                Path(codebook).stat().st_mtime > p["assignments"].stat().st_mtime:
            dirty = True

    as_summary = {"dropped": []}
    if dirty or not p["assignments"].exists():
        as_summary = td_assign.assign(p["extracted"], assign_source, p["assignments"],
                                      assign_call, sleep=sleep)
        dirty = True

    if codebook is not None:  # 기타 수집·경고 (고정 코드북 약점 방어)
        other = td_assign.collect_other(p["assignments"])
        (d / "other-report.json").write_text(
            json.dumps(other, ensure_ascii=False, indent=1), encoding="utf-8")
        if other["warning"]:
            log.warning(f"Other 비율 {other['ratio']:.0%} — 코드북 갱신 필요 신호")

    if dirty or not p["aggregates"].exists():
        td_aggregate.aggregate(p["assignments"], p["extracted"], p["aggregates"])
        dirty = True
    if dirty or not workshop.exists():
        td_render.write(p["aggregates"], p["extracted"], p["assignments"], workshop,
                        failed=ex_summary["failed"],
                        extract_dropped=len(ex_summary["dropped"]),
                        assign_dropped=len(as_summary["dropped"]))
    log.info(f"파이프라인 완료 → {workshop}")
    return {**{k: str(v) for k, v in p.items()}, "workshop": str(workshop)}


def run_retrieval(data_dir, *, extract_call, embed, n=200, seed=0,
                  force=False, sleep=None, anonymize=False):
    """S4: 추출→색인→사전 조회 묶음. 카테고리화(taxonomy/codebook/배정) 스테이지 없음.
    색인은 인메모리(비영속) — extracted·digest만 skip-if-exists."""
    d = Path(data_dir)
    d.mkdir(parents=True, exist_ok=True)
    sources, extracted = d / "sources.json", d / "extracted.json"
    digest = d / "digest.md"
    dirty = force

    if dirty or not sources.exists():
        td_sources.write(sources, n=n, seed=seed)
        dirty = True
    if dirty or not extracted.exists():
        td_extract.run_extract(sources, extracted, extract_call, sleep=sleep)
        dirty = True
    if dirty or not digest.exists():
        persons = json.loads(extracted.read_text(encoding="utf-8"))
        idx = td_index.build(persons, embed)
        td_digest.write(idx, embed, persons, digest, anonymize=anonymize)
        dirty = True
    log.info(f"검색 파이프라인 완료 → {digest}")
    return {"sources": str(sources), "extracted": str(extracted), "digest": str(digest)}


def main(argv):
    """실 LLM 실행. --codebook <경로> 주면 S2(코드북 배정), 없으면 S1(taxonomy 유도).
    모델 이원화: 유도=큰 모델, 배정=작은 모델을 별도 call로 넘길 수 있다(기본 동일)."""
    import llm
    data_dir = ROOT / "data" / "task_discovery"
    codebook = None
    args = list(argv)
    if "--codebook" in args:
        i = args.index("--codebook")
        codebook = args[i + 1]
        del args[i:i + 2]
    if args:
        data_dir = args[0]
    llm.init()
    if "--search" in args:                      # S4: 검색 파이프라인(카테고리화 없음)
        args.remove("--search")
        run_retrieval(data_dir if not args else args[0],
                      extract_call=llm.call_gemini, embed=llm.embed_text)
        return
    run_all(data_dir, extract_call=llm.call_gemini, taxo_call=llm.call_gemini,
            assign_call=llm.call_gemini, codebook=codebook)


if __name__ == "__main__":
    main(sys.argv[1:])
