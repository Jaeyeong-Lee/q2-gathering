#!/usr/bin/env bash
# 2750 남은 두 렌더(scene2, scene2-noglow) 순차 실행 — 디스크 확보 후 재시도.
set -uo pipefail
WT="/Users/winter/orca/workspaces/nebula-hyperframes-2750"
RESULTS="$WT/render/results2.txt"
: > "$RESULTS"

for pair in "scene2:nebula-scene2-2750.mp4" "scene2-noglow:nebula-scene2-2750-noglow.mp4"; do
  d="${pair%%:*}"; out="${pair##*:}"
  echo "=== $d → $out : $(date '+%H:%M:%S') ===" | tee -a "$RESULTS"
  df -h /System/Volumes/Data | tail -1 | tee -a "$RESULTS"
  ( cd "$WT/video-2750/$d" && { time npx hyperframes render --quality high --fps 30 --output "$WT/render/$out" ; } 2>&1 \
      | tail -20 | tee -a "$RESULTS" )
  ls -la "$WT/render/$out" 2>&1 | tee -a "$RESULTS"
done
echo "RENDER2 DONE $(date '+%H:%M:%S')" | tee -a "$RESULTS"
