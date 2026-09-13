# engine-claude — 2부 live 레이아웃 재설계

지시서: `docs/engine-layout-brief.md`. 바꾼 파일은 `nebula/templates/nebula.html` 하나다(CSS 전체 + JS 한 줄).

## 콘셉트

1. **하늘이 화면 전체다.** 격자(header 62 · hero 164 · 지도 | inspector 336 · footer 84)를 없애고 지도를 1920×1080 전체에 깔았다. 나머지는 모두 그 위에 뜬다.
2. **가장자리 네 곳만 쓴다.** 왼쪽 위는 장면 제목, 오른쪽 위는 숫자와 합성 배지, 아래는 진행 단계와 조작 버튼이다. 가운데는 별만 남긴다.
3. **인스펙터는 필요할 때만 뜬다.** 사람·과제·성운·역량을 선택했을 때, 검색어를 입력했을 때, 검색창에 포커스가 있을 때만 오른쪽 아래 검색창 위로 카드가 올라온다. 평소에는 검색창 하나만 보인다.

## 바꾼 것 (전 → 후, 1920×1080 기준)

| 요소 | 전 | 후 |
|---|---|---|
| 전체 구조 | 4행 격자 + 지도/인스펙터 2열 | 지도 전면(`position:absolute; inset:0`), 나머지는 오버레이 |
| 지도 배율 | viewBox 1200×720 → 약 1.04배(1530×747 칸) | 약 1.23배(위 116px · 아래 80px만 비움). 면적 약 1.4배 |
| header | 62px 띠: 브랜드 + 배지 + 읽는 법 + 전체 화면 | 띠 없음. 읽는 법·전체 화면은 오른쪽 위 합성 배지 왼쪽. 브랜드 문구 숨김. 합성 빌드에서는 `.badge`를 숨긴다(합성 배지와 중복) |
| hero | 164px 띠, 숫자 48px | 띠 없음. 제목은 지도 왼쪽 위에 겹치고 위쪽에 짙은 그라데이션을 깐다. 숫자는 72px로 오른쪽 위 |
| inspector | 336px 고정 열(항상 보임) | 폭 440px 떠 있는 카드. `:has(.back)` · 검색어 입력 · `:focus-within`일 때만 열린다 |
| 검색 | 인스펙터 맨 위 | 오른쪽 아래, 조작 줄과 같은 높이. 카드는 그 위로 열린다 |
| toolbar | 지도 왼쪽 위 | 오른쪽 아래 검색창 왼쪽. 평소 투명도 .72, 마우스를 올리면 1. 범위 문구는 숨김 |
| legend · footnote | 11px · 10px, 지도 왼쪽 아래 | 18px · 16px, 같은 자리 |
| footer | 84px 띠, 단계 12px, 버튼 12px | 96px 그라데이션, 단계 20px, 버튼 18px |
| 본문 글자 | 기본 14px, 패널 10–15px | 기본 18px, 패널 16–24px(최소 16px), 성운·격자 라벨 21/16px, 역량 SVG 글자 17/14 viewBox px |
| h1 | `clamp(32px,3.35vw,54px)` | `clamp(40px,3.15vw,60px)` |
| 폰트 | `"Apple SD Gothic Neo","Malgun Gothic",sans-serif` | `"Pretendard","Apple SD Gothic Neo","Malgun Gothic",sans-serif` |
| `#synthetic-mark` | story에서만 표시(12px) | live에서도 표시. 16px 알약 모양, 오른쪽 위 |
| `@media` 3단계 | 1800+ · ≤1000 · ≤700 | 삭제. 1920×1080 1단 설계. 카드 폭·각주 폭만 `clamp`/`vw`로 줄어든다 |
| story 모드 | — | 달라진 것 없음. 공유 요소의 크기 변경은 `body:not(.story)`로 한정했고 `body.story{font-size:14px}`로 기본 글자 크기를 원래대로 고정했다 |

**JS 한 줄**: `$('synthetic-mark').hidden=!(S.mode==='story'&&D.synthetic)` → `!D.synthetic`. 기존 코드는 live에서 배지를 숨기므로 CSS만으로는 "live에서도 항상 보임"을 만족할 수 없다. 실데이터 빌드(`D.synthetic=false`)에서는 "합성" 표시가 거짓이 되므로 계속 숨긴다.

## 알려진 한계

- **Pretendard CDN `@import`는 넣지 않았다.** 지시서끼리 충돌한다. `tests/nebula_browser.cjs`(39·185행)와 `tests/q3_story_check.cjs`(56·76행)는 네트워크 요청 0을 검사하므로, 넣으면 필수 테스트 2종이 실패한다. `q3-visual-brief.md` §8도 "외부 요청 0: CDN·웹폰트 없이"라고 적는다. 게다가 `<style>` 안 `@import`는 렌더링을 막는다. 내부망 방화벽이 요청을 조용히 버리면 타임아웃까지 화면이 비어 있을 수 있다. 대신 폰트 스택 맨 앞에 Pretendard를 두었다. 설치된 PC에서는 Pretendard로, 없으면 Apple SD Gothic Neo → Malgun Gothic으로 표시된다. 꼭 필요하면 `<head>`에 한 줄이지만 위 테스트 2종을 고쳐야 한다.
- 인스펙터 열림 조건은 CSS `:has()`에 의존한다(Chrome 105+ / Edge 105+). 발표장 Chrome이면 문제없다. 구형 브라우저에서는 선택해도 카드가 열리지 않는다.
- 장면 설명(overview: "별 하나에, 한 사람이 있습니다", PJT 목록 등)은 평소에는 보이지 않고 검색창을 클릭해야 나온다. 장면 제목·설명은 이미 왼쪽 위에 있고, 설명은 발표자 멘트가 맡는다고 봤다.
- 카드가 열리면 지도 오른쪽 약 23%를 가린다. 클로즈업은 화면 중앙에서 일어나서 괜찮지만, PJT 성운에서 성운을 선택하면 오른쪽 성운 일부가 카드 아래로 들어간다.
- 1000px 미만(태블릿·모바일)은 조정하지 않았다. 기존 3단계 `@media`를 지웠기 때문이다. `nebula_browser.cjs`의 390px 검사는 `matrix.html`만 대상이라 통과한다.
- 헤더 버튼 위치(`right: edge + 206px`)는 합성 배지 폭에 맞춘 값이다. 배지 문구를 바꾸면 이 값도 바꿔야 한다. 배지가 숨겨진 실데이터 빌드는 `:has(#synthetic-mark[hidden])`로 오른쪽 끝에 붙는다.
- 브랜드 문구("근원경쟁력 AN ATLAS OF FUTURE WORK")를 숨겼다. 필요하면 `.brand{display:none}` 한 규칙만 지우면 된다(단, 위치는 다시 잡아야 한다).

## 검수 결과 (2026-09-13, 커밋 직전 워크트리)

| 검사 | 결과 |
|---|---|
| `pytest tests/test_nebula_{pipeline,http,network,fixture,deck}.py -q` | 40 passed, 7 subtests passed |
| `node tests/nebula_q3.cjs` | PASS: Q3 public engine, search, split, grid, PJT entry, reload, story mode |
| `node tests/nebula_presentation.cjs` | PASS: zero tasks, zero approvals, autoplay, first person, provenance, escaped unclassified PJT |
| `node tests/nebula_browser.cjs data/q3-visual/browser-check` | PASS: … mobile, … offline |
| `node tests/q3_story_check.cjs docs/q3-visual/story-claude/story.js <scratch>` (선택된 story, `#mode=story`) | PASS: 9 beats 34001ms, reduced motion 8567ms |
| story 육안 비교 | `1-6` 스크린샷이 `docs/q3-visual/story-claude/shots/1-6.png`와 같다. `#synthetic-mark` story·live 모두 표시 |
| 외부 요청 · 페이지 오류 (스크린샷 스크립트) | 0 · 0 |

### 320명 픽스처, 장면 1 → 2 전환 프레임

Playwright Chromium(headless, 소프트웨어 렌더링) 1920×1080. `browser.startTracing`(Chrome Performance 트레이스)으로 녹화하면서 `requestAnimationFrame` 간격을 쟀다. `go(2)`가 resolve되고 300ms 뒤까지다.

| | 프레임 수 | 50ms 넘는 프레임 | 최악 |
|---|---|---|---|
| before | 35 | **14** | 133ms |
| after | 54 | **11** | 133ms |

지도가 약 1.4배 넓어졌는데도 느린 프레임은 늘지 않았다. 인스펙터 열(336px DOM 패널)이 없어진 영향으로 보인다. 카드에는 `backdrop-filter`를 쓰지 않았다. 애니메이션되는 SVG 위에서 매 프레임 다시 그리게 되기 때문이다. 절대값은 headless 소프트웨어 렌더링 기준이라 GPU가 있는 발표 PC에서는 더 낮을 것이다. 전후 비교용으로만 본다.

## 스크린샷

`shots/before-*.png`(기존), `shots/after-*.png`(새 레이아웃). 합성 픽스처 `nebula/fixtures/q3/`(320명, 예시 인물 P000), 1920×1080 live 모드.

| 파일 이름 | 장면 |
|---|---|
| `*-0-people` | 장면 0 사람 |
| `*-1-closeup` | P000 클로즈업 + 과제 분열(인스펙터 카드가 열린 상태) |
| `*-2-split` | 장면 1 전원 분열 |
| `*-3-grid` | 장면 2 PJT 격자 |
| `*-4-pjt-nebula` | P000의 PJT 성운 |
