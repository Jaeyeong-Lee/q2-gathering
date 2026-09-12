# 3Q 분기회 발표 계획 — 개념 덱과 실데이터 성운 데모

> 작성 2026-09-13. **상태: Jay 컨펌 반영(2026-09-13). 발표일 2026-09-15.**
> 발표 작업의 정본 계획이다. 위치 요약은 [[q3-presentation-index]].
> 코드 경로는 특별한 표시가 없으면 `codex/future-task-capability-map` 브랜치(= T0 이후 통합 브랜치) 기준이다.

## 0. 읽는 법

| 누구 | 읽을 곳 |
|---|---|
| 모든 에이전트 | §1–§3, §9 |
| 티켓을 받은 에이전트 | §4, §5, 자기 티켓(§6) |
| 내부망 opencode·사람 | §6 T5, §8 |

## 1. 배경

- **자료** — 후공정 DRAM 테스트 부서 구성원 **300여 명**이 "근원경쟁력" 제목으로 각자 쓴 PPT 회고. 2Q 이후 새로 작성한 사람까지 포함한다. 1인 1텍스트로 파싱돼 있다. 성질과 한계: `docs/source-material-brief.md`.
- **요구** — 상사의 한 문장 "우리 팀 사람들이 쓴 근원경쟁력 기반으로, 우리 팀의 꿈이 담긴 향후 10년 로드맵". 자료는 개인의 근미래 서술이라 10년·순서·전략이 자료에 없다. 10년은 리더십 토론을 여는 해석 프레임으로 다룬다.
- **2Q 분기회(T-Talk)** — Heritage Archive. 사람 단위 임베딩 → 코사인 유사도 → 힘 기반 네트워크, 이름 검색·에고 뷰·워드클라우드. 무대에서 통했고 상시 아카이브로 남았다. 코드 `archive/template.html`·`scripts/build.py`, 설명 `README.md`·`docs/handoff.md`.
- **3Q 이번** — 같은 기록에서 사람별 미래 과제를 LLM으로 추출하고, PJT 안에서 닮은 과제를 미래 과제군(성운)으로 묶는다. 코드 `nebula/`, 계약 `docs/nebula-spec.md`, 운영 `docs/nebula-internal-runbook.md`, 에이전트 규칙 `nebula/CLAUDE.md`, 품질 문제 `HANDOFF.md`.
- **발표 태도** — `docs/design-candidates-2026-09-11/deck-soul.md`. 성운 개념은 구체화된 지 며칠 안 됐다. **장면 흐름은 이 문서 §2가 deck-soul의 "이야기의 뼈대"보다 우선**하고, deck-soul의 "화면의 태도"·"정직성"은 그대로 따른다.

## 2. 발표 흐름

메시지: 엔지니어들이 치열하게 고민해 쓴 PPT를, 더 잘 보이게 생명력을 불어넣어 그 노력이 heritage로 남도록 했다. 2Q에는 사람끼리의 닮음을, 3Q에는 각자의 미래를 읽었다.

### 1부 — 개념 덱 (합성 데이터 + Jay 예시, 스크립트 진행)

ELI5 수준의 큰 그림. 기술 설명은 발표자의 말로, 화면은 전환으로.

| # | 장면 | wow | 담당 |
|---|---|---|---|
| 1-0 | 도입 문장 — 치열하게 쓴 기록, heritage | | 스토리 레이어 |
| 1-1 | 2Q: PPT 이미지 → 텍스트 → 임베딩 아이콘을 지나며 별이 됨 | wow1 | 스토리 레이어 |
| 1-2 | 2Q: 벡터끼리의 닮음 → 카메라가 멀어지며 별 300여 개 네트워크 | wow2 | 스토리 레이어 → 엔진 장면 0 |
| 1-3 | 3Q: 별 하나 클로즈업 → LLM 아이콘을 지나며 미래 과제로 분열 (Jay 예시) | wow3 | 엔진 장면 0 |
| 1-4 | 원래 화면으로 빠짐 → 넘기면 전원이 분열 — **한 번 재생되는 전환** | wow4 | 엔진 장면 1 |
| 1-5 | 과제 별이 PJT 칸(8개면 4×2)으로 해쳐모임 | | 엔진 장면 2 |
| 1-6 | 한 PJT에 들어가 닮은 과제끼리 성운 | wow5 | 엔진 장면 2 |
| 1-7 | 과제 하나의 확보/필요 역량 (결정 4에 따라 생략 가능) | | 엔진 장면 3 + 스토리 카드 |
| 1-8 | 맺음 — "우리의 미래 경쟁력이 팀의 로드맵" | | 스토리 레이어 |

비트별 화면·엔진 호출·끝 상태는 `docs/q3-visual-brief.md` §2가 정본이다.

### 2부 — 실제 산출물 (실데이터, 발표자 조작)

| # | 조작 | 화면 |
|---|---|---|
| 2-0 | 시작 | 2Q 유사도 네트워크 (Heritage 이식본, 300여 명 전원) |
| 2-1 | 사람 이름 검색 | 그 사람에게 클로즈업(수 초) → 끝나면 자동으로 그 사람의 추출 과제가 터짐 |
| 2-2 | 넘김 | 전원 분열 — 한 번 재생되는 전환 |
| 2-3 | 넘김 → PJT 칸 클릭 | 과제 별이 PJT 칸(4×2)으로 해쳐모임. 검색한 사람의 PJT 칸과 그 사람 과제 하이라이트 → 칸을 클릭하면 그 PJT로 들어가 과제군 성운. 뒤로 가면 격자. 사람 선택 해제 시 하이라이트 없음 |
| 2-4 | 과제 클릭 | 그 과제의 원문 인용과 확보/필요 역량 근거 (결정 4) |

발표 뒤 청중이 같은 화면을 각자 웹으로 연다(T7).

## 3. 확정된 결정 — 2026-09-13, Jay

1. **데이터 원천은 nebula.** td 파이프라인(`extracted.json`)은 이번 발표에 쓰지 않는다.
2. **Heritage Archive를 nebula에 이식한다.** 두 앱을 잇지 않고, nebula 발표 화면이 2Q 네트워크 장면을 갖는다.
3. **시간 장면(단기·중기·장기)은 잠정 보류.** 코드는 두고 발표 순서에서 뺀다. 관련 이슈 #49와 #53도 보류.
4. **역량은 선택.** 실데이터 품질이 끝내 안 나오면 1-7·2-4에서 뺀다. T5 품질 점검으로 판단.
5. **1부와 2부는 같은 엔진.** 1부 = 합성 페이로드 + 스토리 스크립트, 2부 = 실데이터 페이로드 + 수동 조작.
6. **분열 장면(1-3)은 Jay 예시.** 데이터는 추후 전달(§5.3).
7. **실제 PJT 이름은 저장소에 쓰지 않는다.** 시연 PJT는 발표 빌드에서만 지정한다.
8. **발표일은 2026-09-15.**
9. **인원은 300여 명 전원.** 2Q 이후 새로 작성한 사람도 네트워크와 과제에 모두 들어간다 → 2Q 유사도 네트워크를 전원 기준으로 다시 계산한다(T5-1).
10. **전원 분열은 한 번 보여주는 전환, 성운은 PJT별로만.** 전체 과제 별을 머무는 탐색 화면으로 두지 않고, 전체 PJT를 동시에 성운으로 모으지 않는다. 발표 노트북과 청중 서빙 양쪽의 성능을 위한 결정이다.
11. **청중용 웹 버전에 전원 원문을 포함해도 된다.**
12. **검토는 전원 대상으로 한다.** 부분 승인으로 줄이지 않는다.
13. **성운은 PJT 격자에서 클릭해 들어간다.** 과제 별이 먼저 PJT 칸(8개면 4×2)으로 해쳐모이고, 칸 하나를 클릭하면 그 PJT 과제만 과제군 성운으로 모인다. 결정 10의 "PJT별로만"을 구체화한 것이다.

## 4. 설계 — 한 엔진, 두 모드

### 4.0 무엇을 고치나

**코드 1벌, 빌드 2벌.** 1부 덱과 2부 산출물은 같은 `nebula.html`을 서로 다른 데이터로 빌드한 것이다(결정 5). 이번 작업의 코드는 거의 전부 nebula 수정이다.

| 고치는 곳 | 무엇 | 티켓 |
|---|---|---|
| `nebula/templates/nebula.html` | 장면 재구성, 검색·클로즈업, PJT 격자, story 모드 | T3 |
| `nebula/templates/story.js` (새 파일) | 1부 도입·wow1·wow2·맺음, 1부 스크립트 | T4 |
| `nebula/render.py` | 빌드 타임 레이아웃, `__STORY__` 인라인 | T2, T4 |
| `nebula/demo.py`·`nebula/__main__.py`, `nebula/fixtures/q3/` | `demo --input`, 320명 합성 픽스처 | T1 |
| `tests/nebula_*.cjs`, `tests/test_nebula_pipeline.py` | 새 장면에 맞춘 테스트 | T1–T3 |

추출·분류 파이프라인(`pipeline.py`·`model.py`·`prompts.py`·`llm.py`)은 고치지 않는다. 품질 이슈 #49·#53은 보류, #51은 역량을 유지할 때만 연다.

| 산출물 | 빌드 | 티켓 |
|---|---|---|
| 1부 덱 | 합성 픽스처 → `nebula.html#mode=story` | T1–T4, T8 |
| 2부 산출물 | 내부망 실데이터 → `nebula.html` (live) | T5, T7 |

### 4.1 지금 있는 것

**`nebula/templates/nebula.html`** — 오프라인 단일 HTML, SVG + CSS transition.
- 상태 `S={scene,pjt,category,task,person,skill,query}`. 장면 0–4 = 사람·과제·성운·시간·역량.
- `target(t)`가 장면별 과제 별 좌표를 정하고 `transform` transition(1.65s)이 이동을 그린다. 장면 0의 사람 좌표는 페이로드 `people[].x/y`(0–1), 없으면 원형 배치.
- `go(i)`·`selectTask(id)`·`selectCategory(id)`·`render()`, 해시 저장·복원(`#scene=&pjt=&category=&task=&person=`), 자동 발표 `#play`.
- 과제 패널에 원문 인용과 역량 근거(`skills[].relation_quote`)가 이미 있다 → 2-4는 새로 만들 것이 적다.
- 페이로드는 `nebula/render.py` `build_nebula()`가 만든다. 사람 전원의 `text`가 들어간다(결정 11로 그대로 둔다).
- 테스트가 잡는 셀렉터: `.step.active` 텍스트, `#sky g.task / g.person / g.skill`, `[data-scene]`, `#panel`, `#play`, `[data-person-node]` — `tests/nebula_browser.cjs`, `tests/nebula_presentation.cjs`, `tests/test_nebula_pipeline.py::NebulaPresentation`.

**`archive/template.html`** — 2Q, canvas.
- 레이아웃: `seedPositions`(PJT 앵커 주변 원반, `Math.random`), `tick()`(반발 + 유사도 스프링 + PJT 앵커 인력 + 감쇠), `warmUp(300)` — 945–1096행.
- 에고 뷰 `egoTargets`·`enterEgo`·`exitEgo`, 이름 검색 `renderResults`, 배경 별밭 `drawStars`, 글로우 스프라이트.
- 입력: `persons.json` + `neighbors.json`(`{"<id>":[{"id","similarity"}]}`, 인당 K=30).

**`nebula/network.py`는 heritage `neighbors.json` 형식을 이미 받는다.** 좌표가 없을 뿐이다.

### 4.2 이식 범위 — Heritage → nebula

| 가져온다 | 방식 |
|---|---|
| 유사도 기반 힘 배치 | 빌드 타임 파이썬 포팅(4.3) |
| 유사도 연결선 | 기존 `edges`, 전체 뷰는 인당 상위 N개만 |
| PJT 색 | 기존 `PALETTE` |
| 이름 검색 | 템플릿에 검색 입력 추가 |
| 클로즈업 | 에고 뷰 대신 카메라 줌 + 분열(4.4) |
| 배경 별밭·글로우 | 2Q 화면으로 알아볼 수준만(선택) |

가져오지 않는다: 워드클라우드, CL 필터, Top-N 슬라이더, How it Works 오버레이, 태그 필터, 노드 드래그.

### 4.3 레이아웃 — 빌드 타임, 결정적

- heritage `tick()`을 파이썬으로 옮기고 시드 고정 난수를 쓴다. PJT 앵커는 PJT 색인으로 원형 배치해 일반화한다.
- 위치: `build_nebula()` 안에서, 제공된 좌표가 없고 연결선이 있을 때만 계산한다. **렌더 단계라 `result.json`·`run_id`·검토 승인은 그대로다.**
- 제공된 좌표가 있으면 그대로 쓴다(기존 동작).
- 화면 문구는 "배치 = 기존 유사도 연결로 계산한 표시용 배치"로 밝힌다. 새 유사도는 만들지 않는다.
- 2Q와 똑같은 자리는 나오지 않는다(2Q는 난수 시드·실시간 물리, 인원도 늘었다). 같은 유사도·같은 힘으로 군집 모양이 닮는 것이 목표다.

### 4.4 장면 재구성 — 엔진

스텝 바에 남는 장면:

| 새 번호 | 이름 | 기존 대응 | 비고 |
|---|---|---|---|
| 0 | 사람 (2Q 네트워크) | 장면 0 + 검색·클로즈업·개인 분열 상태 | 전원 표시 |
| 1 | 미래 과제로 펼치기 | 장면 1 | 한 번 재생되는 전환(결정 10) |
| 2 | 성운 | 장면 2 | PJT 격자 → 클릭한 PJT 안에서만 과제군 성운. 선택 인물 하이라이트 |
| 3 | 과제·역량 | 과제 패널 중심 | 기존 장면 4(과제군 역량 버블)는 결정 4에 따름 |
| 보류 | 시간 | 기존 장면 3 | 스텝 바에서 제외, 코드 보존 |

장면 0의 개인 흐름:
1. 검색 결과 선택 또는 별 클릭 → `S.person` 설정 → 월드 그룹 `<g>`의 transform으로 그 사람에게 줌(약 2초).
2. 줌이 끝나면 자동으로 그 사람의 과제 별만 사람 자리에서 갈라져 나온다(장면 1의 `seq` 오프셋 재사용).
3. ESC 또는 빈 곳 클릭 → 줌 아웃, 과제 별은 사람 자리로 돌아간다.

장면 1 — 한 번 재생되는 전원 분열:
- 들어오면 전원의 과제 별이 사람 자리에서 갈라져 나오는 전환을 한 번 재생하고 멈춘다. 반복 재생·과제 클릭 탐색은 이 장면의 역할이 아니다.
- 다음으로 넘기면 장면 2의 PJT 격자로 간다.

장면 2 — PJT 격자에서 들어가는 성운:
1. **격자**: 과제 별이 PJT 칸으로 해쳐모인다. PJT가 8개면 4열×2행이고, 개수가 달라도 4열 격자로 둔다(PJT 수는 코드에 고정하지 않는다 — `docs/nebula-internal-runbook.md` §2). 칸마다 PJT 이름과 과제 수를 적는다. 칸 안의 별은 느슨한 구름이며 과제군으로 나누지 않는다. `S.person`이 있으면 그 사람의 PJT 칸과 과제를 하이라이트한다.
2. **진입**: 칸 클릭 → 그 칸이 화면 전체로 커지고 다른 칸의 별은 사라진다(DOM 제거 또는 `display:none`) → 그 PJT 과제가 과제군 성운으로 모인다. 이때 움직이는 노드는 한 PJT분이다.
3. **나가기**: ESC 또는 뒤로 → 격자로 돌아간다. 해시는 격자면 `pjt` 없음, 진입 상태면 `pjt=<색인>`.
- PJT 안 과제군 배치는 기존 `clusterCenter`(과제군 수와 무관한 격자+링)를 재사용한다.

글자는 줌되는 SVG 밖 HTML 레이어에 둔다(글자가 같이 커지지 않게). 근거: `docs/nebula-opening-scene-concept.md` 백로그 절.

### 4.5 두 모드와 계약

| | story (`#mode=story`) | live (기본) |
|---|---|---|
| 페이로드 | 합성 픽스처 + 예시 인물(§5) | 내부망 실행 결과, `--approved-only` |
| 화면 틀 | 헤더·패널·스텝 바 숨김, 중앙 문장 한 줄 | 현행 레이아웃 + 검색 |
| 진행 | Space/→ 다음 비트, ← 이전, R 다시 | 발표자 조작 |
| 스토리 레이어 | 켜짐 (1-0·1-1·1-2·1-7 카드·1-8) | 꺼짐 |
| 합성 표시 | 항상 | 없음 |

**엔진 ↔ 스토리 계약(`window.nebula`, `window.nebulaCopy`, `window.nebulaStory`), 화면 문구 파일 `nebula/templates/deck.md` 형식, 시각 작업 폴더 규칙의 정본은 `docs/q3-visual-brief.md` §3·§5다.** 바꾸려면 그 문서를 먼저 고친다.

## 5. 가짜 데이터

### 5.1 이미 있는 것

- `python3 -m nebula demo --out <dir>` — `nebula/demo.py` `source()`: 합성 200명, 8 PJT, `FakeClient`(LLM 0회), TF-IDF 이웃 인당 4명, 좌표 없음. 출력 `<dir>/synthetic-persons.json`·`synthetic-network.json`·`result.json`·HTML 3종.
- `FakeClient`는 `source()`의 문장 모양("…과제를 추진하고 싶다.", "이 과제에는 …", "이를 위해 … 역량이 더 필요하다.")만 추출한다.

### 5.2 만든 것 — `nebula/fixtures/q3/` (T1 완료, 커밋, 전부 합성)

| 파일 | 내용 | 실데이터 대응 |
|---|---|---|
| `persons.json` | **320명**, 8 PJT(`demo.py` `TEAM_TOPICS` 이름), 과제 0–4개 분포(0개 약 5%), `FakeClient` 문장 모양. PJT 인원은 고르지 않게(가장 큰 PJT 70명 안팎 — 장면 2 성능 확인용) | runbook §2 `persons.json` |
| `neighbors.json` | heritage 형식, 전원, 인당 상위 30 | T5-1에서 다시 계산한 전원 `neighbors.json` |
| `showcase.json` | `{"person_id": "P000", "pjt": "<합성 PJT>", "task_index": 0}` — 1부 스크립트의 예시 인물·PJT·과제 | 발표 빌드에서만 지정 |
| `make.py` | 위 셋을 결정적으로 생성 | — |
| `README.md` | 합성 명시, 재생성 명령, `P000` 교체 절차 | — |

- `P000` "예시 인물": 과제 4개·역량 연결 8개를 쓴 자리표시 원문. Jay 예시가 오면 이 한 사람만 바꾼다(5.3).
- `demo`는 `--input`을 받는다: 있으면 `source()` 대신 그 파일을 쓴다.
- `FakeClient`는 `기타 `로 시작하는 과제를 분류하지 않는다 → 픽스처에서 미분류 경로가 재현된다. 기존 `demo` 200명 결과는 변경 전후 동일.
- **실측**: 320명, 과제 682, 과제군 40(PJT당 5), 과제 0개 19명, 미분류 17건, PJT별 과제 39–159, 연결선 5,923개(좌표 없음). 빌드 0.66초. 연결선이 많으니 장면 0은 그리기 전에 인당 상위 N개로 줄인다(§4.2).

모든 에이전트 공통 재현:

```sh
python3 nebula/fixtures/q3/make.py
python3 -m nebula demo --input nebula/fixtures/q3/persons.json \
  --network nebula/fixtures/q3/neighbors.json --out <스크래치>/q3
# 브라우저로 file://<스크래치>/q3/nebula.html#mode=story
```

실데이터 빌드는 같은 모양의 파일로 `run --input … --network …`만 다르다. 픽스처가 곧 입력 계약의 예시다.

### 5.3 대기 중 — Jay 예시 (분열 장면)

- 받을 것: 예시 원문 1편, 거기서 나온 미래 과제 3–4개(원문 인용 그대로), 선택적으로 과제별 확보/필요 역량.
- 넣는 곳: `persons.json`의 `P000.text` 교체 → `make.py` 재실행. `FakeClient` 문장 모양에 안 맞으면 `P000`만 `--corrections`로 추출 결과를 넣는다(runbook §7).
- 공개 여부: 저장소가 GitHub에 있다. 커밋해도 되는 내용인지 Jay가 먼저 확인한다. 안 되면 `P000`은 합성으로 두고 발표 빌드 때만 로컬에서 바꾼다.

## 6. 작업 티켓

의존: `T0 → {T1, T2, T3, T4}` 병렬. `T5`는 지금 바로 병렬(내부망). `T3 + T4 → T6`. `T5 → T7`.

규칙:
- 각 에이전트는 통합 브랜치에서 자기 브랜치를 따고, 끝나면 통합 브랜치로 머지한다.
- `nebula/templates/nebula.html`은 T3만 고친다. T4는 `story.js`와 `render.py`의 `__STORY__` 한 곳, T1·T2는 파이썬과 픽스처만.
- 티켓이 끝나면 아래 상태 표에 커밋을 적는다.

| 티켓 | 상태 | 커밋 |
|---|---|---|
| T0 | 완료 — 워크트리 `~/orca/workspaces/q2-gathering/q3-nebula`, #47 닫음 | `0033854` (머지. `CLAUDE.md` 충돌은 두 절 모두 유지) |
| T1 | 완료 — 계약 테스트 34 passed, mypy 통과 | `3ca66ef` |
| T2 | 완료 (Codex 작성, Claude 검증·커밋) — `nebula/layout.py`, 결정성·비변경 테스트 | (T3와 같은 커밋) |
| T3 | 뼈대 완료 (Codex 작성, Claude 검증·커밋) — 네 장면·검색·클로즈업·4열 PJT 격자·`window.nebula`·story 모드, `tests/nebula_q3.cjs`. 모션·톤은 시각 작업 몫. 시각 담당 안내 `docs/q3-visual-brief.md` | (이 표를 담은 커밋) |
| T4 | L0 완료(deck.md·빌드 인라인·`NEBULA_STORY`·`splitPerson`·`q3_story_check`), V-story·V-engine 대기 — 역할과 완료 기준은 `docs/q3-visual-brief.md` §4 | L0: (이 행을 담은 커밋) |
| T5 | 대기 | (내부망, 커밋 없음) |
| T6 | 대기 | |
| T7 | 대기 | |
| T8 | 대기 — 문구는 `nebula/templates/deck.md`(L0이 초안 작성, Jay가 수정) | |

### T0 통합 브랜치 — 순차, 가장 먼저

- 선행: 이 문서와 `docs/q3-presentation-index.md`를 `Jaeyeong-Lee/feat-td-extract-ax`에 커밋·push.
- 머지:
  ```sh
  git switch -c Jaeyeong-Lee/q3-nebula-presentation codex/future-task-capability-map
  git merge Jaeyeong-Lee/feat-td-extract-ax
  ```
  2026-09-13 `git merge-tree`로 충돌 없음을 확인했다. 디자인 브랜치 쪽 고유 커밋은 문서·스킬 5개(`8803475`~`154b558`)뿐이다.
- GitHub #47 닫기(커밋 `d256e91`로 끝났는데 열려 있음).
- **완료**: 브랜치 push, `docs/q3-presentation-plan.md`·`docs/design-candidates-2026-09-11/`·`nebula/`가 한 브랜치에 존재, `pytest tests/test_nebula_pipeline.py tests/test_nebula_http.py tests/test_nebula_network.py -q` 통과.

### T1 합성 픽스처 — 에이전트

- §5.2 전부 + `demo --input`.
- **완료**: §5.2 재현 명령이 `Completed: persons=320`을 출력; `make.py` 두 번 실행 결과가 바이트 동일; 과제 0개 인물과 미분류 과제가 각각 1건 이상; `--input`이 `source()`를 대체하는 테스트 1개 추가; nebula 계약 테스트 통과.

### T2 빌드 타임 레이아웃 — 에이전트

- §4.3. 참고 `archive/template.html` 945–1096행.
- T1 전에는 `demo` 200명으로 개발한다.
- **완료**: 같은 입력 → 같은 좌표 테스트; 제공된 좌표는 그대로 쓰는 테스트; `test_supplied_layout_is_normalized_and_absence_is_reported`의 부재 표기를 "계산된 배치" 표기로 갱신; 320명 빌드 30초 이내(`ponytail:` 주석으로 O(n²) 한계 명시); 장면 0 스크린샷에서 원형이 아닌 PJT 군집이 보임.

### T3 엔진: 장면 재구성·검색·클로즈업·모드 — 에이전트, `nebula.html` 단독

- §4.4 전부, §4.5의 엔진 쪽과 `window.nebula` 계약 구현.
- **완료**:
  - 두 브라우저 테스트를 새 장면 번호에 맞게 고치고 통과. `nebula/CLAUDE.md` 계약 5의 셀렉터 유지.
  - 새 브라우저 검사(1920×1080, 픽스처 320명):
    - 검색 → `focusPerson` resolve 뒤 그 사람의 보이는 `g.task` 수 = 페이로드상 그 사람 과제 수.
    - 장면 2 격자에서 PJT 칸 수 = 페이로드 PJT 수, 칸마다 적힌 과제 수가 페이로드와 일치. `S.person`이 있으면 그 사람의 PJT 칸과 과제만 하이라이트.
    - 칸 클릭 → `enterPjt` resolve 뒤 보이는 `g.task` 수 = 그 PJT 과제 수. ESC → 격자 복귀. `#scene=2&pjt=<색인>`으로 새로고침하면 진입 상태 복원.
    - `#mode=story`에서 헤더·패널·스텝 바 숨김.
    - 콘솔 오류 0.
  - 시간 장면이 스텝 바와 자동 진행에 나오지 않음.
  - `nebula/CLAUDE.md`·`docs/nebula-internal-runbook.md`·`README.md`의 "다섯 장면" 서술을 새 구성으로 갱신.

### T4 스토리 레이어: 1부 9비트 스크립트 — 세부 역할·완료 기준은 `docs/q3-visual-brief.md` §4

- §2 1부 전체를 `window.nebula` 계약으로 구동한다. T3 전에는 계약을 흉내 내는 스텁으로 개발한다.
- 시각 출발점: `docs/design-candidates-2026-09-11/pitch-cosmos-v2/`(문서 압축·점화 모션). 태도: `deck-soul.md`(검은 배경, 중앙 문장 하나, 대강당 거리에서 읽히는 글자, 자동 슬라이드 없음). 아이콘: `docs/nebula-opening-scene-concept.md`(얇은 선 아이콘, 크로스페이드).
- wow1의 PPT 이미지는 판독할 수 없는 추상 슬라이드로 그린다.
- **완료**: `docs/q3-visual-brief.md` §4의 V-story·통합 완료 기준. 비트별 스크린샷 9장은 후보 폴더 `docs/q3-visual/<agent-id>/shots/`에 커밋한다.

### T5 내부망 실데이터 — opencode + 사람 (Claude·Codex 제외)

1. **입력**: 3Q `persons.json`(runbook §2) — 2Q 이후 새로 작성한 사람 포함 300여 명 전원.
2. **네트워크 재계산**: 추가 작성자까지 **전원을 같은 임베딩 모델**로 계산해 `neighbors.json`을 새로 만든다(모델이 섞이면 유사도를 비교할 수 없다). 2Q 모델을 내부망에서 그대로 쓸 수 없으면 전원을 내부 임베딩 모델로 다시 계산한다. 유사도 → 이웃 변환은 `scripts/similarity.py`(인당 K=30). ID는 `persons.json`과 같은 체계, ID로만 결합한다.
3. **실행**: `python3 -m nebula run --input … --network … --out /secure/runs/q3-001` (내부 endpoint).
4. **품질 표본 점검**: `docs/nebula-quality-evaluation.md`. 특히 과제–역량 연결 → **결정 4 판단**.
5. **시연 선정**: 2-1 검색 인물, 1-5·2-3 시연 PJT, 2-4 시연 과제(역량 근거가 있는 것).
6. **전원 검토** → `review.json` → `python3 -m nebula build --out … --review … --approved-only`.
- 외부 에이전트에게 넘기는 것: 인원 수·과제 수·PJT 수·PJT별 과제 수 최댓값·미분류 비율·역량 연결 수, 실패 시 `status.json`의 stage와 오류 코드. 이름·원문·과제군 이름은 넘기지 않는다.
- **완료**: 전원 기준 `neighbors.json`, `status.json` complete, 승인 빌드 생성, 시연 대상 ID가 내부에만 보관됨, 결정 4 기록.

### T6 성능·리허설 — 에이전트 + 사람 (T3·T4 후)

- 발표 노트북, 1920×1080, `file://`, 네트워크 끊은 상태. 청중이 여는 일반 사내 PC 한 대에서도 같은 확인.
- 확인 지점: 장면 0 전원 네트워크, 장면 1 전원 분열 한 번, 장면 2 격자로 해쳐모이기 한 번, 가장 큰 PJT 진입 성운. 끊기면 연결선 수와 blur 필터부터 줄인다.
- 1부 통리허설, 2부 검색 → 분열 → 성운 → 과제 클릭 통리허설.
- **완료**: 체크리스트 전 항목 기록, 1부 녹화 영상 백업 여부 결정.

### T7 청중용 웹 서빙 — 사람 결정 후 에이전트

- 정할 것: 사내 정적 호스팅 위치, 접근 범위. 전원 원문 포함은 결정 11로 확정.
- 실데이터 HTML은 사내 호스팅에만 둔다. `dist/`와 저장소는 GitHub로 공개되며, nebula 코드도 `dist` 출력을 거부한다.
- **완료**: 청중 URL 확정, 그 URL에서 `file://`과 같은 동작 확인.

### T8 화면 문장·발표 멘트 — 사람 + 에이전트 초안

- 비트별 화면 문장 1줄, 발표자 노트, 맺음 문장.
- 기준: `nebula/CLAUDE.md` "산출물에서 하지 말 것" — 작성자 수는 중요도가 아니고, 성운 배치는 분류 품질의 증명이 아니며, 자동 로드맵이 아니다.
- **완료**: `story.js`에 문장 반영, 노트 파일 1개.

## 7. 일정 — 발표 2026-09-15

| 날 | 할 일 |
|---|---|
| 09-13 (D-2) | T0 → T1·T2·T3·T4 착수. T5-1·2 네트워크 재계산, T5-3 실행 시작 |
| 09-14 (D-1) | T3·T4 통합, T6 성능 1차. T5-4 품질 → 결정 4, T5-5 시연 선정, T5-6 전원 검토. T8 초안 |
| 09-15 (D-day) | 오전: 승인 빌드, T6 통리허설, T7 서빙 |

## 8. 남은 위험

| # | 무엇 | 왜 문제인가 | 대응 |
|---|---|---|---|
| 1 | Jay 예시 데이터 | wow3가 자리표시로 남는다 | §5.3. D-1까지 받으면 반영 |
| 2 | 네트워크 재계산 | 추가 작성자 임베딩이 없거나 2Q 모델을 다시 못 쓰면 전원 재계산이 필요하다 | T5-2 가장 먼저. 막히면 D-2 안에 알린다 |
| 3 | 역량 품질 | 과제에 들어갔는데 역량이 비어 보일 수 있다 | 결정 4. 시연 과제는 역량 근거가 있는 것으로 |
| 4 | 성능 | 전원 네트워크 + 전원 분열 한 번 + 격자 해쳐모이기 한 번 + 가장 큰 PJT 성운 | 결정 10·13으로 범위를 줄였다. T2 직후 320명으로 조기 측정 |
| 5 | 검토 일정 | 전원 검토가 D-1 하루에 몰린다 | T5-3 실행을 D-2에 끝내 둔다 |
| 6 | 2Q 화면과의 연속성 | canvas 글로우·별밭과 nebula SVG의 톤이 다르다 | 4.2 선택 항목. "지난번 화면"으로 알아볼 수준까지만 |
| 7 | 병렬 충돌 | 템플릿이 40KB 한 파일이다 | T3 단독 소유 + `story.js` 분리 + §4.5 계약 |
| 8 | 인원 숫자 | 1부 300여는 연출, 실제 수는 실행 결과 | 1부는 합성 표시, 2부 숫자는 페이로드에서 계산(현행) |
| 9 | 청중 호스팅 위치 | 미정 | T7, D-1까지 사람 결정 |

## 9. 모든 에이전트가 지킬 것

- **실데이터** — Claude Code·Codex·외부 모델은 실데이터와 nebula 실행 출력(`result.json`, `view.json`, HTML 3종, `cache/**`)을 열지 않는다. 규칙은 루트 `CLAUDE.md`와 `nebula/CLAUDE.md`. 개발·검증은 §5 픽스처로 한다. opencode는 `AGENTS.md`를 따른다.
- **nebula 계약** — `nebula/CLAUDE.md` "깨면 안 되는 계약" 7개. 인용 정확 일치, 검증을 풀지 않고 프롬프트나 정정으로 고침, 템플릿 셀렉터 유지.
- **정직성** — `deck-soul.md` 정직성 절. 위치·거리·크기·밝기는 우열·중요도·준비도를 뜻하지 않는다.
- **서빙** — 데이터를 인라인한 단일 정적 HTML. 검증은 `file://`로 연다.
- **시안 보존** — `docs/design-candidates-2026-09-11/`의 기존 파일은 그대로 두고 새 파일로 추가한다.

## 10. 링크

| 무엇 | 경로 | 브랜치 |
|---|---|---|
| 자료 성질·요구 | `docs/source-material-brief.md` | 공통 |
| 발표 태도 | `docs/design-candidates-2026-09-11/deck-soul.md` | feat-td-extract-ax |
| 최신 모션 시안 | `docs/design-candidates-2026-09-11/pitch-cosmos-v2/` | feat-td-extract-ax |
| 5모델 디자인 리뷰 | `docs/design-candidates-2026-09-11/llm-reviews-2026-09-12.md` | feat-td-extract-ax |
| 오프닝·클로즈업 컨셉 | `docs/nebula-opening-scene-concept.md` | codex |
| nebula 에이전트 규칙 | `nebula/CLAUDE.md` | codex |
| nebula 명세 | `docs/nebula-spec.md` | codex |
| nebula 운영 | `docs/nebula-internal-runbook.md` | codex |
| nebula 품질 문제 | `HANDOFF.md` | codex |
| nebula 품질 평가표 | `docs/nebula-quality-evaluation.md` | codex |
| 발표 화면 연결 경위 | `docs/nebula-handoff-2026-09-11.md` | codex |
| `--agent` 모드 | `docs/nebula-agent-run.md` | codex |
| 발표 템플릿 | `nebula/templates/nebula.html` | codex |
| 페이로드·빌드 | `nebula/render.py` | codex |
| 네트워크 입력 | `nebula/network.py` | codex |
| 합성 데모 | `nebula/demo.py` | codex |
| 2Q 화면 | `archive/template.html` | 공통 |
| 2Q 빌드·데이터 계약 | `scripts/build.py`, `README.md` | 공통 |
| 2Q 유사도 → 이웃 | `scripts/similarity.py` | 공통 |
| 2Q 설계 경위 | `docs/handoff.md` | 공통 |
| 8/14 임원 보고 원고 | `docs/2026-08-14-exec/script.md` | exec-deck-narrative-flow |

T0 전에는 다른 브랜치 파일을 워크트리를 옮기지 않고 `git show <브랜치>:<경로>`로 읽는다. T0 뒤에는 모두 통합 브랜치에 있다.
