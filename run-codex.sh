#!/usr/bin/env bash
# Hyperframes x nebula 장면 렌더 실험 — codex(OpenRouter 종량) 런처
# 재실행 가능: 같은 스크립트를 다시 돌리면 이어서 진행한다.
set -uo pipefail

WT="/Users/winter/orca/workspaces/nebula-hyperframes"
LOG="$WT/codex-run.log"

cd "$WT" || exit 1

export OPENROUTER_API_KEY
OPENROUTER_API_KEY="$(grep -m1 '^OPENROUTER_API_KEY=' "$HOME/.hermes/.env" | cut -d= -f2-)"
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "OPENROUTER_API_KEY not found" >&2
  exit 2
fi

{
  echo "=== run start $(date '+%Y-%m-%d %H:%M:%S') ==="
  echo "cwd=$WT  branch=$(git rev-parse --abbrev-ref HEAD)  model=z-ai/glm-5.2"
} >> "$LOG"

codex exec -p openrouter -m z-ai/glm-5.2 \
  --dangerously-bypass-approvals-and-sandbox \
  -C "$WT" \
  "$(cat "$WT/BRIEF.md")" >> "$LOG" 2>&1 < /dev/null

echo "EXIT=$? $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG"
