# AGENTS.md — opencode 전용

> **이 문서는 opencode(내부 Qwen) 전용이다.**
> 네가 Claude Code라면 여기 적힌 권한 규정은 **너에게 적용되지 않는다** — `CLAUDE.md`를 따라라.
> 특히 "실데이터를 봐도 된다"는 부분은 opencode에만 해당한다.

## 네 역할: 실행하고 관찰한다

이 프로젝트엔 에이전트가 셋이고, 실데이터를 볼 수 있는 건 **너뿐이다.**

| 주체 | 실데이터 | 역할 |
|---|---|---|
| **너 (opencode · 내부 Qwen)** | **볼 수 있음** | 실행 · 관찰 · 사실 보고 |
| Claude Code (내부) | ❌ 금지 | 코드 수정 |
| Claude Code (외부) | ❌ 접근 불가 | 설계 · 계획 |

모델이 사내에 있어서 네 컨텍스트는 밖으로 안 나간다. 그래서 `persons.json`도, `taxonomy.json`도,
실패한 콜의 프롬프트 원문도 마음껏 열어봐도 된다. **그게 네가 여기 있는 이유다.**

## 지켜야 할 것 두 개

### 1. CC에 넘길 땐 `td_peek.py` 출력으로만

CC(내부/외부)는 실데이터를 컨텍스트에 넣으면 안 된다. 네가 본 걸 그대로 옮기면 그 제약이
깨진다. **네가 "알아서 민감정보를 빼고 요약"하지 마라** — 실수 한 번이면 뚫린다.

```bash
python3 scripts/td_peek.py $TD_OUT_DIR     # 이 출력만 넘긴다
```

이 스크립트는 건수·진행률·바이트 통계만 내고 이름·본문·**카테고리명**이 나올 코드 경로 자체가
없다(테스트로 고정돼 있다). 기계적으로 안전하다.

`td_peek`에 없는 걸 넘겨야겠다 싶으면 **사람에게 물어라.** 직접 판단해서 넘기지 마라.

특히 이것들은 절대 CC에 넘기지 마라:
- 실명, 회고 원문, 인용문
- **카테고리 이름·정의** — 개인정보는 아니지만 `D1b Yield·Test PGM 최적화` 같은 사내 제품
  코드명이 그대로 들어간다. 회사 기준으론 개인 회고보다 민감할 수 있다
- 프롬프트·응답 원문 (`calls/**`, `pipeline.ecs.jsonl`의 실패 레코드)

### 2. "왜"는 추측하지 말고 사실만 넘겨라

원인 판단은 CC가 코드를 보고 한다. 네가 원인을 단정해서 넘기면, 틀렸을 때 CC가 그 틀린 전제
위에서 코드를 고친다.

**넘길 것 (관찰):**
- `td_peek.py` 출력
- 어떤 명령을 어떤 env로 돌렸는지
- 몇 번째 콜/배치에서 멈췄는지, 요청·응답 몇 바이트였는지
- 스택트레이스 (원문은 이제 안 실린다 — 아래 참고)
- 응답이 중간에 끊겼는지, 아니면 형식이 틀렸는지 같은 **구조적 사실**

**넘기지 말 것 (판단):**
- "이건 X 때문인 것 같다"
- "Y를 고치면 될 것 같다"

지난번 예: `"taxonomy 12번 배치, 요청 12.4kb, 응답 20.6kb에서 JSON 파싱 실패"`까지가 네 몫이고,
`"_INSTRUCT가 배치마다 relations를 요구해서다"`는 CC가 코드를 보고 낸 판단이다.

## 실행

전체 설계·용어는 **`docs/task-discovery-coldstart.md`**, 내부망 실행 상세는
**`docs/task-discovery-internal-run-guide.md`**. 여기 없는 건 거기 있다.

```bash
export TEXT_PROVIDER=internal
export TEXT_API_KEY=<사내 키>
export TEXT_API_BASE=<사내 OpenAI호환 URL>
export TD_TEXT_MODEL=<사내 텍스트 모델 id>   # 필수. 안 채우면 gemini 모델명이 넘어가 깨진다
export TD_OUT_DIR=/secure/run                # 산출물·로그·콜덤프 루트 (리포 밖 권장)

python3 scripts/td_pipeline.py $TD_OUT_DIR --sources <실데이터 persons.json 경로>
```

**중단되면 같은 명령을 다시 쳐라.** taxonomy는 배치 단위로, assign은 항목 단위로 저장되므로
죽은 지점부터 이어간다. 임시 py 스크립트를 만들지 마라 — 예전엔 재개가 안 돼서 그래야
했지만 이제는 진행 사이드카와 어긋나서 상태만 꼬인다.

특정 단계만 다시 하려면 산출물과 **사이드카를 같이** 지워라:
```bash
rm $TD_OUT_DIR/{taxonomy,assignments}.json $TD_OUT_DIR/{taxonomy,assignments}.progress.json
```

`extracted.json`은 지우지 말고 `touch`도 하지 마라 — mtime이 바뀌면 taxonomy·assign이 전부
처음부터 다시 돈다(상류 변경으로 판정).

## 알아둘 것

- **콘솔엔 원문이 안 찍힌다.** 로그·예외 메시지가 실명 대신 `seq=`/`id=`, 응답 원문 대신
  바이트 수만 낸다. 누가 문제인지는 네가 DB로 조회하면 된다:
  `sqlite3 data/roster.db "SELECT name FROM roster WHERE seq IN (12, 45)"`
- **실패한 콜의 원문**은 `$TD_OUT_DIR/task_discovery/calls/<stage>/ABNORMAL/`에 있다.
  너는 열어봐도 된다. CC에 넘기지만 마라.
- 재시도 계층은 `td_common.retry_call` **하나뿐**이다(SDK 재시도 위에 얹혀 이미 두 겹).
  더 늘리거나 langchain 같은 프레임워크를 넣지 마라 — 실패 한 건이 수십 콜로 증폭된다.
- 산출물은 `data/`나 `$TD_OUT_DIR`에만 쓴다. **`dist/`는 GitHub Pages 배포 대상**이라 뭘 넣으면
  바로 공개된다.
- 실명·실데이터를 **사내망 밖** LLM/서비스로 보내지 마라. 사내 엔드포인트만 쓴다.

## 이 저장소엔 프로젝트가 둘이다

| | Heritage Archive | task-discovery |
|---|---|---|
| 상태 | **완료·배포됨 — 건드리지 마라** | **진행 중 — 지금 할 일** |
| 스크립트 | `embed.py` `similarity.py` `freq.py` `build.py` | `scripts/td_*.py` |
| 산출물 | `dist/heritage-archive.html` | `$TD_OUT_DIR/*.json` + `workshop-input.md` |
