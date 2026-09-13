# engine-opus round2 — 「초월적 여백」 (Transcendent)

지시서: `docs/engine-layout-round2-brief.md`, 구도 배정은 실행 프롬프트(`run-engine-opus.sh`)에서 받았다. 바꾼 파일은 `nebula/templates/nebula.html` 하나다. live 레이아웃 CSS를 새로 썼고 JS는 2줄만 고쳤다. engine-opus에는 round1 폴더가 없어서 비교 기준은 이 브랜치의 기존 템플릿과 round1 세 후보가 수렴한 "풀블리드 지도 + 오버레이 HUD"다.

## 구도 원리

1. **화면의 약 60%는 비워 둔다.** 위쪽 띠와 왼쪽 기둥이 이어진 L자 어둠에는 지도도, 버튼도, 별 배경도 없다.
2. **여백에는 장면 문장 하나만 둔다.** 1920 기준 약 119px 글자를 쉼표에서 두 줄로 끊어 왼쪽 위에 놓는다. 눈은 그 문장에서 출발해 대각선 아래의 빛나는 블록으로 내려간다.
3. **나머지는 오른쪽 아래 블록 하나에 촘촘히 모은다.** 지도, 장면 라벨, 숫자, 검색, 설명 패널, 단계, 조작이 한 블록에 들어가고, 화면의 빛은 이 블록에서만 난다. 클릭 대상 사이에는 여백을 끼우지 않는다.

## 왜 이 구도인가

10m 스크린 앞 300명의 시선은 저절로 한 점에 모이지 않는다. 지도가 화면 전체를 채우면 사람마다 다른 구석을 본다. 화면 대부분을 어둡게 비우면 볼 곳이 하나만 남는다. 문장 하나와 빛나는 블록 하나다. 문장은 크고 혼자라서 먼저 읽히고, 블록은 유일한 광원이라 그다음에 보인다. 발표자가 별을 누르는 곳도 그 블록 안이다. 청중의 시선과 조작 지점이 같은 자리에 모인다.

70% 비움에서 60%로 줄인 이유는 조작 때문이다. 지도가 너무 작아지면 320명 규모에서 사람 별을 정확히 누르기 어렵다. 그래서 비율보다 블록 안 밀도를 우선했다. 블록 가장자리에 여유를 두지 않고 지도와 레일을 맞붙였다.

## round1과 근본적으로 다른 점

1. **빈 곳이 주인공이다.** round1은 화면 전체를 지도로 채우고 남은 곳에 UI를 띄웠다. round2는 먼저 비울 곳을 정하고 남은 40%에 지도와 UI를 함께 넣는다. 지도는 배경이 아니라 어둠 속에 놓인 물체다.
2. **글자와 별이 한 픽셀도 겹치지 않는다.** round1의 HUD는 지도 위에 얹혔다. round2에서 장면 문장은 지도가 없는 영역에만 있고, 나머지 글자는 지도 옆 레일에만 있다. 오버레이는 툴팁과 PJT 격자 칸처럼 원래 지도에 붙어야 하는 것만 남겼다.
3. **시선의 경로가 정해져 있다.** round1은 시선이 중앙에서 가장자리로 흩어졌다. round2는 왼쪽 위 문장에서 오른쪽 아래 블록으로 향하는 대각선 한 방향이다. 다섯 장면 모두 문장 자리와 블록 자리가 같고 문장 내용만 바뀐다.

## 5컷

`shots/after-*.png`는 합성 픽스처 `nebula/fixtures/q3/`(320명, 예시 인물 P000)를 live 모드 1920×1080으로 찍은 것이다. 각 동작 뒤 2.2초 기다려 전환이 끝난 뒤 찍었다.

| 파일 | 장면 | 이 컷에서 보이는 원리 |
|---|---|---|
| `after-0-people` | 장면 0 사람 | L자 여백 + 문장 하나 + 오른쪽 아래 블록 |
| `after-1-closeup` | P000 클로즈업(분열 후) | 확대와 인물 과제 목록이 둘 다 블록 안에서 끝남 |
| `after-2-split` | 장면 1 분열 | 같은 자리, 문장만 교체 |
| `after-3-grid` | 장면 2 PJT 격자 | 격자 칸(클릭 대상)이 블록 안에 촘촘히 |
| `after-4-pjt-nebula` | P000의 PJT 성운 | PJT 진입 후에도 구도 유지 |

블록(UI 요소 전체의 외접 사각형, `#synthetic-mark` 포함)이 화면에서 차지하는 비율은 1920×1080에서 **37.6%(여백 62.4%)**, 1600×1000에서 41.9%다. 다섯 컷 모두 같다. 페이지 오류 0, 외부 요청 0.

## 무엇을 바꿨나

| 요소 | 기존 템플릿 | round2 |
|---|---|---|
| 뼈대 | 헤더 / hero / 지도+인스펙터 / 푸터 4단 격자 | `.app` 4열×8행 격자. 1행·1열은 여백, `--h:62dvh` 높이 블록은 오른쪽 아래, 바깥 여백은 `--m` |
| 블록 배경 | 없음 | `.app::before`가 블록 칸에 깔려 유일한 광원 역할(테두리 + 보라 그림자) |
| 장면 문장 `h1` | hero 안 54px | 여백 칸 전체(`grid-area:1/1/2/4`) 아래쪽 정렬, `clamp(52px,6.2vw,132px)`, weight 400 |
| eyebrow · 보조 문장 · 숫자 | hero 안 | `.hero{display:contents}`로 풀어 레일 위 세 칸에 배치 |
| 지도 | 가운데 넓게 | 지도 열 너비 = `(--h − 136px) × 5/3`(viewBox 비율). 위 40px 툴바, 아래 44px 범례·각주 줄과 겹치지 않도록 `#sky` 높이를 줄임 |
| 인스펙터 | 오른쪽 390px | 레일 320px 아래 칸, 검색 + 스크롤 패널 |
| 단계 · 조작 | 맨 아래 전폭 | `footer{display:contents}`로 풀어 지도 열 아래 · 레일 아래 |
| 배지 | 헤더 | `#synthetic-mark`가 보이면 `:has()`로 숨김(같은 말을 두 번 하지 않도록). 실데이터 배지는 그대로 표시 |
| `#synthetic-mark` | story 모드에서만 | live에서도 표시(성역 규칙). 블록 오른쪽 위 모서리 바로 위에 캡션처럼 붙임 |
| 작은 화면 | 1000/700px 미디어쿼리 | 가로 1180px 이하 또는 세로 760px 이하에서는 여백을 포기하고 DOM 순서대로 쌓아 스크롤 |

story 모드 규칙(`body.story …`)은 한 글자도 바꾸지 않았다. `.app`·`.workspace`·`.universe`·`#sky`·`#pjt-back`·`#synthetic-mark`처럼 story 모드와 함께 쓰는 요소의 새 규칙은 모두 `body:not(.story)`로 한정했다.

**JS 2줄**
- `#title`: 장면 문장을 `", "` 뒤에서 `<span>`으로 나눠 쉼표 자리에서 줄을 바꾼다. 조각을 `' '`로 다시 이어 붙이므로 `textContent`는 이전과 같다(`q3_story_check`의 live 단언). CSS만으로는 쉼표에서 끊을 수 없다. `text-wrap:balance`는 "사람의 기록이, 여러 / 미래로 펼쳐집니다."처럼 끊는다.
- `#synthetic-mark`: `hidden=!(story && synthetic)` → `hidden=!synthetic`.

`window.nebula`, `nebulaCopy`, 페이로드, 테스트 셀렉터는 그대로다.

## 알려진 한계

- **지도가 작아졌다.** 1920×1080에서 지도는 약 889×534px로, 기존 템플릿(약 1246×748)의 선 길이 기준 71%다. 과제 별의 클릭 반경은 10 → 약 7.4px, 장면 3 역량 원 안의 SVG 글자는 약 10px로 줄었다. 레일 목록과 검색으로 같은 대상을 고를 수 있지만, 사람 별을 직접 겨누는 조작은 기존보다 어렵다.
- **여백 칸에는 두 줄까지만 들어간다.** 1920 기준 여백 높이는 346px이고 119px 두 줄은 약 250px다. `deck.md`의 장면 문장에 쉼표가 두 개 이상 생기면 세 줄이 되어 블록 윗변에 닿는다. 지금 scene-0~3 문장은 쉼표가 모두 하나다.
- **블록이 화면 아래쪽에 있다.** 경사가 없는 강당에서는 앞사람 머리에 블록 아랫부분(단계·조작 줄)이 가릴 수 있다. 가려지는 줄은 발표자용이라 청중이 볼 필요는 없다고 판단했다. 지도 아래 끝은 y≈920이다.
- **설명 패널이 짧다.** 1080 기준 레일 패널 높이는 약 350px이라 인물 과제 목록과 근거 카드는 스크롤된다.
- **문장 전환에 연출이 없다.** `textContent`만 바뀐다. 암전이나 페이드는 story.js의 몫으로 남겼다.
- `:has()`(Chrome/Edge 105+)에 의존한다. 지원하지 않는 브라우저에서는 배지와 합성 표시가 둘 다 보이는 정도로만 달라진다.
- 1920×1080과 1600×1000 두 크기에서 겹침이 없는 것만 확인했다. 1181~1366px 폭 노트북에서는 블록이 좁아져 패널이 더 짧아진다.
- 폰트 스택은 기존 그대로다(로컬 임베딩 금지).

## 검수 결과 (2026-09-14, 커밋 직전 워크트리)

| 검사 | 결과 |
|---|---|
| `pytest tests/test_nebula_{pipeline,http,fixture,deck}.py -q` | 38 passed, 7 subtests passed |
| `node tests/nebula_q3.cjs` | PASS: Q3 public engine, search, split, grid, PJT entry, reload, story mode |
| `node tests/nebula_presentation.cjs` | PASS: zero tasks, zero approvals, autoplay, first person, provenance, escaped unclassified PJT |
| `node tests/nebula_browser.cjs /tmp/opus-demo-after` (합성 demo) | PASS: nebula scenes, matrix, network, tasks, evidence, mobile, review/category correction, extraction correction, stale review, offline |
| `node tests/q3_story_check.cjs tests/q3_story_stub.js /tmp/opus-shots` | PASS: 9 beats 15764ms, reduced motion 1374ms |
| `node tests/q3_story_check.cjs docs/q3-visual/story-claude/story.js …` (선택된 story) | PASS: 9 beats 34013ms, reduced motion 7753ms |
| story 회귀 | 수정 전 템플릿(`fc89db0`)으로 같은 두 story 검수를 먼저 돌려 둔 9비트 스크린샷과 비교했다. stub 9장, story-claude 9장 **모두 바이트 단위로 같다.** |
| 스크린샷 스크립트(1920×1080, 1600×1000) | 페이지 오류 0, 외부 요청 0, 가로·세로 스크롤 없음 |
| 실명 노출 | 없음(합성 픽스처만 사용) |

수정 전 템플릿에서도 같은 검사가 모두 통과했다(pytest 38 passed). 이번 변경으로 깨진 것은 없다.
