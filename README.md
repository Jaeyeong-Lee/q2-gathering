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

## 저장소 구조

```
archive/          화면 소스 — template.html(전부 여기), cloud_logic.js(테스트되는 순수 로직),
                  echarts*.min.js, about/(설명 오버레이 슬롯: ppt.png·sample.md 놓고 재빌드)
scripts/          파이프라인 + build.py, config.py(K/EGO_DISPLAY_N/TOPN_MAX)
data/             persons/neighbors/freq/embeddings JSON (빌드 입력)
dist/             heritage-archive.html (유일한 배포 산출물)
tests/            pytest — 순수 함수(빈도·유사도·태그·클라우드 로직) 단위 테스트
docs/             PRD, handoff(현재 상태 스냅샷 — 에이전트 인수인계용)
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

## 미래 과제 × 역량 지도 (Nebula)

사람별 텍스트와 기존 유사도 네트워크에서 PJT별 미래 과제·시간·보유/필요 역량을 추출하고 검토하는 별도 파이프라인입니다. 기존 Archive와 `td_*` 산출물을 변경하지 않습니다.

발표 산출물은 `nebula.html`입니다. **사람 → 미래 과제로 펼치기 → 성운 → 과제·역량**의 네 장면을 자동 발표(10초 간격)나 좌우 화살표로 넘깁니다. 이름 검색으로 한 사람의 과제를 펼치고, 성운 장면에서 PJT 격자 칸을 눌러 진입합니다. ESC로 격자에 돌아옵니다. 시간 장면은 보류하며 `matrix.html`에서 같은 결과를 시간 × 역량 축으로 볼 수 있습니다. `#mode=story`는 발표 연출용으로 화면 틀을 숨깁니다. 시각 작업 안내는 [공통 요구사항](docs/q3-visual-brief.md)을 봅니다.

```sh
python3 -m nebula demo --out data/nebula-demo
```

`nebula.html`(발표용 네 장면), `matrix.html`(시간 × 역량 버블), `review.html`(검토)을 로컬에서 엽니다. 실제 내부 모델 연결, 입력 계약, 실패 재개, 수정과 승인 빌드는 [내부망 실행 가이드](docs/nebula-internal-runbook.md)를 먼저 읽으세요. 구현 범위와 해석 기준은 [기능 명세](docs/nebula-spec.md)에 있습니다. Python 3.10+ Linux/macOS, 런타임 추가 패키지 없음.
