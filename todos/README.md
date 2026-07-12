# Heritage Archive — 이슈 목록

gh 없이 파일 기반으로 운영하는 이슈 트래커. 이슈 1개 = 파일 1개, 상태는 frontmatter `status`(ready / in-progress / done)로 관리.

출처: docs/PRD-heritage-archive.md

## 📌 현황: Phase 1 — 더미 데이터로 프로토타입 구축

**지금 단계**: 실제 PPT/임베딩 파일 없이 **더미 데이터로 전체 파이프라인 검증**. 
- 001에서 더미 persons/neighbors/freq JSON 생성
- 002~007은 그 더미 데이터로 Archive HTML 전체 기능 (네트워크, 워드클라우드, 태그, 인물 카드) 동작 확인
- 무대 라이브 테스트는 이후 단계 (Jay가 실제 PPT/임베딩 제공 후)

**실데이터 연동은 이후**: Jay가 PPT 3개 파싱 + 사내 임베딩 API 호출 → persons/neighbors/freq 데이터 제공 → 빌드 조립 재실행 → 배포

| # | 이슈 | Blocked by |
|---|---|---|
| [001](001-data-interface-dummy-build.md) | 데이터 인터페이스 + 더미 데이터 생성기 + 단일 HTML 빌드 조립 | 없음 |
| [002](002-similarity-neighbors-script.md) | 코사인 유사도 → top-K 이웃 JSON 스크립트 | 001 |
| [003](003-morpheme-freq-script.md) | 형태소/빈도 집계 스크립트 | 001 |
| [004](004-tag-extraction-batch.md) | LLM 태그 추출 배치 스크립트 | 001 |
| [005](005-wordcloud-view.md) | 워드클라우드 (전체/팀/CL + 유사군 연동) | 001 |
| [006](006-tag-ux.md) | 태그 칩/필터/엣지 라벨 | 001 |
| [007](007-person-card.md) | 인물 카드 (회고 md 렌더) | 001 |
| [008](008-consolidate-pool-guard.md) | tags.py consolidate_pool 실패 가드 (리뷰 발견) | 004 |

001이 스키마·더미 데이터·빌드 조립을 깔면 002~007은 전부 병렬 진행 가능. 실데이터 연동(PPT 파싱, 임베딩 API 호출)은 Jay 담당이라 이슈에서 제외.
