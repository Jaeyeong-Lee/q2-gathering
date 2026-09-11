import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

# 테스트를 실데이터 트리에서 떼어낸다 (#010). pipeline_log.OUT_DIR과 td_common.CALLS_DIR은
# import 시점에 TD_OUT_DIR로 고정되는 모듈 상수라, 테스트 모듈이 import되기 전인 여기서
# 잡아야 한다. 이게 없으면 run_all을 타는 테스트가 콜덤프를 data/task_discovery/calls/에
# 그대로 써서 실행 기록을 합성 프롬프트로 덮어쓴다 — 실제로 그러고 있었다.
# setdefault라 밖에서 TD_OUT_DIR을 준 경우(내부망 점검 등)는 그쪽이 이긴다.
os.environ.setdefault("TD_OUT_DIR", tempfile.mkdtemp(prefix="td-test-"))
