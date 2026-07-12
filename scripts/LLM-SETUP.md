# LLM API 상세 설정

## 개요

2개의 독립적인 API:
1. **TEXT** (태그 추출): LLM 텍스트 생성 모델 — `scripts/run_extraction.py`
2. **EMBED** (임베딩): 임베딩 모델 — `scripts/embed.py`

각각 다른 서버/키 가능. OpenAI Compatible API 지원.

---

## 환경변수

### 텍스트 생성 (태그 추출)

```bash
TEXT_PROVIDER=openai_compat      # 고정
TEXT_API_KEY=your-api-key        # API 키
TEXT_API_BASE=http://server:8000/v1  # 서버 주소
```

### 임베딩

```bash
EMBED_PROVIDER=openai_compat     # 고정
EMBED_API_KEY=your-api-key
EMBED_API_BASE=http://server:9000/v1  # 다른 서버 가능
```

---

## 설정 시나리오

### A. 같은 서버, 같은 키

```bash
export TEXT_PROVIDER=openai_compat
export TEXT_API_KEY=mykey
export TEXT_API_BASE=http://llm.internal:8000/v1

export EMBED_PROVIDER=openai_compat
export EMBED_API_KEY=mykey
export EMBED_API_BASE=http://llm.internal:8000/v1

./scripts/pipeline.sh
```

### B. 다른 서버

```bash
# 태그: 내부 LLM
export TEXT_PROVIDER=openai_compat
export TEXT_API_KEY=text-key
export TEXT_API_BASE=http://llm-server:8000/v1

# 임베딩: 별도 서버 (아직 미확정)
export EMBED_PROVIDER=openai_compat
export EMBED_API_KEY=embed-key
export EMBED_API_BASE=http://embed-server:9000/v1

./scripts/pipeline.sh
```

### C. .env 파일로 저장

루트에 `.env` 생성 (git ignore됨):

```bash
cat > .env <<'EOF'
TEXT_PROVIDER=openai_compat
TEXT_API_KEY=text-key
TEXT_API_BASE=http://llm-server:8000/v1

EMBED_PROVIDER=openai_compat
EMBED_API_KEY=embed-key
EMBED_API_BASE=http://embed-server:9000/v1
EOF

source .env && ./scripts/pipeline.sh
```

---

## 서버별 설정

### vLLM

```bash
export TEXT_API_BASE=http://vllm-server:8000/v1
export TEXT_API_KEY=dummy  # 보안 비활성화 시 아무 값
```

사용 가능한 모델 확인:
```bash
curl http://vllm-server:8000/v1/models | jq .data[].id
```

### Ollama

```bash
export TEXT_API_BASE=http://localhost:11434/v1
export TEXT_API_KEY=ollama
```

### LM Studio

```bash
export TEXT_API_BASE=http://localhost:1234/v1
export TEXT_API_KEY=not-needed
```

---

## 임베딩 모델 미확정 시

아직 임베딩 서버/모델이 정해지지 않은 경우:

**임시방편:** 텍스트와 임베딩을 같은 LLM 서버에서 처리

```bash
export TEXT_PROVIDER=openai_compat
export TEXT_API_KEY=key
export TEXT_API_BASE=http://llm:8000/v1

export EMBED_PROVIDER=openai_compat
export EMBED_API_KEY=key
export EMBED_API_BASE=http://llm:8000/v1

./scripts/pipeline.sh
```

**향후:** 임베딩 모델 정해진 후 `EMBED_API_BASE` 변경

---

## llm.py 코드

`llm.py`는 provider별로 다른 클라이언트 사용:

```python
# TEXT 초기화 (태그 추출용)
if TEXT_PROVIDER == "openai_compat":
    _text_openai_client = OpenAI(api_key=TEXT_API_KEY, base_url=TEXT_API_BASE)

# EMBED 초기화 (임베딩용)
if EMBED_PROVIDER == "openai_compat":
    _embed_openai_client = OpenAI(api_key=EMBED_API_KEY, base_url=EMBED_API_BASE)
```

추가 provider (예: 특수한 인증방식) 필요 시 `llm.py`에 추가.

---

## 모델명 확인

현재 가능한 모델:

```bash
curl $TEXT_API_BASE/models | jq .
```

예시 응답:
```json
{
  "data": [
    {"id": "gpt-3.5-turbo", "owned_by": "openai"},
    {"id": "text-embedding-3-small", "owned_by": "openai"}
  ]
}
```

---

## 에러 해결

| 에러 | 해결책 |
|------|--------|
| "API_KEY 필수" | `echo $TEXT_API_KEY` / `echo $EMBED_API_KEY` 확인 |
| "연결 거부" (refused) | 서버 실행 확인: `curl $TEXT_API_BASE/health` |
| "모델을 찾을 수 없음" | 모델명 확인: `curl $TEXT_API_BASE/models` |
| "인증 실패" | API 키 및 base URL 재확인 |

---

## 성능 참고

150명 기준:
- 태그 추출: ~10분 (RPM 제한에 따라 가변)
- 임베딩: ~8분
- 형태소 분석: ~30초
- 유사도 계산: ~2초
- 빌드: ~5초

---

## 향후 임베딩 모델 추가

임베딩 모델 정해진 후:
```bash
export EMBED_PROVIDER=openai_compat
export EMBED_API_KEY=embed-service-key
export EMBED_API_BASE=http://embedding-service:9000/v1
```

기존 설정과 분리되므로 재배포 불필요.

---

빠른 시작은 `scripts/LLM-QUICK.md` 참고.
