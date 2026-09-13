# engine-kimi — 2부 live 모드 레이아웃 재설계

## 콘셉트 (3줄)
- 지도를 주인공으로: 고정 격자(62px header + 164px hero + 84px footer + 336px inspector)를 걷어내고, 지도를 `100dvh` 풀블리드로 펼쳤다. UI는 모두 지도 위에 뜬 오버레이 레이어다.
- inspector는 상시 고정열이 아니라 오른쪽 플로팅 패널(bottom 56px, width ≤34vw, `backdrop-filter: blur`)로 띄워, 지도 위에서 필요할 때만 시선을 빌린다. 발표장 300명이 보는 것은 패널이 아니라 지도다.
- 대강당 기준 16px 미만 본문 금지: 본문 16px·패널 본문 15~21px·H1 46px·숫자 56px로 상향. 폰트 스택을 Pretendard 우선으로 교체하고 `Malgun Gothic` 폴백을 유지한다.

## 바꾼 것 (전 → 후)
| 영역 | 전 | 후 |
|---|---|---|
| 그리드 | `header 62px / hero 164px / workspace 1fr+336px / footer 84px` 고정 격자 | 고정 격자 해체. 지도가 `100dvh` 전체, UI는 모두 지도 위 절대배치 오버레이 |
| inspector | 지도 오른쪽을 갈라먹는 336px 고정 열 | 오른쪽 플로팅 오버레이(≤34vw, `backdrop-filter: blur(16px)`). 지도를 덮지만 가시 폭을 크게 줄임 |
| hero | 지도 위 164px를 상시 점유 | 지도 위에 뜨는 상단 캡션(그라데이션 배경, 텍스트 영역만큼만 차지) |
| 숫자 | hero 오른쪽에 나란히 | hero에서 분리, 지도 우상단 오버레이로 이동 |
| footer/steps | 지도 아래 84px 밴드 | 지도 위 하단 오버레이(투명, pointer-events:none + 자식만 auto) |
| legend/footnote | 지도 안 하단 | 지도 위 좌하단 오버레이, steps와 겹치지 않게 bottom 정렬 |
| 본문 크기 | 12~14px | 15~16px (숫자·제목은 그대로 크게) |
| 폰트 | `"Apple SD Gothic Neo","Malgun Gothic"` | `"Pretendard","Apple SD Gothic Neo","Malgun Gothic"` |
| 합성 배지 | story 모드에서만 표시 | live 모드에서도 항상 표시 (`hidden=!D.synthetic`) |

## Pretendard @import에 관하여
브리프 §3의 `@import url("https://cdn.jsdelivr.net/...pretendard...")` 지시는 **적용하지 않았다.**
`tests/nebula_browser.cjs`가 `assert.deepEqual(requests, [])`로 외부 요청 0을 강제하고, 발표장은 `file://` 오프라인(§8 “외부 요청 0”)이다. 웹폰트 링크를 `<head>`에 넣는 순간 이 테스트가 실패하므로, **스택 맨 앞에 `"Pretendard"`를 선언하고(설치된 환경이면 자동 적용) 미설치·네트워크 단절 환경에서는 `Apple SD Gothic Neo` → `Malgun Gothic`으로 폴백**하게 두는 쪽을 택했다. 브리프의 진의(대강당 한글 폰트)는 스택만으로 달성하고 오프라인 계약을 깨지 않는 선택이다.

## 알려진 한계
- `1920×1080` 한 단 기준으로 레이아웃을 우선 맞췄다. 700px 이하는 모바일 폴백을 유지했으나 중간 구간(1000~1500px)은 오버레이 폭을 %로 두어 최적화하지 않았다.
- inspector가 지도 위에 떠 있어, 오른쪽 끝 PJT 성운이 패널에 부분 가려진다. live에서 패널을 접지 않으면 해당 영역 조작이 불편하다(토글 UI는 이번 범위 밖).
- `footnote`(좌하단 배치 설명)는 11px로, 대강당에서 읽히기보다는 발표자/운영자 참고용이다.

## 검수 결과
- `pytest tests/test_nebula_pipeline.py tests/test_nebula_http.py tests/test_nebula_network.py tests/test_nebula_fixture.py tests/test_nebula_deck.py -q` → 40 passed
- `node tests/nebula_q3.cjs` → PASS
- `node tests/nebula_presentation.cjs` → PASS
- `node tests/nebula_browser.cjs /tmp/kimi-demo-after` → PASS (외부 요청 0, 오프라인 확인)
- `node tests/q3_story_check.cjs tests/q3_story_stub.js /tmp/kimi-story-shots` → PASS (story 모드 회귀 없음)
- `#mode=story` 수동 확인: header/hero/inspector/footer/steps 전부 숨김, `#synthetic-mark`만 노출 (nebula_q3.cjs가 검증)
- 퍼포먼스(320명 픽스처 → 실제 200명 fixture로 측정, scene 1→2 전환): frame 478개, 평균 11.8ms, **>50ms 3프레임, 최대 208.8ms** (go(1→2) 직후 초기 레이아웃/페인트 스파이크. 이후 안정)
