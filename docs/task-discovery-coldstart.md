# task-discovery (콜드스타트 재설계) — 개요와 사용법

> 브랜치 `feat/task-discovery-coldstart`. 유사도 네트워크(Heritage Archive) 이후 작업.
> 상사 요구("근원경쟁력 기반 팀 10년 로드맵")를 **정직하게** 다루기 위해, 딥리서치 3종을
> 모아 도출한 **3개 방안(S1/S2/S4)을 전부 구현**했다. 셋은 공유 추출층 위에 공존하며,
> 실데이터가 오면 나란히 돌려 비교·택일할 수 있다.

작성 2026-07-26. 실데이터 미검증(전부 합성 코퍼스 + 가짜 LLM으로 개발). 실 LLM/ES 연동은 사내 몫.

---

## 1. 왜 이렇게 설계했나 (핵심 전제)

- **데이터에 로드맵이 없다.** 회고는 상향식·개인·근미래(1~3년) 서술이다. 10년·시퀀싱·전략·"꿈"은
  데이터에 없고 *원재료*(방향·역량갭·모멘텀)만 있다. 파이프라인이 로드맵을 만들면 환각이다.
- 그래서 **산출물 = 완성 로드맵이 아니라 "리더십 워크숍 입력물"**이다. "10년"은 문자 그대로가
  아니라 해석 프레임(리더십 토론 촉발). 시간축·꿈은 워크숍에서 사람이 채운다.
- **모든 항목은 원문 인용에 고정**된다. 인용이 원문에 실제 있는지 대조해 통과 못 하면 버린다.
- **무내용 문서는 억지 분류하지 않고 격리**한다(`signal_present:false`). 그 비율은 커버리지 리포트로.
- **개발은 합성 코퍼스 + 가짜 LLM으로.** 실데이터는 보안상 반출 불가라 눈으로 튜닝할 수 없다.
  실데이터엔 검증된 파이프라인만 사내에서 투입.

이 전제들은 딥리서치 3종(gemini/opus/claude)이 **독립적으로 같은 결론에 수렴**한 것이다.
근거: `docs/task-discovery-requirements.md`, `docs/task-discovery-deepresearch-{gemini,opus,claude}.md`.

---

## 2. 세 방안 (무엇이 다른가 = "카테고리를 누가/어떻게 만드나")

| 방안 | 카테고리 출처 | 강점 | 약점 | 티켓 |
|---|---|---|---|---|
| **S1 Taxonomy-first** | LLM이 facet을 읽고 taxonomy 생성 | 도메인 용어 무지를 구조적 우회, k 추측 불필요 | 사내 LLM의 *생성* 품질에 종속(미검증) | #16~#22 |
| **S2 Codebook-first** | 사람이 확정한 코드북, LLM은 배정만 | 설명가능·재현성, LLM 생성 리스크 없음 | 사람 시간 필요, 새 주제가 `기타`로 뭉갬 | #23~#25 |
| **S4 Retrieval-first** | 카테고리화 안 함 (검색으로 답) | 환각 표면적 최소, 반박 여지 없음 | "조직 큰 흐름 한 장"이 안 나옴 | #26~#29 |

**택일이 아니라 조합 가능.** S1 실패 시 그 taxonomy 초안을 S2 코드북으로 승격(코드 경로 존재:
`td_codebook.propose_draft`가 `td_taxonomy.induce` 재사용). S4 검색은 S1/S2 워크숍의 "그 근거 뭔데?"
즉답 도구로 겹쳐 쓸 수 있다. PRD: #13/#14/#15.

**실측으로 버린 것:** BERTopic/HDBSCAN 밀도군집 — 합성 282문장 POC에서 쓸 만한 토픽 수일 때
노이즈 28%(모든 응답이 중요한 이 과제에 부적합). 그래서 S1은 임베딩 군집이 아니라 LLM 독해로 간다.

---

## 3. 아키텍처 — 공유 추출층 + 방안별 + 단일 파이프라인

```
                    ┌─ td_sources   합성 코퍼스(원문)      ─┐
   공유 (세 방안)    ├─ td_extract   원문 → facet 추출        │  seam = 주입된 call(prompt)->str
                    └─ td_common    인용검증·재시도 헬퍼    ─┘  (tags.py 패턴)

   S1  td_taxonomy → td_assign → td_aggregate → td_render      (taxonomy 유도)
   S2  td_codebook → td_assign → td_aggregate → td_render      (사람 코드북, +기타수집)
   S4  td_index → td_query → td_digest                         (카테고리화 없음, 검색)

   td_pipeline:  run_all(codebook=None) = S1 / run_all(codebook=…) = S2 / run_retrieval() = S4
```

### 모듈 지도

| 모듈 | 역할 | 쓰는 방안 |
|---|---|---|
| `td_sources` | 합성 원문 회고 생성 (name·cl_level·pjt·part·text, 4케이스) | 공유 |
| `td_extract` | 원문 → facet(사람 단위 signal_present + 4축), 인용검증·항목폐기·배치내성 | 공유 |
| `td_common` | `norm`/`quote_in_source`/`text_is_copy_of_quotes`, `retry_call`(단일 계층) | 공유 |
| `td_taxonomy` | facet 배치반복 → 역량 taxonomy 생성·정제 | S1 |
| `td_codebook` | 코드북 로드·검증, 초안 제안(=taxonomy 재사용) | S2 |
| `td_assign` | facet → 카테고리 배정(+Other), 인용검증, `collect_other` | S1·S2 |
| `td_aggregate` | 확산도(distinct pjt·cl)·갭(have vs gap)·준비도 3구간·소수의견 트랙 | S1·S2 |
| `td_render` | 워크숍 입력물 md + 교차표 + 커버리지 + 미결질문 | S1·S2 |
| `td_index` | facet 단위 색인("한 문서=한 주제"), 인메모리 백엔드 | S4 |
| `td_query` | 하이브리드(키워드+벡터 RRF) 질의 + 필터 + 분포집계 | S4 |
| `td_digest` | 사전 조회 묶음(정적 md, ES 다운 백업) + 커버리지 | S4 |
| `td_pipeline` | 배선(skip-if-exists, 모델 이원화 call site) | 전부 |
| `td_cards` | 산출물 조인(카테고리↔항목↔사람↔조직, horizon 복원). 렌더링을 모름 | 워크숍 도구 |
| `td_inspect` | 역추적 탐색기 HTML (근거 검수·회의용) | 워크숍 도구 |
| `td_roadmap` | 시간축×준비도 매트릭스 + 카드 배치 HTML | 워크숍 도구 |
| `workshop_server` | 투표 취합(stdlib http.server) + 이견 아젠다 | 워크숍 도구 |

**워크숍 도구 넷은 `td_render` 이후 층이고 LLM을 부르지 않는다** — 산출물이 그대로면 몇
번이고 다시 만들 수 있다. 상세: [[task-discovery-workshop-tools]].

---

## 4. facet 스키마 (추출 산출물, 뒤 스테이지가 상속)

```json
{ "person_id": 1, "name": "...", "cl_level": "CL2|CL3|CL4",
  "pjt": "양산기술|공정기술|기획운영", "part": "고장분석(FA) 등",
  "signal_present": true,
  "future_task":     [{"text": "서술", "horizon": "단기|장기|불명", "quotes": ["원문발췌"]}],
  "capability_have": [{"text": "...", "quotes": ["..."]}],
  "capability_gap":  [{"text": "...", "quotes": ["..."]}],
  "direction":       {"text": "지향 1문장", "quotes": ["..."]} | null }
```

각 필드가 하위 산출물에 물린다: `future_task`→테마 카드, `have`+`gap`→역량 갭 뷰,
`horizon`→준비도 3구간, `direction`→워크숍 재료, `signal_present`→커버리지, `quotes`→근거 추적성.

**`confidence`는 스키마 체크포인트에서 의도적으로 제거**했다 — LLM 자기보고라 신뢰 낮고(리서치가
지적) 하위 분석에 불필요한 유일한 필드였다. `pjt`→`part`는 2단(양산/공정/기획운영 → 세부 파트),
`part`는 **선택적**(실데이터가 pjt만 가질 수 있어 확산도 1차 축은 pjt).

---

## 5. 실행 방법

### 개발/검증 (인프라 불필요)
```bash
make test                    # 전체 pytest (td 84 + 기존)
python -m pytest tests/test_td_*.py -q
```
모든 스테이지 테스트는 **가짜 `call`/`embed`를 주입**해 실 API/ES 없이 돈다(seam = 주입된 call 하나).
합성 코퍼스(개발용): `python scripts/td_sources.py 200 0` → `data/task_discovery/sources.json`.

### 내부망 실행 (사내 보안환경)

**1) 엔드포인트 env** (코드 수정 0 — `llm.py`가 라우팅):
```bash
export TEXT_PROVIDER=internal
export TEXT_API_KEY=<사내 키>
export TEXT_API_BASE=<사내 OpenAI호환 URL>
export TD_TEXT_MODEL=<사내 텍스트 모델 id>     # ← 필수. 미지정 시 gemini 모델명이 넘어감
# S4까지 갈 때만:
export EMBED_PROVIDER=internal
export EMBED_API_BASE=<BGE-M3 URL>
export TD_EMBED_MODEL=<임베딩 모델 id>
```

**2) 실행** (추출 입력 = `data/persons.json`):
```bash
make td           SOURCES=data/persons.json     # S1: 추출→taxonomy 유도→배정→집계→렌더 (LLM만)
make td-codebook  SOURCES=data/persons.json     # S2: codebook.json 먼저 작성 (LLM만)
make td-search    SOURCES=data/persons.json     # S4: +임베딩(BGE-M3)
```
- `persons.json`은 `id·name·cl_level·pjt·text`를 그대로 먹는다. `part`는 없어도 됨(확산도 1차 축은 pjt).
- `SOURCES` 없이 실행하면 **합성 코퍼스**를 생성해 돈다(개발용).
- 중간 산출물 있으면 skip(재실행 시 LLM 호출 0), 강제 재실행은 해당 JSON 삭제(또는 `force`).
- 모델 이원화(유도=큰/배정=작은)가 필요하면 `td_pipeline.main`에서 `taxo_call`/`assign_call`에 다른 call 주입.
- 파일 I/O 전부 `encoding="utf-8"` + `ensure_ascii=False`(한글 안전).
- 산출물은 `data/task_discovery/`(gitignore). **`dist/`(GitHub Pages 배포 추적)에 커밋 금지.**

---

## 6. 무엇이 검증됐고, 무엇이 아직 열려 있나

**검증됨(코드 정합):** 83개 td 테스트가 각 스테이지의 외부 행동을 가짜 call로 검증 —
인용 grounding(개행 견딤·text≠quotes 거부), no-signal 격리, 항목단위 폐기, 배치 내성,
단일 재시도, taxonomy 병합·중복방지, 코드북 검증·Other 경고, 하이브리드 검색(약어 정확매칭이
벡터 이웃에 안 밀림), 확산도·갭·준비도, 커버리지. 전 스테이지 스모크가 관통.

**아직 사람·인프라 몫 (green 테스트로 안 풀림):**

| 관문 | 무엇 | 누가 |
|---|---|---|
| **S1 #18 go/no-go** | 사내 실 LLM이 쓸 만한 taxonomy를 *생성*하나 (도메인 용어 반영·중복 없음·Other 과다 여부) — **S1 vs S2 결정이 여기 달림** | 실 LLM + 사람 판정 |
| **S2 코드북 확정** | 도메인 담당자가 `codebook.json` 작성(또는 `td_codebook` 초안 → 편집) | 도메인 담당자 |
| **S4 ES 연동** | 인메모리 백엔드는 개발용 — 운영은 ES(BM25+kNN+nori) 백엔드 + 실 BGE-M3 | 사내 인프라 |
| **미결 product 3** | 산출물 형태·기한 / 실명 표기 정책 / "우리 팀" 범위 — 렌더 기본값으로 구현, 전부 렌더-only 교체라 되돌릴 수 있음 | 상사/Jay |

---

## 7. 주요 설계 결정 로그

- **HDBSCAN/BERTopic 불채택** — 실측 노이즈 28%. S1은 LLM taxonomy 유도로.
- **`confidence` 제거** — 자기보고 신뢰 낮음 + 하위 불필요(스키마 체크포인트).
- **have/gap 2축 분리 유지** — 역량 갭 계산의 핵심(상사가 물은 것).
- **인용 대조는 공백·개행 제거 정규화**(`norm`, 대조용) — PPT 추출 개행이 진짜 인용을 떨구지 않게.
- **인용 표시는 개행 접기**(`oneline`, 표시용) — 인용 속 원문 `\n`이 md blockquote를 깨지 않게(렌더·digest).
- **추출 입력에 `part` 없어도 동작** — `persons.json`은 `part`가 없으므로 프롬프트/스키마가 `.get` 기본값.
- **항목 단위 폐기**(사람 전체 아님) — 부분 성공 보존.
- **소수의견 별도 트랙** — map-reduce over-smoothing 방어(팀의 미래 씨앗이 소수일 수 있음).
- **이름 구조상 분리** — 실명 정책이 익명화로 바뀌면 렌더 교체만으로.
- **오케스트레이션 프레임워크 미도입** — 1회성 200건엔 순차 루프+재시도+영속화로 충분.

---

## 8. 코드리뷰 결과 (2026-07-26, `main...HEAD` 2축 리뷰)

**Spec 축 — 통과.** PRD/티켓의 불변식이 전부 코드에 성립: 인용 grounding(개행 견딤·text≠quotes 거부),
no-signal 격리, 항목단위 폐기, 단일 재시도, confidence 스키마 제거, taxonomy k 미고정·군집 라이브러리
미사용, 코드북 거부/Other/재배정, S4 facet색인·RRF·RAG없음·dist 미타깃, 합성 pjt→part·기획운영 소수.
스코프 크립 없음.

**Standards 축 — 지적 반영 완료(커밋 `ab9c735`).** `_parse` 3중복·`AXES`/facet순회 3중복·인라인 로드를
`td_common`(parse_json·load_json·AXES·iter_facets)으로 통합. confidence 잔여 docstring 제거.

**의도적으로 남긴 것:** `td_index`의 `InMemoryIndex`/`backend` 교체 슬롯 — Standards 축은 "ES 백엔드가
없는데 추상만"이라 speculative로 봤으나, **S4 PRD(#15/#26)가 "검색 백엔드 교체 가능한 얇은 추상"을
명시 요구**한 것(인메모리=개발, ES=운영). 두 축이 갈리는 지점이며 spec이 정당화 → 유지.

## 9. 포인터

- **스테이지별 산출물 포맷(무엇이 어떤 JSON으로 나오나): [[task-discovery-pipeline-reference]]**
- **워크숍 도구(탐색기·매트릭스·투표 서버): [[task-discovery-workshop-tools]]**
- PRD: 이슈 #13(S1) / #14(S2) / #15(S4)
- 티켓: #16~#22(S1) / #23~#25(S2) / #26~#29(S4) — 각 acceptance criteria
- 입력·제약·인프라: `docs/task-discovery-requirements.md`
- 방법론 근거: `docs/task-discovery-deepresearch-{gemini,opus,claude}.md`
- 선행 파일럿(2축·KMeans, 여기서 버린 접근): `feat/task-discovery` 브랜치, `docs/task-discovery-realdata-findings.md`
