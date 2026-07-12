# LLM API 빠른 시작

2개 API가 필요합니다:
- **태그 추출**: LLM 텍스트 생성 모델
- **임베딩**: 임베딩 모델

---

## 1️⃣ Gemini 사용 (기본값, 가장 간단)

API 키 하나만 있으면 됩니다.

```bash
export GEMINI_API_KEY=your-key-here
./scripts/pipeline.sh
```

또는 한 줄로:
```bash
GEMINI_API_KEY=your-key-here ./scripts/pipeline.sh
```

---

## 2️⃣ 내부 LLM 서버 사용

서버가 실행 중이어야 합니다 (vLLM, Ollama 등).

```bash
export TEXT_PROVIDER=internal
export TEXT_API_KEY=your-api-key
export TEXT_API_BASE=http://your-server:8000/v1

export EMBED_PROVIDER=internal
export EMBED_API_KEY=your-api-key
export EMBED_API_BASE=http://your-server:8000/v1

./scripts/pipeline.sh
```

또는 한 줄로:
```bash
TEXT_PROVIDER=internal TEXT_API_KEY=key TEXT_API_BASE=http://server:8000/v1 \
EMBED_PROVIDER=internal EMBED_API_KEY=key EMBED_API_BASE=http://server:8000/v1 \
./scripts/pipeline.sh
```

---

## 3️⃣ 태그 추출은 내부, 임베딩은 Gemini

```bash
# 내부 서버에서 태그 추출
export TEXT_PROVIDER=internal
export TEXT_API_KEY=llm-key
export TEXT_API_BASE=http://your-server:8000/v1

# Gemini에서 임베딩
export GEMINI_API_KEY=gemini-key
export EMBED_PROVIDER=gemini

./scripts/pipeline.sh
```

---

## 4️⃣ .env 파일로 저장 (권장)

프로젝트 루트에 `.env` 파일 생성:

```bash
cat > .env <<'EOF'
TEXT_PROVIDER=internal
TEXT_API_KEY=your-text-key
TEXT_API_BASE=http://localhost:8000/v1

EMBED_PROVIDER=internal
EMBED_API_KEY=your-embed-key
EMBED_API_BASE=http://localhost:8000/v1
EOF
```

그 후 실행:
```bash
source .env && ./scripts/pipeline.sh
```

또는 파이썬으로 직접 로드:
```bash
python3 scripts/embed.py    # llm.init()가 환경변수 읽음
```

---

## 어디서 API 키 얻기

- **Gemini**: https://aistudio.google.com/app/apikey
- **내부 LLM**: 서버 관리자에게 문의
- **Ollama**: 로컬 설치, 키 불필요 (로컬호스트만 지원)

---

## 명령어 모음

| 용도 | 명령어 |
|------|--------|
| Gemini만 사용 | `GEMINI_API_KEY=key ./scripts/pipeline.sh` |
| 내부 LLM (같은 서버) | `TEXT_PROVIDER=internal TEXT_API_KEY=key TEXT_API_BASE=http://server:8000/v1 EMBED_PROVIDER=internal EMBED_API_KEY=key EMBED_API_BASE=http://server:8000/v1 ./scripts/pipeline.sh` |
| .env 파일 사용 | `source .env && ./scripts/pipeline.sh` |
| Make 사용 | `make pipeline` (`.env` 필요) |
| 빠른 재빌드 (API 스킵) | `./scripts/pipeline.sh --skip-embed --skip-extract` |

---

## 문제 해결

**"API 키 필수" 에러**
```bash
echo $GEMINI_API_KEY  # 또는 echo $TEXT_API_KEY / echo $EMBED_API_KEY
# 비어있으면 설정해야 함
```

**"연결 거부" 에러**
```bash
curl http://your-server:8000/v1/models
# 서버가 실행 중인지 확인
```

**모델명 오류**
```bash
# 사용 가능한 모델 확인
curl http://your-server:8000/v1/models | jq .
```

---

## 다음 단계

자세한 설정은 `scripts/LLM-SETUP.md` 참고.
