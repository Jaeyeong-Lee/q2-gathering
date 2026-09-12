# 3Q 발표 — 시각 작업 지시서 (오케스트레이터용)

> 작성 2026-09-13. 발표 2026-09-15.
> **이 파일 하나로 시각 작업을 배분하고 검수한다.** 엔진 함수 계약·텍스트 파일 형식·폴더 규칙·검수 기준의 정본은 이 문서다.
> 발표 전체의 배경과 결정은 `docs/q3-presentation-plan.md` §1–§3에 있다.

## 0. 오케스트레이터 순서

1. **L0는 완료돼 통합 브랜치에 있다**(§4). 3번부터 시작한다.
2. (선택) Jay가 인스트럭션을 더 다듬고 싶을 때 `nebula/templates/deck.md` 문구를 고친다. 시각 작업은 이를 기다리지 않고 초안 문구로 진행한다(§3.4).
3. **V-story N명 + V-engine 1명을 동시에 배정**한다. 각 에이전트에게 이 문서와 자기 `agent-id`, 브랜치, 워크트리 경로를 준다(§5).
4. 에이전트가 끝났다고 보고하면 §6 검수 명령을 직접 돌려 확인하고, 그 브랜치를 통합 브랜치에 머지한다. 폴더가 겹치지 않아 충돌이 없다.
5. Jay와 §7 기준으로 story 후보 하나를 고른다 → **통합**(§4) → 전체 테스트 → 머지.
6. `docs/q3-visual/README.md` 후보 표와 `docs/q3-presentation-plan.md` §6 상태 표를 갱신한다.

| 날짜 | 목표 |
|---|---|
| 09-13 | L0 완료·머지, V-story·V-engine 착수 |
| 09-14 | 후보 제출(오후), 선택·통합(저녁) |
| 09-15 | 오전 리허설, 발표 |

## 1. 무엇을 만드나

- 발표는 **1부 개념 덱**(ELI5, 합성 데이터)과 **2부 실데이터 라이브 데모**로 나뉜다. 둘은 같은 엔진 `nebula/templates/nebula.html`을 쓴다.
- **파일이 다르다.** 1부 = 합성 픽스처로 빌드한 `nebula.html`을 `#mode=story`로 연 것. 2부 = 내부망 실데이터로 빌드한 `nebula.html`. 시각 작업은 전부 1부(합성)에서 한다.
- 엔진은 장면·검색·클로즈업·PJT 격자·상태 복원을 이미 갖고 있고 테스트가 붙어 있다(Codex 뼈대). 1부 연출은 **`story.js`가 엔진 함수를 호출**해서 만든다.
- **화면 문장과 발표자 멘트는 `nebula/templates/deck.md` 한 파일에 둔다.** 빌드가 이 파일을 읽어 HTML에 넣는다. Jay가 문구를 고치고 다시 빌드하면 그대로 반영된다. 코드에는 문구를 쓰지 않는다.
- **재량 — 모델의 창의성을 환영한다.** §2 표와 deck-soul은 출발점이다.
  - 비트 안의 연출·은유·색·질감·타이밍·카메라·아이콘 모양은 각 모델이 해석해도 된다.
  - 저장소의 과거 산출물(§9)을 가져다 쓰거나 해체해 재조합해도 된다.
  - 고정되는 것은 네 가지뿐이다: 비트 ID 9개와 순서(검수·비교를 위해), §3 계약, §8 태도·정직성·데이터 규칙, §6 검수 PASS.
  - 비트를 합치거나 나누는 편이 낫다고 보면, 구현은 9개 ID에 맞추고 폴더 `README.md`에 제안과 이유를 적는다.

## 2. 1부 비트 명세

비트는 9개다. ID는 `deck.md`의 절 제목, `window.nebulaStory.beats`, 스크린샷 파일 이름에 똑같이 쓴다.

| ID | 이름 | 화면에서 일어나는 것 | 엔진 호출 | 끝 상태 |
|---|---|---|---|---|
| `1-0` | 도입 | 검은 화면. 판독할 수 없는 PPT 실루엣 몇 장이 느리게 겹쳐 떠 있다. 큰 움직임 없이 조용히 시작 | 없음 | 문장 + 멈춘 실루엣 |
| `1-1` | wow1 임베딩 | PPT 한 장이 중앙으로 → 텍스트 줄(판독 불가 막대)로 풀림 → 얇은 선의 임베딩 아이콘을 통과 → 빛나는 별 하나 | 없음 | 중앙 별 하나 |
| `1-2` | wow2 유사도 | 별이 전원 수만큼 늘어나며 연결선이 생김 → 카메라가 뒤로 빠짐 → 별이 엔진 좌표로 이동 → 스토리 레이어가 걷히며 엔진 장면 0이 드러남 | `await go(0)` 후 `peoplePositions()` | 엔진 장면 0, 별 위치가 튀지 않음 |
| `1-3` | wow3 추출 | 예시 인물에게 클로즈업 → LLM 아이콘이 그 별을 통과(점화) → 미래 과제 별로 분열 | `await focusPerson(i, {split:false})` → 아이콘 연출 → `await splitPerson()` | 예시 인물의 과제 별 |
| `1-4` | wow4 전원 분열 | 줌 아웃 → 전원의 과제가 한 번 갈라짐 | `await clearPerson()` → `await go(1)` | 전원 과제 별 |
| `1-5` | PJT 격자 | 과제 별이 PJT 칸(4열 격자)으로 해쳐모임 | `await go(2)` | 격자, 예시 인물의 PJT 칸 강조 |
| `1-6` | wow5 성운 | 예시 인물의 PJT 칸으로 들어가 닮은 과제끼리 성운 | `await enterPjt(p)` | 그 PJT 과제군 성운 |
| `1-7` | 역량 | 예시 과제 하나가 강조되고, 확보/필요 역량 카드(라벨 + 원문 인용 한 줄)가 뜬다 | `selectTask(id)` + 카드는 story 오버레이 | 카드 |
| `1-8` | 맺음 | 화면이 어두워지고 중앙 문장 | 없음 | 문장 |

- **예시 인물·PJT·과제**: 페이로드(§3.1) `people`에서 `pid === 'P000'`인 사람, 그 사람의 `pjt`, 그 사람의 첫 과제(`tasks`에서 `person`이 같은 첫 항목). 픽스처 `nebula/fixtures/q3/showcase.json`과 같다.
- `1-7`: story 모드에서는 엔진의 우측 패널이 숨겨지므로 역량 카드는 story가 페이로드 `tasks[].skills`(`kind`=`have`|`gap`, `label`, `quote`)로 직접 그린다. 결정 4(역량 생략)가 나면 이 비트는 문장만 남기거나 빠진다.
- **진행 조작**
  - Space / → : 모션 중이면 그 비트의 끝 상태로 바로 가고, 끝났으면 다음 비트를 재생한다.
  - ← : 이전 비트의 끝 상태로 간다. 역재생은 만들지 않는다.
  - R : 현재 비트를 처음부터 다시 재생한다.
  - N : 발표자 멘트(`note`)를 작은 오버레이로 켜고 끈다.
  - 자동 진행은 없다. 비트 모션은 1.5–4초, wow는 짧은 정적(0.3–0.8초) 뒤 전환한다.
  - ESC는 쓰지 않는다. 엔진이 ESC로 개인·PJT 선택을 해제한다.

## 3. 계약

### 3.1 엔진 함수 `window.nebula`

```js
window.nebula = {
  go(sceneIndex),                 // 0 사람 · 1 전원 분열 · 2 PJT 격자/성운 · 3 과제·역량. 전환이 끝나면 resolve
  focusPerson(personIndex, opts), // 줌 → 과제 분열. opts.split === false면 줌만 하고 멈춤(L0 추가). 끝나면 resolve
  splitPerson(),                  // 줌 상태인 사람의 과제를 분열(L0 추가). 끝나면 resolve
  clearPerson(),                  // 줌 아웃. 끝나면 resolve
  enterPjt(pjtIndex),             // 격자 → 그 PJT 성운. 끝나면 resolve
  leavePjt(),                     // 성운 → 격자. 끝나면 resolve
  selectTask(taskId),             // 과제 선택(장면 3으로 이동). 동기
  peoplePositions(),              // 장면 0 사람 중심의 [{id, x, y}] — 브라우저 뷰포트 px
};
```

- 페이로드는 `JSON.parse(document.getElementById('data').textContent)`로 읽는다. 엔진 변수(`D` 등)는 블록 안에 있어 전역이 아니다. story는 읽기만 한다.
- 인자: 사람 = 페이로드 `people[].id`(색인), PJT = `pjts` 색인, 과제 = `tasks[].id`.
- 최소 동작 예시는 `tests/q3_story_stub.js`(연출 없이 비트별 호출 순서만 있다).
- 새 명령이 오면 이전 명령의 남은 단계는 취소되고 이전 Promise는 정상 종료한다. story도 비트가 바뀐 뒤 옛 비트의 후속 호출을 실행하지 않도록 관리한다.
- story 모드에서 엔진은 ←/→ 키를 처리하지 않는다. 진행은 story가 맡는다.
- 페이로드의 좌표·과제 수·분류는 연출용으로 바꾸지 않는다.

### 3.2 문구 `window.nebulaCopy` (L0 추가)

```js
window.nebulaCopy = {
  "1-0": { screen: ["첫 줄", "둘째 줄"], sub: "보조 라벨 또는 null", note: "발표자 멘트 또는 null" },
  // … "1-8", "scene-0" … "scene-3"
};
```

- `{people}` `{tasks}` `{pjts}` 자리는 이미 페이로드 값으로 채워져 있다.
- 화면에 넣을 때는 `textContent`로만 넣는다. `screen`의 원소 하나가 한 줄이다.

### 3.3 story가 내놓는 것 `window.nebulaStory`

```js
window.nebulaStory = {
  beats: ["1-0", "1-1", "1-2", "1-3", "1-4", "1-5", "1-6", "1-7", "1-8"],
  goto(beatId),   // 그 비트를 처음부터 재생하고 끝 상태에서 resolve하는 Promise
  current(),      // 현재 비트 ID
};
```

- `location.hash`에 `mode=story`가 있을 때만 그리고, 이 객체도 그때만 만든다. live 모드에서는 아무것도 하지 않는다.
- `story.js` 전체를 즉시 실행 함수로 감싸, 전역에 추가하는 이름은 `nebulaStory` 하나로 둔다.
- `story.js`에 `</script>` 문자열이 있으면 빌드가 거부한다(HTML에 인라인되기 때문).
- 검수 스크립트(§6)가 `goto`로 비트마다 스크린샷을 찍는다.

### 3.4 텍스트 파일 `nebula/templates/deck.md`

```md
# 3Q 발표 문구

## 1-0 도입
화면: 치열하게 고민해 쓴 기록들이
화면: 조금 더 오래 남도록.
멘트: 엔지니어들이 각자 치열하게 고민해 PPT를 썼습니다. …

## 1-3 wow3 추출
화면: 한 사람에게도, 여러 미래가.
보조: LLM 추출 · 별 하나 = 미래 과제 하나
멘트: 그런데 한 사람이 앞으로 하고 싶은 일은 하나일까요?

## scene-0 사람
화면: {people}명이 적어둔, 아직 오지 않은 일들.
보조: 지난번에는 서로 닮은 사람을 찾았습니다. 이번에는 그 사람들이 바라보는 다음을 봅니다.
```

- 절 제목은 `## <ID> <이름>`. ID는 `1-0`…`1-8`(1부 비트), `scene-0`…`scene-3`(2부 엔진 장면 제목·설명) 13개로 고정.
- 키는 `화면`(큰 문장, 반복하면 줄바꿈), `보조`(작은 라벨 한 줄), `멘트`(발표자 노트, 화면에 안 나옴). `scene-*`에서 `화면`은 장면 제목, `보조`는 제목 아래 설명이다.
- ID가 빠지거나, 모르는 ID·키·자리표시가 있으면 **빌드가 오류로 멈춘다**. 빈 슬라이드가 조용히 나가지 않게 하기 위해서다.
- 반영: 1부는 §6의 픽스처 빌드를, 2부는 내부망에서 `python3 -m nebula build --out <실행 out>`을 다시 돌린다. 둘 다 LLM을 호출하지 않는다.
- **문구 수정은 선택이다.** 지금 파일은 초안이며 시각 작업은 이 초안으로 바로 진행한다. Jay가 인스트럭션을 다듬고 싶을 때만 고친다. 시각 담당은 문구를 고치지 않고 `deck-suggestions.md`에 제안한다.

## 4. 역할과 완료 기준

| 역할 | 인원 | 선행 | 고칠 수 있는 곳 | 산출물 |
|---|---|---|---|---|
| L0 로직 준비 | 1 (Codex 또는 Claude) | 없음 | `nebula/render.py`, `nebula/templates/nebula.html`(계약 추가분만), `nebula/templates/deck.md`, `tests/`, `docs/q3-visual/README.md` | 통합 브랜치 커밋 |
| V-story | N (병렬) | L0 머지 | `docs/q3-visual/<agent-id>/` 안만 | 1부 전체 `story.js` 후보 |
| V-engine | 1 | L0 머지 | `nebula/templates/nebula.html`의 CSS·모션, `docs/q3-visual/engine/` | 엔진 모션·톤 개선 |
| 통합 | 오케스트레이터 | 후보 선택 | `nebula/templates/story.js`, 문서 상태 표 | 통합 브랜치 커밋 |

### L0 로직 준비 — 완료 (2026-09-13, Claude)

1. `nebula/templates/deck.md` 초안 — 13개 ID 전부. 문구 출처:
   - Jay의 문장: 도입 "엔지니어들이 치열하게 고민해 쓴 PPT를, 더 잘 보이게 생명력을 불어넣어 그 노력이 heritage로 남도록", 맺음 "우리의 미래 경쟁력이 팀의 로드맵입니다"
   - `docs/design-candidates-2026-09-11/pitch-cosmos-v2/presentation.js`의 `scenes[]` `title`·`say`
   - 엔진 `nebula.html`의 장면 제목·설명 배열(`scene-*`로 옮김, 시간 장면 문구는 버림)
   - `docs/q3-presentation-plan.md` §2
2. `render.py`: `deck.md`를 파싱해 `nebula.html`에 인라인한다(§3.4 규칙과 오류). `NEBULA_STORY` 환경변수가 있으면 그 파일을, 없으면 `nebula/templates/story.js`를 `__STORY__`에 넣는다.
3. `nebula.html`: `window.nebulaCopy` 노출(자리표시 채움), 2부 장면 제목·설명을 `scene-*`에서 읽기, `focusPerson(i, {split:false})`와 `splitPerson()` 추가.
4. `tests/q3_story_check.cjs <story.js 경로> <스크린샷 폴더>`:
   - `NEBULA_STORY`로 픽스처를 `data/q3-visual/check/`에 빌드한다.
   - 1920×1080에서 `#mode=story`로 열고 `nebulaStory.beats`가 §2의 9개와 같은지 본다.
   - 비트마다 `await goto(id)` 후 `<폴더>/<id>.png`를 저장한다.
   - 확인할 것: 페이지 오류 0, `file://` 외 요청 0, `#synthetic-mark` 표시, `1-2` 뒤 엔진 장면 0, `1-6` 뒤 PJT 진입, 각 비트의 `screen` 첫 줄이 화면에 보임.
   - `prefers-reduced-motion`으로 한 번 더 돌려 9비트 전부 끝나는지 본다.
5. `docs/q3-visual/README.md`: 후보 표 틀(agent-id·브랜치·커밋·검수 결과·선택 여부).

**완료**:
- 엔진 장면 제목이 `nebulaCopy`와 같다(`q3_story_check.cjs`의 live 검사). 모르는 ID·키·자리표시, 중복·누락 비트는 빌드 오류(`tests/test_nebula_deck.py`).
- 스텁 `tests/q3_story_stub.js`로 `q3_story_check.cjs` PASS.
- 기존 검사 전부 통과: pytest 4파일, `nebula_q3.cjs`, `nebula_presentation.cjs`, `nebula_browser.cjs`.
- 통합 브랜치에 push.

### V-story (에이전트마다)

- 자기 폴더에 1부 9비트 전체를 구현한 `story.js` 후보를 만든다(§2, §3). 문구는 `nebulaCopy`에서만 읽는다.
- 문구를 바꾸고 싶으면 `deck-suggestions.md`에 제안을 적는다. `deck.md`는 고치지 않는다.
- 폴더 `README.md`에 콘셉트 3줄, 비트별 연출 한 줄씩, 알려진 한계, 검수 결과를 적는다.
- **완료**: §6 story 검수 PASS, `shots/`에 9장, 자기 폴더 밖 변경 0, 자기 브랜치에 커밋·push 후 브랜치·커밋을 오케스트레이터에게 보고.

### V-engine

- 엔진의 모션과 톤만 다듬는다.
  - 클로즈업에서 과제 별이 겹치지 않게
  - 분열·격자·PJT 진입 궤적
  - 성운 안개
  - 2Q 화면을 떠올리게 하는 배경 별밭
  - 2부 live 모드의 대강당 글자 크기
- 유지할 것: `window.nebula` 시그니처, 테스트가 잡는 셀렉터, 페이로드 구조, `nebulaCopy`.
- 폴더 `docs/q3-visual/engine/`에 `README.md`와 `shots/before-*.png`·`shots/after-*.png`(장면 0, 클로즈업, 분열, 격자, PJT 성운)를 둔다.
- **완료**:
  - 기존 검사 전부 통과.
  - 320명 픽스처에서 장면 1·2 전환을 Chrome Performance로 한 번씩 녹화해 50ms 넘는 프레임 수를 README에 기록.
  - 자기 브랜치에 커밋·push 후 보고.

### 통합 (선택 후 오케스트레이터)

1. `docs/q3-visual/<선택 id>/story.js`를 `nebula/templates/story.js`로 복사한다. 후보 폴더는 그대로 둔다.
2. V-engine 브랜치를 먼저 머지했다면 선택 story로 §6 story 검수를 다시 돌린다.
3. 기존 검사 전부 + `q3_story_check.cjs nebula/templates/story.js <스크래치>` PASS → 커밋·push.
4. `docs/q3-visual/README.md`에 선택 결과, plan §6에 T4·T8 상태를 적는다.

## 5. 폴더·브랜치·경로

```
docs/q3-visual/
  README.md                  # 후보 표 (L0이 틀 생성, 오케스트레이터가 채움)
  <agent-id>/                # 에이전트 한 명 = 폴더 하나
    README.md
    story.js                 # V-story만
    deck-suggestions.md      # 선택
    shots/1-0.png … 1-8.png  # V-story. V-engine은 before-*/after-*
data/q3-visual/<agent-id>/   # 빌드 결과. data/는 gitignore라 커밋되지 않는다
```

- `agent-id`: 소문자·숫자·하이픈. 예: `story-claude`, `story-codex`, `story-gemini`, `engine`.
- 브랜치: `Jaeyeong-Lee/q3-visual-<agent-id>`. **L0이 머지된** `Jaeyeong-Lee/q3-nebula-presentation`에서 딴다.
- 워크트리: `~/orca/workspaces/q2-gathering/q3-visual-<agent-id>`.
- 커밋은 자기 폴더 안에서만 한다(V-engine은 `nebula/templates/nebula.html` 포함). 머지는 오케스트레이터가 한다.
- `shots/`의 PNG는 합성 화면이라 커밋한다.

## 6. 설치·빌드·검수 명령

워크트리 루트에서 실행한다.

```sh
# 새 워크트리 준비 (한 번)
python3 -m venv .venv && ./.venv/bin/pip install -r requirements-nebula-dev.txt
npm install --prefix nebula/browser-tests && npx --prefix nebula/browser-tests playwright install chromium

# 1부 미리보기 빌드
NEBULA_STORY=docs/q3-visual/<agent-id>/story.js ./.venv/bin/python -m nebula demo \
  --input nebula/fixtures/q3/persons.json --network nebula/fixtures/q3/neighbors.json \
  --out data/q3-visual/<agent-id>
# 브라우저: file://<워크트리 절대경로>/data/q3-visual/<agent-id>/nebula.html#mode=story

# story 검수 (V-story 완료 기준)
NEBULA_PYTHON=$PWD/.venv/bin/python node tests/q3_story_check.cjs \
  docs/q3-visual/<agent-id>/story.js docs/q3-visual/<agent-id>/shots

# 기존 검사 (L0·V-engine·통합 완료 기준)
./.venv/bin/python -m pytest tests/test_nebula_pipeline.py tests/test_nebula_http.py \
  tests/test_nebula_network.py tests/test_nebula_fixture.py tests/test_nebula_deck.py -q
NEBULA_PYTHON=$PWD/.venv/bin/python node tests/nebula_q3.cjs
NEBULA_PYTHON=$PWD/.venv/bin/python node tests/nebula_presentation.cjs
./.venv/bin/python -m nebula demo --out data/q3-visual/browser-check && \
  NEBULA_PYTHON=$PWD/.venv/bin/python node tests/nebula_browser.cjs data/q3-visual/browser-check
```

## 7. 후보 선택 기준 (Jay + 오케스트레이터, 각 1–5점)

| 기준 | 보는 곳 |
|---|---|
| 첫 10초 | `1-0`·`1-1`이 조용하지만 시선을 붙잡는가 |
| 인과 | wow1–5에서 무엇이 무엇으로 바뀌는지 설명 없이 읽히는가 (문서→별, 사람→과제, 과제→성운) |
| 이음매 | `1-2`→엔진 장면 0, `1-3` 점화→분열의 타이밍 |
| 대강당 가독성 | 스크린샷을 50%로 줄여도 문장과 별이 읽히는가 |
| 절제·정직성 | §8 태도·정직성 위반이 없는가 |
| 안정성 | 검수 PASS, reduced-motion, 끊김 없음 |

## 8. 공통 규칙

**태도** — `docs/design-candidates-2026-09-11/deck-soul.md`
- 검은 배경, 중앙 문장 하나. 조용한 시작과 세 번의 큰 전환(문서→별, 사람→과제, 과제→성운)의 대비.
- 화면은 별·선·빛으로만 말한다. 우주 사진·과한 가스·SF 장식 없이, 사람의 기록이라는 출발점이 보이게.
- 설명은 발표자 멘트로 보내고 화면 글자는 최소로. 화면 문장 64px 이상, 보조 28px 이상(1920×1080 기준).
- 인과는 실제 이동·분열·응집으로 보여준다. 밝기 토글이나 설명 글로 대신하지 않는다.

**정직성**
- 위치·거리·크기·밝기는 중요도·준비도·우열이 아니다.
- 실제 인물의 감정·작성 과정을 재현하지 않는다. PPT는 판독할 수 없는 추상 표현.
- 합성 표시(`#synthetic-mark`)는 늘 보이게 둔다.

**데이터**
- 합성 픽스처만 쓴다. 실데이터·실제 분류명·실제 PJT 이름을 쓰지 않고, 실데이터 빌드 출력을 열지 않는다.

**기술**
- 외부 요청 0: CDN·웹폰트·원격 이미지 없이, 이미지는 SVG·Canvas 코드로 그린다. 발표장은 `file://` 오프라인이다.
- 1920×1080 기준. 창 비율이 다르면 레터박스.
- `prefers-reduced-motion`에서는 이동 대신 페이드.
- 콘솔 오류 0. 문구는 `nebulaCopy`에서 `textContent`로.
- `1-0`–`1-2`의 별 수백 개는 Canvas 한 장으로 그리는 편이 엔진 SVG에 부담을 주지 않는다.

## 9. 참고 — 과거 산출물 포함

필요하면 저장소 안의 과거 산출물을 열어 보고 모션·색·레이아웃·문장 톤을 가져다 쓴다. 그대로 옮겨도, 해체해 재조합해도 된다.

- 열지 않는 곳: `data/`(자기 빌드 결과 `data/q3-visual/` 제외), `dist/`, 루트 `CLAUDE.md`의 실데이터 경로 표.
- 과거 산출물에서 실명이나 실제 회고로 보이는 내용이 나오면 더 읽지 말고 오케스트레이터에게 알린다.

| 무엇 | 경로 | 가져갈 만한 것 |
|---|---|---|
| 발표 계획(배경·결정·티켓) | `docs/q3-presentation-plan.md` | 발표 흐름과 결정의 이유 |
| 발표 태도 | `docs/design-candidates-2026-09-11/deck-soul.md` | 화면의 태도, 정직성, 바꿔도 되는 것과 이유가 필요한 것 |
| Cosmos v2 모션 시안 | `docs/design-candidates-2026-09-11/pitch-cosmos-v2/` | 문서 압축·점화·분열·응집 모션, 발표자 노트·조작 UI |
| Cosmos v1 | `docs/design-candidates-2026-09-11/candidate-pitch-cosmos.html` | 밝은 기록 화면 → 암전·점화 |
| 성운 후보 4종 | `docs/design-candidates-2026-09-11/candidate-*.html` | 5모델 리뷰에서 A로 평가된 분열→성운 전환(`candidate-50`) |
| 5모델 디자인 리뷰 | `docs/design-candidates-2026-09-11/llm-reviews-2026-09-12.md` | 공통 지적: 첫 장면 임팩트, 작은 글자, 15분 리듬 |
| 이미지 방향 탐색 | `docs/design-candidates-2026-09-11/image-directions-v1.jkBVOa/` | 종이 중심 vs 빛 중심 분위기 보드 |
| 오프닝·클로즈업 컨셉 | `docs/nebula-opening-scene-concept.md` | 쌓임→유사도→추출→택소노미 아이콘 전환, 클로즈업 기법 메모 |
| 성운 발표 원본 프로토타입 | `docs/nebula-prototype/future-nebula.html` | 지금 엔진의 출발점, 성운 안개 표현 |
| 2Q 화면 소스 | `archive/template.html` | 캔버스 별밭·글로우 스프라이트·에고 뷰·힘 배치 |
| 2Q 유사도 네트워크 프로토타입 | `docs/similarity-network-prototype.html` | 사람 네트워크 초기 연출 |
| 은하수 라이트 톤 프로토타입 | `docs/heritage-archive-light-prototype-2026-09-03.html` | 밝은 톤 대안 |
| 사람·미래 과제 합성 데모 | `templates/td_people_atlas.html` | 검색·렌즈·발표 모드 |
| 미래 지도 덱 프로토타입 | `docs/task-discovery-future-map.html` | 1280×720 덱 구성, 궤도·중력 연출 |
| 파이프라인 설명 자료 | `docs/pipeline-3stages.html`, `docs/task-discovery-eli30-2026-08-25.html` | 기술을 쉽게 설명하는 방식(1-1·1-3 멘트 참고) |
| 산출물 후보 제안서 | `docs/deliverable-candidates-2026-08-28.html`, `docs/deliverable-candidates-fable-2026-08-30.html` | 화면 아이디어 목록 |
| 로드맵 매트릭스 목업 | `docs/roadmap-matrix-mockup.html`, `docs/task-discovery-roadmap-mockup-2026-08-12.html` | 역량 표현 대안(1-7) |
| 8/14 임원 보고 덱 | `git show Jaeyeong-Lee/exec-deck-narrative-flow:docs/2026-08-14-exec/deck.html` (원고 `script.md`) | 요구와 자료의 간극을 설명한 문장 |
| 엔진 | `nebula/templates/nebula.html` | 호출할 함수, 장면 톤 |
| 엔진·story 검수 | `tests/nebula_q3.cjs`, `tests/q3_story_check.cjs`, `tests/q3_story_stub.js` | 계약의 실제 동작 |
| 빌드·인라인 | `nebula/render.py` | `deck.md` 파싱, `NEBULA_STORY` |
| 합성 픽스처 | `nebula/fixtures/q3/` (README 포함) | 320명·예시 인물 P000 |
| nebula 에이전트 규칙 | `nebula/CLAUDE.md` | 깨면 안 되는 계약 |
