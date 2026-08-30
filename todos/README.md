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
| [009](009-realdata-followups.md) | 실데이터 반영 후속: 유사도 정규화 · 잔여 임베딩 · 태그 재검토 | 없음 |

001이 스키마·더미 데이터·빌드 조립을 깔면 002~007은 전부 병렬 진행 가능. 실데이터 연동(PPT 파싱, 임베딩 API 호출)은 Jay 담당이라 이슈에서 제외.

## 📌 트랙 2: task-discovery 산출물 — 샘플데이터로 뽑아보기

출처: docs/deliverable-candidates-2026-08-28.html (후보 10종) · docs/deliverable-candidates-fable-2026-08-30.html (후보 9종)

두 제안서의 산출물 후보를 **합성 코퍼스 + Gemini 실호출**로 만들어 눈으로 비교하는 단계.
입력이 합성이라 외부 API로 나가도 유출 위험이 없고, 010이 만드는 샘플 출력 디렉터리는
실데이터와 분리돼 있어 **모든 에이전트가 읽어도 되는 유일한 td 산출물**이다.

| # | 이슈 | Blocked by |
|---|---|---|
| [010](010-sample-outputs.md) | 샘플 산출물 한 벌 — 합성 코퍼스로 파이프라인 완주 (출력 분리) | 없음 |
| [011](011-td-render-common.md) | ~~렌더 공통 헬퍼 선행 추출~~ → 012에 흡수 (폐기, 결정 기록) | — |
| ✅ [012](012-constellation-map.md) | 성좌 지도 — 별=과제, 결정적 레이아웃 (+ 렌더 헬퍼 추출) | 010 |
| ✅ [013](013-empty-sky.md) | 빈 하늘 — 성좌 지도의 뒷면 토글 | 012 |
| ✅ [014](014-ax-lens.md) | AX 렌즈 — 언급 표시를 지도 위 필터로 | 012 |
| ✅ [015](015-lineage-view.md) | 계보 뷰 — 이 별은 어느 문장에서 왔나 | 012 |
| [016](016-unified-sample-population.md) | 합성 인구 단일화 — 한 인구로 두 지도 | 010 |
| [017](017-person-card.md) | 개인 카드 — 사람 지도에 그 사람의 과제 | 016 |
| ✅ [018](018-team-category-heatmap.md) | 부서 단면 — 팀 × 카테고리 히트맵 | 010, 012 |
| ✅ [019](019-question-cards.md) | 질문 카드 — 집계에서 워크숍 아젠다 | 010 |
| ✅ [020](020-executive-one-pager.md) | 임원 한 장 — 인터랙션 없는 정물 | 012 |
| [021](021-voyage-autopilot.md) | 항해 — 딥링크 자동 시퀀스 | 012 |
| [022](022-higher-lower-quiz.md) | Higher/Lower 퀴즈 (발표 형식 확정 후 착수) | 016 |
| ✅ [023](023-consensus-weight.md) | 합의의 무게 — 사람의 결정이 지도에 | 012 |
| ✅ [024](024-decision-record.md) | 결정 기록 — 고른 것·미룬 것·이견 | 023 |

**2026-08-31 진행**: 012~015·018~020·023·024를 합성 데이터(LLM 0회, `make td-sample-fake`)로
빌드해 헤드리스 검증까지 마쳤다. 남은 것은 016·017(사람 지도 샘플·개인 카드), 021(항해),
022(퀴즈, 형식 확정 게이트), 그리고 010의 Gemini 실호출 완주다.

010이 유일한 프론티어. 012가 열리면 013·014·015·018·020·021·023이 병렬, 016이 열리면
017·022가 병렬. 023 → 024가 유일한 2단 체인이고, 이 둘이 "사람의 결정이 데이터로 돌아오는"
고리를 닫는다. (011은 코드 리뷰 결과 폐기 — 추출을 012가 첫 소비자와 함께 한다.)
