# Heritage Archive — 근원경쟁력 유사도 네트워크

부서원 150명이 쓴 "근원경쟁력" 회고를 임베딩·유사도·형태소 분석으로 가공해,
**단일 정적 HTML** 하나로 탐색하는 인터랙티브 아카이브.
2026 Q2 분기회 라이브 데모용이자, 발표 후 사내 GitHub Pages에 상시 공개되는 배포물이다.

## 빠른 시작

```bash
python3 scripts/build.py        # → dist/heritage-archive.html
open dist/heritage-archive.html # 브라우저로 열면 끝 (서버 불필요)
```

산출물은 데이터·라이브러리 전부 인라인된 자급자족 파일이라 `file://`로 열어도
GitHub Pages에 올려도 동작이 같다. **로컬 dev 서버는 필요 없다.**

> ⚠️ 실명 + 역량 정보가 들어가므로 public GitHub Pages 금지 — 사내 전용 호스팅만.

## 파이프라인 (전부 빌드 타임, 런타임 API 호출 zero)

```
PPT (근원경쟁력 회고)
 └─ 인당 텍스트 추출 → 마크다운 정규화          … Jay 수동 + 스크립트
     └─ persons.json (id, name, pjt, cl_level, text, tags)
         ├─ scripts/embed.py      → embeddings.json  (Gemini, 3072차원/인)
         │   └─ scripts/similarity.py → neighbors.json (코사인 top-K=30/인)
         ├─ scripts/freq.py       → freq.json        (형태소 명사 빈도, 로컬)
         └─ scripts/run_extraction.py                (LLM 태그 추출 배치)
             ⇣
scripts/build.py — 템플릿에 JSON·JS 전량 인라인 → dist/heritage-archive.html
```

더미 데이터는 `scripts/generate_dummy.py`로 생성한다. 실데이터 전환 시 후속 작업은
`todos/009-realdata-followups.md` 참고.

## 화면 사용법 (인터랙션 규칙은 이게 전부)

| 조작 | 동작 |
|---|---|
| 사람(노드) 클릭 | 그 사람 중심 궤도 뷰 — 유사도 상위 이웃 + 공통 태그 라벨 |
| 팀 이름 클릭 (좌하단 범례) | 그 팀만 보기. **다시 클릭 / 빈 공간 클릭 = 전체 복귀** |
| 팀 이름 hover | 그 팀만 순간 강조 (상태 아님, 떼면 복귀) |
| CL 드롭다운 | CL 필터 — 팀 필터와 **교집합**으로 그래프에 적용 |
| Top-N 슬라이더 | 전체 뷰 인당 연결선 수 (2~10) |
| ⛶ (워드클라우드 패널) | 전체 화면 워드클라우드. 뒤에 그래프가 비침. 이때 클라우드 = 팀×CL 교집합 |
| 우하단 소형 클라우드 | 거시 참고용 — 팀 필터만 반영, CL 무시 |
| 우상단 버튼 | 파이프라인 설명 오버레이 (실제 벡터·유사도 수치로 설명) |
| ESC | 열린 것 닫기 (설명 → 최대화 → 궤도 뷰 순) |

딥링크: `#ego=<id>` (특정 인물 궤도 뷰), `#view=cloudmax`, `#view=about` — 데모 점프와
헤드리스 검증 겸용.

## 미래 과제 발굴 (task-discovery)

같은 회고 원문에서 "팀원이 직접 쓴 미래 과제 문장"만 뽑아 군집화한 별도 산출물.
설계는 `docs/task-discovery.md`, 구현 상세(스키마·결정 경로·함정)는
`docs/task-discovery-implementation.md` 참고.

```bash
export GEMINI_API_KEY=...
.venv/bin/python scripts/task_discovery.py   # sources 없으면 더미 20명 자동 생성
                                              # → dist/wiki/ (군집당 md + index.md 총평)
.venv/bin/python scripts/build.py            # 위 wiki가 있으면 heritage-archive.html에
                                              # "과제 지도" 토글로 통합 주입 (#view=tasks)
```

- 파이프라인: 인당 LLM 추출(과제/역량 항목화) → 문장별 임베딩 → KMeans 군집화 →
  군집당 LLM 페이지 생성 + 총평 1콜. 코드는 `scripts/task_discovery.py` 단일 모듈.
- 화면: `heritage-archive.html` 헤더의 [사람 지도|과제 지도] 토글, 또는 위키
  index 상단 "그래프로 보기" 링크. 사람 지도와 상태 미공유(별도 IIFE).
- 스테이지 캐시: `data/task_discovery/`(gitignore)에 추출·임베딩 결과가 있으면
  재실행 시 건너뛴다(LLM 0콜). 스키마를 바꿨으면 해당 JSON을 지우고 재실행할 것.
- 실명 + 원문 인용 산출물 — 사내 한정, `dist/wiki/`도 heritage-archive와 동일 배포 전제.

## 저장소 구조

```
archive/          화면 소스 — template.html(전부 여기, 과제 지도 IIFE 포함), cloud_logic.js(테스트되는 순수 로직),
                  echarts*.min.js, about/(설명 오버레이 슬롯: ppt.png·sample.md 놓고 재빌드)
scripts/          파이프라인 + build.py, config.py(K/EGO_DISPLAY_N/TOPN_MAX), task_discovery.py(미래 과제 발굴)
data/             persons/neighbors/freq/embeddings JSON (빌드 입력), task_discovery/(gitignore, 캐시 겸용)
dist/             heritage-archive.html(유일한 배포 산출물) + wiki/(과제 군집 md, 실명·인용 — 사내 한정)
tests/            pytest — 순수 함수(빈도·유사도·태그·클라우드 로직) + task_discovery 단위 테스트
docs/             PRD, handoff(현재 상태 스냅샷), task-discovery.md(설계)/-implementation.md(구현 해설)
todos/            파일 기반 이슈 트래커
```

## 검증

```bash
.venv/bin/python -m pytest tests/ -q     # 29개, LLM 호출부는 mock

# 화면 스모크 테스트 (구형 --headless는 워드클라우드가 안 그려짐 — 반드시 =new)
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --disable-gpu --window-size=1600,1000 --timeout=8000 \
  --screenshot=/tmp/shot.png "file://$PWD/dist/heritage-archive.html#view=cloudmax"
```

## 커스터마이즈 포인트

- `scripts/config.py` — K(저장 이웃 30) ≥ EGO_DISPLAY_N(10) ≥ TOPN_MAX(10)
- `scripts/build.py` `ABOUT_ANCHOR_ID` — 설명 오버레이의 표본 인물 (실데이터 전환 시 PPT/md 주인공 id로)
- `archive/about/ppt.png`, `archive/about/sample.md` — 넣고 재빌드하면 설명 오버레이에 자동 인라인
- `GEMINI_API_KEY` 환경변수 — embed/태그 추출 스크립트용 (빌드 자체엔 불필요)
