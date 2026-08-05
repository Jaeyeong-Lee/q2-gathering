"""파이프라인 공용 로거 — 콘솔·data/pipeline.log(사람용)·data/pipeline.ecs.jsonl(구조화)
세 곳에 동시에 남긴다.

에러는 log.exception()으로 남기면 스택트레이스까지 파일에 기록됨 → 내부망 트러블슈팅용.
ECS 로그는 extra={"ecs": {...}}로 실은 필드를 그대로 머지한다 — 예: 요청/응답 바이트 수로
내부망 페이로드 한도(요청 쪽인지 응답 쪽인지)를 판명하는 용도(#30).
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).parent.parent / "data" / "pipeline.log"
ECS_LOG_PATH = Path(__file__).parent.parent / "data" / "pipeline.ecs.jsonl"
ECS_VERSION = "8.11"


class ECSJSONFormatter(logging.Formatter):
    """한 줄짜리 ECS(Elastic Common Schema) JSON. filebeat 등이 그대로 읽어갈 형식 —
    ES로의 실제 전송은 이 저장소 범위 밖, 파일 생성까지만."""

    def format(self, record):
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc)
        payload = {
            "@timestamp": ts.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "log.level": record.levelname,
            "message": record.getMessage(),
            "ecs.version": ECS_VERSION,
            "service.name": record.name,
        }
        payload.update(getattr(record, "ecs", {}))
        return json.dumps(payload, ensure_ascii=False)


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
        ecs_fh = logging.FileHandler(ECS_LOG_PATH, encoding="utf-8")
        ecs_fh.setFormatter(ECSJSONFormatter())
        logger.addHandler(fh)
        logger.addHandler(sh)
        logger.addHandler(ecs_fh)
    return logger
