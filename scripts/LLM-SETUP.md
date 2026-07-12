# LLM API 설정 가이드

2개의 LLM 호출:
1. **임베딩 모델** (`scripts/embed.py`) — 텍스트 → 벡터 (3072차원)
2. **태그 추출** (`scripts/run_extraction.py`) — 텍스트 → 성향/역량 태그

`llm.py`는 OpenAI Compatible API를 지원하므로, 어떤 LLM 제공자든 사용 가능합니다.

---

## 1️⃣ Gemini (기본값)

```bash
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your-api-key-here
```

- 임베딩: `models/gemini-embedding-2` (3072차원)
- 텍스트 생성: `models/gemini-2.5-flash`
- 비용: ~$0.20/배치 (150명)
- 제한: 15 RPM (자동 리트라이 + 백오프)

---

## 2️⃣ 내부 LLM 서버 (OpenAI Compatible)

```bash
export LLM_PROVIDER=internal
export LLM_API_KEY=your-api-key
export LLM_API_BASE=http://your-internal-server:8000/v1
```

예시 환경:
- vLLM 서버: `http://llm-server.internal:8000/v1`
- Ollama: `http://localhost:11434/v1`
- LM Studio: `http://localhost:1234/v1`

### 모델 이름 (scripts/embed.py, scripts/run_extraction.py 수정 필요)

임베딩 모델 선택 예시:
- `text-embedding-3-small` (OpenAI)
- `sentence-transformers/all-MiniLM-L6-v2` (오픈소스)
- 내부 모델 이름

텍스트 생성 모델:
- 내부 모델명 (예: `llama2`, `mistral`, `qwen`)

---

## 3️⃣ OpenAI API

```bash
export LLM_PROVIDER=openai_compat
export LLM_API_KEY=sk-...
export LLM_API_BASE=https://api.openai.com/v1
```

### 모델 이름 수정 (scripts/embed.py, scripts/run_extraction.py)

```python
# embed.py 7번 라인
python3 scripts/embed.py data/persons.json data/embeddings.json "text-embedding-3-small" "sk-..."

# run_extraction.py
OPENAI_MODEL=gpt-4-turbo python3 scripts/run_extraction.py
```

---

## 설정 방법

### 임시 (현재 터미널만)

```bash
export LLM_PROVIDER=internal
export LLM_API_KEY=test-key
export LLM_API_BASE=http://localhost:8000/v1
./scripts/pipeline.sh
```

### 영구 (zsh)

```bash
cat >> ~/.zshrc <<'EOF'
export LLM_PROVIDER=internal
export LLM_API_KEY=your-key-here
export LLM_API_BASE=http://your-server:8000/v1
EOF
source ~/.zshrc
```

### 프로젝트 로컬 (.env)

```bash
# .env 파일 생성 (git ignore됨)
cat > .env <<'EOF'
LLM_PROVIDER=internal
LLM_API_KEY=test-key
LLM_API_BASE=http://localhost:8000/v1
EOF

# 실행 시 로드
source .env && ./scripts/pipeline.sh
```

---

## 각 API 키 분리 (선택사항)

임베딩과 텍스트 생성에 다른 API를 사용하고 싶다면, `llm.py`를 확장:

```python
# llm.py 추가
def embed_text(text, model=None, max_retries=5):
    embed_provider = os.getenv("EMBED_PROVIDER", _provider)
    # embed_provider별로 다른 클라이언트 사용
    ...

def call_gemini(prompt, model=None, max_retries=5):
    text_provider = os.getenv("TEXT_PROVIDER", _provider)
    # text_provider별로 다른 클라이언트 사용
    ...
```

사용:
```bash
export LLM_PROVIDER=openai_compat
export LLM_API_BASE=http://text-generation:8000/v1
export LLM_API_KEY=key1

export EMBED_PROVIDER=openai_compat
export EMBED_API_BASE=http://embeddings:9000/v1
export EMBED_API_KEY=key2

./scripts/pipeline.sh
```

---

## 테스트

```bash
# Gemini (기본값)
export GEMINI_API_KEY=your-key
python3 -c "import llm; llm.init(); print(llm.call_gemini('Hi'))"

# 내부 서버
export LLM_PROVIDER=internal
export LLM_API_KEY=test
export LLM_API_BASE=http://localhost:8000/v1
python3 -c "import llm; llm.init(); print(llm.call_gemini('Hi'))"
```

---

## 트러블슈팅

**"LLM_API_KEY 환경변수 필수" 에러**
```bash
echo $LLM_API_KEY  # 확인
```

**"연결 거부" 에러**
```bash
curl http://localhost:8000/v1/models  # API 서버 실행 확인
```

**모델명 오류 ("Model not found")**
```bash
# 사용 가능한 모델 확인
curl http://localhost:8000/v1/models
```

---

## 성능 비교

| Provider | 임베딩 | 텍스트생성 | 비용 | 지연 |
|----------|--------|-----------|------|------|
| Gemini | 3072차원 | gemini-2.5-flash | $0.20 | 원격 |
| 내부 vLLM | 가변 | 내부 모델 | $0 | 로컬 |
| OpenAI | 1536차원 | gpt-4-turbo | $2+ | 원격 |

---

## Makefile 통합

```bash
# .env 파일이 있으면 자동 로드
make pipeline  # → source .env && ./scripts/pipeline.sh
```

(Makefile 수정 필요 시 요청)
