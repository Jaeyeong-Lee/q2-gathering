#!/usr/bin/env bash
# 2750 실규모 렌더 — 에이전트가 작성해 둔 컴포지션 3종을 직접 렌더한다(LLM 불필요).
# 각 렌더는 순차 실행하고 wall time을 기록한다(동시 실행하면 측정이 오염된다).
set -uo pipefail

WT="/Users/winter/orca/workspaces/nebula-hyperframes-2750"
cd "$WT" || exit 1
mkdir -p render
RESULTS="$WT/render/results.txt"
: > "$RESULTS"

render_one () {
  local dir="$1" out="$2" label="$3"
  echo "=== $label : $(date '+%H:%M:%S') ===" | tee -a "$RESULTS"
  ( cd "$WT/video-2750/$dir" && \
    { time npx hyperframes render --quality high --fps 30 --output "$WT/render/$out" ; } 2>&1 \
      | grep -E "^(real|user|sys)|setup|capture|encode|assemble|Total|total|Encode|Done|error|Error" | tee -a "$RESULTS" )
  ls -la "$WT/render/$out" >> "$RESULTS" 2>&1
  echo "--- $label done $(date '+%H:%M:%S') ---" >> "$RESULTS"
}

echo "### lint" | tee -a "$RESULTS"
for d in expand scene2 scene2-noglow; do
  echo "--- $d" | tee -a "$RESULTS"
  ( cd "$WT/video-2750/$d" && npx hyperframes lint 2>&1 | tail -6 | tee -a "$RESULTS" )
done

render_one expand        nebula-expand-2750.mp4       "expand (사람→과제 전개)"
render_one scene2        nebula-scene2-2750.mp4       "scene2 (성운, glow 전체)"
render_one scene2-noglow nebula-scene2-2750-noglow.mp4 "scene2-noglow (강조 노드만 glow)"

echo "ALL DONE $(date '+%H:%M:%S')" | tee -a "$RESULTS"
