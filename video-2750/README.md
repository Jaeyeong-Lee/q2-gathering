# 2,750-task HyperFrames experiment

`generate.mjs` reads only `../fixtures/payload-2750-slim.json` and generates three independent projects:

- `expand/`: 320 people expanding into 2,750 task stars.
- `scene2/`: the round-2 nebula scene with `starGlow` on every person/task node.
- `scene2-noglow/`: the same nebula scene, with `starGlow` only on highlighted PJT 0 nodes.

Regenerate with `node video-2750/generate.mjs`. Each project pins HyperFrames 0.8.73, the current release at experiment time. Round 2 used 0.8.72, so the one-patch CLI difference is recorded as a benchmark caveat.
