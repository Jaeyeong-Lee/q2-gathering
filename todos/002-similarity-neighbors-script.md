---
id: 002
title: 코사인 유사도 → top-K 이웃 JSON 변환 스크립트
status: done # scripts/similarity.py + tests/test_similarity.py, 헤드리스 크롬 렌더 확인 완료
blocked_by: [001]
labels: [ready-for-agent]
---

## Parent

docs/PRD-heritage-archive.md (코드 3번)

## What to build

**Phase 1: 더미 데이터로 프로토타입**. 임베딩 벡터 배열을 입력받아 코사인 유사도 top-K 이웃을 계산해 `neighbors.json`을 생성하는 빌드 타임 스크립트. 

- 현재 단계: 임의 벡터(또는 001에서 생성한 더미 벡터)로 출력이 001의 빌드 조립에 물려 네트워크가 뜨는 것까지 확인
- 실제 데이터: Jay가 사내 임베딩 API로 벡터 생성 후, 이 스크립트만 재실행하면 실데이터 neighbors.json 생성 (스크립트 수정 불필요)

- 입력: 인당 1벡터 (차원수는 사내 API 스펙 확정 전이므로 입력에서 유추, 하드코딩 금지)
- 출력: 001에서 확정한 neighbors.json 스키마, 인당 top-K (K는 build config 상수, 기본 30)
- 순수 함수(벡터[] → 이웃 JSON)로 분리하고 pytest 단위 테스트 작성

## Acceptance criteria

- [x] 코사인 유사도 계산이 정확하다 (알려진 벡터 쌍으로 테스트)
- [x] top-K 정렬·컷오프가 올바르다 (자기 자신 제외 포함)
- [x] 출력이 001의 neighbors.json 스키마와 일치한다
- [x] 더미 벡터 → 이 스크립트 → 001 빌드 조립을 거친 HTML에서 네트워크가 렌더된다 (헤드리스 크롬 스크린샷으로 150노드 네트워크·범례·검색 UI 렌더 확인)
- [x] pytest 테스트 통과

## Blocked by

- todos/001-data-interface-dummy-build.md
