# AGENTS.md

이 저장소엔 프로젝트가 두 개 있다. 헷갈리면 이 표부터 봐라.

| | Heritage Archive (유사도 네트워크) | task-discovery |
|---|---|---|
| 상태 | **완료·배포됨 — 건드릴 필요 없음** | **진행 중 — 지금 할 일** |
| 산출물 | `dist/heritage-archive.html` (단일 정적 파일) | `data/task_discovery/*.json` + `workshop-input.md` |
| 문서 | `README.md`, `docs/PRD-heritage-archive.md` | `docs/task-discovery-coldstart.md` |
| 스크립트 | `scripts/embed.py` `similarity.py` `freq.py` `build.py` | `scripts/td_*.py` |

**지금 작업은 task-discovery다.** Heritage Archive 쪽 파일은 이 작업과 무관하니 손대지 마라.

## task-discovery 5줄 요약

부서원 ~200명 회고(`data/persons.json`) → LLM이 facet 추출 → taxonomy(역량 카테고리) 유도
→ 배정 → 집계 → 워크숍 입력 문서. 전체 설계·근거·용어는 **`docs/task-discovery-coldstart.md`
하나에 다 있다 — 다른 데서 찾지 말고 그거부터 읽어라.**

## 지금 실행할 것

**내부망에서 돌리기 전에 `docs/task-discovery-internal-run-guide.md`를 읽어라.** 재개·로그·
콜 덤프·20kb 진단 방법이 전부 거기 있다(S1-8, 이슈 #30 반영).

`extracted.json`은 이미 만들어져 있고 검증됐다. **다시 추출하지 마라.** 재실행 범위는
taxonomy부터다:

```bash
export TEXT_PROVIDER=internal
export TEXT_API_KEY=<사내 키>
export TEXT_API_BASE=<사내 OpenAI호환 URL>
export TD_TEXT_MODEL=<사내 텍스트 모델 id>   # 필수. 안 채우면 gemini 모델명이 그대로 넘어가서 깨진다
make td SOURCES=data/persons.json
```

중간 산출물(`data/task_discovery/*.json`)이 있으면 자동 skip한다. taxonomy를 다시 만들고
싶으면 `taxonomy.json`과 `taxonomy.progress.json`을 **같이** 지우고 돌려라 —
`extracted.json`은 지우지 말고 `touch`도 하지 마라(mtime이 바뀌면 taxonomy·assign이 전부
처음부터 다시 돈다).

**중단되면 임시 스크립트를 만들지 말고 같은 명령을 다시 쳐라.** taxonomy·assign은 배치/항목
단위로 저장되므로 죽은 지점부터 자동으로 이어간다(예전엔 안 됐지만 이제 된다).

## 실데이터를 네 컨텍스트에 올리지 마라 (제일 중요)

파이프라인이 실데이터를 **처리**하는 것과, 네가 그걸 **읽는** 것은 다른 문제다. 처리는 해야
하지만, 네 컨텍스트에 들어간 내용은 네가 어디서 돌든 밖으로 나간다. 그러니:

**절대 열지 마라** — `Read`든 `cat`/`head`/`grep`/`python -c open(...)`이든:

| 파일 | 왜 |
|---|---|
| `data/persons.json` | 실명 + 회고 원문 |
| `extracted.json` / `assignments.json` | 실명 + 원문 인용 |
| `taxonomy.json` / `aggregates.json` | 카테고리명·정의 = **사내 제품 코드명·기술 전략** |
| `workshop-input.md`, `interpretation/**` | 위 둘 다 |
| `calls/**`, `pipeline.ecs.jsonl` | 프롬프트·응답 원문 |

**카테고리 이름도 안 된다.** 개인정보는 아니지만 `D1b Yield·Test PGM 최적화` 같은 사내
코드명이 그대로 들어간다 — 회사 기준으론 개인 회고보다 민감할 수 있다.

**대신 이렇게 해라:**
- 상태 확인은 `python3 scripts/td_peek.py` 로만. 건수·진행률·바이트 통계만 나오고 본문·이름은
  한 글자도 안 나온다.
- 코드 개발·디버깅은 **합성 코퍼스로만** — `td_sources.py`가 같은 스키마의 가짜 데이터를
  만든다(애초에 그러라고 있는 모듈이다). 테스트도 전부 가짜 `call` 주입식이다.
- 실행은 사람이 한다. 네가 파이프라인을 돌릴 일이 있으면 먼저 물어라.
- 산출물이 이상해 보인다는 **보고를 받았을 때**, 파일을 열어 확인하지 말고 `td_peek.py`
  숫자와 코드 로직으로 원인을 좁혀라. 그래도 안 되면 사람에게 "무엇을 확인해달라"고 요청해라.

내부망 실행 시엔 `TD_OUT_DIR`을 리포 밖(예: `/secure/run`)으로 잡아 로그·콜덤프가 작업
디렉터리에 아예 안 남게 한다 — 자세한 건 `docs/task-discovery-internal-run-guide.md`.

## 지켜야 할 것

- 실명·실데이터는 절대 외부(비-사내) LLM/서비스로 안 보낸다. 사내망 엔드포인트만 쓴다.
- 산출물은 `data/`(gitignore)에만 쓴다. `dist/`는 GitHub Pages 배포 대상이라 여기 뭘 넣으면
  바로 공개된다 — task-discovery 산출물은 절대 넣지 마라.
- 코드 스타일·테스트 패턴은 `scripts/td_*.py`에 이미 있는 걸 그대로 따라라(순수함수 + 주입된
  `call`, `tests/test_td_*.py` 패턴). 새 프레임워크·라이브러리 들이지 마라.
- 막히면 지어내지 말고 `docs/task-discovery-coldstart.md` §6("아직 열려 있는 것")부터 확인하고,
  그래도 안 풀리면 사람한테 물어라.
