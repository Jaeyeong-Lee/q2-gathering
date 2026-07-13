"""파이프라인 공용 로거 — 콘솔과 data/pipeline.log(append)에 동시에 남긴다.

에러는 log.exception()으로 남기면 스택트레이스까지 파일에 기록됨 → 내부망 트러블슈팅용.
"""
import logging
from pathlib import Path

LOG_PATH = Path(__file__).parent.parent / "data" / "pipeline.log"


def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s")
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
        fh.setFormatter(fmt)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(sh)
    return logger
