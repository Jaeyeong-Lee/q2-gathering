---
id: 006
title: Archive 태그 UX — 칩, 필터, 에고 뷰 공통 태그 엣지 라벨
status: done # 칩/필터/엣지 라벨 구현, cloud_logic.js 순수 함수 + 헤드리스 크롬 검증
blocked_by: [001]
labels: [ready-for-agent]
---

## Parent

docs/PRD-heritage-archive.md (코드 4번 중 태그)

## What to build

**Phase 1: 더미 데이터로 프로토타입**. persons.json의 tags 데이터를 Archive 화면에 노출하는 슬라이스. 태그를 노드로 만드는 이분 그래프는 기각됐으므로 제안하지 말 것.

- 현재 단계: 001/004에서 생성한 더미 tags로 칩/필터/에고 뷰 라벨 렌더링 및 상호작용 검증
- 실제 데이터: 004(태그 추출)가 완료되면, persons.json의 tags 필드가 채워져 자동으로 연동

- 인물 디테일 패널에 태그 칩 표시
- 태그 칩 클릭 → 같은 태그 보유자 점등, 나머지 dim (기존 팀 필터와 동일 UX)
- 에고 뷰 엣지에 두 사람의 공통 태그 라벨 표시 — 공통 태그가 있을 때만, 없으면 라벨 없음 (억지 라벨 금지)

## Acceptance criteria

- [x] 인물 클릭 시 디테일 패널에 그 사람의 태그 칩이 보인다 (헤드리스 스크린샷 검증)
- [x] 태그 칩 클릭 시 보유자만 점등되고 나머지는 dim 된다 (클릭 주입 스크린샷, 상단 해제 pill 포함)
- [x] 에고 뷰에서 공통 태그가 있는 엣지에만 라벨이 붙는다 (홀짝 거리 교차로 겹침 방지)
- [x] 공통 태그 0개인 쌍의 엣지는 라벨이 비어 있다 (commonTags → [] 테스트)
- [x] 필터 로직이 순수 함수로 분리되어 테스트된다 (passesTagFilter/commonTags, node로 pytest 검증)

## Blocked by

- todos/001-data-interface-dummy-build.md
