# 3Q 분기회 발표 — 작업 인덱스

2026-09-13 작성. 위치와 상태만 가리킨다. **흐름·결정·티켓·가짜 데이터는 [[q3-presentation-plan]]이 정본이다.**

## 먼저 읽기

1. [[q3-presentation-plan]] §0 — 누가 어디를 읽는지
2. nebula 코드를 고치면 `nebula/CLAUDE.md`
3. 화면을 만들면 `docs/design-candidates-2026-09-11/deck-soul.md`

## 위치

| 무엇 | 브랜치 | 워크트리 |
|---|---|---|
| **통합 브랜치 — 발표 작업의 정본** (nebula 코드 + 계획 + 디자인 시안 + 픽스처) | `Jaeyeong-Lee/q3-nebula-presentation` | `~/orca/workspaces/q2-gathering/q3-nebula` |
| nebula 원래 브랜치 (T0에서 통합됨) | `codex/future-task-capability-map` | `~/Documents/Codex/2026-09-11/future-task-implementation` |
| 디자인 시안 원래 브랜치 (T0에서 통합됨) | `Jaeyeong-Lee/feat-td-extract-ax` | `~/orca/workspaces/q2-gathering/auk` |
| 8/14 임원 보고 덱 (참고) | `Jaeyeong-Lee/exec-deck-narrative-flow` | `~/orca/workspaces/q2-gathering/pufferfish` |

새 작업은 통합 브랜치에서 딴다. 다른 브랜치 파일은 `git show <브랜치>:<경로>`로 읽는다.

## 상태

- 2026-09-13 — 계획 컨펌(발표 09-15). T0 통합 브랜치, T1 합성 픽스처 완료. 다음은 T2·T3·T4 병렬. 티켓 진행은 plan §6 상태 표에 적는다.

## 정본이 아닌 이전 결과물 (보존)

- `scripts/td_people_atlas_demo.py` ([[people-atlas-demo]]) — 200명 합성 사람·과제 데모
- `scripts/td_gallery.py` — 산출물 5종 탭 + 항해 발표 모드
- `dist/heritage-archive.html` — 2Q 무대 화면, 배포 완료
- `docs/design-candidates-2026-09-11/candidate-*.html` — 성운 후보 4종, Cosmos v1
