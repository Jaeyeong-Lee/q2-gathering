#!/usr/bin/env bash
# 후보 B 대기 런처 — A(glm, pid 인자)가 끝난 뒤에 로컬 Codex로 B를 시작한다.
# 이유: A가 렌더 wall time을 측정하므로 CPU를 나눠 쓰면 A의 측정치가 오염된다.
set -uo pipefail

A_PID="${1:?waiting for pid}"
B_WT="/Users/winter/orca/workspaces/nebula-hyperframes-sol"

echo "[queue] A(pid $A_PID) 종료 대기 $(date '+%H:%M:%S')"
while kill -0 "$A_PID" 2>/dev/null; do sleep 20; done
echo "[queue] A 종료 감지 → B 시작 $(date '+%H:%M:%S')"

exec bash "$B_WT/run-codex-local.sh" BRIEF-320.md gpt-5.6-sol "$B_WT"
