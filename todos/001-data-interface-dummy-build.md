---
id: 001
title: 데이터 인터페이스 확정 + 더미 데이터 생성기 + 단일 HTML 빌드 조립
status: done # 코드 완료 및 연동 검증 완료
blocked_by: []
labels: [ready-for-agent, prefactor]
---

## Parent

docs/PRD-heritage-archive.md

## What to build

**Phase 1 프리팩터**: 실제 PPT/임베딩 없이 더미 데이터로 전체 Archive 파이프라인을 관통하는 tracer bullet. 데이터 스키마를 코드로 고정하고, 가상 인물 150명의 더미 JSON으로 기존 프로토타입이 단일 HTML로 조립되어 네트워크/검색/에고 뷰/필터까지 동작하는 것까지 가서 002~007이 병렬로 진행할 기반을 마련한다.

실제 데이터(PPT 파싱 결과, 임베딩 벡터)는 Jay가 별도로 제공할 때까지, 이 이슈에서 생성한 더미 persons/neighbors/freq.json을 표준으로 삼는다.

- PRD의 데이터 인터페이스를 그대로 구현 (프로토타입에서 나온 확정 스키마):

  ```
  persons.json:   { id, name, pjt, cl_level, text, tags: [...] }
  neighbors.json: { [id]: [{ id, similarity }, ...] }   // 인당 top-K
  freq.json:      { [id]: { 단어: 횟수 } }
  ```

- 더미 데이터 생성기: 가상 인물 ~150명의 persons/neighbors/freq JSON 3종 생성 (임의 한글 텍스트/태그/빈도, pjt·cl_level 분포 포함)
- 빌드 조립 스크립트: JSON 3종을 기존 `docs/similarity-network-prototype.html` 기반 Archive HTML에 `<script>` 태그로 전량 인라인 → 외부 파일 참조 없는 단일 `.html` 산출
- 프리팩터: 이웃 수 3계층 변수화 — K(저장 이웃 수)=30, EGO_DISPLAY_N(에고 뷰 표시 수, 기존 하드코딩 10 제거), Top-N 슬라이더 상한. 전부 build-time config 상수, 관계는 K ≥ EGO_DISPLAY_N ≥ 슬라이더 최대값

## Acceptance criteria

- [x] 더미 데이터 생성기 실행 시 persons/neighbors/freq JSON 3종이 스키마대로 생성된다
- [x] 빌드 스크립트 실행 시 외부 참조 없는 단일 HTML 파일 하나가 나온다
- [x] 그 HTML을 브라우저로 열면 더미 150명 네트워크(검색·팀 필터·에고 뷰)가 동작한다 (검증 완료)
- [x] K / EGO_DISPLAY_N / 슬라이더 상한이 하드코딩 없이 config 상수로 분리되어 있다
- [x] neighbors 인당 개수가 K=30으로 생성된다

## Blocked by

None - can start immediately
