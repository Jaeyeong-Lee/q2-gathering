# 작업: cross-PJT 유사 과제 링킹 — 데이터 파이프라인 + 화면 표시 (전 슬라이스)

> Jay 확정 사항(2026-09-13/14):
> - PJT 간 비슷한 과제를 잇는다. 단 **자동 통합은 없다** — 제안 링크(점선)로 표시하고 사람 승인 시 실선 승격.
> - 임베딩 대상은 과제 원문(label+quote). taxonomy 정의는 검증 재료로만.
> - 1부(story)는 원칙적으로 건드리지 않는다. 2부(live)에서만 표시한다.

## 0. 스펙 문구 수정 (먼저 — 이건 설계 결정의 기록이다)

`docs/nebula-spec.md` 8행을:

> "고정 카테고리 수, PJT 간 강제 통합, 과제 자동 협업 매칭은 없다."

이렇게:

> "고정 카테고리 수, PJT 간 강제 통합은 없다. 과제 자동 협업 매칭도 없다 — 대신 cross-PJT 유사 과제를 **제안 링크**로 별도 표시하며, 묶음(merge)은 하지 않고 사람 승인으로만 확정한다."

장면 2 캡션도 함께 수정: "합치지는 않았습니다" → "합치지는 않았습니다. 다만 다른 PJT의 비슷한 과제는 점선으로 이어뒀습니다."

## A. 링크 후보 추출 (임베딩 + kNN) — 신규 스크립트

`scripts/crosslink_extract.py` (신규):

1. 입력: `result.json`의 tasks (label + quote) + categories (이름·정의).
2. 각 과제에 임베딩 생성 — **문자열 = `label + "\n" + quote`** (taxonomy 정의는 여기에 넣지 않는다 —
   정보량이 원문보다 적어 유사성 신호가 약하다).
   - 사내 BGE-M3 임베딩 사용 (외부 API 금지). ES kNN으로 cross-PJT 상위-K 쌍 추출 (K=200 시작).
3. 필터: 같은 PJT끼리는 제외 (cross-PJT만). 자기 자신 제외.
4. 출력: `cross-links-candidates.json` — `{task_a, task_b, similarity}` 배열 (내림차순).
5. 임베딩 실패 시(엔드포인트 미제공 등): TF-IDF 코사인으로 대체 — 기존 유사도 네트워크와 같은 계열.
   어느 방식으로 만들었는지 출력에 남긴다.

## B. LLM 검증 단계 — 파이프라인에 stage 추가

`nebula/pipeline.py`에 `crosslink` stage 신규 (기존 계약 패턴 그대로):

- 각 후보 쌍에 대해:
  - payload: task_a(label+quote+소속 과제군 이름·정의), task_b(동일), 지시문
  - 지시: "이 두 과제가 같은 과제군으로 묶일 수 있는가? 근거 인용은 두 과제의 원문 그대로."
  - 출력 계약: `{verdict: "same"|"different", quote_a, quote_b, reason}` — quote는 원문과 정확히 일치해야 함
    (기존 계약 1번과 동일한 인용 검증 validator를 통과해야 캐시 승격)
- 저장: `result.json`에 `cross_links` 필드 신규:
  ```json
  [{"task_a": "...", "task_b": "...", "status": "proposed", "quote_a": "...", "quote_b": "...", "confidence": 0.87, "verdict": "same"}]
  ```
- **자동 merge 금지** — 과제의 소속 PJT·category ID는 불변 (ID 계약 유지).
- 캐시: 새 stage라 기존 캐시 무효화 없음. 캐시 키는 기존 계약 4번대로 프롬프트+payload digest 포함.
- PC에서는 합성 fixture로 B~D를 개발하고, 실제 링크 생성(A의 임베딩)은 사내 인프라(BGE-M3+ES)라 내부망에서만.
  개발 중에는 합성 링크 fixture로 UI를 검증한다.

## C. review.html 승인 큐

- 제안 링크(proposed) 목록 표: task_a/task_b의 PJT·과제군·원문 인용 나란히, verdict/confidence 표시.
- 각 행: 승인(status→approved) / 거부(status→rejected) 버튼. 승인 결과는 corrections와 같은 방식으로
  사이드카 파일에 기록하고 재실행 시 유지.
- 승인된 링크만 발표 화면에 노출 (proposed는 발표 화면에 보이지 않는다 — 승인 전 수습 구간 보호).

## D. 화면 표시 (nebula.html live 모드만)

1. **장면 2 기본 (PJT 격자)**: 링크 수가 많은 PJT쌍 사이에 **점선 브리지** (쌍 상세 클릭 가능).
   굵기 = 링크 수 비례. 브리지가 0개면 아무것도 그리지 않는다(빈 상태 정직 표시).
2. **장면 2 진입 (PJT 성운 안)**: 타 PJT 유사 과제를 **옅은 타색 점 + 점선**으로, 성운당 상위 3~5개만.
   클릭 → 해당 과제로 카메라 줌(`focusPerson` 패턴 재사용) → 패널에 양쪽 원문 인용 나란히.
3. **장면 3 (과제 클릭 패널)**: "다른 PJT의 유사 과제" 섹션 신규 — 유사도 점수 + 원문 인용 + 이동 버튼.
4. **검색**: 링크된 외부 과제도 자기 PJT 검색에 함께 검색되게.
5. **장면별 범위**: 장면 0(사람 지도), 장면 1(분열 전환), 2Q 네트워크(Heritage 이식)에는 **넣지 않는다** —
   사람 유사도(기존)와 과제 링크(신규)를 섞으면 의미 충돌.
6. 개수 제한 준수: 과다 노출로 성운이 지저분해지는 것 방지. 계약 셀렉터·`#synthetic-mark` 상시 표시 유지.

## E. 1부(story) 처리

- 기본: story 9비트는 건드리지 않는다.
- 선택 사항(구현 후 판단): 1-5(PJT 격자 해쳐모임) 직후 "다른 PJT에서도 비슷한 미래가 쓰였습니다" 하며
  브리지 1~2개 조명하는 삽입 비트(1-5.5). **URL 파라미터로 on/off** — 시간 초과 시 건너뛰기 가능.
  이건 옵션으로 구현하고 발표 리허설에서 채택 여부 결정.

## 절대 유지 (계약)

- `window.nebula` 시그니처, `nebulaCopy`, 페이로드 구조, `result.json`의 `run_id` 봉인.
- 셀렉터: `.step.active`, `#sky g.task`/`g.person`/`g.skill`, `#synthetic-mark` (live에서도 상시).
- 과제의 소속 PJT·과제군 ID 불변 — 링크는 "연결"이지 "이동·병합"이 아니다.
- 인용은 원문과 정확히 일치 (계약 1번).
- taxonomy/assign 파이프라인 로직 자체는 그대로 — 새 stage만 추가.
- `result.json` 직접 수정 금지 — corrections/재실행 패턴 따른다.

## 검수

- 기존 테스트 전부 통과: pytest nebula 4파일, nebula_q3/presentation/browser.cjs, q3_story_check (story 회귀 0).
- 신규: crosslink stage의 요청파일→답→검증→캐시 승격 단위 테스트, 승인 큐 동작 테스트.
- 합성 링크로 화면 표시(점선 브리지·점선 점·패널) 확인 스크린샷.
- **실제 임베딩 생성은 내부망 인프라(BGE-M3+ES) 의존이므로 PC에서는 실행되지 않는다** — 개발·검증은 합성 링크로,
  실제 링크 생성은 내부망에서. 이 구분을 README에 명시.

## 산출·커밋

- 코드: `scripts/crosslink_extract.py`, `nebula/pipeline.py`(crosslink stage), `nebula/prompts.py`,
  `docs/review-*.html`(승인 큐), `nebula/templates/nebula.html`(점선 렌더+패널)
- 문서: `docs/cross-pjt-linking.md` (설계 문서 — 위 명세 전체 + 이전 리뷰 교훈 반영 여부)
- 스펙 수정: `docs/nebula-spec.md` 8행
- 커밋·push 후 브랜치·커밋·검수 결과 보고. 커밋에 원문·인용·과제군 이름 금지 (기존 규칙).
- 브랜치: 현재 작업 브랜치에서 이어서 (docs/nebula-internal-cc-agent-run 계열) — 새 브랜치 만들어도 무방하나 보고할 것.
