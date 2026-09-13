# story-codex

**Agent ID:** story-codex  
**Branch:** Jaeyeong-Lee/q3-visual-story-codex  
**Status:** ✅ 검수 PASS

## 콘셉트

조용한 도입 → 세 번의 구조적 전환 → 정직한 맺음

- **출발점:** pitch-cosmos-v2의 검은 배경·중앙 구도·최소 텍스트, candidate-50의 분열→성운 모션
- **반영 피드백:** 5모델 리뷰 공통 지적 (첫 장면 임팩트, 작은 글자 제거, 15분 리듬)
- **태도:** 사람의 기록이라는 출발점, Canvas로 그린 PPT 실루엣, 실제 이동·분열·응집으로 인과 표현

## 비트별 연출

| Beat | 화면 사건 | 엔진 | 기술 |
|---|---|---|---|
| 1-0 | 검은 화면, 겹친 PPT 실루엣 3장 (판독 불가) | — | Canvas: 0.08 alpha 직사각형 |
| 1-1 | 문서 → 텍스트 줄 → 임베딩 아이콘 (수렴 방사선) → 별 하나 (glow) | — | Canvas 90 frame animation |
| 1-2 | 별 1 → 320 (원형 배치) → 엔진 좌표로 이동 | `go(0) + peoplePositions()` | Canvas 120 frame → engine SVG |
| 1-3 | 클로즈업 → LLM 아이콘 (SVG 펄스 1.2s) → 별 분열 | `focusPerson({split:false}) + splitPerson()` | SVG overlay |
| 1-4 | 줌 아웃 → 전원 과제 별 | `clearPerson() + go(1)` | — |
| 1-5 | 4열 PJT 격자로 해쳐모임 | `go(2)` | — |
| 1-6 | P000 PJT로 들어가 성운 | `enterPjt(person.pjt)` | — |
| 1-7 | 과제 선택, 역량 카드 (엔진 패널), story 텍스트 0.8 opacity | `selectTask(task.id)` | — |
| 1-8 | 암전, 중앙 텍스트 | — | blackout |

## 알려진 한계

- **1-1 임베딩 아이콘:** 수렴 방사선은 "텍스트가 벡터로 압축되는 과정"의 은유. 실제 transformer 구조나 벡터 차원을 재현하지 않음.
- **1-2 별 증식 속도:** 320명이면 Canvas 3px 별로도 충분히 빠름. 더 많은 인원이면 batch draw 최적화 필요.
- **reduced motion:** Canvas 프레임 루프를 건너뛰고 최종 상태만 표시. 전환 의미는 유지됨.
- **1-7 역량 카드:** 엔진 패널이 표시. story layer는 0.8 opacity로 뒤로 물러남. 별도 카드 오버레이를 쌓지 않음.

## 정직성 체크리스트

- [x] 합성 표시 `#synthetic-mark` 항상 표시 (엔진 제공, z-index 20)
- [x] 실명·실제 회고 미포함 (합성 픽스처만 사용)
- [x] PPT 실루엣 판독 불가 (0.08 alpha)
- [x] Canvas에 실데이터 그리지 않음
- [x] 위치·거리·크기·밝기는 우열 아님 (문구로 명시)

## 검수 결과

```
PASS: docs/q3-visual/story-codex/story.js — 9 beats 20569ms, reduced motion 1096ms
shots: /Users/winter/orca/workspaces/q2-gathering/q3-visual-story-codex/docs/q3-visual/story-codex/shots
```

- **실행 시간:** 일반 모드 20.6초, reduced motion 1.1초
- **스크린샷:** 9장 PNG 생성 완료
- **콘솔 오류:** 0
- **계약 준수:** window.nebulaStory.beats, goto, current 검증 통과

---

**Created:** 2026-09-13  
**Commit:** _pending_
