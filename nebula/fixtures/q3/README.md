# 3Q 발표 합성 픽스처

**전부 합성이다.** 실제 인물·원문·조직이 아니다. `make.py`가 결정적으로 만든다 — 같은 코드면 바이트까지 같다.
계획 전체는 `docs/q3-presentation-plan.md` §5.

| 파일 | 내용 | 실데이터에서 대응하는 것 |
|---|---|---|
| `persons.json` | 320명, 8 PJT(`nebula/demo.py` `TEAM_TOPICS` 이름). 과제 0–4개, 과제 0개 인물과 `기타 …` 과제(미분류로 남음) 포함 | runbook §2 `persons.json` |
| `neighbors.json` | heritage 형식 `{"<id>":[{"id","similarity"}]}`, 인당 상위 30 | 전원 기준으로 다시 계산한 `neighbors.json` |
| `showcase.json` | 1부 스크립트의 예시 인물·PJT·과제 색인 | 발표 빌드에서만 지정 |

- 원문은 `nebula.demo.FakeClient`가 추출하는 문장 모양을 따른다. 그래서 LLM 없이 파이프라인을 완주한다.
- `neighbors.json`의 유사도는 합성 원문의 TF-IDF 코사인이다. 실제 임베딩 유사도가 아니다.
- `P000` "예시 인물"은 1부 분열 장면의 자리표시다(과제 4개, 역량 연결 모두 있음).

## 쓰기

```sh
python3 nebula/fixtures/q3/make.py
python3 -m nebula demo --input nebula/fixtures/q3/persons.json \
  --network nebula/fixtures/q3/neighbors.json --out <스크래치>/q3
```

결과 `<스크래치>/q3/nebula.html`을 브라우저로 연다. 입력이 합성이라 출력 디렉터리도 마음껏 열어도 된다.

## P000을 Jay 예시로 바꿀 때

1. `make.py`의 `showcase_text()`를 예시 원문으로 바꾸고 `make.py`를 다시 실행한다.
2. 예시 원문이 `FakeClient` 문장 모양이 아니면 `P000`의 추출 결과를 `--corrections`로 넣는다(runbook §7).
3. 커밋해도 되는 내용인지 먼저 확인한다. 안 되면 발표 빌드 때만 로컬에서 바꾼다.
