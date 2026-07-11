---
id: 004
title: LLM 태그 추출 배치 스크립트 (150콜 루프 + 정규화)
status: done # scripts/tags.py + tag_synonyms.json + tests/test_tags.py (LLM 호출부는 call 주입식, 실데이터 때 연결)
blocked_by: [001]
labels: [ready-for-agent]
---

## Parent

docs/PRD-heritage-archive.md (코드 2번)

## What to build

**Phase 1: 더미 데이터로 프로토타입**. 인당 회고 텍스트에서 성향/역량 태그를 추출해 persons.json의 `tags` 필드를 채우는 빌드 타임 배치 스크립트.

- 현재 단계: LLM 호출을 목킹하고, 더미 태그 응답에서 정규화/파싱 로직만 검증. 006(태그 UX)에서 사용할 수 있게
- 실제 데이터: Jay가 실제 텍스트 제공 후, 이 스크립트의 LLM 호출 활성화 → 150회 배치 실행 → 태그 정규화 → persons.json에 tags 필드 채움

- 1인 1호출 × 150회 배치 (긴 컨텍스트 1회 호출 방식 아님) — 호출 간 간섭 없음, 실패 시 개별 재시도
- 자유추출 + 간단 동의어 정규화만 (정식 온톨로지/2-pass vocabulary는 v2로 이관, 재제안 금지)
- 추출 완료 후 태그 풀 전체를 1~2회 LLM 호출로 표기 일관성 정리
- LLM 호출부는 목킹하고, `LLM 응답 → 정규화된 태그 배열` 변환 로직만 순수 함수로 pytest 테스트. 개별 호출 실패 시 재시도 로직 별도 검증

## Acceptance criteria

- [x] 응답 파싱 → 태그 배열 변환이 순수 함수로 분리되어 테스트된다 (LLM 목킹)
- [x] 개별 호출 실패 시 해당 인물만 재시도된다 (전체 배치 재실행 불필요, 소진 시 해당 인물만 실패 보고)
- [x] 동의어 병합 정규화가 적용된다 (tag_synonyms.json + 풀 전체 1콜 정리)
- [x] 출력 태그가 persons.json 스키마의 tags 필드에 들어간다 (실패자는 기존 태그 유지)
- [x] pytest 테스트 통과

## Blocked by

- todos/001-data-interface-dummy-build.md
