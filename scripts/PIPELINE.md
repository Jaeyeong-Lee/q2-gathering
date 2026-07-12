# 파이프라인 실행 가이드

## 전체 파이프라인 (한 번에)

```bash
./scripts/pipeline.sh
```

옵션:
- `--skip-embed`: Gemini 임베딩 스킵 (이미 embeddings.json 있을 때)
- `--skip-extract`: LLM 태그 추출 스킵 (이미 tags.json 있을 때)

```bash
# 빠른 재빌드 (API 호출 없이)
./scripts/pipeline.sh --skip-embed --skip-extract
```

---

## 개별 단계 실행

### 1️⃣ 임베딩 생성 (3072차원, Gemini)

```bash
GEMINI_API_KEY=xxx python3 scripts/embed.py
```

- 입력: `data/persons.json` (persons[].text)
- 출력: `data/embeddings.json` ({id: [3072]})
- API: Gemini 2.0 Flash
- 비용: ~150명 × 약 1000 tokens/인 = 약 $0.15

### 2️⃣ 형태소 분석 (명사 빈도)

```bash
python3 scripts/freq.py
```

- 입력: `data/persons.json` (persons[].text)
- 출력: `data/freq.json` ({id: {명사: 빈도}})
- 라이브러리: kiwipiepy (한국어 형태소 분석)
- 불용어 튜닝: `scripts/stopwords.txt` 편집

### 3️⃣ 유사도 계산 (코사인, 상위 30명)

```bash
python3 scripts/similarity.py
```

- 입력: `data/embeddings.json`
- 출력: `data/neighbors.json` ({id: [top-30 이웃 id]})
- 알고리즘: 코사인 유사도
- 설정: `scripts/config.py` `K=30`

### 4️⃣ 태그 추출 (LLM 배치)

```bash
GEMINI_API_KEY=xxx python3 scripts/run_extraction.py
```

- 입력: `data/persons.json` (persons[].text)
- 출력: `data/tags.json` ({id: [tags]})
- API: Gemini 2.0 Flash
- 제한: 15 RPM (자동 지연 5초/요청)
- 재시도: 최대 1회
- 비용: ~150명 × 약 500 tokens/인 = 약 $0.05

### 5️⃣ HTML 빌드 (인라인)

```bash
python3 scripts/build.py
```

- 입력: `data/persons.json`, `data/embeddings.json`, `data/neighbors.json`, `data/freq.json`, `data/tags.json`
- 출력: `dist/heritage-archive.html` (자급자족 정적 파일)
- 템플릿: `archive/template.html`
- 기타 에셋: `archive/echarts*.min.js`, `archive/about/*`

---

## 환경 설정

### GEMINI_API_KEY

```bash
# 임시 (현재 터미널만)
export GEMINI_API_KEY=your-key-here

# 영구 (zsh)
echo 'export GEMINI_API_KEY=your-key-here' >> ~/.zshrc
source ~/.zshrc
```

### 파이썬 의존성

```bash
pip install -r requirements.txt
# 또는 개별: pip install kiwipiepy google-generativeai
```

---

## 디버깅

**임베딩 실패?**
- API 키 확인: `echo $GEMINI_API_KEY`
- 배치 요청 지연 조정: `python3 scripts/embed.py data/persons.json data/embeddings.json 2.0`

**태그 추출 실패?**
- 로그 확인: 터미널의 ✗ 메시지
- 재시도: 실패한 인물만 다시 실행하려면 `scripts/run_extraction.py` 수정

**형태소 분석 이상?**
- 불용어 파일 확인: `scripts/stopwords.txt`
- 결과 확인: `cat data/freq.json | jq '.["1"]'`

**빌드 실패?**
- 입력 파일 확인: `ls -la data/*.json`
- 템플릿 확인: `ls -la archive/`

---

## 더미 데이터로 테스트

```bash
python3 scripts/generate_dummy.py  # data/persons.json (더미) 생성
./scripts/pipeline.sh --skip-embed --skip-extract  # API 없이 테스트 빌드
open dist/heritage-archive.html
```

---

## 성능 참고

| 단계 | 시간 | 비용 |
|------|------|------|
| 임베딩 (150명) | ~8분 | $0.15 |
| 형태소분석 | ~30초 | $0 |
| 유사도 계산 | ~2초 | $0 |
| 태그추출 (150명, 15RPM) | ~10분 | $0.05 |
| 빌드 | ~5초 | $0 |
| **전체** | **~20분** | **$0.20** |

---

## 실데이터 전환

자세한 후속 작업은 `todos/009-realdata-followups.md` 참고.

요약:
1. PPT에서 `persons.json` 추출 (텍스트 정규화, 팀/CL 매핑)
2. `./scripts/pipeline.sh` 실행
3. `dist/heritage-archive.html`을 사내 GitHub Pages에 배포
