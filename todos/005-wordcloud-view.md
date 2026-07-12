---
id: 005
title: Archive 워드클라우드 — 전체/팀별/CL별 + 에고 뷰 유사군 연동
status: done # archive/cloud_logic.js + ECharts/echarts-wordcloud 벤더링 + 템플릿 패널, 헤드리스 크롬 검증 완료
blocked_by: [001]
labels: [ready-for-agent]
---

## Parent

docs/PRD-heritage-archive.md (코드 4번 중 워드클라우드)

## What to build

**Phase 1: 더미 데이터로 프로토타입**. Archive HTML에 동적 워드클라우드를 추가한다. 무대 오프닝 훅(전체 클라우드 리빌)과 네트워크 코너의 유사군 클라우드 연동을 담당하는 슬라이스.

- 현재 단계: 001에서 생성한 더미 freq.json으로 전체/팀별/CL별/유사군 클라우드 전환 및 동작 확인
- 실제 데이터: Jay가 실제 텍스트 제공 후 003(형태소/빈도 스크립트) 재실행 → 실데이터 freq.json 생성 → 이 이슈의 워드클라우드 변환 로직은 그대로 사용

- ECharts + echarts-wordcloud (인라인 포함) 사용 — 렌더 품질 문제로 wordcloud2.js에서 교체 (2026-07-12)
- 전환 가능한 4가지 스코프: 전체 / 팀(pjt)별 / CL별 / 유사군(에고 뷰 선택 인물 + top-N 이웃)
- 합산 로직: 인당 빈도 dict를 선택 집합에 대해 단순 덧셈 후 재렌더 (사전 저장된 freq.json만 사용, 런타임 계산 없음)
- 크기는 상대 스케일로 렌더 — (사양 변경 2026-07-12) 호버 툴팁의 절대 횟수 노출 허용
- 합산 인원 5명 미만이면 렌더 회피 또는 경고 표시
- 네트워크에서 인물 클릭(에고 뷰 진입) 시 유사군 클라우드 자동 갱신

## Acceptance criteria

- [x] 전체/팀별/CL별/유사군 클라우드 전환이 동작한다 (전체/팀별 헤드리스 클릭 스크린샷, CL별은 동일 경로 + 단위 테스트)
- [x] 크기는 상대 스케일, 호버 툴팁 절대 횟수는 노출 허용 — 사양 변경 2026-07-12 (cloudState는 합산 절대값 반환, 테스트로 고정)
- [x] 5명 미만 집합에서 렌더 회피/경고가 동작한다 (ok:false + 패널 경고 문구)
- [x] 에고 뷰 진입 시 유사군 클라우드가 자동 연동된다 (#ego 딥링크 스크린샷 검증)
- [x] 더미 데이터 기준 전환/재렌더에 체감 지연이 없다
- [x] 렌더 로직이 `데이터 JSON → 렌더 상태` 순수 함수로 분리되어 테스트된다 (archive/cloud_logic.js, node로 pytest 검증)

## Blocked by

- todos/001-data-interface-dummy-build.md
