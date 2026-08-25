# task-discovery

부서원 회고 원문에서 미래 역량 지도를 뽑아 **리더십 워크숍의 입력물**로 내놓는 파이프라인.
로드맵을 만들지 않는다 — 시간축·시퀀싱·전략은 데이터에 없고 워크숍에서 사람이 채운다.

## Language

**facet**:
`signal_present`인 사람의, 4축 중 비어있지 않은 항목 하나. taxonomy·assign·색인이 모두 이 단위로 돈다.
_Avoid_: 항목(모호), 문장, 청크

**축 (axis)**:
facet이 답하는 질문의 종류 — `future_task` · `capability_have` · `capability_gap` · `direction`.
한 facet은 정확히 한 축에 속한다.
_Avoid_: 필드, 카테고리

**카테고리**:
`taxonomy.json`이 정의하는 **주제** 묶음. "무엇에 관한 과제냐"에 답한다. facet 하나는 카테고리 하나에 배정된다.
_Avoid_: 클러스터, 토픽, 태그

**AX**:
AI Transformation. 이 저장소에서 AX는 **카테고리가 아니라 카드의 직교 속성**이다 —
"무엇에 관한 과제냐"(카테고리)와 "AI로 하겠다는 것이냐"(AX)는 다른 질문이라 같은 자리에서 경쟁시키지 않는다.
_Avoid_: AI 카테고리, AX 축

**`ax_mentioned`**:
그 과제의 **원문 인용에 AX 표현이 실제로 적혀 있었다**는 관찰. "이것이 진짜 AX 과제다"라는 판정이 아니다.
실체 판정은 파이프라인이 하지 않고 워크숍에서 사람이 한다.
_Avoid_: `is_ax`, `ax`, AX 여부

**확산도 (spread)**:
한 카테고리를 말한 서로 다른 조직·직급의 수(`pjt_spread`·`cl_spread`). "우리 부서만의 문제가 아니다"를 나타내는 유일한 신호.
_Avoid_: 커버리지(이건 추출 수율을 가리키는 다른 말이다)
