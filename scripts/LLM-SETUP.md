# LLM API 설정 가이드

**2개의 독립적인 LLM 호출** (각각 다른 API일 수 있음):
1. **임베딩 모델** (`scripts/embed.py`) — 텍스트 → 벡터 (EMBED_PROVIDER)
2. **태그 추출** (`scripts/run_extraction.py`) — 텍스트 → 태그 (TEXT_PROVIDER)

각 API는 독립적인 환경변수로 제어합니다. `llm.py`는 OpenAI Compatible API를 지원하므로, 어떤 LLM 제공자든 사용 가능합니다.

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

## 설정 시나리오

### 시나리오 1️⃣: 모두 Gemini (기본값)

```bash
export GEMINI_API_KEY=your-key
./scripts/pipeline.sh
```

내부적으로:
- TEXT_PROVIDER=gemini, EMBED_PROVIDER=gemini (모두 같은 API 키 사용)

### 시나리오 2️⃣: 텍스트는 내부 LLM, 임베딩은 Gemini

```bash
export GEMINI_API_KEY=gemini-key
export TEXT_PROVIDER=internal
export TEXT_API_KEY=internal-key
export TEXT_API_BASE=http://internal-llm:8000/v1
./scripts/pipeline.sh
```

또는 한 줄로:
```bash
GEMINI_API_KEY=gemini-key \
TEXT_PROVIDER=internal \
TEXT_API_KEY=internal-key \
TEXT_API_BASE=http://internal-llm:8000/v1 \
./scripts/pipeline.sh
```

### 시나리오 3️⃣: 텍스트는 Gemini, 임베딩은 내부 LLM

```bash
export GEMINI_API_KEY=gemini-key
export EMBED_PROVIDER=internal
export EMBED_API_KEY=internal-embed-key
export EMBED_API_BASE=http://embedding-server:9000/v1
./scripts/pipeline.sh
```

### 시나리오 4️⃣: 모두 내부 LLM (텍스트/임베딩 서로 다른 키)

```bash
export TEXT_PROVIDER=internal
export TEXT_API_KEY=llm-key
export TEXT_API_BASE=http://text-gen:8000/v1

export EMBED_PROVIDER=internal
export EMBED_API_KEY=embed-key
export EMBED_API_BASE=http://embeddings:9000/v1

./scripts/pipeline.sh
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
# 옵션 1: 둘 다 같은 서버
cat >> ~/.zshrc <<'EOF'
export LLM_PROVIDER=internal
export LLM_API_KEY=your-key-here
export LLM_API_BASE=http://your-server:8000/v1
EOF

# 옵션 2: 각각 다른 서버
cat >> ~/.zshrc <<'EOF'
export TEXT_PROVIDER=internal
export TEXT_API_KEY=llm-key
export TEXT_API_BASE=http://text-gen:8000/v1

export EMBED_PROVIDER=internal
export EMBED_API_KEY=embed-key
export EMBED_API_BASE=http://embeddings:9000/v1
EOF

source ~/.zshrc
```

### 프로젝트 로컬 (.env)

```bash
# .env 파일 생성 (git ignore됨)

# 옵션 1: 둘 다 같은 서버
cat > .env <<'EOF'
LLM_PROVIDER=internal
LLM_API_KEY=test-key
LLM_API_BASE=http://localhost:8000/v1
EOF

# 옵션 2: 텍스트/임베딩 분리
cat > .env <<'EOF'
TEXT_PROVIDER=internal
TEXT_API_KEY=llm-key
TEXT_API_BASE=http://localhost:8000/v1

EMBED_PROVIDER=internal
EMBED_API_KEY=embed-key
EMBED_API_BASE=http://localhost:9000/v1
EOF

# 실행 시 로드
source .env && ./scripts/pipeline.sh
```

---

## 각 API 키 분리 (기본 지원)

`llm.py`는 이미 TEXT_PROVIDER와 EMBED_PROVIDER를 독립적으로 지원합니다.

**환경변수 우선순위:**

텍스트 생성 (태그 추출):
1. `TEXT_API_KEY` (지정 시)
2. `GEMINI_API_KEY` (Gemini 선택 시)

임베딩:
1. `EMBED_API_KEY` (지정 시)
2. `GEMINI_API_KEY` (Gemini 선택 시)

**예시: 텍스트와 임베딩에 다른 API 사용**

```bash
# 태그 추출: Gemini
export GEMINI_API_KEY=gemini-key

# 임베딩: 내부 LLM 서버 (다른 키)
export EMBED_PROVIDER=internal
export EMBED_API_KEY=embed-key
export EMBED_API_BASE=http://embeddings:9000/v1

./scripts/pipeline.sh
```

또는 `TEXT_API_KEY`를 명시적으로 지정:
```bash
export TEXT_API_KEY=gemini-key
export TEXT_PROVIDER=gemini

export EMBED_API_KEY=embed-key
export EMBED_PROVIDER=internal
export EMBED_API_BASE=http://embeddings:9000/v1

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
