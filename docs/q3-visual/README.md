# 3Q 시각 작업 후보

지시서: `docs/q3-visual-brief.md`. 에이전트 한 명 = 폴더 하나(`<agent-id>/`). 오케스트레이터가 이 표를 채운다.

| agent-id | 역할 | 브랜치 | 커밋 | 검수 | 선택 |
|---|---|---|---|---|---|
| story-claude | V-story | `Jaeyeong-Lee/q3-visual-story-claude` | `e781976`+`d6354e4` | `q3_story_check` PASS | ✅ **선택 (2026-09-13, Jay)** |
| story-codex | V-story | `Jaeyeong-Lee/q3-visual-story-codex` | `8e42efd` | `q3_story_check` PASS | — |
| story-kimi | V-story | `Jaeyeong-Lee/q3-visual-story-kimi` | `ec0ab7b`+`d136e0f` | `q3_story_check` PASS | — |
| engine | V-engine | `Jaeyeong-Lee/q3-visual-engine` | | 기존 검사 4종 | — |

## 선택 결과

- **story-claude 선택** (2026-09-13). Jay 지정. 나머지 2후보는 폴더로 보존 — 이후 변경 대비.
- 통합(§4): `nebula/templates/story.js` 교체 → 전체 테스트 → 통합 브랜치 머지 — **아직 미수행**.
- Jay가 이후 story.js 변경 가능성을 명시함 — 통합 전 문구·연출 조정 여지 있음.
