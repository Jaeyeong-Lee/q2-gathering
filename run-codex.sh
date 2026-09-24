#!/usr/bin/env bash
# Hyperframes x nebula — codex(OpenRouter 종량) 런처
# 사용: run-codex.sh [브리프파일] [모델]   (기본: BRIEF.md, z-ai/glm-5.2)
set -uo pipefail

WT="/Users/winter/orca/workspaces/nebula-hyperframes"
BRIEF="${1:-BRIEF.md}"
MODEL="${2:-z-ai/glm-5.2}"

cd "$WT" || exit 1

export OPENROUTER_API_KEY
OPENROUTER_API_KEY="$(grep -m1 '^OPENROUTER_API_KEY=' "$HOME/.hermes/.env" | cut -d= -f2-)"
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "OPENROUTER_API_KEY not found" >&2
  exit 2
fi

LOG="$WT/codex-run-$(basename "$BRIEF" .md).log"

{
  echo "=== run start $(date '+%Y-%m-%d %H:%M:%S') ==="
  echo "cwd=$WT  branch=$(git rev-parse --abbrev-ref HEAD)  brief=$BRIEF  model=$MODEL"
} >> "$LOG"

codex exec -p openrouter -m "$MODEL" \
  --dangerously-bypass-approvals-and-sandbox \
  -C "$WT" \
  "$(cat "$WT/$BRIEF")" >> "$LOG" 2>&1 < /dev/null

echo "EXIT=$? $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG"
