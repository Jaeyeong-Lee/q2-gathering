"""임베딩 함수 테스트."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import embed
import generate_dummy


def test_embed_persons_with_mocked_api(tmp_path):
    """persons.json 텍스트를 임베딩 벡터로 변환."""
    data_dir = tmp_path / "data"
    generate_dummy.main(out_dir=data_dir)
    persons_path = data_dir / "persons.json"

    def mock_embed(text, model=None):
        # 실제 API 대신 고정된 벡터 반환 (768차원)
        return [0.1] * 768

    with patch("llm.init"), patch("llm.embed_text", side_effect=mock_embed):
        embeddings = embed.embed_persons(persons_path)

    # 모든 인물이 임베딩됨
    assert len(embeddings) == 150
    assert all(len(v) == 768 for v in embeddings.values())
    print(f"✓ {len(embeddings)}명 임베딩 완료 (768차원)")


def test_embed_output_format(tmp_path):
    """임베딩 결과 저장 형식."""
    data_dir = tmp_path / "data"
    generate_dummy.main(out_dir=data_dir)
    persons_path = data_dir / "persons.json"
    out_path = data_dir / "embeddings.json"

    def mock_embed(text, model=None):
        return [0.5] * 768

    with patch("llm.init"), patch("llm.embed_text", side_effect=mock_embed):
        result = embed.embed_persons(persons_path, out_path)

    # JSON 저장 확인
    assert out_path.exists()
    saved = json.loads(out_path.read_text(encoding="utf-8"))
    assert all(v == [0.5] * 768 for v in saved.values())
    print(f"✓ 임베딩 {out_path.name} 저장 완료")
