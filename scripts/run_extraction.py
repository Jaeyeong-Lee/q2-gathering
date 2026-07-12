"""태그 추출을 Gemini로 실행."""
import sys
from pathlib import Path

import llm
import tags

ROOT = Path(__file__).parent.parent


def main(persons_path=None, retries=1, delay=1.0):
    """Gemini 호출 함수를 tags.main에 주입. delay=1초 권장 (레이트 리밋 대응)."""
    if persons_path is None:
        persons_path = ROOT / "data" / "persons.json"

    llm.init()
    print(f"⏱️ 요청 사이 {delay}초 지연으로 천천히 처리...", file=sys.stderr)
    failed = tags.main(persons_path=persons_path, call=llm.call_gemini, retries=retries, delay=delay)

    if failed:
        print(f"추출 실패 {len(failed)}명: {failed}", file=sys.stderr)
    else:
        print("✓ 모든 인물 태그 추출 완료", file=sys.stderr)
    return failed


if __name__ == "__main__":
    main()
