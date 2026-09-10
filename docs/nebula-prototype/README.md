# 성운 발표 화면 원본 (참고 보관)

**이 디렉터리는 빌드되지 않는다.** 실행 경로는 `nebula/templates/nebula.html`이고,
여기 있는 것은 그 화면이 처음 만들어졌을 때의 모습이다. 계보를 확인하거나 옮기는
과정에서 무엇이 바뀌었는지 대조할 때만 본다. 경위는 [[nebula-handoff-2026-09-11]].

2026-09-11 00:48–01:50에 `Documents/Codex/2026-09-11/clear/`에서 만들어졌고,
02:11에 파이프라인 작업이 워크트리로 옮겨가면서 그 자리에 남겨졌다. 그래서 실제
추출 결과와 이어지지 않은 채 자기 fixture에 고정돼 있었다.

| 파일 | 무엇 |
| --- | --- |
| `future-nebula.template.html` | 다섯 장면 템플릿 원본. `nebula/templates/nebula.html`의 출발점 |
| `future-nebula.html` | 위 템플릿에 합성 페이로드를 넣어 렌더한 결과. 그대로 열어볼 수 있다 |
| `build_nebula.py` | 독립 빌더. 이전 합성 사람 지도 JSON 하나만 읽는다 |
| `check_nebula.cjs` | 브라우저 점검 스크립트. `tests/nebula_browser.cjs`가 대체했다 |
| `README.original.md` | 당시 작성된 설명 |

`future-nebula.synthetic.json`(489KB)은 가져오지 않았다. `future-nebula.html`에
같은 페이로드가 그대로 박혀 있어 중복이다.

## 입력은 전부 합성이다

`build_nebula.py`의 `SEED`는 `data/td_sample/people-atlas/synthetic-input.json`을
가리킨다. 200명의 인물, PJT 이름, 24개 카테고리 이름과 모든 원문은 발표 시연을 위해
작성한 fixture이며 실제 조직의 기록이 아니다. 그래서 공개 저장소에 둔다.

## 지금 코드와 다른 점

옮기면서 바뀐 것은 [[nebula-handoff-2026-09-11]]의 대응표에 있다. 요약하면
프로토타입은 자기 fixture의 모양을 전제하고 있었다 — horizon 세 값, PJT당 카테고리
3개, PJT 8개, 정수 ID, 항상 존재하는 좌표. 실제 파이프라인은 그중 어느 것도
보장하지 않는다.
