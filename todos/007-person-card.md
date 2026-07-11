---
id: 007
title: Archive 인물 카드 — 회고 원문(md) 렌더
status: done # mdToHtml(cloud_logic.js) + 디테일 패널 원문 카드, 헤드리스 크롬 검증
blocked_by: [001]
labels: [ready-for-agent]
---

## Parent

docs/PRD-heritage-archive.md (코드 4번 중 인물 카드)

## What to build

**Phase 1: 더미 데이터로 프로토타입**. 인물 디테일에서 그 사람의 근원경쟁력 회고 원문(persons.json의 `text`, md)을 읽을 수 있게 하는 슬라이스. 발표 이후 참석자가 자기 회고를 다시 확인하는 상시 Archive 용도.

- 현재 단계: 001에서 생성한 더미 회고 텍스트(md)로 렌더링 로직 검증
- 실제 데이터: Jay가 PPT에서 추출한 실제 회고 텍스트를 persons.json의 text 필드에 채우면, 이 이슈의 렌더 로직은 그대로 사용

- 인물 선택 시 회고 md 원문을 카드/패널로 렌더 (md → HTML 변환은 인라인 가능한 경량 방식, 외부 런타임 의존 금지)
- PPT 페이지 이미지 export는 스코프 제외 (확정) — 텍스트만
- 긴 원문 대응 (스크롤 등, 오디토리움 스크린에서 가독성 유지)

## Acceptance criteria

- [x] 인물 선택 시 회고 원문이 md 서식대로 렌더된다 (h1~h3/문단/불릿/굵게, 헤드리스 스크린샷 검증)
- [x] 외부 네트워크 요청 없이 동작한다 (자체 md 서브셋 변환, 외부 참조 zero 테스트 유지)
- [x] 긴 텍스트가 레이아웃을 깨지 않는다 (카드 내부 max-height 스크롤 + overflow-wrap)
- [x] md → 렌더 상태 변환이 순수 함수로 분리되어 테스트된다 (mdToHtml, 이스케이프 포함 node 검증)

## Blocked by

- todos/001-data-interface-dummy-build.md
