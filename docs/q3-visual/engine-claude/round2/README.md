# engine-claude round2 — 「무대와 무인」 (Theatrical)

지시서: `docs/engine-layout-round2-brief.md`. 바꾼 파일은 `nebula/templates/nebula.html` 하나다(live CSS 재작성 + JS 3줄 추가·4줄 수정). round1 폴더(`docs/q3-visual/engine-claude/` 최상위)는 건드리지 않았다.

## 구도 원리

1. **화면은 무대다.** 위 2/3는 지도가 떠 있는 무대 공간이고, 아래 1/3은 조명이 떨어지는 바닥 밴드다. 바닥의 앞 모서리에는 장면 진행이 각광(footlight)처럼 켜진다.
2. **문장은 바닥에서 자막처럼 떴다가 사라진다.** 장면 문장은 밴드 가운데에서 떠오르고 약 10초 머문 뒤 사라진다. 막 이름(eyebrow)만 남는다. 숫자와 범례·각주는 무대 양쪽 날개(wing)에 놓았다.
3. **근거는 현장에서 펼쳐진다.** 인스펙터는 없다. 무언가를 고르면 그 별에 조명 링과 스포트라이트가 떨어지고, 지시선 끝에 근거 카드가 그 자리에서 열린다. 장면이 바뀔 때는 짧게 암전됐다가 새 무대로 조명이 들어온다.

## 왜 이 구도인가

10m 스크린 앞 300명은 지도를 **읽지** 않고 **본다**. 사람들이 읽는 것은 한 번에 한 문장이다. 그래서 읽을 문장이 뜨는 자리(바닥)와 볼 대상이 있는 자리(무대)를 위아래로 갈라 서로 겹치지 않게 했다. 발표자가 한 사람을 고르면 청중의 눈은 이미 그 별에 가 있다. 따라서 근거가 화면 구석 패널이 아니라 그 별 옆에서 열려야 시선이 이동하지 않는다. 암전은 "여기서 장면이 바뀐다"는 신호를 말없이 준다.

## round1과 근본적으로 다른 점

1. **화면을 나누는 축이 다르다.** round1은 지도가 화면 전체이고 UI는 네 가장자리에 떠 있었다(중심 + 테두리). round2는 화면을 위 무대와 아래 바닥으로 나눈다(위아래 두 층). 글자는 지도 위에 한 글자도 올라가지 않는다.
2. **정보가 붙는 곳이 다르다.** round1의 카드는 오른쪽 아래 고정 자리에서 열렸다. 선택 대상과는 무관했다. round2의 카드는 선택된 별의 화면 좌표를 따라 열리고, 링과 지시선으로 그 별과 묶인다. 사람, 과제, 성운, 역량마다 거리와 링 크기가 다르다.
3. **시간 설계가 있다.** round1은 정적 배치였다. round2는 장면 전환마다 암전 → 조명 → 자막 등장 → 자막 퇴장이라는 큐 순서를 가진다. 선택이 일어나면 자막이 물러난다. 화면이 시간에 따라 스스로 비워진다.

## 5컷

`shots/after-*.png` — 합성 픽스처 `nebula/fixtures/q3/`(320명, 예시 인물 P000), 1920×1080 live 모드. 각 장면에 들어가고 1.3초 뒤에 찍었다(암전이 걷히고 자막이 떠 있는 순간).

| 파일 | 장면 | 이 컷에서 보이는 원리 |
|---|---|---|
| `after-0-people` | 장면 0 사람 | 떠 있는 지도, 바닥 자막, 양쪽 날개 숫자, 첫 번째 각광 |
| `after-1-closeup` | P000 클로즈업 | 조명 링 + 스포트라이트 + 지시선 끝 현장 카드, 자막 물러남 |
| `after-2-split` | 장면 1 분열 | 같은 무대, 두 번째 각광, 새 자막 |
| `after-3-grid` | 장면 2 PJT 격자 | 격자도 무대 공간 안에만 선다 |
| `after-4-pjt-nebula` | P000의 PJT 성운 | PJT 진입도 암전 큐 하나로 처리 |

## 무엇을 바꿨나

| 요소 | round1 | round2 |
|---|---|---|
| 구조 | 지도 전면 + 가장자리 오버레이 | 위 무대(지도, viewBox 약 1.2배) + 아래 `--floor:33.333vh` 바닥(`footer`가 바닥 자체) |
| 장면 문장(hero) | 왼쪽 위 | 바닥 가운데 3열 그리드의 가운데 칸. `animation`으로 떠올랐다 13초에 걸쳐 사라짐 |
| 숫자 | 오른쪽 위 | `.numbers{display:contents}`로 바닥 왼쪽/오른쪽 날개 |
| 범례 · 각주 | 왼쪽 아래 | 왼쪽 날개(범례) · 오른쪽 날개(각주) |
| 진행 단계 | 맨 아래 | 바닥 앞 모서리의 각광. 활성 단계는 위로 빛이 번짐 |
| 인스펙터 | 오른쪽 아래 떠 있는 카드 | 없음. `#panel`은 선택 대상 옆 현장 카드(`.workspace[data-cue]`) 또는 검색 중에만 검색창 위 프롬프터 |
| 검색 | 오른쪽 아래 | 바닥 가운데 아래(프롬프터 박스 자리) |
| 조작 | 오른쪽 아래 | 왼쪽 아래 PJT 선택, 오른쪽 아래 재생·이동. 평소 투명도 .62 |
| 브랜드 · 읽는 법 · 전체 화면 | 브랜드 숨김, 오른쪽 위 | 왼쪽 위 공연 제목처럼. `#synthetic-mark`는 오른쪽 위 유지 |
| 장면 전환 | 없음 | `.app::after` 암전(1초). 장면별·PJT 진입별로 다른 `animation-name`을 줘 매번 다시 재생 |
| 선택 | 카드만 | `.inspector::before` 조명 링, `::after` 지시선, `.universe::after` 스포트라이트 |

**JS (3줄 추가·4줄 수정)**: CSS는 선택된 별의 화면 좌표를 알 수 없다. 그래서 `renderPanel()` 끝에서 `cue()`를 부른다. `cue()`는 `renderPanel`과 같은 우선순위로 앵커(과제 목표 좌표 · 인물 `600,360` · 역량 원 · 성운 중심)를 고르고, `.workspace`에 `data-cue`/`data-side`와 `--cx`/`--cy`만 쓴다. `drawSkills`가 역량 원 좌표를 `skillAt`에 적고, `ResizeObserver`가 `cue()`를 다시 부른다. round1의 `#synthetic-mark` 한 줄은 그대로 뒀다. `window.nebula`, `nebulaCopy`, 페이로드, 셀렉터는 바꾸지 않았다.

## 알려진 한계

- **자막은 정말 사라진다.** 한 장면에 13초 넘게 머물면 바닥 가운데에는 막 이름만 남는다. 발표자가 오래 설명하는 장면에서는 의도한 동작이다. 다만 그 뒤에 들어온 청중은 문장을 못 본다. `prefers-reduced-motion`이면 자막은 계속 보이고 암전은 없다.
- **현장 카드는 지도를 가린다.** 장면 3에서 과제를 고르면 카드가 오른쪽 "필요 역량" 원을 덮는다. PJT 성운에서 성운을 고르면 반대편 성운 일부가 덮인다. 가려진 역량 근거는 카드 안에 원문으로 있다. 스포트라이트가 나머지를 어둡게 해서 의도된 초점처럼 보이게 했지만, 동시에 두 쪽을 비교하는 용도로는 불리하다.
- **카드는 무대 공간(위 2/3) 안에서만 열리므로 길면 스크롤된다.** 인물 카드는 1920×1080에서 과제 4개가 겨우 들어간다.
- 장면 설명 패널(overview)은 검색창에 포커스가 있을 때만 프롬프터로 보인다.
- 앵커 좌표는 렌더 시점에 계산한다. 창 크기 변경은 `ResizeObserver`로 따라가지만, 과제가 이동하는 1.65초 동안 링은 이미 도착 지점에 있다. 별이 링으로 날아 들어오는 모습이 된다.
- `:has()`(Chrome/Edge 105+)와 `translate` 속성에 의존한다. 1920×1080 한 가지 크기로 설계했고, 1600×1000(테스트 뷰포트)에서 겹침 없이 동작하는 것만 확인했다.
- 같은 키프레임을 장면 수만큼 복사해 뒀다(`dark0~4`, `line0~3`). 애니메이션은 이름이 바뀔 때만 다시 재생되기 때문이다. 장면을 추가하면 한 벌씩 늘려야 한다.
- 폰트 스택과 Pretendard CDN 미적용은 round1과 같다(오프라인 요청 0 테스트와 충돌).

## 검수 결과 (2026-09-13, 커밋 직전 워크트리)

| 검사 | 결과 |
|---|---|
| `pytest tests/test_nebula_{pipeline,http,network,fixture,deck}.py -q` | 40 passed, 7 subtests passed |
| `node tests/nebula_q3.cjs` | PASS: Q3 public engine, search, split, grid, PJT entry, reload, story mode |
| `node tests/nebula_presentation.cjs` | PASS: zero tasks, zero approvals, autoplay, first person, provenance, escaped unclassified PJT |
| `node tests/nebula_browser.cjs /tmp/…/browser-check` (합성 demo) | PASS: … mobile, … offline |
| `node tests/q3_story_check.cjs docs/q3-visual/story-claude/story.js <scratch>` | PASS: 9 beats 33963ms, reduced motion 6971ms |
| `node tests/q3_story_check.cjs tests/q3_story_stub.js <scratch>` | PASS: 9 beats 15419ms, reduced motion 925ms |
| story 회귀 | round1 커밋(`0709f37`)을 임시 worktree로 띄워 같은 story 검수를 돌렸다. 9비트 스크린샷이 round2와 **바이트 단위로 모두 같다**. (`docs/q3-visual/story-claude/shots/`의 1-2·1-3·1-4는 round1·round2 둘 다와 배경 별 위치가 다르다. 저장된 기준 이미지가 이전 커밋 `d6354e4` 시점 것이어서다.) |
| 외부 요청 · 페이지 오류 (스크린샷 스크립트) | 0 · 0 |
| 실명 노출 | 없음(합성 픽스처만 사용) |

### 320명 픽스처, 장면 1 → 2 전환 프레임

round1과 같은 방법이다. Playwright Chromium(headless, 소프트웨어 렌더링) 1920×1080에서 `browser.startTracing`으로 녹화하면서 `requestAnimationFrame` 간격을 쟀다. `go(2)` resolve 후 300ms까지다.

| | 프레임 수 | 50ms 넘는 프레임 | 최악 |
|---|---|---|---|
| round1 after (README 기록) | 54 | 11 | 133ms |
| round2 | 87 | **7** | 133ms |

암전 레이어와 스포트라이트는 `opacity`만 애니메이션한다. `backdrop-filter`는 쓰지 않았다. 절대값은 headless 기준이라 전후 비교용으로만 본다.
