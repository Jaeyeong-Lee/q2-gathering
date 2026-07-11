---
id: 003
title: 형태소/빈도 집계 스크립트 (kiwipiepy + 커스텀 불용어)
status: done # scripts/freq.py + stopwords.txt + tests/test_freq.py
blocked_by: [001]
labels: [ready-for-agent]
---

## Parent

docs/PRD-heritage-archive.md (코드 1번)

## What to build

**Phase 1: 더미 데이터로 프로토타입**. 인당 회고 텍스트(md)를 입력받아 명사 위주 단어 빈도를 집계해 `freq.json`을 생성하는 빌드 타임 스크립트. 워드클라우드와 Higher/Lower 게임 문항의 원천 데이터가 된다.

- 현재 단계: 더미 한글 텍스트로 형태소 추출 및 불용어 필터링 검증. 005(워드클라우드)에서 사용할 수 있게
- 실제 데이터: Jay가 PPT에서 추출한 실제 회고 텍스트 제공 → 이 스크립트 실행 → 실데이터 freq.json 생성

- kiwipiepy(또는 동급 한국어 형태소 분석기)로 명사 추출
- 커스텀 불용어 리스트 적용 — 불용어 품질이 워드클라우드 인상을 좌우하므로 리스트를 별도 파일로 두고 쉽게 편집 가능하게
- 출력: 001에서 확정한 freq.json 스키마 (인당 {단어: 횟수})
- 순수 함수(텍스트 → 빈도 dict)로 분리하고 pytest 단위 테스트 작성

## Acceptance criteria

- [x] 한글 명사 추출이 정확하다 (샘플 문장 테스트, 파생접미사 병합·복수형 정규화 포함)
- [x] 불용어 필터링이 적용된다 (불용어 포함 입력 테스트)
- [x] 출력이 001의 freq.json 스키마와 일치한다
- [x] 더미 텍스트 → 이 스크립트 출력이 001 빌드 조립에 물려 동작한다
- [x] pytest 테스트 통과

## Blocked by

- todos/001-data-interface-dummy-build.md
