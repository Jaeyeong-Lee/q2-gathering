# engine-codex — Observatory Stage

지도를 화면 전체에 펼쳐 320개의 별이 첫 시선과 가장 넓은 면적을 차지한다.
장면 문장·수치·검색·인스펙터는 지도 위에 뜨는 관측 장비처럼 배치해 고정 2열 격자를 없앴다.
하단의 긴 진행 레일은 발표의 현재 위치를 대강당 뒤에서도 읽게 하는 하나의 강한 구조적 장치다.

## 바꾼 것

| 전 | 후 |
|---|---|
| 62px 헤더 + 164px hero + workspace + 84px footer의 4단 격자 | 1080px 전체 지도 위에 헤더·문장·도구·진행 레일을 겹친 단일 무대 |
| 지도 1fr / 인스펙터 336–390px의 고정 2열 분할 | 지도는 전체 폭, 인스펙터는 우측 반투명 플로팅 패널 |
| 10–14px 중심의 본문·라벨 | 본문 17–18px, 도구 14–16px, 제목 42–62px 중심의 발표장 스케일 |
| hero가 지도 높이 164–178px를 차지 | 장면 제목과 수치를 지도 좌측 상단에 직접 오버레이 |
| 화면 아래 분리된 작은 footer | 지도 위를 가로지르는 76px 장면 진행 레일 |
| 합성 배지가 story 모드에서만 표시 | 합성 payload에서는 live/story 모두 `#synthetic-mark` 표시 |
| Apple SD Gothic Neo 우선 폰트 | Pretendard → Apple SD Gothic Neo → Malgun Gothic → sans-serif 순 폴백 |
| 데스크톱에서도 작은 고정 패널 중심 | 1800px+, 1000px 이하, 700px 이하에서 각각 무대·패널·모바일 흐름 재배치 |

## 알려진 한계

- `docs/engine-layout-brief.md`는 Pretendard CDN import를 요구하지만, 정본인 `docs/q3-visual-brief.md`의 외부 요청 0·오프라인 계약 및 `nebula_browser.cjs` 검사를 깨뜨린다. 따라서 원격 import는 넣지 않고 지정된 폰트 스택과 말군고딕 폴백을 유지했다.
- 우측 인스펙터는 지도 위 오버레이이므로 그 아래 별 일부를 가린다. 고정 열로 지도를 축소하지 않으며, 발표자가 근거를 읽을 때의 정보 밀도를 우선했다.
- 이 브랜치에는 `nebula/templates/story.js`가 없다. story 회귀는 저장소의 계약용 `tests/q3_story_stub.js`를 `q3_story_check.cjs`로 열어 9비트와 reduced-motion을 확인했다.

## 검수 결과

- 합성 320명 fixture: 320명 / 682개 과제 / 40개 과제군, before/after 각 5장, 1920×1080.
- Chrome Performance/CDP timeline 기록, 장면 1→2: requestAnimationFrame 표본 45개 중 50ms 초과 4개, 최대 50.10ms. trace는 `/tmp/engine-codex-trace.json`에 생성해 확인했으며 민감 데이터 없이 합성 fixture만 사용했다.
- `pytest tests/test_nebula_pipeline.py tests/test_nebula_http.py tests/test_nebula_network.py tests/test_nebula_fixture.py tests/test_nebula_deck.py -q`: **40 passed, 7 subtests passed**.
- `tests/nebula_q3.cjs`: **PASS**.
- `tests/nebula_presentation.cjs`: **PASS**.
- `tests/nebula_browser.cjs data/q3-visual/browser-check`: **PASS** (mobile 및 offline 포함).
- `tests/q3_story_check.cjs tests/q3_story_stub.js /tmp/engine-codex-story-shots`: **PASS** (9 beats 15877ms, reduced motion 641ms).
- `#mode=story`: 위 story 검사에서 1920×1080 및 reduced-motion으로 열어 회귀 없음 확인.
