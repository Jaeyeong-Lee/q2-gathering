# LLM API 설정

2개 API가 필요:
- **태그 추출** (TEXT): LLM 텍스트 생성 모델 (GPT OSS 122B / Gemma 등)
- **임베딩** (EMBED): 임베딩 모델 (미확정)

---

## 기본 설정

### .env 파일 생성 (권장)

프로젝트 루트에:

```bash
cat > .env <<'EOF'
TEXT_PROVIDER=openai_compat
TEXT_API_KEY=your-text-api-key
TEXT_API_BASE=http://your-llm-server:8000/v1

EMBED_PROVIDER=openai_compat
EMBED_API_KEY=your-embed-api-key
EMBED_API_BASE=http://your-embed-server:9000/v1
EOF
```

실행:
```bash
source .env && ./scripts/pipeline.sh
```

### 한 줄 명령어

같은 서버에서:
```bash
TEXT_PROVIDER=openai_compat TEXT_API_KEY=key TEXT_API_BASE=http://server:8000/v1 \
EMBED_PROVIDER=openai_compat EMBED_API_KEY=key EMBED_API_BASE=http://server:8000/v1 \
./scripts/pipeline.sh
```

---

## 서버 주소별 예시

### vLLM 서버

```bash
export TEXT_PROVIDER=openai_compat
export TEXT_API_KEY=dummy
export TEXT_API_BASE=http://llm-server:8000/v1
export TEXT_MODEL=gpt-3.5-turbo  # 실제 모델명으로 변경
```

### Ollama (로컬)

```bash
export TEXT_PROVIDER=openai_compat
export TEXT_API_KEY=ollama
export TEXT_API_BASE=http://localhost:11434/v1
```

---

## 다른 임베딩 선택

임베딩 서버가 다르거나 아직 미정인 경우:

```bash
export EMBED_PROVIDER=openai_compat
export EMBED_API_KEY=embed-key
export EMBED_API_BASE=http://embed-server:9000/v1
export EMBED_MODEL=text-embedding-3-small  # 실제 모델명으로 변경
```

---

## 실행 방법

| 상황 | 명령어 |
|------|--------|
| .env 사용 | `source .env && ./scripts/pipeline.sh` |
| 직접 환경변수 | `TEXT_PROVIDER=openai_compat TEXT_API_KEY=key ... ./scripts/pipeline.sh` |
| Make | `make pipeline` (.env 필요) |
| 빠른 재빌드 (API 스킵) | `./scripts/pipeline.sh --skip-embed --skip-extract` |

---

## 문제 해결

**"API 키 필수" 에러**
```bash
echo $TEXT_API_KEY
echo $EMBED_API_KEY
```

**"연결 거부" 에러**
```bash
curl http://your-server:8000/v1/models
# 서버 실행 확인
```

---

## 모델명 확인

서버에서 사용 가능한 모델 확인:
```bash
curl http://your-server:8000/v1/models | jq .data[].id
```

자세한 고급 설정은 `scripts/LLM-SETUP.md` 참고.
