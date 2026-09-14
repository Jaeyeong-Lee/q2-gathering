# engine-kimi round2 — 「잉크와 종이」 (Typography-first)

> 2026-09-13. 브리프: `docs/engine-layout-round2-brief.md`. before는 round1(`../shots/`) 참조.

## 구도 원리 (3줄)

- 화면 오른쪽 끝에 폭 `--rail`(약 5.5vw)의 **세로쓰기 서가**를 세우고, 장면 문장(eyebrow·제목·부제)을 모두 `writing-mode: vertical-rl` 잉크 기둥으로 고정한다 — 문장이 장식이 아니라 구도의 축이다.
- 지도는 남은 좌측 전면을 차지하되, 인스펙터는 지도 위 오버레이 패널이 아니라 **문장 여백 아래에 녹아드는 고정 컬럼**(`--margin-w` 안쪽, 서가 왼쪽)으로 둔다 — 클릭해도 화면의 골격이 흔들리지 않는다.
- 5컷 모두 같은 골격(좌: 성운 / 우: 여백 컬럼 / 극우: 세로 서가) 위에 장면 상태만 얹는다. 구도가 서사를 지배하고, 장면 전환은 지도 안에서만 일어난다.

## round1 대비 근본적 차이 (3줄)

- round1(및 세 후보 공통)은 "지도를 최대한 크게 + 그 위에 UI를 띄운다"는 전제에서 출발해, UI가 지도 위를 떠다니는 오버레이 구도로 수렴했다. 이번엔 **문장·여백·지도의 배치 자체를 먼저 설계**하고 지도는 그 안에 할당된 영역이다.
- round1의 인스펙터는 지도 위를 덮는 플로팅 패널이었지만, 이번엔 **레이아웃 골격의 일부(고정 여백 컬럼)**다 — 열리고 닫혀도 지도의 캔버스가 리플로우되지 않는다.
- 타이포그래피가 정보 전달 수단을 넘어 **구도 장치**가 됐다: 세로쓰기 서가는 10m 스크린에서도 "인상"으로 읽히는 세로 잉크 기둥이고, keep-all·자간(0.14–0.42em)을 조판 요소로 쓴다.

## 한계

- 폰트 임베딩은 이번 라운드 범위 밖이라 round1 스택(Pretendard 등) 그대로 — 세로쓰기 인상은 시스템 폰트 의존.
- 좁은 화면(≤1000px)에서는 세로 서가가 가로 모드로 꺾이고(미디어쿼리), 소형에서는 구도 원리가 성립하지 않는다. 대강당 16:9 전제의 구도다.
- 세로 제목은 길이가 긴 장면 문구에서 `max-height`로 잘릴 수 있어, 문구 카피 길이에 상한이 생긴다.
- `body.story` 모드에서는 서가·여백을 모두 숨기고 지도만 남겨, 스토리 회귀는 기존 동작을 유지한다(구도는 발표 라이브 화면 전용).

## 검수 결과 (2026-09-13, 전부 PASS)

- `pytest tests/test_nebula_{pipeline,http,network,fixture}.py -q` — **35 passed**
- `node tests/nebula_q3.cjs` — PASS (public engine, search, split, grid, PJT entry, reload, story mode)
- `node tests/nebula_presentation.cjs` — PASS (zero tasks, zero approvals, autoplay, provenance 등)
- `node tests/nebula_browser.cjs` — PASS (scenes, matrix, network, correction flows, offline)
- `node tests/q3_story_check.cjs docs/q3-visual/story-kimi/story.js` — PASS (9 beats, reduced motion) — story 회귀 없음

## 스크린샷 (1920×1080)

`shots/` — `after-scene0.png`(장면 0), `after-closeup.png`(클로즈업), `after-scene1-split.png`(분열), `after-scene2-grid.png`(격자), `after-pjt-nebula.png`(PJT 성운).
