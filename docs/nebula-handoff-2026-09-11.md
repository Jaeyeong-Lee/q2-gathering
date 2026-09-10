# 인수인계 — 성운 발표 화면을 파이프라인에 연결 (2026-09-11)

이 문서는 코덱스 세션이 usage 한도로 중단된 지점을 클로드 코드가 이어받아 무엇을 했는지
남긴 기록이다. 다음에 이 브랜치를 여는 에이전트가 **왜 이 커밋이 존재하는지** 알기 위한 것이며,
설계 문서가 아니다. 설계는 [[nebula-spec]], 운영은 [[nebula-internal-runbook]]을 본다.

## 중단 지점

코덱스가 커밋 `ce2714d` 직후 스스로 이렇게 적고 멈췄다.

> 내가 실제 파이프라인을 만들면서, 그때의 성운 시각화·다섯 장면·자동 발표를 최종 데이터에
> 연결하는 부분을 빠뜨렸어. 기존 발표 자료와 현재 코드를 비교해서, 그 발표 화면도 실제 추출
> 결과로 생성되도록 연결하겠어. 2차원 버블 화면도 함께 유지할게.

실제로 그 작업은 시작되지 않았다. 워킹트리는 깨끗했고 발표 화면은 워크트리 **밖**에 있었다.

```
00:48–00:57  Codex/2026-09-11/clear/   build_nebula.py + future-nebula.html    ← 발표 화면 원본
01:50        Codex/2026-09-11/clear/   future-nebula.template.html 갱신
02:02–02:04  Codex/2026-09-11/clear/nebula/   파이프라인 stub 시작
02:11        worktree future-task-implementation 생성 → 여기서 nebula 패키지 재작성
07:41        matrix.html + review.html 완성, 커밋 2개 (69ee1aa, ce2714d)
             ← future-nebula.html은 clear/에 남겨둔 채로
```

`clear/build_nebula.py`는 이전 합성 사람 지도 JSON 하나만 읽는 독립 빌더였다. 파이프라인의
`view.json`과 이어지는 경로가 아예 없었다. 그래서 발표 화면은 합성 fixture에 고정돼 있었고,
실제 추출 결과로는 한 장면도 그릴 수 없었다.

## 사용자가 정한 방향

- **성운이 메인, 매트릭스가 보조.** 지금까지는 반대로 커밋돼 있었다.
- `matrix.html`은 (a)안 — 보조 화면으로 함께 출력한다. 코덱스의 "2차원 버블 화면도 함께
  유지"와 같은 결정이다.
- 모바일 폭에서 캔버스가 안 그려지는 문제는 **고치지 않는다.** 발표는 데스크탑이다.

## 한 일

`clear/future-nebula.template.html`을 `nebula/templates/nebula.html`로 편입하고,
`view.json`을 그 템플릿의 페이로드로 바꾸는 어댑터를 붙였다. 빌드가 세 화면을 함께 쓴다.

### 계약 차이와 처리

프로토타입 템플릿은 자기 fixture의 모양을 그대로 전제하고 있었다. 실제 파이프라인 출력과
어긋나는 지점만 옮겼다.

| 프로토타입 전제 | 파이프라인 실제 | 처리 |
| --- | --- | --- |
| `people[].id`가 정수, `edges`가 정수 쌍 | 안정적인 문자열 ID | `build_nebula`가 색인을 부여하고 원래 ID를 `pid`로 병기 |
| `pjt`가 정수 인덱스 | PJT 이름 문자열 | 이름을 정렬해 색인. 색은 8색 팔레트를 modulo로 재사용 |
| horizon이 short·long·unknown 셋 | `HORIZONS`는 **mid 포함 넷** | 중기 링을 추가. 없으면 중기 과제가 화면에서 사라졌다 |
| 카테고리 ID가 `"{pjt}-{index}"` | digest 문자열 | `cat_index`를 페이로드에 실어 보냄 |
| 과제 ID가 `"{person}:{seq}"` | digest 문자열 | `seq`를 페이로드에 실어 보냄 |
| PJT마다 정확히 3개 카테고리, PJT는 정확히 8개 | 둘 다 가변 | `clusterCenter`를 개수 무관 그리드+링으로 일반화 |
| 모든 과제에 카테고리 있음 | 미분류 허용 | PJT별 `미분류` 자리표시 카테고리 |
| 사람 좌표가 항상 있음 | `has_layout`이 false일 수 있음 | 결정적 원형 배치 + 그렇다고 밝히는 문구 |
| 200명·440과제·8PJT·24카테고리가 산문에 박혀 있음 | 실행마다 다름 | 페이로드에서 계산 |
| 역량 원이 한 종류당 한 자리에 고정 | 카테고리당 역량 수 가변 | 종류별로 최대 3개까지 세로 배치, 전체 목록은 패널 |

`skills[].kind`는 파이프라인의 `have`/`need`를 템플릿의 `have`/`gap`으로 옮겨 적는다.
근거 문장은 `relation_quote` — 과제와 역량을 잇는 원문 그 자체다.

### 좌표에 대해

합성 데모는 좌표 없는 네트워크를 넘긴다(TF-IDF 코사인만 계산). 그래서 첫 장면이 원형 배치로
나오고 화면이 그렇다고 말한다. **버그가 아니라 입력의 사실이다.** 프로토타입이 예뻤던 건 이전
합성 사람 지도의 force layout 좌표를 재사용했기 때문이다. 실입력에서 좌표 있는 네트워크를
주면 그대로 쓴다(`test_supplied_layout_is_normalized_and_absence_is_reported`).

발표 인상을 좌표에 의존한다면 데모에도 좌표를 넣는 선택지가 있지만, 그건 없는 유사도를
지어내지 않는다는 규칙과 부딪히므로 사람이 정할 문제로 남긴다.

## 검증

- `tests/test_nebula_pipeline.py::NebulaPresentation` 5개 — 색인 왕복, 미분류 보존,
  좌표 정규화와 부재 표기, 재실행 시 배치 안정성, 세 화면 동시 생성.
- `tests/nebula_browser.cjs` — 다섯 장면을 딥링크로 각각 열어 별이 그려지는지, 중기 링이
  있는지, 별을 눌러 원문이 열리는지 확인한다. **해시만 바뀌는 `goto`는 페이지를 다시 실행하지
  않아** `reload()`가 필요하다. 여기서 한 번 막혔으니 지우지 말 것.
- `mypy nebula --check-untyped-defs` 통과.

## 남은 것

- 모바일 폭(≤700px)에서 SVG가 그려지지 않는다. 사용자가 범위 밖으로 결정했다.
- `clear/` 아래 원본(`build_nebula.py`, `future-nebula.html`, `check_nebula.cjs`)은
  건드리지 않았다. 워크트리 편입이 끝났으니 이제 지워도 되지만, 지우는 건 사람이 정한다.
- `templates/td_people_atlas.html`과 `scripts/td_people_atlas_demo.py`는 이전 발표
  자료 그대로 두었다. 명세의 "기존 발표 HTML을 변경하지 않는다"에 해당한다.
- 실제 내부 endpoint 연결과 의미 검증은 여전히 내부망 몫이다.

## 이 작업에서 읽지 않은 것

`data/**`는 열지 않았다. 합성 데모는 세션 스크래치패드에 따로 생성해 확인했고,
`data/nebula-demo`조차 열지 않았다. 코덱스 세션 로그(`~/.codex/sessions/**`)는 중단 지점을
확인하기 위해 읽었으며, 그 세션들은 모두 "No real data reading" 전제로 실행된 것이다.
