# 3Q 발표 — 시각 작업 공통 요구사항

작업 위치: `~/orca/workspaces/q2-gathering/q3-nebula`, 통합 브랜치 `Jaeyeong-Lee/q3-nebula-presentation`.
흐름·결정·함수 계약의 정본은 [발표 계획](q3-presentation-plan.md) §2–4.5다. 화면 태도는 [deck-soul](design-candidates-2026-09-11/deck-soul.md)의 화면·정직성 절을 따른다.

## 발표 흐름과 작업 경계

기록의 도입 → PPT·텍스트가 사람의 별로 변환 → 전원 네트워크 → 예시 인물 클로즈업·분열 → 전원 분열 → PJT 격자·한 PJT 성운 → 한 과제의 역량 근거 → 맺음.

- T4: 도입·wow1·wow2·맺음과 전체 비트 진행을 `nebula/templates/story.js`에서 만든다. Space/→ 다음, ← 이전, R 다시 시작을 담당한다. 엔진은 story 모드에서 좌우 키를 처리하지 않는다.
- 엔진: 장면 0 사람, 1 전원 분열, 2 PJT 격자·성운, 3 과제·역량. 검색·상태·복원은 `nebula.html`이 담당한다. 시간 장면은 보류다.
- 병렬 시안은 각자 별도 파일 또는 브랜치에 보관하고, 고른 시안 하나를 `story.js`에 합친다. `nebula.html`의 모션·톤 변경은 한 명이 순서대로 맡는다.
- `render.py`의 인라인 연결은 준비됐다. `story.js`가 있으면 `__STORY__`에 삽입하며, 없으면 엔진만 동작한다. `story.js`는 `#mode=story`에서만 연출을 시작해야 한다.

## 엔진과 연결하기

`window.nebula`의 함수 이름·인자는 계획서 §4.5를 그대로 쓴다. 인물·PJT 인자는 페이로드 색인, 과제 인자는 과제 ID다. `P000`은 원본 사람 ID이므로 `people[].pid`로 찾아 `id`를 전달한다.

`focusPerson`, `clearPerson`, `enterPjt`, `leavePjt`, `go`는 전환이 끝나면 resolve한다. 다음 비트는 `await`로 기다린다. 연속 조작으로 새 명령이 오면 이전 개인 분열의 후속 단계는 취소되고 Promise는 정상 종료한다. story 쪽도 비트가 바뀐 뒤 오래된 비트의 후속 호출을 실행하지 않도록 관리한다.

`peoplePositions()`는 현재 사람 중심의 **브라우저 뷰포트 기준 px**를 돌려준다. story 레이어가 다른 원점을 쓰면 그 레이어의 `getBoundingClientRect()`를 빼서 변환한다. wow2 마지막 별 위치를 이 좌표에 맞춘 뒤 엔진 장면 0에 넘긴다. 레이어는 `#sky` 위에 두고, 글자는 줌되는 월드 바깥 HTML로 그린다.

## 태도와 완료 기준

검은 배경, 중앙 문장 하나, 대강당에서 읽히는 글자. 말은 발표자에게 남기고 관점 변화는 실제 이동·분열·응집으로 보여준다. PPT 이미지는 판독할 수 없는 추상 표현을 쓴다. 실제 인물의 감정·수정 흔적을 지어내지 않는다. 위치·밝기·크기는 중요도나 준비도 점수가 아니다.

1920×1080, 오프라인 `file://`에서 확인한다. `prefers-reduced-motion`에서는 이동 대신 페이드를 사용한다. 합성 표시는 상시 보이게 둔다. 비트별 스크린샷 8장은 스크래치 폴더에 보관하며 커밋하지 않는다. 실제 데이터·실제 분류명은 사용하지 않는다.

## 가짜 데이터 실행

```sh
q3_demo_dir=$(mktemp -d /tmp/nebula-visual.XXXXXX)
python3 -m nebula demo --input nebula/fixtures/q3/persons.json \
  --network nebula/fixtures/q3/neighbors.json --out "$q3_demo_dir"
open "$q3_demo_dir/nebula.html"
# 브라우저 주소 끝에 #mode=story 추가
node tests/nebula_q3.cjs
```

픽스처는 320명·8 PJT이고 예시 인물은 `P000`이다. LLM 호출은 없다. 엔진 첫 장면은 전체 연결로 계산한 배치를 사용하고, 화면 연결선만 인물별 상위 4개를 합쳐 그린다. 시각 담당은 계산된 좌표·과제 수·분류를 연출용으로 바꾸지 않는다.
