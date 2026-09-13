# `nebula-internal-cc-run` 비판적 리뷰

검토 대상: `docs/nebula-internal-cc-run.md`  
검토일: 2026-09-14

## 결론

CC-direct는 **품질 실험이나 소수 표본의 endpoint 대체 경로로는 구조적으로 타당**하다. 기존 파이프라인의 프롬프트·검증·캐시·재개 계약을 그대로 쓰면서 모델 호출만 `AgentClient`의 파일 handoff로 바꾸기 때문이다. 그러나 현재 문서대로 70명 전체를 처리하는 것은 가능하더라도 장시간의 반자동 배치 작업이고, 200명 상시 운영 경로로 보기에는 처리량·컨텍스트·동시 실행 안전성·재현성에 대한 통제가 부족하다.

가장 중요한 판정은 다음과 같다.

- **[치명]** “같은 `--out`은 잠금이 걸려 있어 워커는 늘 한 번에 하나”라는 설명은 코드가 보장하지 않는다. 잠금은 `nebula run` 프로세스 한 번의 수명에만 유지되고 종료 코드 2로 끝날 때 해제된다. 워커 세션 전체를 소유하는 lease가 아니므로, 둘 이상의 워커가 다음 턴을 동시에 처리하는 것을 막지 못한다.
- **[경고]** 워커당 추출 답 30개는 최대 입력 계약에서 컨텍스트 상한을 넘길 수 있다. 24,000자 원문이 tasks/capabilities/links 요청마다 반복되므로 30턴이면 요청 본문만 최대 약 720,000자다.
- **[경고]** 70명은 대략 222~238답, 200명은 628~660답 규모다(4 PJT, 1인 평균 과제 1~3개, 전원 links 호출 가정). 직렬 처리에서는 각각 수 시간, 반나절 이상이 될 수 있다.
- **[참고]** taxonomy가 추출보다 앞서야 한다는 주장은 현재 도메인 계약과 맞지 않는다. taxonomy의 입력은 원문이 아니라 검증된 미래 과제 목록이다. 다만 현재의 “사람별 tasks→capabilities→links를 전부 끝낸 뒤 taxonomy”보다 “전원 tasks→taxonomy”를 먼저 만드는 별도 스케줄은 가능하며, 이는 의미 순서가 아니라 운영 순서 최적화 문제다.

## 검토 범위와 전제

근거는 저장소의 코드·문서·합성 테스트에 한정했다. 실데이터와 실데이터 산출물은 열지 않았다. 저장소에는 내부망 Claude Code의 실제 턴 지연시간 측정치가 없으므로 시간 추정은 아래에 가정을 명시한 시나리오 계산이다.

여기서 먼저 용어를 바로잡을 필요가 있다. 현재 저장소의 기존 endpoint 경로는 “`agent-requests` 파일 기반 워커 루프가 GPT-OSS endpoint를 호출하는 구조”가 아니다.

- endpoint 경로는 `OpenAICompatible.complete()`를 `Store.call()`이 직접 호출한다 (`nebula/storage.py:81-114`, `nebula/__main__.py:59-66`).
- `agent-requests` handoff는 `--agent`에서만 선택되는 `AgentClient` 경로다 (`nebula/llm.py:129-139`, `nebula/storage.py:108-145`).

따라서 정확한 대비는 **직접 HTTP 호출** 대 **파일 handoff를 사람이/CC가 직접 응답**하는 구조다. 두 경로가 공유하는 것은 파이프라인과 검증·캐시이고, 파일 워커 루프 자체는 CC-direct 쪽의 추가 구조다.

## 1. 구조적 타당성: 개선과 위험

### 개선점

#### [참고] 파이프라인 계약을 우회하지 않는다

`--agent`는 임의의 별도 변환기를 만드는 대신 기존 `Store.call()`의 호출 경계에서 멈춘다. 요청 파일에는 `stage`, `instructions`, `input`, `answer_path`가 기록되고, 답은 기존 validator를 통과한 뒤에만 동일 stage cache로 승격된다 (`nebula/storage.py:116-145`). 잘못된 답이 캐시에 들어가지 않는 동작은 `tests/test_nebula_pipeline.py:347-359`가 고정한다.

이는 endpoint 교체가 추출·taxonomy·assign의 데이터 계약을 갈라놓지 않는다는 점에서 좋은 구조다. `tasks`, `capabilities`, `links`의 결과 검증과 정확한 원문 인용 검사는 기존 `model.py`를 그대로 사용한다 (`nebula/model.py:164-181`).

#### [참고] 실패 격리와 재개 단위가 작다

사람별 추출을 세 호출로 나눠 한 단계가 실패해도 앞선 단계의 검증된 캐시를 재사용한다 (`nebula/pipeline.py:49-79`). 불완전한 capabilities 응답 뒤 tasks 캐시를 재사용하는 테스트도 있다 (`tests/test_nebula_pipeline.py:246-265`). endpoint 품질이 불안정할 때와 마찬가지로 CC 답의 형식 오류에도 유효한 장점이다.

#### [참고] endpoint 운영 의존성을 제거한다

내부 OpenAI 호환 서버의 인증, JSON mode 지원, timeout, 408/429/5xx retry 문제를 우회한다. 특히 내부 endpoint가 없거나 GPT-OSS 품질이 목적에 맞지 않을 때 동일 계약으로 다른 내부 모델을 시험할 수 있다. 새 `--out` 사용 지침도 provider가 다른 캐시·누적 corrections를 혼동하지 않게 하는 보수적인 선택이다.

#### [참고] 요청 단위로 필요한 입력이 완결돼 있다

links는 검증된 tasks/capabilities와 ref를 입력으로 받고 (`nebula/pipeline.py:70-77`), taxonomy와 assign도 그 단계가 필요한 전체 payload를 받는다 (`nebula/pipeline.py:246-257`, `314-329`). 따라서 워커가 이전 턴의 기억에 의존하지 않아도 된다는 문서의 핵심 주장은 맞다.

### 위험과 결함

#### [치명] 잠금이 워커 직렬성을 보장한다는 설명이 틀리다

`output_lock()`은 `.run.lock`에 non-blocking `flock`을 잡지만 context가 끝나면 즉시 해제한다 (`nebula/storage.py:46-68`). CLI는 한 번 실행하여 현재 답이 없으면 `AgentTurn`을 던지고 종료 코드 2로 프로세스를 끝낸다 (`nebula/storage.py:136-145`, `nebula/__main__.py:102-104`). 즉 워커가 요청을 읽고 답을 작성하는 긴 구간에는 잠금이 없다.

문서의 메인 오케스트레이터가 오직 하나의 워커만 보내면 절차적으로 직렬화되지만, 그것은 잠금의 효과가 아니다. 운영자 실수나 세션 재시도 때문에 워커 둘이 살아 있으면 둘 다 같은 요청을 읽고 같은 answer 파일을 쓸 수 있다. 한쪽 답이 승격·삭제된 뒤 다른 쪽이 늦게 answer를 다시 만들면 stale 답이 남을 수도 있다.

권고: 문구를 “오케스트레이터는 동시에 한 워커만 활성화한다”로 고치고, 강제하려면 run 전체의 소유권을 나타내는 worker lease/claim을 별도로 구현해야 한다. 현재 `flock`을 근거로 세션 직렬성을 주장하면 안 된다.

#### [경고] 모델 정체성과 재현성이 산출물에 남지 않는다

`AgentClient.cache_identity`는 `{"provider":"agent","version":1}`뿐이다 (`nebula/llm.py:135-136`). 문서도 완료 후 평가 파일에 모델 id를 수동 기입하라고 한다. 모델 버전, Claude Code 설정, 시스템 지침, 워커 프롬프트 버전이 캐시 키에 들어가지 않으므로 서로 다른 CC 모델/설정이 같은 `agent` cache를 재사용한다.

새 `--out`을 지키면 실행 간 혼합은 피하지만, 같은 out에서 모델을 바꾸거나 워커 프롬프트를 고쳐도 자동 무효화가 되지 않는다. HTTP 경로가 client identity에 endpoint와 model을 넣는 설계와 비교하면 provenance와 반복 가능성이 약하다.

권고: 최소한 실행 시작 때 `agent_model_id`, 워커 지침 hash, 운영자 지정 run label을 manifest에 고정하고 cache identity에 포함해야 한다.

#### [경고] 보안 경계가 문서상의 선언에만 의존한다

“사내 호스팅 모델의 내부망 Claude Code” 여부는 코드가 확인하지 않는다. `--agent`는 어느 Claude Code에서도 동일하게 동작하며 요청 파일에 원문을 기록한다. 문서 지정과 사람의 허가가 유일한 gate다. 이는 의도된 운영 예외일 수 있지만, 잘못된 세션에서 실행했을 때 fail-closed가 아니다.

또한 `agent-requests/`와 `cache/`뿐 아니라 최종 `result.json`, review용 파일, HTML에도 민감 정보가 남는다. runbook은 이를 적고 있지만 CC-direct 문서의 자료 경계 목록은 일부 파일만 예로 들어 전체 footprint가 작아 보일 수 있다 (`docs/nebula-internal-runbook.md` §6, §10).

권고: CC-direct 문서에서 “코드가 내부망을 검증하지 않는다”와 전체 민감 산출물 목록을 명시하고, 가능하면 내부 실행 wrapper가 환경 식별자를 검사하도록 한다.

#### [경고] 자동 retry가 사라지고 거부 복구가 사람의 주의력에 의존한다

HTTP 경로에는 제한된 재시도가 있지만 CC-direct는 답 하나마다 프로세스를 다시 실행하고, schema/인용 거부를 워커가 해석하여 직접 수정한다. “같은 호출 3번 거부 시 막힘”은 워커 프롬프트 규칙이지 상태 파일이나 코드가 세는 값이 아니다. 워커가 교체되면 이전 거부 횟수를 안정적으로 이어받을 근거도 없다.

#### [경고] 완료 검사의 `.answer.json` 조건은 유용성이 낮다

수락된 answer는 cache로 옮겨진 뒤 삭제된다 (`nebula/storage.py:131-134`). 반대로 아직 답하지 않은 현재 턴에는 request `.json`만 있고 `.answer.json`은 없다. 따라서 `find ... '*.answer.json'`이 빈 것은 “미답 요청 없음”을 증명하지 않는다. 종료 코드 0과 `status.state == complete`가 실제 완료 근거이며 HTML 세 개는 빌드 완료 근거다. 네 번째 조건은 stale late-write 탐지용이라고 명확히 좁혀 쓰거나 request/cache 일관성 검사로 바꿔야 한다.

## 2. 70명·200명 완주 가능성

### 실제 턴 수 공식

사람 수를 `N`, tasks와 capabilities가 모두 있어 links를 호출하는 사람 수를 `L`, PJT 수를 `P`, PJT `p`의 과제 수를 `T_p`, 기본 batch size를 `B=24`라 하면 corrections가 없는 최대 정상 경로의 답 수는 다음과 같다.

```text
개인 추출 = 2N + L
PJT 분류 = 2 × Σ ceil(T_p / B) + P
전체      = 2N + L + 2 × Σ ceil(T_p / B) + P
```

각 사람은 tasks와 capabilities를 항상 호출하고, 둘 중 하나가 비어 있지 않을 때만 links를 호출한다 (`nebula/pipeline.py:56-78`). 각 PJT는 과제를 batch로 taxonomy 초안화하고, 초안이 있으면 consolidate 1회, 같은 batch 수만큼 assign한다 (`nebula/pipeline.py:246-299`, `314-329`). 그러므로 문서의 “210턴 + PJT별 분류 턴”은 상한 설명으로는 맞지만 분류 턴을 `PJT 수` 정도로 읽으면 크게 과소계상한다.

### 규모별 시나리오

아래는 4 PJT에 과제가 대체로 균등하고, 전원이 links 단계까지 가며, 거부·재작업이 없다는 가정이다.

| 인원 | 1인 평균 과제 | 개인 답 | taxonomy batch | consolidate | assign batch | 총 답 |
|---:|---:|---:|---:|---:|---:|---:|
| 70 | 1 | 210 | 4 | 4 | 4 | 222 |
| 70 | 2 | 210 | 8 | 4 | 8 | 230 |
| 70 | 3 | 210 | 12 | 4 | 12 | 238 |
| 200 | 1 | 600 | 12 | 4 | 12 | 628 |
| 200 | 2 | 600 | 20 | 4 | 20 | 644 |
| 200 | 3 | 600 | 28 | 4 | 28 | 660 |

PJT 분포가 불균등하거나 과제가 0개인 사람이 있으면 값은 달라진다. 특히 links 생략은 1인당 한 턴을 줄인다. 반대로 거부 1회는 답 수정과 재실행을 추가하고, taxonomy corrections나 품질 재검토는 이 표 밖의 작업이다.

### 예상 시간

저장소에는 CC 한 답의 실측 latency가 없다. 그래서 답 작성·파일 작업·두 번의 CLI 실행을 합친 평균을 답당 30초/60초/120초로 둔 단순 범위를 제시한다.

| 규모 | 총 답 범위 | 30초/답 | 60초/답 | 120초/답 |
|---:|---:|---:|---:|---:|
| 70명 | 222~238 | 1.9~2.0시간 | 3.7~4.0시간 | 7.4~7.9시간 |
| 200명 | 628~660 | 5.2~5.5시간 | 10.5~11.0시간 | 20.9~22.0시간 |

이는 순수 처리시간이다. 워커 생성·보고·오케스트레이터 재호출, 거부 수정, 컨텍스트 압축/교체, taxonomy 의미 검토, 최종 review는 포함하지 않았다. 따라서 70명은 전용 세션에서 감시하며 돌리면 “완주 가능”하지만 당일 수 시간 작업이고, 200명은 중단 없는 자동화 없이 한 번에 완주할 운영 방식으로는 현실성이 낮다.

### 병목 1 — [경고] 한 답마다 전체 파이프라인 프로세스를 다시 시작한다

Agent mode는 요청 하나를 만들고 종료 코드 2로 끝난다. answer를 쓴 뒤 같은 명령을 실행해야 그 답을 검증·cache하고 다음 미답 요청에서 다시 종료한다 (`docs/nebula-agent-run.md` §루프). 매번 입력 JSON을 읽고 사람 목록 처음부터 순회하며 앞선 cache를 다시 열고 검증한 뒤 현재 지점에 도달한다 (`nebula/__main__.py:53-87`, `nebula/pipeline.py:177-205`).

작은 데이터에서는 모델 사고 시간이 지배적이겠지만, 수백 턴에서는 프로세스 시작·전체 입력 parse·cache 재검증이 누적된다. 구조상 뒤 턴일수록 도달 전에 읽는 캐시가 늘어난다. 테스트는 수렴과 재개 정확성을 증명하지만 70명/200명 처리량은 측정하지 않는다. 합성 200명 회귀 기준이 있다는 것(`nebula/CLAUDE.md:54-56`)도 agent-loop의 성능 검증은 아니다.

### 병목 2 — [경고] “30답”은 원문 길이가 아니라 답 개수만 제한한다

입력 계약은 1인 원문을 기본 24,000자까지 허용한다 (`docs/nebula-internal-runbook.md` §2). tasks와 capabilities payload에는 같은 원문 전체가 각각 들어가고, links에도 같은 원문과 추출 목록이 다시 들어간다 (`nebula/pipeline.py:55-77`). 따라서 워커가 추출 답 30개를 처리하면 최대 요청 본문 누계는 대략 `30 × 24,000 = 720,000자`이고 instructions·응답·도구 출력은 별도다.

일반적으로 30답은 약 10명의 세 단계에 해당한다. 원문이 평균 3,000자라면 반복 원문만 약 90,000자로 훨씬 작지만, 현재 문서는 실제 원문 길이 분포나 워커 context budget을 보지 않고 30을 고정한다. “뒤쪽 거부가 늘면 줄인다”는 후행 지표라 context overflow나 자동 압축 전에 예방하지 못한다.

권고: 답 개수와 함께 누적 request 문자/토큰 예산을 멈춤 조건으로 둔다. 예를 들어 워커는 각 요청 파일 크기를 합산하고 내부 CC의 유효 context 상한에 맞춰 종료해야 한다. 리허설 2명은 기능만 확인할 뿐 30턴 context 지속성과 70명 throughput을 검증하지 못하므로, 합성 30답 soak test와 200명 resume test가 필요하다.

### 병목 3 — [경고] taxonomy 워커의 3답 제한은 세션 교체를 크게 늘린다

70명·평균 과제 2개·4 PJT 예에서는 분류 답이 20개라 최소 7개 taxonomy 워커 구간이 필요하다. 개인 추출 210답은 30개씩 최소 7구간이므로 전체 최소 약 14개 워커 구간이다. 200명 같은 조건이면 개인 추출 20구간, 분류 44답에 15구간으로 약 35개다.

taxonomy payload는 `existing` registry가 누적되고 consolidate에는 drafts 전체가 들어가므로 (`nebula/pipeline.py:246-290`) 추출 요청보다 판단 밀도가 높다. 3답 제한은 품질 방어로 이해할 수 있으나, 오케스트레이터가 수십 차례 새 워커를 생성해야 하는 현재 수동 프로토콜과 결합하면 운영 병목이 된다.

### 병목 4 — [경고] 의미 품질 검토는 턴 계산 밖에 있다

구조 validator는 인용 존재, ref, 누락 배정 등을 보장하지만 “업무 과제인가”, “역량을 추측했는가”, “과제군이 과잉 통합됐는가”를 보장하지 않는다 (`docs/nebula-internal-runbook.md` §9, §13). 완주 시간만 계산해도 70명이 수 시간인데, 실제 완료 정의에는 review와 승인 화면 검토가 추가된다. CC-direct가 GPT-OSS보다 낫다는 품질 근거도 현재 저장소에는 없다. 합성 2명 리허설은 인터페이스 검증이지 의미 품질 비교가 아니다.

## 3. 파이프라인 순서 검증

### [참고] taxonomy보다 미래 과제 추출이 먼저인 현재 순서는 맞다

도메인 spec은 “각 PJT에서 카테고리 초안을 만들고 정의를 비교해 정리한 뒤 개별 과제를 배정”한다고 규정한다 (`docs/nebula-spec.md:8`). 코드도 모든 사람의 extraction을 검증한 뒤 tasks만 모아 PJT별 `minimal` 목록을 만들고, 그것을 taxonomy 입력으로 쓴다 (`nebula/pipeline.py:177-228`). taxonomy 프롬프트 역시 “한 PJT의 미래 과제 목록”을 입력으로 받는 계약이다 (`nebula/prompts.py:37-49`).

따라서 taxonomy를 첫 단계로 옮기려면 무엇을 분류할지 아직 없다. 원문 전체에서 taxonomy를 먼저 만들면 미래 과제가 아닌 회고·역량·일반 업무까지 범주 근거에 섞이고, “원문이 말하지 않은 방향을 덧붙이지 않는다”는 계약을 약화한다. 고정된 사전 taxonomy를 쓰는 별도 제품 요구가 아니라면 taxonomy 선행은 맞지 않는다.

또한 taxonomy는 tasks의 hash에 묶인다. tasks가 바뀌면 기존 taxonomy correction을 거부하도록 구현돼 있고 (`nebula/pipeline.py:225-243`), 이를 고정하는 회귀 테스트도 있다 (`tests/test_nebula_pipeline.py:482-500`). 이는 taxonomy가 task set의 파생물이라는 강한 코드 근거다.

### [참고] `extracted`는 별도 선행 산출 단계가 아니다

현재 코드의 `extracted`는 사람별 `tasks/capabilities/links` 결과를 모으는 로컬 배열 이름이다 (`nebula/pipeline.py:178-208`). 과거 단일 `extract` 호출을 먼저 만들고 다시 쪼개는 단계가 아니다. cache contract 2도 “extract split into tasks/capabilities/links”로 명시한다 (`nebula/storage.py:82-89`). 문서의 표현은 이 점을 명확히 하면 혼동이 줄어든다.

### [경고] 의미 의존성과 실행 스케줄은 분리해서 검토할 가치가 있다

taxonomy는 tasks에만 의존하며 capabilities와 links에는 의존하지 않는다. 현재 구현은 사람 한 명마다 tasks→capabilities→links를 끝내고, 전원 extraction이 완료된 뒤에야 taxonomy를 시작한다. 따라서 210개 개인 답을 모두 마치기 전에는 첫 taxonomy 품질을 볼 수 없다.

대규모 CC-direct 운영을 중요하게 본다면 다음 DAG 스케줄은 의미 계약을 보존하면서 더 일찍 분류 위험을 발견할 수 있다.

```text
전원 tasks ──→ PJT taxonomy/consolidate ──→ assign
     └──────→ 전원 capabilities ──→ links
```

단, 이는 문서만 바꿔서는 되지 않는다. 현재 `extract_person()`과 사람별 correction template 조립이 세 단계를 한 함수에서 순차 실행하므로 (`nebula/pipeline.py:49-79`, `177-205`) pipeline refactor와 회귀 테스트가 필요하다. 전체 답 수는 줄지 않고, tasks와 capabilities가 같은 원문을 각각 읽는 비용도 그대로다. 장점은 taxonomy 조기 관찰과 단계별 전문 워커 운영이지 호출량 절감이 아니다.

## 권고 우선순위

1. **배포 전 필수:** 잠금 설명을 바로잡고, 오케스트레이터의 단일 active worker 규칙을 명시적으로 운영하거나 worker lease를 구현한다.
2. **70명 실행 전:** 실제 원문 길이 통계는 외부로 노출하지 않은 채 내부에서 워커당 누적 request budget을 산출하고, 30답 고정값을 byte/token 예산 기반으로 바꾼다.
3. **70명 실행 전:** 합성 데이터로 최소 30답 연속 soak test와 70명 전체 dry run을 수행해 답당 중앙값·p90 시간, 거부율, worker 재시작 횟수를 기록한다. 이 수치 없이 완료 예정 시간을 확정하지 않는다.
4. **반복 운영 전:** agent model/config/prompt provenance를 manifest와 cache identity에 넣는다.
5. **200명 확장 전:** 한 답당 프로세스 재시작 구조의 실측 profile을 만들고, 필요하면 장기 실행 coordinator가 handoff queue를 관리하도록 바꾼다. 서로 다른 out으로 PJT 단위 병렬화할 경우 최종 병합 계약이 현재 없으므로 단순 병렬 실행으로 해결됐다고 간주하지 않는다.
6. **선택 개선:** taxonomy를 tasks 직후 관찰할 필요가 크면 pipeline을 dependency DAG로 재구성한다. taxonomy 자체를 원문 추출보다 앞세우지는 않는다.

## 최종 판정

- 70명 일회성 실행: **조건부 가능.** 단일 워커 운영을 사람이 보장하고, context-budget 기반으로 더 자주 끊으며, 수 시간의 실행과 별도 의미 검토 시간을 확보해야 한다.
- 200명 실행: **현재 문서만으로는 운영 경로로 부적합.** 기능적으로 수렴할 수는 있지만 600회 이상의 직렬 답, 수십 번의 워커 교체, provenance와 lease 부재 때문에 중단·혼합·장시간 운영 위험이 크다.
- 파이프라인 순서: **현재의 tasks 선행, taxonomy 후행이 타당.** 개선 대상은 taxonomy의 의미적 선행 여부가 아니라, capabilities/links와 taxonomy 사이의 실행 스케줄 및 조기 품질 피드백이다.
