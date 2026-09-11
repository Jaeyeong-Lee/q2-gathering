# task-discovery 파이프라인 레퍼런스 — 무엇이 어떤 포맷으로 나오나

> **이 문서의 범위:** 스테이지별로 **입력 → 출력 → 그 파일 안에 뭐가 들어있나**.
> *왜* 이렇게 설계했는지는 [[task-discovery-coldstart]], *어떻게 돌리나*는
> [[task-discovery-internal-run-guide]]와 `AGENTS.md`.
>
> 아래 JSON 예시는 전부 **합성 예시**다 — 실데이터에서 복사한 게 아니다.
> 작성 2026-08-08, 코드 기준 브랜치 `feat/task-discovery-coldstart`.

---

## 0. 한눈에 — 파일이 어떻게 흘러가나

```
persons.json                (입력 · 사람이 준비)
    │  td_extract      LLM: 사람당 1콜 (재검증 시 최대 2)
    ▼
extracted.json              사람 단위 facet
    │  td_taxonomy     LLM: (facet수/30) + 1콜
    ▼
taxonomy.json               카테고리 목록 + 관계
    │  td_assign       LLM: facet 1개당 1콜  ← 가장 비쌈
    ▼
assignments.json            facet 하나 = 카테고리 하나
    │  td_aggregate    LLM 0콜 (순수 함수)
    ▼
aggregates.json             카테고리별 숫자
    ├── td_render      LLM 0콜 (순수 함수)
    │      ▼
    │   workshop-input.md    ★ Layer 1 최종 산출물
    │
    └── td_narrate     LLM: 1 + 카테고리 수
           ▼
        interpretation/index.md + category-NN.md   ★ Layer 2 (AI 해석)
```

**파일 요약표**

| 파일 | 만드는 스크립트 | 타입 | 읽는 쪽 |
|---|---|---|---|
| `persons.json` | (사람이 준비) | list | extract |
| `extracted.json` | `td_extract` | list | taxonomy, assign, aggregate, render, narrate |
| `taxonomy.json` | `td_taxonomy` | list | assign, narrate |
| `assignments.json` | `td_assign` | list | aggregate, render, narrate |
| `aggregates.json` | `td_aggregate` | **object** | render, narrate |
| `workshop-input.md` | `td_render` | md | 사람 |
| `interpretation/*.md` | `td_narrate` | md | 사람 |
| `*.progress.json` | taxonomy, assign | object | 자기 자신(재개용) |

전부 `$TD_OUT_DIR/task_discovery/` 아래. `indent=1`, `ensure_ascii=False`(한글 그대로), UTF-8.

---

## 1. `persons.json` — 입력

```json
[
  { "id": 0, "name": "홍길동", "cl_level": "CL3", "pjt": "양산기술",
    "part": "고장분석(FA)", "text": "(회고 원문 전체)" }
]
```

- `part`는 **없어도 된다** (실데이터엔 없음). 확산도 1차 축은 `pjt`.
- `id`가 이후 전 스테이지에서 `person_id`로 따라다닌다.
- `merge_persons.py`가 `roster.db` + 정제된 md에서 만든다.

---

## 2. `extracted.json` — 사람 단위 facet

`td_extract` · LLM 사람당 1콜(폐기 항목 있으면 재프롬프트, 최대 2)

```json
[
  { "person_id": 0, "name": "홍길동", "cl_level": "CL3",
    "pjt": "양산기술", "part": "고장분석(FA)",
    "signal_present": true,

    "direction": { "text": "지향 방향 1문장", "quotes": ["원문 발췌"] },

    "future_task": [
      { "text": "대상·방법·이유를 담은 서술", "horizon": "단기|장기|불명",
        "ax_mentioned": true, "quotes": ["원문 발췌"] }
    ],
    "capability_have": [ { "text": "...", "quotes": ["..."] } ],
    "capability_gap":  [ { "text": "...", "quotes": ["..."] } ]
  }
]
```

**핵심 규칙**

- **4축**: `future_task` / `capability_have` / `capability_gap`(리스트) + `direction`(단수 또는 `null`)
- `ax_mentioned`는 **`future_task`에만** 붙는다. LLM이 아니라 코드가 `quotes`에서 AX 표현을 관찰해
  붙이는 사실이지 "진짜 AX 과제냐"는 판정이 아니다 — 실체 판정은 워크숍 몫. 근거: `docs/adr/0001-…`
- `quotes`는 **원문에서 글자 그대로**. 공백·개행 제거 후 대조(`quote_in_source`)해서 통과 못 하면 그 항목을 버린다.
- `text`가 `quotes`의 단순 복사면 거부(`text_is_copy_of_quotes`) — 서술이어야 한다.
- **무내용 문서**는 `signal_present: false` + 모든 축 비움. 억지 분류하지 않는다.
- 폐기는 **사람 전체가 아니라 항목 단위** — 나머지는 보존한다.
- 한 사람이 통째로 실패해도 배치는 안 멈춘다(`failed`에 id만 기록).

**facet이란**: `signal_present`인 사람의, 4축 중 비어있지 않은 항목 하나하나.
`td_common.iter_facets(persons)`가 `(person, axis, item)`으로 산출하고 taxonomy·assign·index가
전부 이걸 쓴다. 축 순서는 `future_task → capability_gap → capability_have → direction` 고정
(assign 재개가 이 순서의 결정성에 의존).

> 200명이면 대략 facet 600~800개. 이 숫자가 assign 콜 수를 결정한다.

---

## 3. `taxonomy.json` — 카테고리 목록

`td_taxonomy` · LLM `ceil(facet수/30) + 1`콜

```json
[
  { "name": "짧은 명사구",
    "definition": "1문장 정의",
    "inclusion_criteria": "어떤 항목이 여기 들어오는지",
    "relations": [ { "to": "다른 카테고리 name", "type": "broader|related" } ] }
]
```

**만드는 방식이 특이하다 — 배치 누적 재작성**

facet을 30개씩 끊어서, 매 배치마다 **지금까지의 taxonomy 전체 + 새 30개**를 주고
**갱신된 taxonomy 전체를 다시 받는다.** 그래서 배치마다 병합·분할·정의 재작성·삭제가 일어난다.
append-only가 아니다.

```
배치1: facet 1-30                        → taxonomy v1 (전체)
배치2: taxonomy v1 + facet 31-60         → taxonomy v2 (전체)
...
배치N: taxonomy vN-1 + facet …           → taxonomy vN
마지막: taxonomy vN                       → relations (엣지만)
```

- 카테고리 개수 **고정 안 함** (프롬프트 가이드 15~25개). 임베딩 클러스터링 안 씀 — 도메인 용어
  무지를 구조적으로 우회하는 게 이 설계의 핵심.
- **`relations`는 배치 루프가 아니라 마지막 1콜.** 배치마다 뽑으면 (a) 아직 없는 카테고리를 가리켜
  버려지고 (b) 응답이 1.5~1.7배로 부풀어 20kb를 넘겨 JSON이 잘렸다 (#30). 그래서 분리했고,
  배치 프롬프트에서도 `relations` 필드를 빼서 보낸다.
- `_normalize`가 매번 정리: `name` 없으면 버림, 댕글링(존재 안 하는 카테고리 가리킴)·자기참조·
  `broader`/`related` 아닌 type 제거.
- `name`·`definition`·`inclusion_criteria`는 **한국어**로 쓰게 지시. 단 기술 용어·약어는 원문 표기
  유지(Burn-in, STDF, ATE, Yield, DPPM 등) — gpt-oss가 영어로 뱉던 문제 때문에 추가.
- **배치 실패는 스킵 안 하고 중단**한다. taxonomy는 전체 facet을 봐야 의미가 있어서, 조용히
  건너뛰면 그 30개가 누락된 채 정상 완료처럼 보인다. (extract가 사람 단위 스킵인 것과 반대 판단)

**사이드카 `taxonomy.progress.json`**

```json
{ "batches_done": 12, "total_batches": 27, "extracted_mtime": 1754... }
```

`total_batches = 배치 수 + 1`(마지막 relations 패스). 완료 판정은 파일 존재가 아니라
`batches_done == total_batches` — 부분 저장 상태로도 `taxonomy.json`은 존재하기 때문.
`extracted_mtime`이 다르면 상류가 바뀐 것으로 보고 **처음부터** 다시 돈다.

---

## 4. `assignments.json` — facet → 카테고리 배정

`td_assign` · LLM **facet 1개당 1콜** (검증 실패 시 최대 2)

```json
[
  { "person_id": 0,
    "axis": "future_task",
    "text": "(facet의 서술)",
    "category": "taxonomy의 name 또는 Other",
    "quote": "근거 인용" }
]
```

한 줄 = facet 하나. **`extracted.json`을 대체하는 게 아니라 옆에 붙는 색인**이다 —
집계·렌더·해석은 `assignments`(어느 카테고리냐)와 `extracted`(그 사람이 누구냐)를 조인해서 쓴다.

- 프롬프트에 **taxonomy 전체 목록**(name·definition·inclusion)을 매번 싣는다 → 요청의 98%가 중복.
  facet 800개면 30MB. 배칭하면 20배 줄지만 **지금은 안 한다** — 먼저 한 번 완주하는 게 우선.
- 맞는 게 없으면 `Other`. taxonomy에 없는 이름을 지어내면 **거부하고 재시도**.
- `quote`는 `text + quotes`를 근거 풀로 놓고 대조 검증. 2번 시도해도 실패하면 그 facet **폐기**.
- `axis` 값은 `future_task` / `capability_have` / `capability_gap` / `direction`.

**사이드카 `assignments.progress.json`**

```json
{ "processed": 431, "total_facets": 812,
  "extracted_mtime": 1754..., "taxonomy_mtime": 1754... }
```

재개는 **텍스트 매칭이 아니라 위치(processed 카운트)** 기준 — 같은 사람·축에 우연히 텍스트가
같은 facet이 둘 있어도 안전하다. `extracted`/`taxonomy` 중 하나라도 mtime이 다르면 처음부터.

> 항목마다 전체 재직렬화라 O(n²). n=800에선 LLM 지연에 묻히지만 수천 단위로 커지면 JSONL append로.

---

## 5. `aggregates.json` — 카테고리별 숫자 *(LLM 0콜)*

`td_aggregate` · 순수 함수. **여기가 "중요도"가 처음 생기는 곳이다** — 추출·배정 어디에도 중요도
개념이 없고, 오직 집계 빈도에서만 발생한다.

**유일하게 list가 아니라 object다:**

```json
{
  "categories": [
    { "name": "카테고리명",
      "people": 17,           // 기여 인원 (중복 제거)
      "pjt_spread": 3,        // 서로 다른 pjt 수  ─┐ 확산도
      "cl_spread": 2,         // 서로 다른 cl 수   ─┘
      "have": 9,              // capability_have 배정 건수
      "gap": 14,              // capability_gap 배정 건수
      "readiness": "갭만 있음",
      "pjts": ["공정기술", "기획운영", "양산기술"],
      "cls": ["CL3", "CL4"] }
  ],
  "minority": [ /* categories 중 people <= 2 인 것만, 같은 객체 */ ]
}
```

**`readiness` 3구간 — 판정 순서 주의**

| 조건 | 값 | 뜻 |
|---|---|---|
| `people <= 2` | `선행 신호` | 소수 언급 = weak signal |
| `gap > have` | `갭만 있음` | 필요는 다수, 보유 희박 |
| 그 외 | `이미 함` | 보유가 우세 |

**위에서부터 순서대로 판정**한다. 그래서 2명이 전부 gap만 말한 카테고리는 `갭만 있음`이 아니라
`선행 신호`로 잡힌다 — 의도된 것(표본이 적으면 갭 판정 자체를 신뢰 안 함).

- `categories`는 `people` 내림차순 정렬. **이게 파이프라인이 내놓는 유일한 순위다.**
- `minority`는 `categories`의 **부분집합을 복사한 것** — 두 배열에 같은 카테고리가 중복 등장한다.
  다수 요약에 흡수(over-smoothing)되는 걸 막으려고 별도 트랙으로 뽑아둔 것.
- `Other`도 그냥 카테고리 하나로 여기 들어온다. 비율이 높으면 taxonomy 품질 신호.
- **`definition`이 여기 없다.** `taxonomy.json`에만 있고 집계는 이름만 들고 온다. (→ 8절)

LLM을 안 쓰므로 **재실행 비용 0**. `assignments.json`만 있으면 몇 번이고 다시 돌려도 된다.

---

## 6. `workshop-input.md` — Layer 1 최종 산출물 *(LLM 0콜)*

`td_render` · 순수 함수. 5개 섹션 고정:

```markdown
# 미래 역량 지도 — 리더십 워크숍 입력물
> 이 문서는 확정된 10년 로드맵이 아니라 리더십 워크숍의 입력물이다.
> 시간축·시퀀싱·전략("꿈")은 데이터에 없으며 워크숍에서 사람이 채운다.

## 역량 테마 카드
### 카테고리명  `갭만 있음`
- 기여 17명 · 확산도 pjt 3/cl 2 · 보유 9 / 갭 14
  > 인용 한 줄 — 홍길동          ← 카테고리당 최대 3개
  > ...

## pjt × cl_level 교차표
| pjt \ cl | CL2 | CL3 | CL4 |
|---|---|---|---|
| 양산기술 | 12 | 31 | 4 |          ← 인원 수(중복 제거)

## 소수 의견 (별도 트랙)
- 카테고리명 (2명) `선행 신호`

## 커버리지 리포트
- 대상 203명 · 무신호 11명 (5%)
- 배정 812건 · Other 47건 (6%)
- 추출 폐기 인원 2 · 인용검증 폐기 항목 19

## 워크숍 미결 질문 (데이터가 답하지 못한 것)
- 'X' 갭을 언제·어떻게 메울 것인가? (준비도만 있고 시점은 데이터에 없음)   ← 갭만 있음 전부
- 이 역량들이 향하는 팀의 10년 "꿈"은 무엇인가? (know-why 공백)
- 소수 의견 중 팀의 미래 씨앗으로 키울 것은?
```

**알아둘 것**

- **인용은 카테고리당 3개까지**(`[:3]`). `assignments` 등장 순서대로라 대표성 있는 3개가 아니라
  **앞에서 3개**다. 근거를 다 보려면 `assignments.json`을 봐야 한다.
- **실명이 그대로 들어간다.** `anonymize=True`면 `P0` 형태로 바뀌지만 `td_pipeline`은
  이 인자를 안 넘기므로 **기본이 실명**이다. 익명화가 필요하면 렌더 단계 교체만으로 된다.
- 커버리지 리포트의 "추출 폐기 / 인용검증 폐기"는 **이번 실행분만** 집계된다. `extracted.json`을
  재사용해 스킵했으면 0으로 뜬다 — 파이프라인이 부실해서가 아니라 그 스테이지를 안 돌았다는 뜻.
- 정렬은 `aggregates.categories` 그대로 = 인원 많은 순.

---

## 7. `interpretation/` — Layer 2 (AI 해석)

`td_narrate` · LLM **1콜(총평) + 카테고리 수**(각각 최대 2회 시도)

**Layer 1과 절대 안 섞는다.** 별도 디렉터리 + 모든 제목에 `AI 해석` 라벨.

```
interpretation/
├── index.md            총평(큰 흐름 2~4 + 소수의견·특이점 1~3) + 카테고리 목차
├── category-00.md      인원 1위 카테고리
├── category-01.md
└── ...
```

`category-NN.md` 내용:

```markdown
# 카테고리명  `AI 해석`

17명 · 확산도 pjt 3/cl 2 · 보유 9 / 갭 14 · 갭만 있음

(LLM이 쓴 2~4문장 서사)

**근거 인용**

> 인용 — 홍길동
> 인용 — 김철수

**관련 카테고리** (taxonomy에서 그대로, LLM 재검증 없음)
- broader: 상위 카테고리명
- related: 연관 카테고리명
```

**grounding 방식이 앞 스테이지와 다르다**

extract·assign은 "LLM이 뱉은 인용이 원문에 있나" 대조했는데, 여기선 **근거 풀을 id로 미리
못박고 LLM은 id로만 인용**한다:

```
근거:
[0] (카테고리A) 홍길동: 인용문...
[1] (카테고리A) 김철수: 인용문...
→ LLM 응답: {"narrative": "...", "citation_ids": [0, 1]}
```

렌더링은 우리가 원본을 그대로 하므로 **LLM이 인용을 다시 타이핑하다 변형할 여지가 없다.**

- `citation_ids`가 범위를 벗어나면 그 인용을 버리고, **근거가 하나도 안 남은 문장은 통째로 버린다.**
  근거 없는 주장은 안 한다.
- 근거 풀 상한: 카테고리 페이지 12개, 총평은 카테고리당 3개.
- 근거가 아예 없는 카테고리는 **페이지를 안 만든다.** 그래서 `category-NN.md`의 번호가 중간에
  비어 있을 수 있다(NN은 `aggregates.categories`의 인덱스).
- 총평이 근거 부족으로 실패하면 `- (근거 부족으로 생성 안 됨)`이 찍힌다. 정상 동작이다.
- **여기도 실명이 기본**이다(`anonymize=False`).
- 10년·전략·"꿈"을 만들어내지 말라고 프롬프트에 명시. Layer 1이 이미 보여주는 흐름을 산문으로
  정리할 뿐.

> `td_narrate`는 **사내망 실 LLM으로 아직 한 번도 안 돌아봤다.** 가짜 call 테스트만 통과한 상태.

---

## 8. 알려진 구멍

| | 무엇 | 영향 |
|---|---|---|
| 1 | `aggregates.json`에 `definition`이 없는데 `td_narrate._category_prompt`가 `cat.get("definition","")`를 읽는다 | 카테고리 정의가 **해석 프롬프트에 절대 안 실린다**(항상 빈 문자열). LLM이 이름만 보고 서사를 쓴다 |
| 2 | 커버리지의 폐기 수가 이번 실행분만 | `extracted.json` 재사용 시 "폐기 0"으로 보임 |
| 3 | assign 재개 시 `dropped`가 이번 세그먼트분만 | `assignments.json`(정답)엔 영향 없음, 리포트 숫자만 과소 |
| 4 | 렌더 인용이 앞에서 3개 | 대표성 아님 |

1번은 고칠 값어치가 있어 보이는데(`taxonomy.json`을 이미 `narrate`가 읽고 있으니 거기서 정의를
당겨오면 됨) **아직 안 고쳤다.** 실 LLM 결과를 보고 정한다.

**나중에 추가로 발견한 것 두 가지** (둘 다 [[task-discovery-workshop-tools]]에서 다룬다):

- `future_task[].horizon`이 `td_assign`에서 유실된다 — 시간축의 유일한 데이터 힌트다.
  `td_cards`가 조인하면서 되살리므로 **재배정은 필요 없다.**
- `td_aggregate`의 준비도 판정에서 `have=0·gap=0`인 카테고리가 `이미 함`으로 잡힌다.
  실제로는 "역량 언급이 없다"이지 "보유가 우세하다"가 아니다.

---

## 9. 곁가지 — S2 / S4

메인 경로(S1)는 위까지. 두 대안 경로가 코드에 공존한다.

**S2 코드북 (`--codebook <경로>`)**
`td_taxonomy`를 건너뛰고 **사람이 확정한 `codebook.json`**으로 배정한다. 포맷은 taxonomy와
호환(`name`·`definition`·`inclusion`/`inclusion_criteria`, 추가로 `exclusion` 지원).
`other-report.json`이 추가로 나오고 `Other` 비율 20% 넘으면 "코드북 갱신 필요" 경고.
`td_codebook.propose_draft`가 `td_taxonomy.induce`를 재사용하므로 **S1 결과를 S2 코드북 초안으로
승격**할 수 있다.

**S4 검색 (`--search`)**
카테고리화를 아예 안 한다. `extracted` → `td_index`(facet 단위 색인) → `td_digest`(사전 조회
묶음) → `digest.md`. 임베딩(BGE-M3) 필요. 색인은 인메모리라 비영속.

---

## 10. 파이프라인 재실행 규칙

`td_pipeline.run_all`은 **dirty 캐스케이드**다 — 앞 스테이지가 돌면 뒤도 전부 다시 돈다.

- 산출물이 있으면 스킵. 단 taxonomy·assign은 파일 존재가 아니라 **사이드카 완료 판정**을 쓴다.
- 한 스테이지만 다시 돌리려면 **산출물과 사이드카를 같이** 지운다:
  ```bash
  rm $TD_OUT_DIR/task_discovery/{taxonomy,assignments}.json \
     $TD_OUT_DIR/task_discovery/{taxonomy,assignments}.progress.json
  ```
- `extracted.json`은 **지우지도, `touch`하지도 말 것** — mtime이 바뀌면 "상류 변경"으로 읽혀
  taxonomy·assign이 처음부터 다시 돈다.
- `aggregate`·`render`는 LLM을 안 쓰므로 언제든 공짜로 다시 돌릴 수 있다.

---

## 11. 여기가 끝 — 그 다음은 사람

`workshop-input.md`와 `interpretation/`이 나오면 파이프라인의 몫은 끝난다.
**시간축·시퀀싱·전략은 데이터에 없다.** 리더십 워크숍에서 사람이 채운다.

워크숍을 실제로 진행하는 도구는 전부 이 산출물들을 **읽기만** 하는 render 이후 층이다.
셋 다 만들어져 있다 — 탐색기 · 로드맵 매트릭스 · 투표 서버:
**[[task-discovery-workshop-tools]]**.

그 도구들은 `td_cards`라는 조인 하나 위에 얹혀 있고 **LLM을 부르지 않는다.** 산출물이
그대로면 몇 번이고 다시 만들 수 있다.

---

## 포인터

- **워크숍 도구(탐색기·매트릭스·투표 서버): [[task-discovery-workshop-tools]]**
- 설계 근거·왜: [[task-discovery-coldstart]]
- 사내망 운영: [[task-discovery-internal-run-guide]] · `AGENTS.md`
- 이번 신뢰성 개선 내역: [[task-discovery-migration-2026-08]]
- 온톨로지 개념: [[task-discovery-ontology-onboarding]]
- 발표용: [[task-discovery-overview-slides]]
