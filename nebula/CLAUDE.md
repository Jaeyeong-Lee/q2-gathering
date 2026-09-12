# nebula — 이 디렉터리에서 작업하는 에이전트용

`nebula`는 task-discovery와 **별개 패키지**다. 사람별 회고 텍스트에서 미래 과제·역량을 뽑아
PJT별 미래 과제군으로 묶고, 오프라인 HTML 네 장면으로 발표한다. 루트 `CLAUDE.md`의 실데이터
금지는 여기서도 그대로 적용된다 — 이 파일은 그것을 대체하지 않고 nebula 쪽 사정만 더한다.

발표 작업 기준은 `Jaeyeong-Lee/q3-nebula-presentation`, 워크트리는 `~/orca/workspaces/q2-gathering/q3-nebula`다. 계획은 `docs/q3-presentation-plan.md`를 따른다.

## 읽는 순서

1. `docs/nebula-spec.md` — 무엇을 만들기로 했나 (19줄, 짧다)
2. 이 파일 — 어떻게 굴리고 무엇을 깨면 안 되나
3. `docs/nebula-internal-runbook.md` — 운영·실패·재개·검토. **현재 계약의 living 문서다**
4. `docs/nebula-agent-run.md` — LLM endpoint 대신 **네가 직접 각 단계의 답을 쓰는** 방법
   (`--agent`). 합성 코퍼스 전용이다. 실데이터에는 쓰지 않는다.

`HANDOFF.md`와 `docs/nebula-handoff-2026-09-11.md`는 특정 시점의 기록이다. 왜 이 커밋이
존재하는지 알려주지만 **현재 상태가 아니다.** 현재 상태는 코드와 runbook과 gh 이슈다.

## 실데이터

출력 디렉터리는 통째로 민감하다 — `result.json`, `view.json`, `nebula.html`, `matrix.html`,
`review.html`, `cache/**` 모두 원문을 담는다. 열지 않는다.

대신 합성으로 돌린다. 입력이 가짜라 마음껏 열어도 된다:

```
./.venv/bin/python -m nebula demo --out /tmp/<임시>   # 200명 합성, LLM 0회
```

로그·예외 메시지에 원문을 되돌려 넣지 않는다. 디버깅이 편해지는 대신 이 구조가 무너진다.

## 개발 루프

새 워크트리라 `.venv`가 없으면 `python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt`.
`nebula` 자체는 표준 라이브러리만 쓴다 — 설치가 필요한 것은 테스트 도구뿐이다.

```
./.venv/bin/python -m pytest tests/test_nebula_pipeline.py tests/test_nebula_http.py tests/test_nebula_network.py tests/test_nebula_fixture.py -q
NEBULA_PYTHON=$PWD/.venv/bin/python node tests/nebula_browser.cjs /tmp/<demo out>
NEBULA_PYTHON=$PWD/.venv/bin/python node tests/nebula_presentation.cjs
NEBULA_PYTHON=$PWD/.venv/bin/python node tests/nebula_q3.cjs
```

- nebula 계약 테스트는 2초면 끝난다. 고칠 때마다 돌린다.
- `pytest tests/` 전체는 이 머신에서 `scripts/` 쪽 테스트(`test_llm_integration`,
  `test_normalize_person_text`)에 걸려 완주하지 않는 알려진 문제가 있다. **nebula 변경과 무관하다**
  (무수정 커밋에서도 같은 지점에서 멈추는 것을 확인했다). nebula 파일만 돌리거나 `--deselect`한다.
- 브라우저 테스트는 playwright가 필요하다: `npm install --prefix nebula/browser-tests` 후
  `npx --prefix nebula/browser-tests playwright install chromium`.
- **회귀 판정의 기본**: 합성 200명 `result.json`의 `tasks`/`capabilities`/`links`/`categories`/
  `assignments`를 변경 전후로 비교한다. 계약만 바꾼 작업이면 여기가 완전히 동일해야 한다.

## 깨면 안 되는 계약

1. **인용은 원문과 정확히 일치한다** — 공백·개행 포함. `occurrence`로 같은 문장을 구별하고,
   ID는 `digest([person_id, kind, quote, occurrence])` 기반의 안정값이다. ID가 흔들리면
   이전 승인과 정정이 전부 무효가 된다.
2. **모델이 추측하게 만들지 않는다** — `horizon`은 원문이 그 과제를 두고 단기/중기/장기라고
   직접 말할 때만 붙는다. 미분류 비율을 낮추려고 계약을 느슨하게 하지 않는다.
3. **검증을 통과한 응답만 캐시된다.** 실패한 호출은 캐시에 남기지 않는다. 검증을 풀어서
   통과시키는 것은 언제나 틀린 수정이다 — 프롬프트를 고치거나 사람 정정을 입력한다.
4. **캐시 키에 프롬프트와 payload가 들어간다.** 프롬프트를 고치면 그 단계만 자동으로 무효가 된다.
   의미 계약이 바뀌면 이전 정정·승인이 잘못 재사용되지 않는지 확인한다.
5. **템플릿의 `__PAYLOAD__` 자리**와 브라우저 테스트가 잡는 셀렉터(`.step.active` 텍스트,
   `#sky g.task` / `g.person` / `g.skill`)를 유지한다. 리디자인하면 두 브라우저 테스트를 돌린다.
6. **`result.json`은 `run_id`로 봉인돼 있다.** 직접 수정하지 않는다. 고칠 일이 있으면
   `corrections-template.json`을 편집해 재실행한다.
7. **한 호출은 한 종류의 판단만 한다.** 결과가 나쁠 때 프롬프트를 더 길고 복잡하게 만들기 전에,
   판단을 단계로 나눌 수 있는지 먼저 본다. 추출이 `tasks`/`capabilities`/`links` 세 단계인 이유다.

## 산출물에서 하지 말 것

- 작성자 수를 중요도·준비도·역량 수준으로 해석하지 않는다. 그냥 그 말을 쓴 사람 수다.
- 보유 역량과 필요 역량의 차이를 조직의 gap 수치로 표시하지 않는다. 자기서술의 언급 차이다.
- 과제군 개수를 고정하지 않고, 원문에 없는 지능화·고도화·플랫폼화를 이름에 덧붙이지 않는다.
- 자동 10년 로드맵을 산출하지 않는다. 원자료는 개인의 근미래 서술이다.
- 성운 배치가 분류 품질을 증명한다고 설명하지 않는다. 배치는 설명을 위한 것이다.

## 지금 상태

`gh issue list`의 #47~#53이 이 트랙이다. #47·#48·#50 완료, **#49·#51·#52·#53 남음**.
#49(제목에 있는 시간 근거)가 #53을 막고 있는 유일한 체인이다.

커밋 제목은 기존 관례대로 `(#번호)`로 끝낸다. 구조 검증이 통과해도 **의미 품질은 증명되지 않는다** —
실제 판정은 내부망에서 `docs/nebula-quality-evaluation.md`의 표본 평가로만 가능하다.
