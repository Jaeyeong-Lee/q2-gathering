# Handoff: task-discovery Layer 2 착수 (2026-08-04 기준)

다음 에이전트/모델이 이 작업을 이어받을 때 읽는 문서. **파이프라인 전체 개요·아키텍처는
`docs/task-discovery-coldstart.md`가 정본**이고, 여기는 이번 세션에서 새로 생긴 것과
**아직 확정 안 된 것**을 남긴다.

## 가장 중요한 것 먼저: 이 작업은 컨셉 확정 전 초안이다

상사 요구("근원경쟁력 기반 팀 10년 로드맵")를 감당하려고 산출물을 **Layer 1(근거)/Layer 2(해석)**
2층으로 나누기로 했다(`docs/roadmap-requirement-and-two-layer-framing` 논의, 이 세션 이전 결정).
Layer 1은 이미 완성된 파이프라인 그 자체. **Layer 2(서사화·해석)는 이번 세션에서 처음 코드로
착수**했는데, 착수 직후 사람(Jay)이 "컨셉 확정이 오늘 회의에 달려 있다"고 못박았다.

**즉: 아래 `td_narrate.py` 구현은 실제 채택 여부·스코프가 회의 결과에 따라 바뀔 수 있다.**
이 문서를 읽고 이어서 작업한다면, 먼저 Jay에게 회의 결과(아래 "확정 필요 항목" 참고)를
확인하고 시작할 것 — 특히 카테고리별 페이지까지 만들지(현재 구현은 이 스코프로 되어 있음)
재확인 필요.

## 이번 세션에 생긴 것

**커밋 `ee894b6`(이미 push됨):**
- `scripts/td_taxonomy.py` — 카테고리에 `relations: [{to, type: broader|related}]` 필드 추가.
  `_normalize`가 댕글링 참조·자기참조·잘못된 type을 제거(관계만 버림, 카테고리는 안 버림).
- `AGENTS.md` — 내부망에서 작업할 에이전트용 프로젝트 방향·실행법 요약.
- `docs/task-discovery-ontology-onboarding.md` — 온톨로지 개념 자체를 처음 보는 사람 기준 설명.
- `docs/task-discovery-ontology-slides.md` (+ `dist/presentations/*.html` 렌더본) — 위 온보딩을
  Marp 9장으로 압축.

**이번 커밋에 새로 포함되는 것:**
- `scripts/td_narrate.py` — **Layer 2 스테이지(신규, td_pipeline 6번째 단계)**. 상세는 아래.
- `scripts/td_pipeline.py` — `run_all`에 narrate 단계 배선(render 다음, skip-if-exists,
  `narrate_call` 파라미터 추가. 기본값은 `extract_call` 재사용).
- `tests/test_td_narrate.py`(신규 10개) + `tests/test_td_pipeline.py`/
  `test_td_pipeline_codebook.py` 갱신(narrate 가짜 call 추가) — 전체 스위트 151개 통과 확인함.
- `docs/task-discovery-overview-slides.md` — task-discovery **전체**를 도메인 지식 없는 사람
  기준으로 설명하는 회의용 Marp 덱(21장). Layer 1/Layer 2 구조, 매트릭스뷰·온톨로지
  그래프뷰 SVG 목업, "오늘 정해야 할 것" 5가지 포함.

## `td_narrate.py` (Layer 2) 설계 — 왜 이렇게 짰나

**grounding 방식이 extract/assign과 다르다.** 그쪽은 원문 대조(`quote_in_source`, 부분문자열
매칭)로 검증하지만, 여기는 **근거 풀을 id로 미리 못박고 LLM은 id로만 인용**하게 한다
(`citation_ids: [0, 2]` 같은 정수 배열). 이유: LLM이 인용을 다시 타이핑하다 살짝 바꿔 쓸
여지 자체를 없앤다 — 렌더링은 항상 우리가 들고 있는 원본 문자열을 쓰고, LLM 응답에서
문자열 자체는 안 믿는다. `citation_ids`가 범위를 벗어나면 그 항목만 버리고, 근거가 하나도
안 남는 문장(총평 흐름/소수의견/카테고리 서사)은 통째로 버린다 — 근거 없는 주장 금지 원칙은
Layer 1과 동일하게 유지.

**산출물 구조** (`data/task_discovery/interpretation/`, git 추적 안 됨):
- `index.md` — 총평("큰 흐름"+"소수 의견·특이점") + 카테고리별 페이지 링크
- `category-NN.md` — 카테고리 하나당 서사 2~4문장 + 근거 인용 + (taxonomy에 있으면) 관계
  카테고리 목록(`relations` 필드 그대로 렌더, LLM 재검증 없음 — 이미 taxonomy 단계에서
  검증됨)

**입력**: `aggregates.json`(카테고리 요약) + `assignments.json`(카테고리별 실명 인용,
카테고리당 최대 12개로 절단) + `extracted.json`(이름 조회, anonymize 지원) + `taxonomy.json`
(관계 표시용, 선택— S2/코드북 모드처럼 taxonomy.json이 없으면 `None`으로 넘겨도 동작).

**Jay의 요청 그대로 반영한 것**: "카테고리별 주요 코멘트(빈번했던거)가 재료가 될 수 있냐"는
질문에 "그렇다"고 답한 뒤 구현 — `assignments.json`에 이미 카테고리별 실명+인용이 쌓여 있고,
`aggregates.json`의 `people` 수 자체가 빈도 지표라서 새로 계산할 게 없었다.

## 확정 필요 항목 (회의 결과 반영 필수)

`docs/task-discovery-overview-slides.md`의 "오늘 정해야 할 것" 슬라이드와 동일:

1. **Layer 2 컨셉** — 팀 총평만? 카테고리별 서사 페이지까지? (**현재 구현은 후자로 되어 있음**)
2. **시각화 방향** — 매트릭스뷰(시간축×준비도) + 온톨로지 그래프뷰로 갈지. 지금은 더미
   데이터 목업만 있음: Artifact `https://claude.ai/code/artifact/8816f28e-d13f-4050-9937-9795bbd072d8`
   (JS 목업, `taxonomy.json`/`aggregates.json` 실제 연동 코드는 **아직 없음**)
3. **실명 표기 정책**, 4. **"우리 팀" 범위**, 5. **산출물 형태·기한** — 전부 렌더 단계
   교체만으로 반영 가능(파이프라인 앞단 안 바뀜)

## 다음에 할 일 (우선순위 순)

1. 회의 결과로 위 1~2번 확정 → `td_narrate.py` 스코프 재확인(이미 맞으면 그대로, 아니면
   총평만으로 축소하거나 반대로 확장)
2. 시각화를 실제 데이터에 연동 — 더미 `CATS`/`EDGES` 배열을 `taxonomy.json`(relations 포함)
   + `aggregates.json`으로 교체하는 스크립트/렌더 필요(아직 미착수)
3. 사내망 실 LLM으로 Layer 2까지 포함한 전체 파이프라인 1회 실행, 결과물 사람이 검수
4. 3~5번 product 결정을 `td_render.py`/`td_narrate.py` 렌더 옵션에 반영

## 검증 상태

- `tests/` 전체 151개 통과(`.venv/bin/python -m pytest tests/ -q`, 약 4분 소요 — 대부분은
  heritage-archive 쪽 브라우저/스크린샷 테스트로 추정, td_* 서브셋만 돌리면 수십 ms).
- 실 LLM/사내망으로 `td_narrate` 단계를 돌려본 적은 아직 없음 — 가짜 call로만 검증됨.
