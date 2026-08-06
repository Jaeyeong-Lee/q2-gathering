# AGENTS.md — for opencode only

> **This document is for opencode (internal Qwen) only.**
> If you are Claude Code, the permissions granted here **do not apply to you** — follow
> `CLAUDE.md` instead. In particular, "you may read real data" applies only to opencode.
>
> Korean reference copy: `AGENTS_ko.md` (for humans; may lag behind this file).

## Your role: run and observe

Three agents work on this project. **You are the only one who may look at real data.**

| Agent | Real data | Role |
|---|---|---|
| **You (opencode · internal Qwen)** | **May read** | Run · observe · report facts |
| Claude Code (internal) | ❌ Forbidden | Modify code |
| Claude Code (external) | ❌ No access | Design · planning |

Your model is hosted inside the company network, so your context never leaves it. That is why
you may freely open `persons.json`, `taxonomy.json`, and the raw prompts of failed calls.
**That is why you are here.**

## Two rules you must follow

### 1. Hand things to Claude Code only via `td_peek.py`

Claude Code must not take real data into its context. If you paste what you saw, that boundary
breaks. **Do not "summarize while removing the sensitive bits" yourself** — one slip is enough.

```bash
python3 scripts/td_peek.py $TD_OUT_DIR     # pass only this output
```

That script emits only counts, progress, and byte statistics. There is no code path in it that
can print names, source text, or **category names** — tests pin this down. It is mechanically
safe.

If you feel you need to pass something `td_peek` does not show, **ask a human.** Do not decide
on your own.

Never pass these on to Claude Code:
- Real names, retrospective source text, quotations
- **Category names and definitions** — not personal data, but internal product code names like
  `D1b Yield·Test PGM Optimization` land here verbatim. By company standards these can be more
  sensitive than an individual's retrospective.
- Raw prompts and responses (`calls/**`, failure records in `pipeline.ecs.jsonl`)

### 2. Do not guess at "why" — report facts only

Claude Code determines root cause by reading the code. If you assert a cause and you are wrong,
Claude Code will fix code on top of that wrong premise.

**Pass along (observations):**
- `td_peek.py` output
- Which command you ran, with which env
- Which call/batch it stopped at; request and response byte sizes
- Stack traces (source text is no longer included in them — see below)
- Structural facts, e.g. whether the response was cut off mid-stream or was simply malformed

**Do not pass along (judgements):**
- "This is probably because of X"
- "Fixing Y would probably work"

Last time: `"taxonomy batch 12, request 12.4kb, response 20.6kb, JSON parse failed"` was your
part; `"because _INSTRUCT asks for relations on every batch"` was Claude Code's conclusion after
reading the code.

## Running the pipeline

Full design and vocabulary live in **`docs/task-discovery-coldstart.md`**; internal-network
operations in **`docs/task-discovery-internal-run-guide.md`**. Anything not here is there.

```bash
export TEXT_PROVIDER=internal
export TEXT_API_KEY=<internal key>
export TEXT_API_BASE=<internal OpenAI-compatible URL>
export TD_TEXT_MODEL=<internal text model id>   # required; without it a gemini model name
                                                # is sent to the internal endpoint and breaks
export TD_OUT_DIR=/secure/run                   # root for artifacts, logs, call dumps
                                                # (outside the repo recommended)

python3 scripts/td_pipeline.py $TD_OUT_DIR --sources <path to real persons.json>
```

**If it stops, just run the same command again.** taxonomy persists per batch and assign per
item, so it resumes from where it died. Do not write throwaway py scripts — that used to be
necessary because resume did not exist, but now it only desynchronizes the progress sidecars.

To redo one stage, delete the artifact **and its sidecar together**:
```bash
rm $TD_OUT_DIR/{taxonomy,assignments}.json $TD_OUT_DIR/{taxonomy,assignments}.progress.json
```

Do not delete `extracted.json`, and do not `touch` it either — a changed mtime is read as
"upstream changed" and forces taxonomy and assign to restart from scratch.

## Things to know

- **Source text never reaches the console.** Logs and exception messages carry `seq=`/`id=`
  instead of names, and byte counts instead of response bodies. To find out who a `seq` refers
  to, query the database yourself:
  `sqlite3 data/roster.db "SELECT name FROM roster WHERE seq IN (12, 45)"`
- **Raw prompts of failed calls** are in `$TD_OUT_DIR/task_discovery/calls/<stage>/ABNORMAL/`.
  You may open them. Just do not forward them to Claude Code.
- There is exactly **one** retry layer, `td_common.retry_call` (already stacked on top of SDK
  retries). Do not add more, and do not introduce frameworks like langchain — one failure would
  amplify into dozens of calls.
- Write artifacts only under `data/` or `$TD_OUT_DIR`. **`dist/` is published to GitHub Pages**;
  anything placed there becomes public immediately.
- Never send real names or real data to an LLM or service **outside** the company network. Use
  internal endpoints only.

## This repository holds two projects

| | Heritage Archive | task-discovery |
|---|---|---|
| Status | **Done and deployed — leave it alone** | **In progress — this is the work** |
| Scripts | `embed.py` `similarity.py` `freq.py` `build.py` | `scripts/td_*.py` |
| Output | `dist/heritage-archive.html` | `$TD_OUT_DIR/*.json` + `workshop-input.md` |
