"""LLM 통합 테스트 (Gemini 모킹)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import tags


def test_extraction_with_mocked_gemini(tmp_path):
    """tags.main이 LLM 호출을 받아서 태그 추출."""
    import json
    import generate_dummy

    data_dir = tmp_path / "data"
    generate_dummy.main(out_dir=data_dir)
    persons_path = data_dir / "persons.json"

    call_count = [0]

    def mock_gemini(prompt):
        call_count[0] += 1
        if "회고:" in prompt:  # 인당 추출
            return '["혁신리더", "문제해결형", "데이터드리븐"]'
        return "{}"  # 풀 정리: 병합 없음

    failed = tags.main(persons_path=persons_path, call=mock_gemini, retries=0)

    assert failed == []
    after = json.loads(persons_path.read_text())
    assert after[0]["tags"] == ["혁신리더", "문제해결형", "데이터드리븐"]
    assert call_count[0] > 1  # 최소 배치 호출 + 풀 정리
    print(f"✓ LLM 호출 {call_count[0]}회, 태그 추출 완료")
