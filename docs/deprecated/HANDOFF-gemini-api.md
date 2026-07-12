# Handoff: q2-gathering 임베딩 & 태그 추출 파이프라인

**Session Date:** 2026-07-12  
**Status:** Partially complete - embedding successful, tag extraction blocked by rate limit

---

## Summary

구축 중인 150명 인물 네트워크 시각화 프로젝트의 임베딩 & 태그 추출 파이프라인.

**완료:**
- ✅ 임베딩 파이프라인 (Gemini API) - 98명 × 3072차원 벡터
- ✅ 코사인 유사도 계산 - 98명 × 30 이웃
- ✅ 가짜 데이터 생성

**미완료:**
- ❌ 태그 추출 - Rate limit 초과 (20명만 처리)

---

## API 호출 현황

### 1. 임베딩 (성공) ✅

**모델:** `models/gemini-embedding-2`  
**엔드포인트:** `genai.embed_content()`  
**결과:** 98명 완료 (3072차원)

```python
# scripts/llm.py
def embed_text(text, model="models/gemini-embedding-2"):
    result = genai.embed_content(model=model, content=text)
    return result['embedding']  # [3072차원]
```

**호출 방식:**
```bash
GEMINI_API_KEY=xxx python scripts/embed.py
```

**출력:** `data/embeddings.json` (3.9MB)

---

### 2. 태그 추출 (실패) ❌

**모델:** `models/gemini-2.5-flash`  
**엔드포인트:** `model.generate_content()`  
**결과:** 20명만 처리 후 Rate limit 초과

```python
# scripts/llm.py
def call_gemini(prompt, model="models/gemini-2.5-flash", max_retries=5):
    # 429 에러 시 지수 백오프 (1, 2, 4, 8, 16초)
    for attempt in range(max_retries):
        try:
            response = model_obj.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait = 2 ** attempt
                time.sleep(wait)
```

**호출 방식:**
```bash
GEMINI_API_KEY=xxx python scripts/run_extraction.py
```

---

## 문제 발생 및 해결

### Problem 1: 모델명 오류

**증상:**
```
404 models/gemini-1.5-flash is not found for API version v1beta
```

**원인:** 존재하지 않는 모델명 사용

**해결:**
```bash
# 사용 가능한 모델 확인
python -c "
import google.generativeai as genai
genai.configure(api_key=KEY)
models = genai.list_models()
for m in models:
    if 'generateContent' in str(m.supported_generation_methods):
        print(m.name)
"
```

**결과:** `models/gemini-2.5-flash` 사용

---

### Problem 2: Rate Limit (Quota Exceeded)

**증상 (태그 추출):**
```
429 You exceeded your current quota
Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
limit: 0, model: gemini-2.0-flash
```

**증상 (임베딩):**
```
429 Quota exceeded for metric: embed_content_free_tier_requests
limit: 100, model: gemini-embedding-2
Quota exceeded for metric: GenerateContentInputTokensPerMinutePerUserPerProjectPerModel-FreeTier
```

**원인:** 프리티어 쿼터 소진
- 태그 추출: 분당 무제한이지만 일일/분당 쿼터 다 씀
- 임베딩: 분당 100개 요청 제한

**완화 조치:**
```python
# tags.py
def extract_all(persons, call, retries=1, delay=0.5):
    """1초 지연으로 천천히 처리"""
    for i, p in enumerate(persons):
        ...
        if delay > 0:
            time.sleep(delay)  # 요청 사이 1초
```

**근본 해결:** API 키 쿼터 리셋 필요

---

### Problem 3: 잘못된 임베딩 모델

**증상:**
```
404 models/text-embedding-004 is not found
```

**원인:** 사용 가능한 임베딩 모델 확인 부족

**사용 가능한 모델:**
- `models/gemini-embedding-001`
- `models/gemini-embedding-2-preview`
- `models/gemini-embedding-2` ← **사용함**

---

## 데이터 구조

### 입출력 흐름

```
persons.json (150명)
  ├─ ID, 이름, 회고 텍스트, 기존 태그
  │
  ├→ [Gemini 임베딩 API]
  │   └→ embeddings.json (98명 × 3072차원) ✅
  │       
  └→ [코사인 유사도]
      └→ neighbors.json (98명 × 30 이웃) ✅
```

### 파일 위치

- `data/persons.json` - 입력 (150명 회고)
- `data/embeddings.json` - 임베딩 벡터 (98명 × 3072차원, 3.9MB)
- `data/neighbors.json` - 유사도 기반 이웃 (98명 × 30)
- `data/freq.json` - 키워드 빈도 (준비됨)

### 벡터 범위
```
값 범위: [-0.1789, 0.1530]
차원: 3072
```

---

## 코드 위치

**API 호출:**
- `scripts/llm.py` - Gemini API 래퍼 (call_gemini, embed_text)
- `scripts/embed.py` - 임베딩 실행
- `scripts/run_extraction.py` - 태그 추출 실행

**테스트:**
- `tests/test_llm_integration.py` - LLM 통합 테스트 (모킹)
- `tests/test_embedding.py` - 임베딩 테스트 (모킹)

**빌드:**
- `scripts/similarity.py` - 코사인 유사도 계산
- `scripts/generate_dummy.py` - 더미 데이터 생성

---

## 다음 단계

### 우선순위

1. **API 쿼터 리셋 확인**
   - 새 API 키로 교체 또는 기존 키 쿼터 리셋 대기
   - `GEMINI_API_KEY=***` 재설정

2. **태그 추출 재실행**
   ```bash
   GEMINI_API_KEY=xxx python scripts/run_extraction.py
   ```
   - 현재 20명만 처리됨
   - 150명 전체 필요

3. **형태소 분석** (frequency 계산)
   - `scripts/freq.py` 실행 준비됨 (kiwipiepy 사용)
   - 로컬 처리이므로 API 관계 없음

4. **프론트 통합**
   - 임베딩 벡터 기반 네트워크 시각화
   - 워드클라우드 렌더링

---

## 설정 & 의존성

**requirements.txt:**
```
pytest
kiwipiepy  # 형태소 분석
google-generativeai  # Gemini API (deprecated, google-genai로 마이그레이션 필요)
```

**환경 변수:**
```bash
export GEMINI_API_KEY=<your-key>
```

**모델 선택:**
- 텍스트 생성: `models/gemini-2.5-flash`
- 임베딩: `models/gemini-embedding-2`
- 형태소: kiwipiepy (로컬)

---

## 주의사항

1. **Rate Limit 대응**
   - 분당 요청 수 제한 있음 (특히 프리티어)
   - delay=1.0 권장 (현재 설정)

2. **API 키 노출**
   - `.env` 파일 사용 권장
   - git에 커밋하지 말 것

3. **모델 마이그레이션**
   - `google-generativeai` → `google-genai` 전환 필요
   - FutureWarning 발생 중

---

## 테스트 현황

```bash
# 모두 통과
pytest tests/test_tags.py tests/test_llm_integration.py tests/test_embedding.py
# 9/9 passed
```

---

## Suggested Skills

- `/code-review` - 임베딩 파이프라인 코드 리뷰
- `ponytail` - API 호출 최적화 (불필요한 요청 제거)
- `claude-api` - Gemini API 마이그레이션 가이드

---

**Generated:** 2026-07-12 | Session: Gemini API Integration
