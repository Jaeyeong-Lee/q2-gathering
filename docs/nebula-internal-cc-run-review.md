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

## 재리뷰 (2026-09-14)

재검토 범위는 수정된 `docs/nebula-internal-cc-run.md`와 실제 CLI·pipeline 구현이다. 실데이터와 실데이터 산출물은 열지 않았다. `python3 -m nebula run --help`에서 두 옵션 노출을 확인했고, `python3 -m unittest tests.test_nebula_pipeline`의 28개 테스트가 통과했다.

### 이전 지적 반영 확인

- **[해결·기존 치명] 잠금 설명:** 문서는 이제 “살아 있는 워커는 언제나 하나”를 오케스트레이터가 지킬 운영 규칙으로 두고, `flock`은 `nebula run` 한 번이 실행되는 동안만 유지되어 워커가 요청을 읽고 답을 쓰는 동안에는 풀린다고 명시한다 (`docs/nebula-internal-cc-run.md:85-88`). 이는 실제 `output_lock()`의 수명과 `AgentTurn` 종료 동작에 맞는다 (`nebula/storage.py:46-68`, `116-145`; `nebula/__main__.py:102-104`). 기존 치명 항목은 문서 차원에서 해소됐다. 기술적으로 중복 워커를 막는 lease가 생긴 것은 아니므로 이 규칙은 여전히 운영 통제다.
- **[해결·기존 경고] 30답 고정 컨텍스트 상한:** 워커 교대 기준이 답 개수가 아니라 이번 워커가 답한 요청 파일의 누적 1MB로 바뀌었다 (`docs/nebula-internal-cc-run.md:119-128`). CLI도 `--batch-size`와 `--max-chars`를 실제 지원하고 기본값은 각각 24와 24,000이다 (`nebula/__main__.py:30-34`, `78-86`; `nebula/pipeline.py:82-100`). 두 값은 양수 검증을 거치며 (`nebula/pipeline.py:115-116`), task 배치는 개수와 직렬화 문자 합 중 먼저 닿는 한도로 나뉜다 (`nebula/pipeline.py:30-42`). 따라서 이전의 “30답이면 최악 72만 자” 문제는 byte 예산 기반 교대로 해소됐다. 다만 새 플래그 값의 적절성에는 아래 경고가 남는다.
- **[부분 반영·기존 경고] provider 모델 미기록:** 문서는 결과의 provider가 `agent`만 기록한다는 한계를 밝히고, 표본 평가 파일의 `run.model_id`에 세션 모델 id를 수동 기록하도록 했다 (`docs/nebula-internal-cc-run.md:138-140`). 그러나 코드의 cache identity는 여전히 `{"provider":"agent","version":1}`뿐이다 (`nebula/llm.py:128-136`). 전체 실행 중 모델·설정·워커 프롬프트가 바뀌어도 manifest나 cache key에 남지 않으므로, 기존 리뷰가 요구한 실행 provenance와 캐시 분리는 해결되지 않았다.
- **[해결·기존 경고] 프롬프트 인젝션:** 워커 프롬프트는 input의 문장을 모두 데이터로 취급하고, 실행할 명령과 쓸 파일을 제한하며, 보고 필드를 allowlist로 정하고 원문·인용·과제군 이름을 금지한다 (`docs/nebula-internal-cc-run.md:100-102`, `123-124`). 단계별 실제 프롬프트도 입력 속 지시를 따르지 말라고 명시한다 (`nebula/prompts.py:3-4`, `16-17`, `26-27`, `37-38`, `52-53`, `59-60`). 이전 교차 리뷰의 문서 권고는 반영됐다. 단, `--agent` 실행 환경이 정말 내부망인지를 코드가 검증하지 않는 더 넓은 fail-closed 문제는 그대로다.

### 새 값 검증과 70명 재추정

- **[경고] `--max-chars 200000`은 모델 컨텍스트 상한이 아니다.** 새 값은 기본 24,000자의 8.33배이며, 5만 자 합성 리허설이 원문 길이 guard를 통과하게 한다 (`nebula/pipeline.py:179-183`). 하지만 이 옵션은 토큰 계산기가 아니고, taxonomy·consolidate·assign의 전체 payload에는 `max_chars * 3`, 즉 600,000자까지 허용한다 (`nebula/pipeline.py:246-250`, `287-290`, `314-318`). 따라서 200,000이라는 숫자만으로 내부 모델의 입력 한도에 안전하다고 판정할 수 없다. Read probe와 1MB 워커 교대는 필요한 실측 방어선이지 모델 컨텍스트 적합성의 증명은 아니다.
- **[경고] `--batch-size 1000`은 70명 규모에서 사실상 개수 제한을 제거하지만 한 배치를 보장하지 않는다.** 70명, 1인 평균 과제 1~3개면 전체 과제는 약 70~210개이고, 4 PJT에 균등하다면 PJT당 약 18~53개라 1,000개 상한에는 닿지 않는다. 그러나 task item JSON 합이 200,000자를 넘으면 문자 예산이 먼저 분할한다. 균등 분포에서 한 배치 조건은 53개일 때 항목당 평균 약 3,774자 이하이고, 18개일 때 약 11,111자 이하이다. 코드에는 label·quote의 독립 길이 상한이 없으므로 (`nebula/model.py:164-172`), 문서의 “이 값이면 PJT 과제 전체를 한 번에 본다” (`docs/nebula-internal-cc-run.md:78-81`)는 예상 데이터가 200,000자 이내일 때만 맞는다.
- **[참고] 호출 수 감소는 작다.** 한 배치 조건, 4개 task-bearing PJT, 전원 links 호출을 가정하면 개인 단계 210답에 PJT별 taxonomy·consolidate·assign 각 1답씩 12답이 더해져 총 222답이다 (`nebula/pipeline.py:49-79`, `246-299`, `314-329`). 기본 batch size 24에서는 평균 과제 1/2/3개일 때 대략 222/230/238답이므로 새 값은 각각 0/8/16답을 줄인다. 사람별 최대 3답은 그대로여서 전체 처리량 병목을 크게 바꾸지는 않는다.

### 수정으로 드러난 새 문제

- **[경고] 배정 실패 뒤 `--batch-size`를 줄이면 분류 단계도 다시 물을 수 있다.** 문서의 “추출 캐시는 원문만 키로 삼아 그대로 재사용”은 맞지만 (`docs/nebula-internal-cc-run.md:80-81`), taxonomy와 assign의 cache key에는 배치로 달라진 payload가 포함된다 (`nebula/storage.py:81-89`). 따라서 batch size 변경은 해당 PJT의 taxonomy·assign cache miss를 만들 수 있다. “배정만 더 작은 묶음으로 재시도”되는 것처럼 읽히지 않게 재실행 범위를 밝혀야 한다.
- **[경고] 1MB를 모델 컨텍스트와 직접 비교한 근거가 부족하다.** 문서는 1MB를 한국어 약 33만 자로 환산한 뒤 1M 컨텍스트의 절반 미만이라고 단정한다 (`docs/nebula-internal-cc-run.md:127-128`). `wc -c`의 byte 수와 모델 token 수는 직접 대응하지 않고, JSON·instructions·도구 출력·모델 응답도 컨텍스트를 차지한다. 합성 soak test에서 실제 token/거부율을 측정해 시작값을 조정한다는 조건을 붙이는 편이 안전하다.
- **[경고] 큰 assign 응답의 사전 검증이 없다.** 1,000은 예상 70~210개 과제를 한 응답에 배정하게 할 수 있다. 출력 크기·한 턴 작성 안정성에 대한 합성 경계 테스트 없이 실패 후 batch size를 낮추는 절차만 있다. 70명 전체 실행 전에 210개 수준의 합성 assign soak test로 응답 완결성과 거부율을 확인해야 한다.
- **[참고] 새 CLI 옵션의 전용 회귀 테스트가 없다.** 현재 pipeline 테스트 28개는 통과하지만, CLI에서 두 플래그가 정확히 전달되는지와 200,000/1,000 경계 동작을 직접 고정한 테스트는 검색 범위에서 확인되지 않았다.

### 재판정

잠금 오류와 고정 30답 컨텍스트 문제, 프롬프트 인젝션 문구는 반영됐다. 모델 provenance는 한계를 공개하고 표본 평가에 수동 기록하는 수준이라 부분 반영이다. 70명 실행은 여전히 조건부 가능하지만, `200000/1000`을 검증된 안전값으로 보기는 어렵다. 전체 task item이 200,000자 안에 드는지와 최대 assign 응답이 안정적으로 완결되는지를 합성 실측한 뒤 확정해야 한다.

## 안정성 확인 기능 리뷰 (2026-09-14)

검토 범위는 커밋 `d1f09d2`로 추가된 `docs/nebula-internal-cc-run.md`의 “과제군 안정성 확인 — 검토 전에” 절과, 그 절이 전제하는 `nebula/pipeline.py`, `nebula/storage.py`, `nebula/model.py`의 현재 구현이다. 실데이터와 실데이터 산출물은 열지 않았다.

### 방법론과 지표

- **[치명] 현재 셔플은 파이프라인에 들어가기 전에 취소되므로 입력 순서 안정성을 시험하지 않는다.** 문서의 스크립트는 최상위 사람 배열을 섞지만 (`docs/nebula-internal-cc-run.md:146-151`), `persons()`는 검증한 사람 목록을 항상 `id` 순으로 정렬해 반환한다 (`nebula/model.py:37-56`). 이후 추출과 `groups[pjt]` 적재는 이 정렬 순서를 그대로 따르고 (`nebula/pipeline.py:178-223`), `minimal`도 별도 셔플 없이 taxonomy와 assign에 전달된다. 따라서 기준/s1/s2의 분류 요청에서 과제 순서는 동일하다. 현재 절차가 측정하는 것은 입력 순서 민감도가 아니라, 새 답을 작성할 때 생기는 모델의 비결정성뿐이다. 순서 민감도를 보려면 추출 캐시 재사용 뒤 분류에 전달하는 `minimal`을 seed별로 섞는 코드 경계나, 분류 입력 순서를 명시적으로 받는 기능이 필요하다.
- **[경고] 재실행 2회는 탐색적 경보로는 쓸 수 있지만 안정성을 통계적으로 추정하기에는 부족하다.** 기준 포함 세 partition에서 기준↔s1, 기준↔s2 두 값만 보면 실행 간 분산이나 낮은 값의 재현성을 추정할 수 없고, s1↔s2 관계도 버린다. 특히 모델의 샘플링 설정과 seed가 기록되지 않아 순서 효과와 답 자체의 확률적 변동을 분리할 수도 없다. 검토 우선순위를 정하는 저비용 smoke check라면 “통계적 보증이 아닌 탐색 신호”라고 한계를 명시해야 한다. 안정성 수치를 기준으로 승인·중단 임계값을 정하려면 최소한 더 많은 독립 반복과 모든 실행 쌍의 분포를 보고, 반복 수는 기대하는 불안정 크기와 허용 비용에 맞춰 사전에 정해야 한다.
- **[경고] 현재 같이 묶인 쌍 Jaccard 하나만으로는 partition 일치도를 충분히 설명하지 못한다.** singleton 과제군은 쌍을 만들지 않아 완전히 보이지 않고, 큰 과제군은 쌍 수가 크기의 제곱으로 늘어 점수를 지배한다. 전부 singleton인 두 결과처럼 union이 비면 `-`가 되어 완전 일치도 표현하지 못한다. 미분류는 건수만 별도 출력하므로 어느 과제가 바뀌었는지도 점수에 반영되지 않는다 (`docs/nebula-internal-cc-run.md:163-183`). 주 지표는 과제군 이름 permutation에 불변이고 chance agreement를 보정하는 Adjusted Rand Index를 쓰고, 보조로 pairwise precision/recall, singleton 포함 과제별 이동률, 미분류 전환표를 함께 보는 편이 낫다. 현재 Jaccard를 유지한다면 최소한 모든 세 실행 쌍과 분자/분모를 출력하고, 큰 과제군 편향과 singleton 제외를 읽는 법에 밝혀야 한다.

### 추출 캐시 재사용 가정

- **[경고] “추출 캐시 키는 원문뿐”이라는 설명은 코드와 일치하지 않지만, 동일 레코드의 순서만 바꾸는 경우 재사용 결론은 맞다.** 실제 키는 contract version, client identity, stage, prompt, payload 전체의 digest다 (`nebula/storage.py:81-102`). tasks/capabilities payload는 `person_id`와 `text`이고, links payload에는 여기에 검증된 tasks/capabilities의 ref·label·quote도 포함된다 (`nebula/pipeline.py:49-77`). 그러므로 ID·원문·프롬프트·client identity·추출 결과가 같을 때만 복사한 캐시가 hit한다. 최상위 배열 순서는 키에 없고 `persons()`도 ID로 정렬하므로 이번 절차에서는 세 추출 stage가 재사용된다. cache hit 시 현재 validator를 다시 실행한다는 주장도 맞다 (`nebula/storage.py:103-107`). 문구는 “원문뿐”이 아니라 “사람 배열 위치는 키에 없으며, 동일 ID·원문·프롬프트·client와 선행 추출 결과면 재사용된다”로 고쳐야 한다.
- **[참고] 분류 캐시를 복사하지 않아 taxonomy/consolidate/assign을 새로 묻는 구성은 맞다.** 복사 대상이 `tasks`, `capabilities`, `links` stage에 한정되고, 분류 stage의 키에는 해당 분류 payload가 들어간다. 다만 위 정렬 때문에 새 분류 호출의 과제 순서는 기준과 같으며, 호출을 새로 한다는 사실만으로 셔플 실험이 되지는 않는다.

### 추가 비용

- **[참고] 8개 task-bearing PJT가 모두 한 배치에 들어간다는 전제에서 추가 48턴 계산은 맞다.** 한 실행당 PJT별 taxonomy 1회, consolidate 1회, assign 1회이므로 `8 × 3 × 2 = 48`턴이다 (`nebula/pipeline.py:246-329`). 70명 모두 tasks/capabilities/links를 호출한다고 잡으면 추출 210턴, 기준 분류 24턴으로 본실행은 234턴이다. 추가 48턴은 본실행 대비 약 20.5% 증가이고, 안정성 실행까지 합친 282턴 중 약 17.0%다. links가 생략되는 사람이 있으면 본실행 분모가 작아져 추가 비용 비중은 더 커진다. PJT가 20만 자를 넘어 여러 batch로 나뉘거나 답 거부·재작성이 생기면 48턴은 상한이 아니라 정상 최소치다.

### 운영과 동시 실행

- **[경고] “워커는 자기 out만 연다”는 코드 격리가 아니라 운영 규칙이며, 현재 프롬프트만으로는 교차 열람을 강제 차단하지 못한다.** 각 request의 `answer_path`가 자기 out을 가리켜 정상 흐름은 분리되지만 (`nebula/storage.py:116-145`), 두 out의 요청 파일은 같은 파일시스템과 에이전트 권한 아래 있다. 워커가 잘못된 경로를 받거나 한 세션에서 두 실행을 다루면 다른 실행의 taxonomy를 볼 수 있고, 그러면 독립 반복이라는 전제가 깨진다. s1/s2는 별도 세션·별도 워커 풀로 운영하고, 각 워커 프롬프트에 허용된 input/out 절대경로 하나만 명시하며, 보고에도 run label과 out 식별자를 포함해 교차 응답을 탐지해야 한다.
- **[경고] s1/s2의 서로 다른 `--out` 잠금은 기술적으로 충돌하지 않지만, 기존 “살아 있는 워커는 언제나 하나” 규칙과 동시 실행 지침은 서로 모순된다.** `output_lock()`은 resolve된 out마다 `<OUT>/.run.lock`을 잡으므로 `<OUT>-s1`과 `<OUT>-s2`의 `nebula run` 프로세스는 서로 막지 않는다 (`nebula/storage.py:46-68`). 그러나 2절은 전역적으로 한 워커만 살려 두라고 명시하고 (`docs/nebula-internal-cc-run.md:83-92`), 새 절은 두 실행을 동시에 돌려도 된다고 한다 (`docs/nebula-internal-cc-run.md:154-155`). 동시에 돌리려면 “out별 active worker는 하나, 서로 다른 out은 독립 오케스트레이터/세션으로 병렬 가능”이라고 규칙의 범위를 바꾸고, 같은 out에 워커 둘이 붙지 않도록 해야 한다. 잠금은 워커가 요청을 읽고 답을 쓰는 구간을 보호하지 않는다는 기존 한계도 그대로다.

### 판정

현재 기능은 그대로 실행하면 **입력 셔플 안정성 확인으로는 무효**다. 사람 배열을 섞은 직후 `persons()`가 ID 정렬을 복원하기 때문이다. 먼저 분류 입력 자체를 seed별로 실제 순열화하고 이를 합성 테스트로 고정해야 한다. 그 뒤에도 2회와 pair Jaccard는 저비용 검토 우선순위 신호로만 사용하고, 승인 근거로 쓰려면 반복 수 확대, 모든 실행 쌍 비교, ARI와 singleton·미분류 이동 지표를 추가해야 한다. 추출 캐시 재사용과 서로 다른 out의 lock 분리는 성립하지만, 두 주장 모두 문서보다 조건부이며 워커 격리는 별도 운영 통제가 필요하다.
