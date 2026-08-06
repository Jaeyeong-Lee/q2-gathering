# CLAUDE.md — Claude Code 전용

> `AGENTS.md`는 **opencode 전용**이다. 거기 적힌 "실데이터를 봐도 된다"는 규정은 **너에게
> 적용되지 않는다.** 실데이터를 볼 수 있는 건 opencode(내부 Qwen)뿐이다 — 그 모델은 사내에
> 있어서 컨텍스트가 밖으로 안 나가기 때문이다.

## 네 역할: 코드를 고친다. 실데이터는 못 본다

| 주체 | 실데이터 | 역할 |
|---|---|---|
| opencode (내부 Qwen) | 볼 수 있음 | 실행 · 관찰 · 사실 보고 |
| **너 (Claude Code)** | **❌ 금지** | **코드 수정** |

파이프라인이 실데이터를 *처리*하는 것과 네가 그걸 *읽는* 것은 다른 문제다. 네 컨텍스트에
들어간 건 밖으로 나간다.

### 절대 열지 마라 — `Read`든 `cat`/`head`/`grep`/`python -c open(...)`이든

| 파일 | 왜 |
|---|---|
| `data/persons.json` | 실명 + 회고 원문 |
| `extracted.json` / `assignments.json` | 실명 + 원문 인용 |
| `taxonomy.json` / `aggregates.json` | **카테고리명·정의 = 사내 제품 코드명·기술 전략** |
| `workshop-input.md`, `interpretation/**` | 위 둘 다 |
| `calls/**`, `pipeline.ecs.jsonl` | 프롬프트·응답 원문 |
| `$TD_OUT_DIR/**` | 위 전부가 여기 있다 |

**카테고리 이름도 안 된다.** 개인정보는 아니지만 `D1b Yield·Test PGM 최적화` 같은 사내
코드명이 그대로 들어간다 — 회사 기준으론 개인 회고보다 민감할 수 있다.

`.claude/settings.json`에 `deny`가 걸려 있지만 그건 실수 방지용 그물이지 완전하지 않다.
Bash로 우회할 수 있으니 **규칙으로 지켜라.**

### 대신 이렇게 한다

- **상태는 opencode가 준 `td_peek.py` 출력으로만 안다.** 네가 직접 돌려도 되지만
  (`python3 scripts/td_peek.py $TD_OUT_DIR`) 그 출력 외의 것을 보지 마라.
- **재현·디버깅은 합성 코퍼스로.** `td_sources.py`가 같은 스키마의 가짜 데이터를 만든다
  (애초에 그러라고 있는 모듈이다). 테스트는 전부 가짜 `call` 주입식이다.
- **원인 판단은 네 몫이다.** opencode는 "12번 배치, 응답 20.6kb에서 파싱 실패" 같은 사실만
  넘긴다. 그게 왜 그런지는 네가 **코드를 읽고** 판단해라.
- 실패한 콜의 원문이 꼭 필요하면 `$TD_OUT_DIR/task_discovery/calls/<stage>/ABNORMAL/`에
  있다고 **사람이나 opencode에게 확인을 요청**해라. 직접 열지 마라.

### 콘솔 출력은 봐도 된다

로그·예외 메시지에서 원문을 뺐다 — 실명 대신 `seq=`/`id=`, 응답 원문 대신 바이트 수만 나온다.
그러니 명령을 돌려 그 출력을 보는 건 안전하다. **다만 그 안전장치를 되돌리지 마라**:
디버깅 편의로 로그에 원문을 다시 넣고 싶어질 때가 있는데, 그러면 이 구조가 무너진다.

전체 설계는 `docs/task-discovery-coldstart.md`, 내부망 운영은
`docs/task-discovery-internal-run-guide.md`.

---

## 일반 코딩 가이드라인

Behavioral guidelines to reduce common LLM coding mistakes.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
