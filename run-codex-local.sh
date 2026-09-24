#!/usr/bin/env bash
# 후보 런처 — 로컬 Codex(ChatGPT 구독, OAuth). OpenRouter 프로파일을 쓰지 않는다.
# 사용: run-codex-local.sh <브리프파일> <모델> <작업디렉토리>
set -uo pipefail

BRIEF="${1:?brief}"
MODEL="${2:-gpt-5.6-sol}"
WT="${3:?worktree}"

cd "$WT" || exit 1

LOG="$WT/codex-run-$(basename "$BRIEF" .md)-${MODEL//\//_}.log"

{
  echo "=== run start $(date '+%Y-%m-%d %H:%M:%S') ==="
  echo "cwd=$WT  branch=$(git rev-parse --abbrev-ref HEAD)  brief=$BRIEF  model=$MODEL  route=local-codex(subscription)"
} >> "$LOG"

codex exec -m "$MODEL" \
  --dangerously-bypass-approvals-and-sandbox \
  -C "$WT" \
  "$(cat "$WT/$BRIEF")" >> "$LOG" 2>&1 < /dev/null

echo "EXIT=$? $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG"
