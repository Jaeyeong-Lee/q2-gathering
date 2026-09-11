# 내부 표본 품질 평가 — GPT-OSS 120B

티켓 #47의 사람 평가 계약이다. 내부 운영자가 변경 전후에 동일한 표본을 확인할 때 사용한다. 파이프라인 실행·정정 방법은 [내부 실행 가이드](nebula-internal-runbook.md)를 따른다. 평가 기록은 모델 입력이나 발표 승인 파일이 아니며 파이프라인이 자동으로 읽지 않는다. 자동 비교 리포트는 #52에서 이 형식을 사용한다.

## 표본 선정과 기준선 보관

1. 내부에서 PJT마다 2~3명을 고른다. 가능하면 제목·불릿 양식 준수 1명, 자유 서술 1명, 과제 무신호 또는 희소 과제 1명을 포함한다. 인원이 부족하면 전원을 고르고 이유를 기록한다. 성공한 추출 결과만 보고 고르지 않는다.
2. 원본 입력을 고정하고 표본의 person_id, PJT, 선정 이유를 manifest에 기록한다. person_id는 파이프라인 입력과 동일한 문자열 ID이며 이름으로 매칭하지 않는다. 비교 중 표본을 바꾸면 새 sample_set_id를 사용한다.
3. 입력 text를 바꾸지 않고 기존 파이프라인을 실행한다. 결과의 run_id, schema_version, 실제 모델 식별자, 코드 커밋을 기록한다. 입력 내용 해시는 기존 nebula.model.digest(text) 규칙(SHA-256, JSON ensure_ascii=False, sort_keys=True, separators=(",", ":"))을 사용한다. 원문은 평가 JSON에 복사하지 않는다.
4. 각 사람의 원문 전체를 먼저 읽어 기대 과제·역량을 확인하고 결과와 대조한다. 과제 0개인 사람도 평가한다. 아래 여섯 항목을 독립 판정한다.
5. 기준선 평가 파일을 내부 실행 출력 폴더의 별도 quality 하위 폴더에 보관한다. 평가 수정은 assessment_id를 새로 부여하고 이전 파일을 보존한다. 후속 실행도 같은 manifest와 원문 해시를 사용하되 run_id와 모델·계약 정보를 새로 기록한다.

표본은 실패 형태를 살펴보기 위한 의도적 소수 표본이다. 전체 부서의 오류율이나 모델 정확도를 추정하지 않는다. 실명, PJT명, 원문, 인용, 과제군명, 모델 응답, 평가 메모 및 해시는 모두 내부에 보관하며 저장소·외부 로그·스크린샷으로 전달하지 않는다. 익명 ID로 바꾸었다고 안전한 파일이 되는 것은 아니다.

## 공통 판정

| status | 의미 | findings |
|---|---|---|
| not_evaluated | 아직 확인하지 않았거나 실행 실패로 평가 불가 | 빈 배열. 평가 불가 이유는 note에 기록 |
| pass | 적용 가능한 항목을 확인했고 아래 기준상 오류를 찾지 못함 | 빈 배열 |
| fail | 하나 이상의 구체적 오류를 확인함 | 최소 한 건 |
| not_applicable | 확인했으나 평가 대상 자체가 없음 | 빈 배열. note에 이유 필수 |

pass는 표본에서 오류를 발견하지 못했다는 뜻이며 모델 품질 보증이 아니다. 시간 표현이 없으면 unknown 보존 여부를 평가할 수 있으므로 time_evidence는 pass 또는 fail이다. 과제와 역량이 모두 없는 경우 link_accuracy는 not_applicable로 쓸 수 있다. 항목 일부만 확인했다면 not_evaluated를 유지한다.

## 여섯 평가 항목

| 키 | 확인할 것 | 합성 실패 예시 / 통과 기준 |
|---|---|---|
| task_omission | 원문에 적힌 미래 업무가 빠졌는가 | ‘검증 절차를 자동화하겠다’가 과제에 없으면 fail. ‘열심히 하겠다’만 있는 글에서 과제 0개는 pass |
| task_invention | 원문에 없는 대상·행동·목표를 추가했는가 | ‘로그를 정리하겠다’를 ‘AI 예측 플랫폼 구축’으로 바꾸면 fail. 표현을 충실하게 줄였으면 pass |
| time_evidence | 시간 표현·범위가 과제에 연결되고 안전하게 표시되는가 | ‘단기 목표’ 아래 불릿의 근거를 누락하면 fail. 별도 기준 없는 ‘하반기’를 보존하고 unknown으로 두면 pass. ‘중장기’를 장기로 단정하면 fail |
| capability_omission | 보유 경험과 필요 역량을 각각 보존했는가 | 다른 섹션의 ‘로그 분석 경험 보유’를 링크가 없다는 이유로 버리면 fail. 글에 없는 역량을 요구하지 않음 |
| link_accuracy | 직접 연결을 놓치거나 근거 없이 연결했는가 | ‘이 경험을 활용해’라는 명시적 연결 누락은 fail. 단순 공존을 확정 연결로 처리하면 fail. 후보를 후보로 보존하면 pass |
| task_group_fit | 같은 PJT 안에서 원문 변화 방향을 충실히 묶는가 | 구체적 자동화 과제를 ‘데이터’라는 분야명으로만 묶거나 무관한 대상을 합치면 fail. 희소 과제의 적절한 미분류는 pass. 근거 있는 한국어 이름과 약어 보존도 확인 |

시간 평가의 목표는 미명시 비율을 무조건 낮추는 것이 아니다. 기준선에서 제목 시간 누락처럼 구 계약상 예상된 결과도 목표 동작에 비춰 fail로 기록하되 note에 구 계약 한계를 적는다. 모델 잘못과 계약 한계를 이 기록만으로 단정하지 않는다. 후보 연결 기능이 없는 기준선에서 후보가 없다는 것만으로 link_accuracy를 fail로 만들지 않는다.

## 교환 형식 v1

[빈 양식](nebula-quality-template.json)을 내부 폴더에 복사해 작성한다. null은 미입력 표시이며, 평가 시작 전에 식별자와 manifest를 채워야 한다. criteria 객체 여섯 개를 사람마다 복제한다. 완성 기록의 계약은 다음과 같다.

- format_version은 1, rubric_version은 "future-task-quality-v1"이다. 평가 기준을 바꾸면 rubric_version을 올리고 서로 다른 기준의 점수를 직접 비교하지 않는다.
- assessment_id, sample_set_id는 내부에서 부여한 비어 있지 않은 고유 문자열이다. assessed_at은 ISO 8601 시간대 포함 시각, evaluator_id는 내부 평가자 식별자다.
- run은 run_id, result_schema_version, model_id, code_commit, state를 가진다. state는 complete 또는 failed이다. 실패 실행은 run_id와 result_schema_version이 없으면 null로 두고 모든 평가를 not_evaluated로 둔다. 실행 성공률은 이 수동 평가 파일에서 추정하지 않는다.
- manifest는 person_id, pjt, source_hash, selection_reason을 가진 배열이다. ID는 중복 없이 입력 ID와 일치해야 한다. source_hash는 위 해시 규칙의 64자리 소문자 16진수다.
- evaluations는 manifest의 각 사람에 대해 정확히 한 행이며 person_id, criteria를 가진다. criteria는 위 여섯 키를 모두 가진다. 각 항목은 status, note(문자열), findings(배열)를 가진다.
- finding은 target_type(source/task/capability/link/category), target_id(결과에 있으면 문자열, 없으면 null), source_span, observation을 가진다. source_span은 원문 text의 0부터 시작하는 유니코드 코드포인트 오프셋 [start, end) 또는 null이다. 원문 누락은 source와 span으로 표시한다. 결과 ID가 없는 누락에 가짜 ID를 만들지 않는다. link의 target_id는 null로 두고 observation에 두 결과 ID를 기록한다.
- observation은 관찰된 오류를 적는다. source_span이 있으면 해당 원문 길이를 넘지 않아야 한다. category처럼 단일 원문 구간으로 특정할 수 없으면 null을 쓰고 관찰 근거를 내부 note에 적는다.

후속 비교는 sample_set_id뿐 아니라 person_id 집합, PJT, 각 source_hash, rubric_version을 확인해야 한다. 변경된 원문·표본·기준은 직접 비교 불가로 표시한다. not_evaluated와 not_applicable을 pass로 세지 않는다. 평가별 분모를 함께 표시하고 소수 표본을 전사 지표로 확대하지 않는다.

## 합성으로 한 번 따라 하기

다음 두 사람은 가상이며 같은 가상 PJT의 최소 표본이다. 아래 결과는 사람이 만든 실패 예시이고 실제 모델 실행 결과가 아니다.

| person_id | text | 선정 이유 | 가상 결과 |
|---|---|---|---|
| S01 | 단기 목표\n검증 절차 자동화\n보유 역량\n로그 분석 경험 | 제목·불릿 양식 | 과제 ‘검증 절차 자동화’, 시간 unknown, 역량 없음, 연결 없음, 과제군 ‘자동화’ |
| S02 | 앞으로도 열심히 하겠습니다. | 무신호 | 과제·역량·연결·과제군 없음 |

S01은 과제 누락·창작 pass, 제목의 시간 근거 누락과 역량 누락 fail이다. 연결을 명시하지 않았으므로 link_accuracy는 pass이며 링크를 강제로 요구하지 않는다. 과제군은 대상과 변화가 충분히 드러나지 않아 task_group_fit fail로 기록한다. S02는 과제 누락·창작·시간·역량 항목 pass, 링크·과제군 항목 not_applicable이다.

작성 순서: 두 사람을 manifest에 등록 → 원문 해시 기록 → 내부 run 정보를 기록 → 처음에는 모든 항목 not_evaluated → 원문과 결과 대조 후 위 판정과 findings 입력 → 대상 ID·span·필수 항목 확인 → 기준선 파일 보존. 합성 연습에서는 run.model_id를 "synthetic-manual", run.run_id를 "synthetic-baseline"으로 기록해 실제 GPT-OSS 실행과 구분한다.

[작성된 합성 평가 기록](nebula-quality-example.json)은 위 두 사람의 해시·판정·오류 위치까지 채운 예시다. 예시 시각과 실행 식별자는 가상 값이다.

검증 완료의 범위는 평가 양식과 절차가 작성 가능하다는 것까지다. 실제 GPT-OSS 120B의 의미 품질은 내부 운영자가 실제 표본에 대해 이 절차를 수행한 뒤에만 판단한다.
