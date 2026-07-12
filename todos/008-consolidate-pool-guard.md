---
id: 008
title: tags.py — consolidate_pool 실패 가드 (실데이터 배치 전 결정)
status: ready
labels: [review-finding]
---

## Parent

todos/004-tag-extraction-batch.md (2026-07-12 코드 리뷰에서 발견)

## What to build

`scripts/tags.py main()`이 `consolidate_pool()`을 가드 없이 호출한다. 인당 추출은
개별 재시도로 보호되지만, 풀 정리 LLM 호출 1회가 실패(예외/파싱 불가)하면
`persons.json` 저장 전에 raise되어 추출 결과 전체가 버려진다 — 004의 "실패 시
전체 배치 재실행 불필요" 의도와 어긋남.

방향(택1, 실데이터 배치 전에만 결정하면 됨):
- `consolidate_pool`을 try/except로 감싸고 실패 시 정리 없이 추출 결과 그대로 저장 + 경고
- 또는 추출 결과를 먼저 저장하고 풀 정리를 별도 단계로 분리

## Acceptance criteria

- [ ] 풀 정리 호출이 실패해도 인당 추출 태그가 persons.json에 저장된다 (테스트로 고정)
