# 내부망 마이그레이션 지시서 (2026-08-06)

> **대상**: 내부망 리포에 `feat/task-discovery-coldstart` 최신본을 반영하는 사람/에이전트.
> 커밋 범위는 `e1eb678`~`f66a78e` (11개). 태그 `td-s1-8-complete`가 그 중간 지점이다.
>
> 이 문서는 **한 번 쓰고 버리는 문서**다. 반영이 끝나면 상시 참고는
> `docs/task-discovery-internal-run-guide.md`로 옮겨간다.

---

## 0. 왜 이 마이그레이션이 필요한가

내부망에서 파이프라인을 돌리면 LLM 호출 하나가 실패할 때 **그 스테이지의 진행분이 통째로
사라졌다.** 그래서 매번 임시 py 스크립트로 작업을 쪼개 손으로 돌리고 있었다. 원인은 셋:

1. JSON 파싱 실패가 재시도 루프 **밖**에 있어 재시도조차 안 됨
2. `td_extract`를 뺀 스테이지에 예외 처리가 아예 없음
3. 저장이 루프 종료 후 1회뿐이라 부분 실패 = 전체 손실

여기에 "20kb 넘으면 깨진다"던 증상의 정체도 밝혀졌다 — **응답 쪽 한도였고, 범인은
`td_taxonomy`가 배치마다 `relations` 필드까지 요구한 것**이었다.

이번 반영으로 전부 해결됐고, 추가로 **에이전트별 데이터 접근 경계**가 코드와 문서에 들어갔다.

---

## 1. 반영 순서

### 1-1. 코드 가져오기

```bash
git fetch origin
git log --oneline HEAD..origin/feat/task-discovery-coldstart   # 11개 확인
git merge origin/feat/task-discovery-coldstart                 # 또는 rebase
```

충돌이 나면 `scripts/td_*.py`는 **원격 것을 택해라.** 내부망에서 임시로 손댄 게 있으면
그건 이번 변경이 대체하는 것들이다(재개·로깅 관련).

### 1-2. 테스트로 검증

```bash
python3 -m pytest tests/ -q      # 185개 전부 통과해야 함 (약 4분)
```

네트워크 없이 도는 테스트다. 여기서 실패하면 LLM 설정 문제가 아니라 코드 반영 문제다.

### 1-3. env 설정 (**바뀐 게 있다**)

```bash
export TEXT_PROVIDER=internal
export TEXT_API_KEY=<사내 키>
export TEXT_API_BASE=<사내 OpenAI호환 URL>
export TD_TEXT_MODEL=<사내 텍스트 모델 id>

export TD_OUT_DIR=/secure/run          # ★ 신규 — 아래 §3 참고

# S4(검색)까지 갈 때만
export EMBED_PROVIDER=internal
export EMBED_API_BASE=<BGE-M3 URL>
export TD_EMBED_MODEL=<임베딩 모델 id>
```

### 1-4. 기존 산출물 처리 (**여기가 제일 주의**)

**`taxonomy.json`·`assignments.json`이 이미 있으면 "미완성"으로 판정된다.** 완료 판정이
"파일 존재"에서 "진행 사이드카의 `done == total`"로 바뀌었고, 기존 파일엔 사이드카가 없다.

→ `make td`를 돌리면 taxonomy·assign이 **다시 실행된다.**

**권장: 그냥 재실행해라.** 이제 중간에 죽어도 잃는 게 없고, 기존 `taxonomy.json`은 어차피
`relations` 프로토콜이 바뀌기 전 것이라 다시 만드는 게 맞다.

`extracted.json`은 **지우지 마라.** 추출은 재사용한다(가장 비싼 단계).

> 정말 기존 taxonomy를 살려야겠다면 사이드카를 손으로 만들 수 있다 —
> `internal-run-guide.md` §6.3에 스크립트가 있다. 단 그 taxonomy엔 `relations`가
> 없거나 옛 방식으로 만들어진 것이라 온톨로지 뷰가 비어 있게 된다.

---

## 2. LLM 호출에 대한 지시 (**반영 후 달라지는 것**)

### 2-1. 모델 지정이 일원화됐다

이전엔 `td_pipeline.py`만 `TD_TEXT_MODEL`을 읽어서, 스테이지를 단독 실행하면 사내
엔드포인트에 gemini 모델명(`models/gemini-2.5-flash`)이 그대로 넘어가 즉시 깨졌다.

지금은 `llm.text_call()` / `llm.embed_call()`이 그 로직을 갖고 있고 **모든 진입점이 이걸
쓴다.** 그래서 아래가 전부 정상 동작한다:

```bash
python3 scripts/td_extract.py   <persons.json 경로>
python3 scripts/td_taxonomy.py  $TD_OUT_DIR/extracted.json
python3 scripts/td_assign.py    $TD_OUT_DIR/extracted.json $TD_OUT_DIR/taxonomy.json
python3 scripts/td_narrate.py   $TD_OUT_DIR
python3 scripts/td_index.py     $TD_OUT_DIR/extracted.json   # TD_EMBED_MODEL 사용
python3 scripts/td_digest.py    $TD_OUT_DIR/extracted.json   # TD_EMBED_MODEL 사용
```

**새 스크립트를 만들어 LLM을 부를 일이 생기면 반드시 `llm.text_call()`/`llm.embed_call()`을
써라.** `llm.call_gemini`/`llm.embed_text`를 맨몸으로 부르면 같은 버그가 재발한다.

### 2-2. 재시도 계층은 하나뿐이다 — 늘리지 마라

```
llm.py 의 max_retries (SDK 레벨, 429 백오프)
  └─ td_common.retry_call  ← 여기가 유일한 애플리케이션 재시도
       └─ td_common.retry_json  ← 파싱까지 감싼 것 (신규)
```

스테이지 코드에 `for attempt in range(...)`를 새로 만들거나, langchain 같은 프레임워크를
넣지 마라. 이미 두 겹이라 한 겹 더 얹으면 **실패 한 건이 수십 콜로 증폭된다.**

LLM을 부르는 새 코드는 이 형태를 따라라:

```python
from td_common import retry_json
parsed = retry_json(call, prompt, stage="<스테이지명>", call_id=<순번>)
```

`stage`/`call_id`는 로깅과 콜 덤프 파일명에 쓰인다. 빼먹으면 어느 호출이 실패했는지 추적이
안 된다.

### 2-3. 프롬프트를 고칠 땐 응답 크기를 생각해라

`relations` 사고의 교훈이다. **매 호출마다 다시 뱉을 필요가 없는 필드를 요구하지 마라.**

- taxonomy 배치 루프: 카테고리를 누적해서 전체를 주고받는다 → 응답이 카테고리 수에 비례
- 여기에 `relations`(전체 구조에 대한 속성)까지 얹으니 응답이 1.5~1.7배가 되어 20kb 초과
- 해결: 배치는 `name`/`definition`/`inclusion_criteria`만, `relations`는 **배치가 다 끝난 뒤
  1콜**로 엣지 리스트만 받는다 (`derive_relations`)

크기 실측(카테고리 25개 기준): 배치 응답 13.1kb → **7.9kb**.

프롬프트 스키마에 필드를 추가할 일이 생기면, 그게 **호출마다 반복 생성될 필요가 있는지** 먼저
따져라. 아니라면 마지막에 한 번 뽑는 별도 패스로 빼라.

### 2-4. 로그·예외에 원문을 다시 넣지 마라

디버깅 편의로 응답 원문을 로그에 찍고 싶어질 때가 있다. **그러면 데이터 경계가 무너진다.**

콘솔·예외 메시지는 실명 대신 `seq=`/`id=`, 응답 원문 대신 바이트 수만 낸다. 원문은
`$TD_OUT_DIR` 안의 콜 덤프와 ECS 로그에만 있고, 그건 opencode와 사람만 본다.

관련 코드: `td_common.parse_json`(길이만), `td_extract`(추출 폐기 시 id만),
`normalize_person_text`·`merge_persons`·`split_md_by_person`(전부 `seq`만).

---

## 3. `TD_OUT_DIR` — 신규 env

로그·콜덤프가 리포 안에 하드코딩돼 있던 걸 밖으로 뺄 수 있게 했다.

```bash
export TD_OUT_DIR=/secure/run
python3 scripts/td_pipeline.py /secure/run --sources /secure/persons.json
```

| 산출물 | 위치 |
|---|---|
| extracted / taxonomy / assignments / aggregates | `$TD_OUT_DIR/` |
| workshop-input.md, interpretation/ | `$TD_OUT_DIR/` |
| pipeline.log, pipeline.ecs.jsonl | `$TD_OUT_DIR/` |
| 콜 덤프 (프롬프트 원문) | `$TD_OUT_DIR/task_discovery/calls/` |

**미설정 시 기존 경로(`<리포>/data/`) 그대로** 동작하므로, 로컬 합성 데이터 개발엔 아무것도
안 해도 된다.

### 디스크 용량을 확인해라

콜 덤프는 **모든** 호출을 남긴다. 200명 기준 약 2,100개 파일이고, taxonomy 프롬프트가 수십
kb라 **수백 MB까지 갈 수 있다.** `$TD_OUT_DIR`이 있는 파티션 여유를 먼저 확인해라.

부족하면 완주 후 성공분을 지우고 `ABNORMAL/`만 남겨라.

---

## 4. 에이전트 역할 분리 (신규)

이번 반영에 문서 두 개가 갈라졌다. **읽는 주체가 다르다:**

| 파일 | 읽는 주체 | 내용 |
|---|---|---|
| `AGENTS.md` | **opencode** | 실행·관찰자. 실데이터 봐도 됨. CC엔 `td_peek` 출력만 넘김 |
| `CLAUDE.md` | **Claude Code** | 수정자. 실데이터 금지(카테고리명 포함) |
| `.claude/settings.json` | Claude Code | `Read(./data/**)` deny — opencode엔 영향 없음 |

**확인할 것**: opencode 쪽 설정이 `AGENTS.md`를 읽도록 돼 있는지. 다른 파일명을 보게
설정돼 있으면 그 이름으로 바꿔야 한다.

### `td_peek.py` — 에이전트 간 전달 창구

```bash
python3 scripts/td_peek.py $TD_OUT_DIR
```

건수·진행률·바이트 통계만 낸다. 이름·본문·카테고리명이 출력될 코드 경로가 없고 테스트가 그걸
고정한다(`tests/test_td_peek.py`). **여기에 이름을 출력하는 기능을 추가하지 마라.**

---

## 5. 반영 후 첫 실행 — 체크리스트

```bash
# 1. 테스트
python3 -m pytest tests/ -q                      # 185 passed

# 2. 실행
python3 scripts/td_pipeline.py $TD_OUT_DIR --sources <persons.json>

# 3. 중단되면 → 같은 명령 다시 (자동 재개)

# 4. 상태 확인
python3 scripts/td_peek.py $TD_OUT_DIR
```

**완주 후 사람에게 보고할 것 세 가지:**

1. **`td_peek` 출력 전체** — 특히 `[LLM 호출]`의 요청·응답 최대 바이트.
   `relations` 분리로 응답이 20kb 아래로 내려갔는지 이걸로 확인한다.
2. **`ABNORMAL/`에 실패가 몇 건인지** — 0건이면 완주 성공.
3. **taxonomy 카테고리가 몇 개 나왔고 그룹핑이 납득 가능한지** ← 이건 **사람이 직접**
   `taxonomy.json`을 열어서 판정한다. 에이전트에게 시키지 마라(품질 판정은 사람 몫이고,
   CC는 그 파일을 볼 수 없다).

이 완주가 지금 미결인 제품 결정들(Layer 2 스코프, 시각화 방향, 워크숍 투표 옵션, 산출물
형태)의 **선행조건**이다. 결과가 나와야 그것들을 정할 수 있다.

---

## 6. 막히면

| 증상 | 확인 |
|---|---|
| 모델명 오류 | `TD_TEXT_MODEL` 설정됐나. `curl $TEXT_API_BASE/models`로 id 확인 |
| 재실행했는데 처음부터 돎 | `extracted.json` mtime이 바뀌었나 (`touch`, `cp`도 원인) |
| 완료했는데 또 돎 | `*.progress.json`이 지워졌나 |
| 응답 20kb 초과 재발 | `td_peek`의 `[LLM 호출]` 응답 최대치 확인 → `internal-run-guide.md` §4 |
| 그 외 | `$TD_OUT_DIR/task_discovery/calls/<stage>/ABNORMAL/`의 원문 (opencode·사람만) |
