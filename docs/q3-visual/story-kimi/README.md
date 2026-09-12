# story-kimi — 1부 story 후보

## 콘셉트 (3줄)

- 기록 한 장이 텍스트 줄로 풀리고, 임베딩 다이아몬드를 지나 빛나는 별 하나가 된다 — 문서→별의 인과를 실제 변형으로 보여준다.
- 별이 전원 수만큼 증식해 연결선을 그린 뒤 엔진 좌표로 "흘러들어" 장면 0과 한 몸처럼 이어진다 — 이음매가 이 후보의 핵심.
- 검은 화면·별·선·빛만 쓰고 글자는 `nebulaCopy`에서만 읽는다. 점화(LLM 스파크 하강)와 역량 카드(원문 인용) 두 곳에만 시각적 강조를 둔다.

## 비트별 연출

- `1-0` 검은 화면 위 판독 불가 PPT 실루엣 5장이 느리게 표류(결정적 난수, 매 빌드 동일 화면).
- `1-1` 실루엣 한 장이 중앙으로 → 보라색 텍스트 막대로 풀림 → 민트색 임베딩 다이아몬드로 수렴 → 별 하나 점등.
- `1-2` 별이 320개로 증식·근접 별끼리 연결선 → `go(0)`와 동시에 베일 페이드 → 별들이 `peoplePositions()` 좌표로 이동하며 엔진 장면 0에 안착(캔버스 소거).
- `1-3` `focusPerson(split:false)` 줌 → 예시 인물에 옅은 고리 → 민트 스파크가 위에서 내려와 별을 통과(점화 플래시) → `splitPerson()` 분열.
- `1-4` `clearPerson()` 줌 아웃 → `go(1)` 전원 분열 → 직후 0.7초 잔광 플래시.
- `1-5` `go(2)` 격자 → 예시 인물의 PJT 칸(`data-pjt-cell`)에 펄스 링 1회.
- `1-6` `enterPjt(person.pjt)` 성운 진입.
- `1-7` `selectTask(task.id)` + 좌하단 story 오버레이 카드(● 보유 경험 / ◯ 필요한 역량, 라벨 + 원문 인용, `textContent`만 사용).
- `1-8` 베일이 천천히 올라와 암전, 중앙 문장만 남김.

## 알려진 한계

- `1-3`의 점화 고리·스파크 위치는 엔진 줌 종료 시점의 `peoplePositions()`를 쓰는데, 엔진 줌 배율이 바뀌면 고리 반경(34px)이 별보다 크거나 작아 보일 수 있다(시각 문제만, 검수에는 무관).
- `1-5` 펄스 링은 칸의 기준점 좌표에 그려 칸 중심과 다를 수 있다(짧게 사라지는 보조 연출).
- reduced-motion에서는 모든 이동·분열 연출이 끝 프레임만 남고 페이드로 대체된다(검수 통과, 연출 풍부함은 모션 버전 기준).
- `1-2` 스토리 별 수는 `min(people, 340)`으로 제한 — 320명 픽스처에서는 전원과 일치한다.

## 검수 결과

```
NEBULA_PYTHON=$PWD/.venv/bin/python node tests/q3_story_check.cjs \
  docs/q3-visual/story-kimi/story.js docs/q3-visual/story-kimi/shots
PASS: docs/q3-visual/story-kimi/story.js — 9 beats 28129ms, reduced motion 1135ms
```

- 콘솔 오류 0, 외부 요청 0, `#synthetic-mark` 상시 표시, `1-2` 뒤 장면 0, `1-6` 뒤 PJT 진입, 각 비트 `screen` 첫 줄 표시 — 모두 PASS.
- 스크린샷 9장: `shots/1-0.png` … `shots/1-8.png` (합성 화면).

## 민감정보

- 작업 중 실명·실제 회고로 보이는 내용을 발견하지 못했다(중단 사유 없음). 읽은 것은 브리프가 허용한 파일뿐: `docs/q3-visual-brief.md`, `nebula/templates/deck.md`, `nebula/templates/nebula.html`, `nebula/render.py`, `nebula/demo.py`, `nebula/fixtures/q3/`(합성), `tests/q3_story_check.cjs`, `tests/q3_story_stub.js`.
