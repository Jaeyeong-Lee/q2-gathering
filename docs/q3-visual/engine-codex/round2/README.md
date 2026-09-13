# engine-codex round2 — 관측 궤도

카메라는 고정된 지도를 내려다보지 않고, 장면마다 성운의 고도와 피치를 바꾸며 우주 안을 이동한다.
사면 0은 지평선에 붙은 저고도 관측, 인물 클로즈업과 분열은 선택한 별 주변의 근접 궤도, PJT 격자는 탑뷰다.
HUD는 하단 중앙의 단일 관측 레일로 줄이고, 근거가 필요한 선택 상태에서만 우측 패널이 도킹한다.

## 왜 이 구도인가

발표의 서사는 같은 지도를 설명하는 네 개의 슬라이드가 아니라, 관측 거리가 달라지며 대상의 의미가 바뀌는 여정이다. 낮은 앵글에서는 320명의 기록이 지평선처럼 펼쳐지고, 한 사람에게 접근하면 주변 별이 멀어지며 개인의 네 과제가 궤도 위에 나타난다. PJT 장면에서는 카메라가 상승해 전체 배치를 비교 가능한 관측면으로 바꾼다.

## round1과 근본적으로 다른 점

1. round1은 지도가 고정된 무대이고 UI가 그 위를 이동했지만, round2는 관측면 자체의 `rotateX`·회전·스케일이 장면 전환의 주동작이다.
2. round1은 언제나 전면 지도와 큰 플로팅 인스펙터를 함께 보여줬지만, round2는 평상시 정보를 한 줄로 접고 선택 순간에만 근거 패널을 도킹한다.
3. round1의 장면 차이는 별 배치 변화가 중심이었지만, round2는 저고도 지평선 → 근접 궤도 → 탑뷰라는 카메라 문법으로 같은 데이터의 읽는 거리를 바꾼다.

## 5컷

- `shots/after-scene-0.png`: 장면 0, 저고도 지평선 관측.
- `shots/after-closeup.png`: 예시 인물 별에 접근한 근접 궤도.
- `shots/after-split.png`: 같은 궤도에서 네 과제가 분열된 상태.
- `shots/after-grid.png`: 카메라가 상승한 PJT 탑뷰.
- `shots/after-pjt-nebula.png`: 탑뷰에서 데이터 플랫폼 성운으로 진입.

모든 캡처는 합성 fixture만 사용했으며 1920×1080이다.

## 알려진 한계

- CSS 원근 변환은 SVG 전체 관측면에 적용하므로 저고도 장면의 별과 연결선도 함께 납작해진다. 실제 3D 좌표나 개별 깊이 정렬은 이번 범위에 포함하지 않았다.
- `:has()`로 현재 장면과 선택 패널을 감지한다. 검수 대상 Chromium에서는 동작하지만 오래된 브라우저에서는 카메라 구도와 도킹 상태가 기본 평면 배치로 폴백할 수 있다.
- 모바일에서는 가독성과 조작성을 위해 원근 카메라를 해제하고 기존 수직 흐름을 유지한다.

## 검수 결과

- 합성 fixture 빌드: 320명 / 682개 과제 / 40개 과제군.
- `pytest tests/test_nebula_pipeline.py tests/test_nebula_http.py tests/test_nebula_network.py tests/test_nebula_fixture.py tests/test_nebula_deck.py -q`: **40 passed, 7 subtests passed**.
- `NEBULA_PYTHON=$PWD/.venv/bin/python node tests/nebula_q3.cjs`: **PASS** — public engine, search, split, grid, PJT entry, reload, story mode.
- `NEBULA_PYTHON=$PWD/.venv/bin/python node tests/nebula_presentation.cjs`: **PASS**.
- `NEBULA_PYTHON=$PWD/.venv/bin/python node tests/nebula_browser.cjs data/q3-visual/browser-check`: **PASS** — scenes, mobile, corrections, stale review, offline.
- `NEBULA_PYTHON=$PWD/.venv/bin/python node tests/q3_story_check.cjs tests/q3_story_stub.js /tmp/engine-codex-r2-story-shots`: **PASS** — 9 beats 16640ms, reduced motion 1006ms.
