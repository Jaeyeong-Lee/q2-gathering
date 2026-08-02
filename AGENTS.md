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
싶으면 `taxonomy.json`(또는 그 이후 산출물)만 지우고 돌려라 — `extracted.json`은 지우지 마라.

## 지켜야 할 것

- 실명·실데이터는 절대 외부(비-사내) LLM/서비스로 안 보낸다. 사내망 엔드포인트만 쓴다.
- 산출물은 `data/`(gitignore)에만 쓴다. `dist/`는 GitHub Pages 배포 대상이라 여기 뭘 넣으면
  바로 공개된다 — task-discovery 산출물은 절대 넣지 마라.
- 코드 스타일·테스트 패턴은 `scripts/td_*.py`에 이미 있는 걸 그대로 따라라(순수함수 + 주입된
  `call`, `tests/test_td_*.py` 패턴). 새 프레임워크·라이브러리 들이지 마라.
- 막히면 지어내지 말고 `docs/task-discovery-coldstart.md` §6("아직 열려 있는 것")부터 확인하고,
  그래도 안 풀리면 사람한테 물어라.
