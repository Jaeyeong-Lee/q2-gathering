"""합성 코퍼스 + LLM 0회로 샘플 산출물 한 벌 만들기 (#010).

`make td-sample`(Gemini 실호출)의 대체 경로. 화면(#012~)을 개발하는 동안 산출물을 몇 번이고
다시 만들어야 하는데 그때마다 API를 때릴 이유가 없다. 결정적이라 화면 회귀 비교도 된다.

usage: python3 scripts/td_sample_build.py [출력디렉터리] [인원수]
       기본: data/td_sample/task_discovery, 120명
"""
import shutil
import sys
from pathlib import Path

import td_fake_llm
import td_pipeline
from pipeline_log import get_logger

ROOT = Path(__file__).parent.parent
DEFAULT_DIR = ROOT / "data" / "td_sample" / "task_discovery"
log = get_logger("td_sample_build")


def build(out_dir=DEFAULT_DIR, n=120, seed=0, fresh=True):
    """샘플 산출물 한 벌. fresh=True면 기존 산출물을 지우고 처음부터 — 스텁을 고친 뒤
    skip-if-exists 때문에 옛 결과가 남는 사고를 막는다."""
    out_dir = Path(out_dir)
    if fresh and out_dir.exists():
        shutil.rmtree(out_dir)
    res = td_pipeline.run_all(out_dir, n=n, seed=seed, sleep=lambda _: None,
                              **td_fake_llm.calls())
    log.info(f"샘플 산출물 완료 (LLM 0회) → {out_dir}")
    return res


def main(*argv):
    out_dir = Path(argv[0]) if argv else DEFAULT_DIR
    n = int(argv[1]) if len(argv) > 1 else 120
    res = build(out_dir, n=n)
    print(f"샘플 {n}명 → {res['workshop']}", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
