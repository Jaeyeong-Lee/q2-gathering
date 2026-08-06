# CLAUDE.md — for Claude Code only

> `AGENTS.md` is **for opencode only**. The permission it grants — "you may read real data" —
> **does not apply to you.** Only opencode (internal Qwen) may read real data, because that
> model is hosted inside the company network and its context never leaves it.
>
> Korean reference copy: `CLAUDE_ko.md` (for humans; may lag behind this file).

## Your role: modify code. You do not get to see real data

| Agent | Real data | Role |
|---|---|---|
| opencode (internal Qwen) | May read | Run · observe · report facts |
| **You (Claude Code)** | **❌ Forbidden** | **Modify code** |

The pipeline *processing* real data and you *reading* it are different things. Whatever enters
your context leaves the network.

### Never open these — not via `Read`, nor `cat`/`head`/`grep`/`python -c open(...)`

| File | Why |
|---|---|
| `data/persons.json` | Real names + retrospective source text |
| `extracted.json` / `assignments.json` | Real names + verbatim quotations |
| `taxonomy.json` / `aggregates.json` | **Category names/definitions = internal product code names, tech strategy** |
| `workshop-input.md`, `interpretation/**` | Both of the above |
| `calls/**`, `pipeline.ecs.jsonl` | Raw prompts and responses |
| `$TD_OUT_DIR/**` | All of the above lives here |

**Category names are off limits too.** They are not personal data, but internal code names such
as `D1b Yield·Test PGM Optimization` land there verbatim — by company standards that can be more
sensitive than an individual's retrospective.

`.claude/settings.json` carries `deny` rules, but that is a safety net against mistakes, not a
guarantee — it can be bypassed through Bash. **Honor this as a rule, not as a fence.**

### Do this instead

- **Learn state only from `td_peek.py` output** that opencode gives you. You may run it
  yourself (`python3 scripts/td_peek.py $TD_OUT_DIR`), but do not look at anything beyond
  its output.
- **Reproduce and debug against the synthetic corpus.** `td_sources.py` generates fake data with
  the same schema — that is exactly what it exists for. Every test injects a fake `call`.
- **Root-cause analysis is your job.** opencode hands you facts like "batch 12, parse failed at
  20.6kb response". Why that happens is for you to determine **by reading the code**.
- If you truly need the raw text of a failed call, it is in
  `$TD_OUT_DIR/task_discovery/calls/<stage>/ABNORMAL/` — **ask a human or opencode to check it.**
  Do not open it yourself.

### Console output is safe to read

Source text has been stripped from logs and exception messages — `seq=`/`id=` instead of names,
byte counts instead of response bodies. So running a command and reading its output is fine.
**But do not undo those guards**: it is tempting to put raw text back into logs for easier
debugging, and that collapses this whole structure.

Full design: `docs/task-discovery-coldstart.md`. Internal-network operations:
`docs/task-discovery-internal-run-guide.md`.

---

## General coding guidelines

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

Strong success criteria let you loop independently. Weak criteria ("make it work") require
constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to
overcomplication, and clarifying questions come before implementation rather than after mistakes.
