# 내부망 실행 가이드 (2026-08-06, S1-8 반영본)

> **이 문서를 읽는 대상은 내부망에서 이 파이프라인을 돌릴 에이전트/사람이다.**
> 전체 설계·용어는 `docs/task-discovery-coldstart.md`가 정본이고, 여기는 **내부망에서 실제로
> 돌릴 때 알아야 할 것**만 담는다. 이번(S1-8, 이슈 #30) 변경으로 실행 방식이 바뀌었으니
> 예전 기억이나 예전 문서 내용과 충돌하면 **이 문서가 최신이다.**

---

## 1. 무엇이 바뀌었나 (S1-8, 이슈 #30 / #31~#36)

### 이전에 무슨 일이 있었나

내부망에서 `make td`를 돌리면 LLM 호출 하나가 실패하는 순간 **그 스테이지의 진행분이 통째로
사라졌다.** 그래서 작업자가 파이프라인을 포기하고 매번 임시 py 스크립트로 작업을 잘게 쪼개
손으로 돌리고 있었다. 실패해도 아무 기록이 안 남아서 "페이로드가 20kb를 넘으면 깨진다"는
증상의 정체(요청 쪽인지 응답 쪽인지, 정확한 임계값이 얼마인지)조차 확인할 수 없었다.

원인은 세 가지가 겹친 것이었다:

1. **JSON 파싱 실패가 재시도 밖에 있었다.** 코드가 `parse_json(retry_call(...))` 순서라,
   모델이 JSON이 아닌 걸 뱉으면(서문·reasoning 붙임, 응답 잘림) 재시도 없이 즉시 예외.
2. **예외를 잡는 스테이지가 `td_extract` 하나뿐이었다.** taxonomy·assign·narrate엔 `try`가
   단 하나도 없었다.
3. **저장이 루프 종료 후 1회뿐이었다.** taxonomy는 전 배치, assign은 facet 600~800개를
   전부 돈 뒤에야 파일을 썼다.

거기에 **스테이지 단독 실행도 막혀 있었다** — 각 스크립트의 `main()`이 `TD_TEXT_MODEL`을
안 읽어서 사내 엔드포인트에 gemini 모델명이 그대로 넘어갔다.

### 지금은 어떻게 되었나

| 항목 | 이전 | 지금 |
|---|---|---|
| JSON 파싱 실패 | 재시도 없이 즉사 | `retry_json`이 재시도 루프 **안**에서 파싱 — 재시도 대상 |
| taxonomy 중단 | 전부 증발 | 배치마다 즉시 저장, 중단 지점부터 재개 |
| assign 중단 | 전부 증발 (~800콜) | facet마다 즉시 저장, 중단 지점부터 재개 |
| 실패 기록 | 없음 | `data/pipeline.ecs.jsonl` (ECS JSON) + 콜별 입출력 파일 |
| 스테이지 단독 실행 | 모델명 틀려서 깨짐 | `TD_TEXT_MODEL`/`TD_EMBED_MODEL` 정상 반영 |
| 완료 판정 | 파일 존재 여부 | 진행 사이드카의 `done == total` |

---

## 2. 실행 방법

### 환경변수 (변경 없음)

```bash
export TEXT_PROVIDER=internal
export TEXT_API_KEY=<사내 키>
export TEXT_API_BASE=<사내 OpenAI호환 URL>
export TD_TEXT_MODEL=<사내 텍스트 모델 id>   # 필수 — 안 채우면 gemini 모델명이 넘어가 깨진다

# S4(검색)까지 갈 때만
export EMBED_PROVIDER=internal
export EMBED_API_BASE=<BGE-M3 URL>
export TD_EMBED_MODEL=<임베딩 모델 id>
```

### 전체 실행

```bash
make td SOURCES=data/persons.json
```

### 스테이지 단독 실행 (S1-8에서 새로 가능해짐)

전체를 한 번에 돌리기 부담스러우면 스테이지별로 나눠 돌려라. **이제 각 스크립트가
`TD_TEXT_MODEL`을 제대로 읽는다.**

```bash
python3 scripts/td_extract.py   data/persons.json     # → extracted.json
python3 scripts/td_taxonomy.py  data/task_discovery/extracted.json   # → taxonomy.json
python3 scripts/td_assign.py    data/task_discovery/extracted.json data/task_discovery/taxonomy.json
python3 scripts/td_aggregate.py                       # LLM 안 씀
python3 scripts/td_render.py                          # LLM 안 씀
python3 scripts/td_narrate.py   data/task_discovery   # Layer 2
```

**중요: 임시 py 스크립트를 새로 만들지 마라.** 예전엔 그럴 이유가 있었지만(재개가 안 돼서),
이제 위 명령들이 중단·재개를 알아서 한다. 새 스크립트를 만들면 진행 사이드카와 어긋나서
오히려 상태가 꼬인다.

---

## 3. 중단됐을 때 — 그냥 같은 명령을 다시 쳐라

taxonomy·assign은 **어디서 죽든 직전까지의 결과가 파일에 남아 있고, 같은 명령을 다시 실행하면
그 지점부터 이어간다.** 이미 끝난 배치/항목은 LLM을 다시 부르지 않는다.

```bash
# 배치 7에서 죽었다면
python3 scripts/td_taxonomy.py data/task_discovery/extracted.json
# → 배치 1~6은 건너뛰고 7부터 재개
```

### 진행 상태 확인

```bash
cat data/task_discovery/taxonomy.progress.json
# {"batches_done": 6, "total_batches": 12, "extracted_mtime": ...}

cat data/task_discovery/assignments.progress.json
# {"processed": 340, "total_facets": 812, "extracted_mtime": ..., "taxonomy_mtime": ...}
```

`done == total`이면 완료다. 다르면 미완성이고, 다시 돌리면 이어간다.

> **taxonomy의 `total_batches`는 facet 배치 수 + 1이다.** 마지막 1스텝이 관계(relations)
> 도출 패스이기 때문. 예: facet 배치가 11개면 `total_batches`는 12. `11/12`에서 멈춰 있으면
> 카테고리는 다 만들어졌고 관계만 남은 상태이고, 재실행하면 관계 콜 1번만 돈다.

### 상류가 바뀌면 자동으로 처음부터 다시 한다

`extracted.json`(taxonomy·assign 둘 다) 또는 `taxonomy.json`(assign만)의 **mtime이
사이드카에 기록된 값과 다르면** 이어가지 않고 처음부터 다시 시작한다. 옛 입력으로 만든
결과에 새 입력 결과를 이어붙이면 정합성이 깨지기 때문이다.

**즉, `extracted.json`을 손으로 고치거나 다시 만들면 taxonomy·assign이 전부 재실행된다.**
의도한 것이면 괜찮지만, 아니라면 파일을 건드리지 마라 (`touch`만 해도 mtime이 바뀐다).

### 처음부터 강제로 다시 하고 싶으면

산출물 파일과 사이드카를 같이 지워라. 사이드카만 남으면 상태가 어긋난다.

```bash
rm data/task_discovery/taxonomy.json data/task_discovery/taxonomy.progress.json
rm data/task_discovery/assignments.json data/task_discovery/assignments.progress.json
```

---

## 4. 실패 진단 — 로그와 콜 덤프

### ECS JSON 로그: `data/pipeline.ecs.jsonl`

한 줄이 JSON 하나. 나중에 사내 ES로 보낼 형식이고, 지금은 파일로만 쌓인다.

| 상황 | 레벨 | 남는 것 |
|---|---|---|
| 호출 성공 | INFO | 요청/응답 **바이트 수만** |
| 시도별 실패 | WARNING | 바이트 수 + 에러 타입/메시지 |
| 재시도 소진 후 최종 실패 | WARNING | **프롬프트·응답 원문 전체** + 에러 |

성공 로그에 원문을 안 싣는 건 호출 수백 건에 로그가 부풀지 않게 하려는 것이다. 실패는
진단이 목적이므로 전문을 남긴다.

### 20kb 문제 — 원인 규명됨 (2026-08-06)

> **결론: 응답 쪽 한도였고, 원인은 taxonomy의 `relations` 필드였다. 이미 고쳐졌다.**
>
> `td_taxonomy.py`의 `_INSTRUCT`가 **배치마다** `relations`(카테고리 간 관계)까지 요구해서,
> 응답이 카테고리 25개 기준 7.8kb → 13kb+로 부풀었고 실제 사내망에서 20kb를 넘겨 JSON이
> 잘렸다. `relations`는 taxonomy **전체 구조**에 대한 속성이라 배치 루프에 있을 이유가
> 없었다 — 카테고리가 아직 다 안 만들어진 중간 배치에서 관계를 매기면 존재하지 않는
> 카테고리를 가리켜 버려지고, 다음 배치에서 전부 다시 뱉는 낭비였다.
>
> **고친 방식**: 배치 루프는 `name`/`definition`/`inclusion_criteria`만 받고,
> 관계는 배치가 다 끝난 뒤 **마지막 1콜**로 엣지 리스트(`{from, to, type}`)만 받는다.
> 배치 응답이 7.9kb로 내려갔고(한도의 40%), 관계 패스 응답은 엣지뿐이라 더 작다.
> `taxonomy.json` 스키마는 그대로라 downstream 영향 없고, 관계 품질은 오히려 좋아졌다
> (완성된 taxonomy 전체를 보고 한 번에 매기므로).
>
> **그래도 아래 절차는 그대로 유효하다** — 다른 스테이지(assign·narrate·extract)에서
> 같은 증상이 나거나, 카테고리 수가 예상보다 많아 다시 한도에 걸릴 때 쓴다.

### 페이로드 한도를 판명하는 방법

파이프라인을 한 번 돌린 뒤 이 명령을 실행해라:

```bash
python3 - <<'PY'
import json
for line in open("data/pipeline.ecs.jsonl"):
    d = json.loads(line)
    print(d.get("service.name"), d.get("log.level"),
          "req=", d.get("http.request.body.bytes"),
          "resp=", d.get("http.response.body.bytes"),
          d.get("error.message", ""))
PY
```

읽는 법:

- **요청 바이트가 어떤 값을 넘을 때만 실패한다** → **요청 쪽 한도**다.
  대응: `batch_size`를 줄이거나, taxonomy 프롬프트에 싣는 기존 카테고리 필드를 줄인다.
- **요청은 통과했는데 파싱만 실패하고, 응답 바이트가 특정 값에서 멈춰 있다** → **응답이
  잘리는 것**(출력 토큰 한도). ← `relations` 건이 이 경우였다.
- 두 경우 모두, **정확한 임계 바이트 수를 사람에게 보고해라.** 그 수치가 나와야 다음 결정을
  할 수 있다.

**응답 한도에 다시 걸리면 이 순서로 검토해라:**

1. **모델이 매 호출마다 다시 뱉을 필요가 없는 필드가 있나?** `relations`가 그런 경우였다.
   전체 구조에 대한 속성이면 루프에서 빼고 마지막에 한 번만 뽑아라 — 크기도 줄고 품질도 는다.
2. 그래도 크면 `batch_size`를 줄인다(`td_pipeline.py`의 기본값 30). 단, 배치 응답은 누적
   taxonomy 전체라서 batch_size를 줄여도 **응답은 거의 안 줄어든다** — 요청만 준다.
   응답이 문제일 땐 효과가 작다는 걸 알고 써라.

> **"신규분만 반환"으로 바꾸는 건 최후 수단이다.** 배치마다 전체 taxonomy를 주고받는 건
> 모델이 카테고리를 병합·분할·정의 재작성·삭제할 수 있게 하는 의도된 설계다
> (`td_taxonomy.py`의 `_prompt`). 신규분만 받으면 taxonomy가 append-only가 되어 배치 1에서
> 얇은 근거로 만든 카테고리가 끝까지 그대로 남는다. 위 1·2번을 먼저 다 해보고, 그래도 안
> 되면 그때 사람과 상의해라.

### 콜별 입출력 덤프: `data/task_discovery/calls/`

모든 LLM 호출의 입출력이 파일로 남는다. 예전에 작업자가 손으로 `N_input.json`/
`N_output.json`을 만들던 것을 자동화한 것이다.

```
data/task_discovery/calls/
  extract/
    1_input.json      # {stage, call_id, prompt, timestamp}
    1_output.json     # {response, success}
    ...
  taxonomy/
    1_input.json ...
    ABNORMAL/         # ← 재시도 끝에 최종 실패한 콜만 여기 중복 저장
      7_input.json
      7_output.json
  assign/
  narrate/
```

**`ABNORMAL/` 디렉토리를 먼저 봐라.** 비어 있으면 실패한 호출이 없는 것이고, 파일이 있으면
그 `call_id`가 몇 번인지 바로 보인다. `_input.json`의 `prompt`를 그대로 다시 던져보면
재현할 수 있다.

`call_id`가 뭘 가리키는지:

| 스테이지 | `call_id` |
|---|---|
| extract | 사람 id |
| taxonomy | 배치 번호 (1부터), 마지막 관계 도출 패스는 `"relations"` |
| assign | facet 처리 순번 (1부터) |
| narrate | `"team"`(총평) 또는 카테고리 인덱스 |

> 주의: 이 덤프는 **감사·재현용이지 재개 판정의 근거가 아니다.** 재개는 오직
> `*.progress.json` 사이드카가 담당한다. `calls/` 안의 파일을 지우거나 고쳐도 재개엔 영향이
> 없고, 반대로 이걸 보고 진행 상황을 판단하면 안 된다.

---

## 5. 스테이지별 실패 처리 방식이 다르다 (의도된 차이)

| 스테이지 | 항목 하나가 최종 실패하면 |
|---|---|
| **extract** | 그 사람만 버리고 **계속 진행** (한 명 빠져도 나머지는 유효) |
| **taxonomy** | **스테이지 전체를 중단** (예외 전파) — 관계 패스 실패도 마찬가지 |
| **assign** | 그 facet만 `dropped`에 넣고 **계속 진행** |
| **narrate** | 그 카테고리 페이지만 안 만들고 계속 |

**taxonomy만 중단하는 이유**: taxonomy는 전체 facet을 다 봐야 의미가 있다. 실패한 배치를
조용히 건너뛰면 그 배치의 30개 항목이 카테고리 체계에서 누락된 채 "정상 완료"처럼 보인다.
그건 실패보다 나쁘다. 그래서 멈추고, 사람이 원인을 보고, 고친 뒤 재개하게 한다.

---

## 6. 내부망 마이그레이션 시 참고 사항

내부망 저장소에 이 변경을 반영할 때 확인할 것들.

### 6.1 새로 생기는 파일 — 전부 `data/` 아래, gitignore 대상

```
data/pipeline.ecs.jsonl                        # ECS 로그 (계속 append됨)
data/task_discovery/taxonomy.progress.json     # taxonomy 진행 상태
data/task_discovery/assignments.progress.json  # assign 진행 상태
data/task_discovery/calls/**                   # 콜별 입출력 덤프
```

- **`dist/`엔 절대 아무것도 쓰지 마라.** GitHub Pages 배포 대상이라 넣는 즉시 공개된다.
- `data/`는 이미 `.gitignore`에 있으니 별도 조치 불필요.

### 6.2 디스크 용량을 신경 써라 — 이게 가장 현실적인 리스크다

콜 덤프는 **모든** 호출을 남긴다. 200명 기준 대략:

| 스테이지 | 호출 수 | 파일 수 |
|---|---|---|
| extract | ~200 | ~400 |
| taxonomy | ~20-30 (+ 관계 1) | ~60 |
| assign | ~600-800 | ~1,600 |
| narrate | ~16-26 | ~50 |
| **합계** | ~850-1,050 | **~2,100** |

프롬프트가 큰 편(taxonomy는 수십 kb)이라 **수백 MB까지 갈 수 있다.** 내부망 디스크가
빠듯하면:

- 완주 후 `calls/`에서 성공분을 지우고 `ABNORMAL/`만 남겨라.
- 또는 실행 전에 `data/task_discovery/calls/`를 통째로 비우고 시작해라(재개엔 영향 없음).

`data/pipeline.ecs.jsonl`도 append-only라 계속 자란다. 실행마다 새로 시작하고 싶으면
돌리기 전에 지워라. 로그 로테이션은 지금 구현에 없다.

### 6.3 기존 산출물과의 호환성

- **`taxonomy.json`·`assignments.json`의 스키마는 안 바뀌었다.** 기존 파일을 그대로 쓸 수 있고
  downstream(`td_aggregate`, `td_render`, `td_narrate`)도 영향 없다.
- 다만 **사이드카가 없는 기존 파일은 "미완성"으로 판정된다.** `is_complete()`가 사이드카를
  요구하기 때문이다. 그래서 `make td`를 돌리면 taxonomy·assign이 **다시 실행된다.**
  - 이미 검증된 산출물이 있어서 재실행하기 싫다면, 사이드카를 손으로 만들어 완료로 표시해라:
    ```bash
    # 예: taxonomy가 이미 완료된 상태로 인정시키기
    # batches_done == total_batches, extracted_mtime은 현재 extracted.json 값
    python3 - <<'PY'
    import json, math
    from pathlib import Path
    d = Path("data/task_discovery")
    persons = json.loads((d/"extracted.json").read_text(encoding="utf-8"))
    import sys; sys.path.insert(0, "scripts")
    from td_common import iter_facets
    n = len(list(iter_facets(persons)))
    total = math.ceil(n / 30) + 1   # batch_size 기본값 30, +1은 관계 도출 패스
    (d/"taxonomy.progress.json").write_text(json.dumps({
        "batches_done": total, "total_batches": total,
        "extracted_mtime": (d/"extracted.json").stat().st_mtime}, indent=1))
    print("taxonomy를 완료 상태로 표시:", total, "스텝")
    PY
    ```
    ⚠️ 단, **기존 `taxonomy.json`이 `relations` 필드 없이 만들어진 것이면** 이렇게 완료로
    표시했을 때 관계가 영영 안 뽑힌다. 온톨로지 뷰가 필요하면 그냥 재실행하거나,
    `td_taxonomy.derive_relations(taxonomy, call)`만 따로 돌려서 관계를 채워라.
  - 이게 번거롭거나 확신이 없으면 **그냥 재실행하는 편이 안전하다.** 재실행해도 이제는
    중간에 죽어도 잃는 게 없다.

### 6.4 `extracted.json`을 건드리지 마라

`AGENTS.md`에 이미 적혀 있지만 이제 이유가 하나 더 늘었다: **mtime이 바뀌면 taxonomy와
assign이 전부 처음부터 다시 돈다.** 내용을 안 고치고 `touch`만 해도 그렇다. 파일을 복사하거나
옮길 때도 mtime이 보존되는지 확인해라 (`cp -p`, `rsync -a`).

### 6.5 재시도 계층을 늘리지 마라

재시도는 `td_common.retry_call` **한 곳뿐**이고, 그 위에 `retry_json`이 파싱까지 감싼다.
SDK 재시도(`llm.py`의 `max_retries`)와 이미 두 겹이라 여기서 더 늘리면 실패 한 건이 수십 번의
호출로 증폭된다. langchain 같은 프레임워크를 넣는 것도 같은 이유로 하지 마라 — 그 프레임워크의
재시도가 또 한 겹 쌓인다.

### 6.6 이번 변경으로 열린 다음 단계

이 작업의 목적은 **"내부망에서 S1 파이프라인을 실데이터로 끝까지 한 번 완주"**를 가능하게
하는 것이다. 그게 되면 그 결과물이 아래 결정들의 입력이 된다 (전부 지금 미결):

1. Layer 2(`td_narrate`) 스코프 — 총평만 vs 카테고리별 서사까지
2. 시각화 방향 — 매트릭스뷰 + 온톨로지 그래프뷰로 갈지 (지금은 더미 목업만 있음)
3. 워크숍 투표 방식 — 투표 옵션 종류 (찬성/반대? 점수? 순위?)
4. 산출물 형태 — 워크숍 자료 한 번인지, 반복 산출인지

**완주 후 사람에게 보고할 것**: ① 20kb 정체(요청/응답 + 정확한 바이트 수), ② `ABNORMAL/`에
실패가 몇 건 있었는지, ③ 생성된 taxonomy 카테고리가 몇 개고 그룹핑이 납득 가능한지.

---

## 7. 빠른 참조

```bash
# 실행
make td SOURCES=data/persons.json

# 중단됐으면 → 같은 명령 다시 (자동 재개)

# 진행 상태
cat data/task_discovery/taxonomy.progress.json
cat data/task_discovery/assignments.progress.json

# 실패 확인
ls data/task_discovery/calls/*/ABNORMAL/

# 20kb 진단
grep -c . data/pipeline.ecs.jsonl
python3 -c "import json;[print(json.loads(l).get('http.request.body.bytes'), json.loads(l).get('http.response.body.bytes'), json.loads(l).get('error.message','ok')) for l in open('data/pipeline.ecs.jsonl')]"

# 처음부터 다시 (사이드카까지 같이 지울 것)
rm data/task_discovery/{taxonomy,assignments}.json data/task_discovery/{taxonomy,assignments}.progress.json
```
