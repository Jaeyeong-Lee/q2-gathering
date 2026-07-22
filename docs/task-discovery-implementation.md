# task-discovery 확장 구현 해설 (#8~#10) — 로컬 모델용 자기완결 문서

이 문서의 독자는 **저장소를 자유롭게 탐색하기 어려운 로컬 모델/신규 에이전트**다.
코드를 열지 않아도 이번 확장(이슈 #8·#9·#10)의 구조·데이터 스키마·결정 경로를
이해할 수 있도록 썼다. 설계 정본은 `docs/task-discovery.md`, 저장소 전반 인수인계는
`docs/handoff.md` — 이 문서는 그 사이의 "구현이 왜 이렇게 생겼는지" 상세다.

---

## 0. 전체 그림 (30초 버전)

근원경쟁력 회고(인당 pptx 텍스트, 지금은 더미)에서 **팀원이 직접 쓴 미래 과제 문장**을
뽑아 지도로 만든다. 전부 빌드타임, 런타임 API 0.

```
sources.json (인당 원문, 더미 생성기)
  → run_extract   인당 LLM 1콜: tasks[]/capabilities[] 항목화     → extracted.json
  → run_embed     문장별 임베딩 (사람당 1개 아님)                  → task_vectors.json 등
  → run_cluster   정규화+KMeans (유클리드=코사인)                  → clusters.json 등
  → run_pages     군집당 LLM 1콜(제목·요지·파생 제안)
                  + 총평 LLM 1콜(#9)                               → dist/wiki/*.md
  → build.py      과제 그래프 페이로드 주입(#10)                   → dist/heritage-archive.html
```

- 파이프라인 코드는 **`scripts/task_discovery.py` 단일 모듈**. LLM은 `call`/`embed`
  함수 주입식이라 테스트는 전부 mock (키 불필요).
- 화면은 **`archive/template.html` 단일 파일** → `scripts/build.py`가 데이터를 문자열
  치환으로 인라인해 `dist/heritage-archive.html` 하나로 만든다. GitHub Pages 정적 서빙,
  `file://` 로 열어도 동작 (로컬 dev 서버 제안 금지 — 사용자 반복 지적 사항).

---

## 1. 문제의식과 세 갈래 — 생각의 경로

2026-07-18 그릴링 세션의 출발점: **"파이프라인이 '모으기'까지만 하고, 의미를 찾거나
정제하는 단계가 없다. 위키에 군집을 나열하는 것만으로는 보여주는 의미가 약하다."**

이 문제의식에서 대안들을 걸러낸 경로:

| 검토한 것 | 결론 | 이유 |
|---|---|---|
| 우선순위 제안 (군집에 순위 매기기) | **보류** | 가중치 근거 시비. "인원수·단기 비중·역량 근접도 지표 3개만 표로 노출, 순위 없음" 제안까지 갔고 Jay 결정 대기. 구현하지 말 것 |
| 사람 단위 요약으로 회귀 | 기각 | 원래 설계가 기각한 방향(사람 지도로 되돌아감). 문장 단위 유지 |
| 요약층(총평)을 별도 페이지로 | 기각 | index 나열 "위에" 얹는 게 목적 — index.md 맨 위 섹션으로 |
| 그래프 뷰를 별도 HTML로 | 기각 (Jay 결정) | 기존 heritage-archive에 **통합**. 단 탈출구: IIFE가 심하게 복잡해지면 별도 파일로 후퇴 |
| 두 지도(사람/과제) 필터 상태 공유 | 기각 | 과거 교훈 "필터 경로가 두 개면 헷갈린다". **상태 미공유** 확정 |
| 사람 지도 카드 연계 (`#ego=` 링크) | **보류** | 아카이브 더미 150명과 task 더미 20명이 서로 다른 인구라 이어질 사람이 없음. 실데이터에서 id 정합 후 |

그리고 구현 직전에 하나 더 발견된 문제(#8의 기원): 데모 더미가 한 줄짜리라 안 보였지만,
실 pptx는 과제 하나를 반 페이지씩 서술한다. 당시 추출은 항목당 한 줄로 압축했으므로
**구체성이 추출 단계에서 소실**된다. "요약 아님, 항목화" 원칙이 금지한 것은 *사람 단위*
압축이지 *항목 내부* 압축이 아니었다는 재해석이 나왔고, 항목 내부도 충실해야 한다로 확정.

**구현 순서는 3→1→2** (#8 추출 충실화 → #9 총평 → #10 그래프): 추출 스키마(quotes[])가
바뀌면 뒤 단계가 전부 그 위에 서기 때문에 스키마 확정이 먼저다.

### 이슈 분해 방식 — vertical slice 아님 (의도적)

#8~#10은 각자 독립적으로 병렬 착수 가능한 vertical slice가 **아니라**, 한 파일
위에 순차로 쌓는 레이어 분해다. GitHub 이슈에 그대로 명시돼 있다:

- #9 body: `Blocked by: #8 (추출 스키마 quotes[] 확정 후)`
- #10 body: `Blocked by: #8 (과제 벡터·추출 스키마 확정 후)`

실제 diff도 세 이슈가 전부 `scripts/task_discovery.py`를 건드린다 — #8이 만든
`quotes[]` 스키마 위에 #9가 총평 로직을, #10이 그래프 페이로드 조립을 얹는 구조
(§5 파일 맵 참고). 병렬로 브랜치를 나눴다면 같은 파일에서 충돌했을 조합이다.

이전 확장(heritage-archive, `todos/001~007`)과 대조하면 이 차이가 분명해진다 —
거기서는 001(스키마·더미·빌드 조립)이 기반을 깔고 나면 002~007이 **서로 다른
파일**(유사도 스크립트/빈도 스크립트/태그 배치/워드클라우드 뷰/태그 UX/인물 카드)을
건드리는 독립 조각이라 `todos/README.md`에 "001이 깔리면 002~007은 전부 병렬
진행 가능"이라 명시했다. #8~#10은 그런 병렬성이 설계 목표가 아니었다 — 한 세션이
순서대로 처리하는 걸 전제로 짰고, 실제로도 한 세션·한 브랜치에서 fdb6382 → 9021ac8
→ b94f29b 순으로 순차 커밋됐다.

---

## 2. #8 추출 충실화 — text 서술화 · quotes[] 복수화 · verbose 더미

### 왜

임베딩 입력은 추출된 `text`다. text가 "물류 자동화"처럼 뭉개지면 군집이 죽처럼 붙고,
"OO공정 반출 물류를 AMR로 자동화" 수준이면 군집이 갈라진다. **군집 품질 = 추출 text 품질.**
또 verbose 원문에선 한 과제 얘기가 문서 여러 곳에 흩어져 있어, 연속 발췌 하나(quote 단수)로는
근거를 다 담을 수 없다.

### 무엇을 바꿨나 (전부 `scripts/task_discovery.py`)

1. **추출 프롬프트 `_EXTRACT_RULES`**: text는 "짧은 라벨이 아니라 원문의 구체성(대상
   공정·방법·이유)을 보존한 충실한 서술(여러 문장 허용)"로, 흩어진 언급은 quotes 배열로.
2. **스키마**: 항목당 `"quote": "..."` → `"quotes": ["...", "..."]`

   ```json
   {"tasks": [{"text": "충실한 서술...", "horizon": "단기|장기|불명",
               "quotes": ["원문 발췌1", "원문 발췌2"]}],
    "capabilities": [{"text": "...", "quotes": ["..."]}]}
   ```
3. **검증 `extract_person`**: quotes가 비면 실패, quotes **각각**을 원문과 대조.
   대조는 `_norm(s) = "".join(s.split())` — 공백·줄바꿈 전부 제거 후 부분문자열 비교.
   **하나라도 불일치하면 그 사람 전체 폐기** (재시도 1회 후). 이 규칙은 기존과 동일하게
   유지 — 인용 신뢰가 이 wiki의 존재 이유라서다.
4. **더미 생성기 `_TPL_CL23`/`_TPL_CL4`**: 한 줄 → 문단 단위 verbose 서술로. 핵심은
   **같은 도메인(d1, d2)이 서로 다른 문단에 다시 등장**하게 만든 것 — 흩어진 언급을
   quotes 복수 인용으로 담는 경로를 더미로 검증할 수 있어야 하기 때문. CL4 템플릿의
   문장 중간 줄바꿈("역량을\n확보해 왔다")은 **일부러 남겼다** — 실 LLM에서 전원 폐기를
   일으켰던 함정(아래 §7)의 회귀 감시용.
5. **후속 파급**: `run_pages`는 인용 블록을 `quotes` 개수만큼 찍고, 파생 제안 검증
   `_grounded`는 evidence 인용을 `it["quotes"]` 각각과 대조한다.

### 왜 "공백 정규화" 비교인가 (사연)

실 LLM 실행에서 원문에 문장 중간 줄바꿈이 있으면, LLM은 줄바꿈 없이 인용을 돌려준다.
엄격한 부분문자열 비교는 이 **진짜 인용**을 전부 떨궈 CL4 전원이 폐기됐다(커밋 `a1e3ff4`).
당시 "무료 티어 쿼터 끝났나"로 오진할 뻔했던 사건 — 검증 로직을 만질 때 이 사연을 기억할 것.
`_norm`은 이 함정의 해답이고, `test_quote_matches_across_linebreaks`가 회귀를 막는다.

### 어떤 테스트가 어떤 규칙을 고정하나 (`tests/test_task_discovery.py`)

- `test_scattered_mentions_become_multiple_quotes` — 흩어진 언급→quotes 2개, 그중 하나만 틀려도 폐기
- `test_bad_quote_fails_person` / `test_quotes_are_substrings_of_source` — 폐기·대조 규칙
- `test_generate_sources_verbose_with_scattered_mentions` — 더미가 문단 단위(200자+)이고
  같은 도메인이 두 문단 이상에 등장
- `test_generate_sources_deterministic_*` — 고정 시드 재현성 유지

---

## 3. #9 요약층 — 위키 index 맨 위 "총평"

### 왜

index가 군집 링크 나열이면 "그래서 팀이 어디로 가는데?"에 답이 없다. 확정된 총평 구성은
두 가지뿐: ① **큰 흐름 2~3개** (팀 전체가 어디로 수렴 중인가) ② **소수 의견·특이점**
(한두 명만 쓴 독특한 과제, 군집에 잘 안 붙는 외톨이 문장). 우선순위는 보류(§1 표 참조).

### 어떻게 (전부 `scripts/task_discovery.py`)

- `OVERVIEW_PROMPT`: 전 군집의 제목·요지·규모 + 과제 문장 전체를 입력으로
  `{"trends": [...], "outliers": [...]}` JSON을 요구. 각 항목은
  `evidence: [{person_id, quote}]` 필수.
- `_overview_lines(pages, call)`: **LLM 추가 호출은 정확히 1콜** (군집당 1콜 + 총평 1콜이
  전부 — `test_overview_is_single_extra_call`이 콜 수를 고정). 반환된 각 항목을
  `_grounded`로 검증 — evidence 인용이 실제 추출 항목(quotes 또는 text)과 `_norm` 대조
  실패하면 **그 항목 폐기**. trends/outliers 모두 폐기되면 **총평 섹션 자체를 내지 않는다**
  (빈 섹션 금지).
- 출력 위치: `index.md` 제목 바로 아래 `## 총평 \`AI 요약\`` — 팀원 작성물과 AI 생성물을
  배지로 구분하는 기존 관례(`AI 제안` 배지)를 따른다.
- 파생 제안과 총평이 같은 "이름: “인용”" 근거 표기를 쓰므로 렌더 헬퍼 `_refs`로 공유.

### 생각의 경로 (요약층)

인용 원칙을 총평에도 강제한 이유: 총평은 "AI의 해석"이라 가장 신뢰 시비가 붙기 쉬운
층이다. 근거 문장이 대조 가능해야 팀장 앞에서 "이 흐름은 이 사람들이 실제로 쓴 문장"으로
방어된다. 검증 실패 시 조용히 놔두는 대신 **폐기**하는 것도 같은 이유 — 근거 없는 문장이
하나라도 섞이면 층 전체의 신뢰가 무너진다.

---

## 4. #10 과제 문장 그래프 — heritage-archive 통합

위키(글로 읽는 지도)와 그래프(눈으로 보는 지도)는 **같은 군집 결과의 출구 두 개**다.
새 군집화를 하는 게 아니라, 이미 있는 `task_vectors.json` + `clusters.json`을 화면에 얹는다.

### 빌드타임: `scripts/build.py`의 `build_tasks(vectors, clusters, wiki_dir)`

`data/task_discovery/task_vectors.json`과 `clusters.json`이 있으면 페이로드를 만들어
템플릿의 `/*__TASKS__*/null` 마커에 JSON으로 주입한다. 없거나 빈 평면이면 `null` 주입
→ 화면에서 토글째 숨김.

```json
{"nodes": [{"id": 0, "cluster": 3, "person_id": 7, "name": "김민준", "cl": "CL3",
            "horizon": "단기", "text": "...", "quotes": ["..."], "outlier": false}],
 "neighbors": {"0": [{"id": 5, "w": 0.93}]},
 "clusters": [{"id": 3, "title": "지능형 검사 체계", "page": "wiki/cluster-03.md", "count": 7}]}
```

구현 디테일과 그 이유:

- **엣지 = 유사도 top-K**: `similarity.py`의 `top_k_neighbors`를 **재사용** (사람 지도와
  동일 문법 — 새 유사도 코드를 쓰지 않는다), k=6 고정.
- **벡터 재결합**: clusters.json의 items에는 vec이 없다(군집 파일을 가볍게 유지).
  `(person_id, text)` 키로 task_vectors.json에서 벡터를 되찾는다. 두 파일이 같은
  `run_all` 산출이라는 가정이며, 스테이지 캐시가 어긋나면 **KeyError로 죽는 게 의도**
  (조용한 오배치보다 낫다 — 코드에 `ponytail:` 마커로 명시).
- **외톨이(소수 의견) 판정**: 노드의 단위벡터와 소속 군집 중심(단위화한 평균)의 코사인을
  구하고, **전체 평균 − 1σ 미만**이면 `outlier: true`. 총평의 "소수 의견" 텍스트 항목과
  시각적으로 짝을 이루는 게 목적. 전역 문턱은 의도적 단순화 — 실데이터에서 표시가
  과소/과다하면 군집별 문턱으로 바꾼다(`ponytail:` 마커).
- **군집 제목**: 페이지 생성 LLM이 지은 제목은 `dist/wiki/cluster-XX.md` 첫 줄 `# 제목`에만
  있다 — 빌드가 그 첫 줄을 읽는다. 파일이 없으면 "군집 N".
- **빈 평면 가드**: `run_cluster`는 항목 0건이면 `"[]"`를 쓴다. 파일 "존재"만 보고 진행하면
  ZeroDivisionError — 그래서 노드 0건이면 `None` 반환 (리뷰에서 잡힌 버그, §6).

### 런타임: `archive/template.html`의 과제 지도

**통합 방식이 핵심 결정이다.** 사람 지도는 2,000줄 IIFE 하나에 물리·카메라·에고 뷰·
워드클라우드가 얽혀 있다. 여기에 두 번째 그래프를 끼워 넣으면 상태 분리("두 지도 상태
미공유")를 코드로 보장하기 어렵다. 선택한 구조:

- **별도 오버레이 스테이지** `#taskStage` (z-index 30, 불투명 배경) + **별도 IIFE**.
  사람 지도 IIFE는 **한 줄도 수정하지 않았다**. 사람 지도는 뒤에서 계속 돌지만 불투명
  오버레이에 가려진다 — 워드클라우드 최대화(cloud-max)가 그래프를 스크림 뒤에 두는
  기존 선례와 같은 수법.
- 이 구조 덕에 "상태 미공유"가 공짜다: 두 IIFE는 변수를 하나도 공유하지 않는다.
- **물리 엔진은 사람 지도의 상수·패턴을 의도적으로 복제**했다 (repulsion 900*(W/1400),
  스프링 자연길이 `(1-w)*200+95`, 군집 간 스프링 ×0.05, 앵커 인력 0.008, `warmUp(300)`).
  공유 모듈로 뽑지 않은 이유: 사람 지도 IIFE를 건드리지 않는 것이 더 큰 원칙이고,
  이 상수들은 "함부로 되돌리지 말 것" 목록(handoff)에 있는 튜닝 결과라 값 동기화가
  중요하지 구조 공유가 중요하지 않다. **이 복제가 유지보수를 해치기 시작하면 그때가
  설계에 명시된 탈출구("별도 파일로 후퇴") 시점이다.**
- **워밍업**: 처음 과제 지도를 켤 때 `warmUp(300)` — tick 300회를 화면 밖에서 돌려
  빅뱅 요동을 숨긴다(사람 지도와 같은 이유. 빼면 노드가 폭발하는 걸 보게 된다).
- **UI 요소**: 헤더 토글 `[사람 지도|과제 지도]`(topbar 안, topbar z-index를 35로 올려
  오버레이 위에 유지) · 노드 클릭 → 인용 카드(과제 서술 + 군집 칩 + 실명·CL·horizon·
  소수의견 배지 + quotes 인용 블록 + 군집 위키 링크) · 좌하단 군집 범례(제목·규모·위키 링크)
  · 군집 라벨은 실시간 중심(centroid) 위에 표시 · 외톨이는 점선 링.
- **`#view=tasks` 딥링크**: 기존 `#view=` 패턴 그대로 로드 시 1회 해석. 딥링크 진입 시
  발표 인트로 오버레이는 건너뛴다(데모·헤드리스 검증용 점프라서).
- 위키 → 그래프 진입점: `index.md` 상단에 "[그래프로 보기](../heritage-archive.html#view=tasks)"
  링크 (그릴링 합의: 진입점은 위키 index 상단).

### 검증 방법

pytest(`tests/test_pipeline.py`: `test_build_tasks_payload`, `test_build_injects_tasks_or_null`)
+ 헤드리스 크롬 스크린샷. **반드시 `--headless=new`** — 구형 headless는 렌더가 달라
"고장"으로 오판한다(과거 실제 헛발질). 스모크: `file://...#view=tasks` 스크린샷에서
군집 색·라벨·범례·점선 링 확인.

---

## 5. 파일 맵 — 무엇이 어디에 있나

| 파일 | 역할 (이번 확장 관련) |
|---|---|
| `scripts/task_discovery.py` | 파이프라인 전부. #8: `_EXTRACT_RULES`·`extract_person`·`_TPL_CL23/_TPL_CL4`·`_norm`. #9: `OVERVIEW_PROMPT`·`_overview_lines`·`_refs`. 공용 검증 `_grounded` |
| `scripts/build.py` | 화면 조립. #10: `build_tasks()` + `/*__TASKS__*/` 주입, 모듈 레벨 `unit()` |
| `scripts/similarity.py` | `top_k_neighbors` — 사람 지도와 과제 그래프가 공유하는 top-K 계산 |
| `archive/template.html` | 화면 원본. 끝부분의 두 번째 `<script>` IIFE = 과제 지도, `.task-stage` 마크업, `.map-toggle` CSS. 사람 지도 IIFE는 무수정 |
| `tests/test_task_discovery.py` | 파이프라인 규칙 고정 (21개, LLM mock) |
| `tests/test_pipeline.py` | 그래프 페이로드·주입·빈 평면 가드 |
| `dist/heritage-archive.html` | 빌드 산출물 (직접 수정 금지 — build.py 재실행) |
| `dist/wiki/` | 위키 산출물 (추적됨). 실명+인용이라 사내 한정 |
| `data/task_discovery/` | 중간 산출물 (gitignore — 실데이터 프라이버시). 캐시 겸용 |
| `docs/task-discovery.md` | 설계 정본 (결정·기각 이유의 원출처) |
| `docs/handoff.md` | 저장소 전반 인수인계 + 함정 목록 |

---

## 6. 리뷰에서 나온 것 (2축 리뷰: Standards / Spec)

구현 후 병렬 2축 코드리뷰를 돌렸고, 반영/기각 이력:

**반영한 것** (커밋 `9ecadbb`):
- 빈 벡터/군집 세트에서 `build_tasks`가 ZeroDivisionError → `None` 반환 가드 + 테스트
- 코사인 단위화가 build.py 안에 두 벌 → 모듈 레벨 `unit()`으로 공유
- 아무도 안 넘기는 `k` 파라미터 제거 (Speculative Generality)
- 벡터 재결합 가정에 `ponytail:` 마커, 폐기 로그 문구 일반화

**알고 남겨둔 것** (알려진 한계):
- 과제 지도 alpha 감쇠가 상수(0.994)로 하드코딩 — 사람 지도는 변수. 값 드리프트 시작점이
  될 수 있으나 현재 무해. 복제 비용이 커지면 별도 파일 분리 탈출구 발동
- 과제 엣지 k=6 vs 사람 지도 `config.K` — 문법은 같고 값은 다름 (의도)
- `_grounded`가 evidence를 `text`(LLM 서술)와도 대조 허용 — 총평 인용이 pptx 원문에
  글자 그대로는 없을 수 있음 (추출 항목 대조는 보장)
- **커밋된 데모 실물(dist/)이 pre-#8 데이터 기준으로 구식** — 재생성 시도와 현재 상태는 §6.1

### 6.1 데모 재생성 시도 (2026-07-20) — 부분 성공, 중단

실 키로 `data/task_discovery/*.json` 삭제 후 `scripts/task_discovery.py` 전체 재실행:

- **추출·임베딩·군집화는 성공** — verbose 더미 20명, 실 Gemini(`gemini-2.5-flash`)로
  `quotes[]` 복수 인용까지 정상 동작 확인(예: "품질 데이터 분석을(를) 표준 플랫폼으로
  통합하는 것이 목표다" + "지금은 라인마다 ... 방식이 서로 달라 ..." 두 인용이 한
  항목에 담김 — #8이 실 LLM에서도 의도대로 작동). 결과는 `data/task_discovery/`에
  캐시돼 있다(gitignore, 디스크에는 남아 있음).
- **페이지 생성 단계에서 쿼터 소진**: `run_pages`가 8군집 중 2개(cluster-00, 01)를
  새 데이터로 다 쓴 뒤, 3번째 군집 호출에서 재시도 5회 초과로 `RuntimeError`.
  같은 실행에서 `run_all`이 캐시를 스킵하는 건 추출·임베딩뿐이라, 군집·페이지는
  항상 재실행 대상이라 부분 실패가 그대로 `dist/wiki/`에 반영될 뻔했다.
- **되돌린 것**: `cluster-00.md`/`cluster-01.md`만 새 내용으로 덮이고 나머지 6개+
  index.md는 예전 그대로 남아 있어 위키가 내적으로 불일치하는 상태였다 —
  `git checkout -- dist/wiki/cluster-00.md cluster-01.md`로 커밋된 데모를 원상
  복구했다. **의도적 판단**: 절반만 새로운 위키를 커밋하는 것보다, 캐시(추출·임베딩)는
  살려두고 다음에 "군집+페이지 단계만" 저렴하게(약 9콜: 8페이지+총평 1) 재실행하는 게 낫다.
- **시도했다가 되돌린 것**: 쿼터 우회로 `llm.py`의 `call_gemini` 기본 모델을
  `gemini-3-flash-preview`로 바꿨었다 — 그런데 이 함수는 `run_extraction.py`(메인
  아카이브 태그 추출 파이프라인)도 기본값으로 쓰므로, task-discovery만을 위한
  우회가 무관한 파이프라인의 기본 동작까지 바꾸는 범위 이탈이었다. **원복함**
  (`git checkout -- scripts/llm.py`). 다음에 재시도할 땐 기존 오버라이드 패턴을
  따를 것 — `normalize_person_text.py`/`llm_review.py`가 이미 쓰는
  `lambda p: llm.call_gemini(p, model="gpt-oss")` 식으로, `task_discovery.py`
  호출부에서만 모델을 바꾼다(전역 기본값은 그대로 둔다).
- **다음에 재개할 때**: `data/task_discovery/extracted.json`·벡터 파일은 지우지
  말 것(캐시 재사용, LLM 0콜) — `clusters.json`도 그대로 둬도 무방(재실행 때
  덮어써짐). 그냥 `task_discovery.py`를 모델 오버라이드와 함께 다시 돌리면
  8페이지+총평만 호출한다. 성공하면 `build.py` 재빌드로 그래프 데이터까지 최신화된다.

---

## 7. 함정·제약 — 로컬 모델이 틀리기 쉬운 지점

1. **데모 실물 재생성이 아직 안 끝남** (2026-07-20 재시도, §6.1): 추출·임베딩·군집화는
   실 LLM으로 성공해 `data/task_discovery/`에 캐시돼 있다(gitignore, 디스크엔 있음).
   페이지 생성만 쿼터로 중단됐다. **`data/task_discovery/*.json`을 지우지 말고**
   그대로 `task_discovery.py`를 모델 오버라이드와 함께 재실행하면 캐시 덕에
   추출·임베딩은 스킵되고 페이지+총평(약 9콜)만 다시 돈다.
2. **스테이지 캐시**: `run_all`은 extracted.json/벡터가 있으면 LLM 0콜로 건너뛰고,
   군집·페이지는 항상 재실행한다. **스키마를 바꿨을 때만** 옛 JSON을 지울 것 —
   지금처럼 스키마는 그대로고 실행이 중단된 경우엔 지우면 오히려 손해(재추출 20콜 낭비).
3. **무료 티어 Gemini 쿼터**: 2.5-flash 일일 한도가 금방 소진된다. 우회 모델
   `gemini-3-flash-preview`를 쓰려면 **`llm.py`의 전역 기본값을 바꾸지 말고**
   `task_discovery.py` 호출부에서만 `lambda p: llm.call_gemini(p,
   model="models/gemini-3-flash-preview")`로 오버라이드할 것 — 전역 기본값을 바꾸면
   `run_extraction.py`(메인 아카이브 태그 추출)까지 영향받는다(§6.1에서 실제로
   이 실수를 했다가 되돌림).
4. **인용 검증은 `_norm` 공백 정규화** — 엄격 비교로 "고치지" 말 것 (§2의 사연).
5. **`data/`는 gitignore** — 중간 산출물이 커밋 안 되는 건 의도다 (실데이터 프라이버시).
6. **헤드리스 검증은 `--headless=new`**, 배포는 GitHub Pages 정적, **로컬 dev 서버 제안 금지**.
7. **보류 항목을 구현하지 말 것**: 우선순위 지표, 사람 지도 카드 연계 (§1 표).
