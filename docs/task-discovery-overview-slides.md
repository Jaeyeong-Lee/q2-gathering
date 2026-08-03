---
marp: true
theme: default
paginate: true
size: 16:9
html: true
---

# task-discovery — 무엇을, 왜 만들었나
### 제로베이스 설명 · 회의용

---

## 한 줄로

부서원 **~200명**이 쓴 회고에서, 팀의 **미래 과제 · 역량 갭**을 찾아
**워크숍 자료**로 만드는 작업

---

## 왜 시작했나

상사 요구: **"근원경쟁력 기반 팀 10년 로드맵"**

- "근원경쟁력 회고" = 부서원 각자가 자기 프로젝트·직급 맥락에서 "앞으로 할 일 ·
  필요한 역량 · 부족한 역량 · 방향"을 자유 서술한 글
- 총 ~200명분, **1회성 작성**(다시 안 씀), **보안상 외부 반출 금지**(사내망 LLM만 사용 가능)

---

## 문제: 회고엔 "로드맵"이 없다

회고는 **상향식·개인·근미래(1~3년)** 서술이다

- "10년 뒤 우리 팀은..." 같은 문장은 아무도 안 썼다
- 전략·시퀀싱·"꿈"은 데이터에 없다 — **없는 걸 만들면 환각**

그래서 데이터에서 뽑을 수 있는 건 **원재료**뿐: 방향·역량갭·모멘텀

---

## 방향 전환

산출물 = **완성된 로드맵이 아니라 "리더십 워크숍 입력물"**

- "10년"은 문자 그대로가 아니라 **해석 프레임**(토론을 촉발하는 틀)
- 시간축을 긋고 전략을 정하는 건 **워크숍에서 사람이** 한다
- 우리가 만드는 건: 팀이 지금 뭘 향해 가고 있는지 보여주는 **근거 있는 정리본**

---

## 산출물 구조 — Layer 1 / Layer 2

정직하게 가려고 **2층으로 분리**한다

| | Layer 1 — 근거 | Layer 2 — 해석 |
|---|---|---|
| 내용 | 팀 방향 지도 + 역량 갭 + 소수 의견 | Layer 1을 산문으로 종합한 것 |
| 인용 | 전부 **실명·원문 인용** | 문장마다 Layer 1 인용으로 **역추적 가능** |
| 라벨 | (그 자체가 사실 기반) | **"AI 해석 — 사실 아님, 종합 추론"** 명시 |
| 지금 | 이번 세션까지 만든 파이프라인 전체 | **오늘 컨셉 확정 필요** |

**절대 안 섞는다** — Layer 2는 별도 문서/섹션. Layer 1이 못 보여주는 "10년·꿈"을
Layer 2가 몰래 채우면 그건 창작이다 — Layer 2도 Layer 1 인용 밖으로 못 나간다.

---

## 어떻게 만드나 (5단계)

1. **추출** — 회고 원문에서 "미래 과제 / 보유 역량 / 필요 역량 / 방향" 뽑기
2. **카테고리 만들기** — 비슷한 과제들을 묶어서 이름 붙이기 (예: "Burn-in 신뢰성 고도화")
3. **배정** — 뽑힌 항목 하나하나를 해당 카테고리에 넣기
4. **집계** — 카테고리별 인원수 · 역량 있음/부족 · 준비도 계산
5. **정리** — 사람이 읽을 문서로(카테고리 카드 + 인용 + 표) 만들기

각 단계는 LLM이 하지만, 결과를 사람이 검토·수정할 수 있게 **중간 산출물을 전부 파일로 남긴다.**

---

## 각 단계의 스크립트 · 산출물

| 단계 | 스크립트 | 중간 산출물 |
|---|---|---|
| ① 추출 | `td_extract.py` | `extracted.json` |
| ② 카테고리 만들기 | `td_taxonomy.py` | `taxonomy.json` |
| ③ 배정 | `td_assign.py` | `assignments.json` |
| ④ 집계 | `td_aggregate.py` | `aggregates.json` |
| ⑤ 정리 | `td_render.py` | `workshop-input.md` (최종) |

모두 `data/task_discovery/` 밑에 쌓인다(회고 실데이터 포함이라 git 추적 안 함).

**실행은 한 줄:** `make td SOURCES=data/persons.json` — 5단계를 순서대로 다 돈다.
중간 산출물이 이미 있으면 그 단계는 건너뛴다(LLM 재호출 없음). 특정 단계만 다시
하고 싶으면 그 단계의 json만 지우고 다시 실행하면 됨.

---

## 안전장치 — 왜 이 결과를 믿을 수 있나

- **인용 검증** — 지어낸 말 금지. 원문에 실제 있는 문장만 근거로 인정
- **무신호 표시** — 할 말이 없는 회고는 억지로 분류하지 않고 "신호 없음"으로 따로 뺌
- **소수의견 보존** — 다수 의견에 묻히지 않게 인원 적은 카테고리도 별도 트랙으로 남김
- **커버리지 리포트** — 전체 중 몇 %가 무신호/기타로 빠졌는지 투명하게 공개

이 네 가지는 딥리서치 3종(방법론 검토)이 공통으로 요구한 필수 항목이다.

---

## 개발 방식

실데이터는 보안상 **개발 중엔 못 만진다** (반출 금지, 눈으로 튜닝 불가)

→ **가짜 데이터 + 가짜 LLM**으로 코드부터 완성·검증(테스트 87개)
→ **검증된 코드만** 사내망에 투입해서 실데이터를 돌린다

---

## 지금 산출물이 어떻게 생겼나 (예시 · 합성 데이터)

**카테고리 카드**
> STDF 기반 고장분석·품질(DPPM) 자동화 — 52명
> "HFT(고온 최종 검사) 과정에서 발생하는 DPPM(불량률)을 상세 FA(고장분석) 결과와
> 연동해 자동 진단 로직을 개선하고 싶습니다."

- **프로젝트 × 직급 교차표** — 어느 조직·연차에서 많이 나왔는지
- **소수의견 섹션** — 인원은 적지만 눈여겨볼 만한 방향
- **커버리지 리포트** — "대상 200명 · 무신호 N명 · Other N건"

---

## 최근에 추가한 것 — 카테고리 간 "관계"

카테고리를 낱개 목록으로 두지 않고, **관계**까지 표현

- "AX 기반 테스트 지능화"가 다른 카테고리들의 **상위개념**
- 서로 **연관은 있지만 위계는 없는** 카테고리 쌍도 표시

팀이 "온톨로지" 개념에 익숙하지 않은 점을 감안해, 우리 데이터로 실물을 만들며
**스터디 소재**로도 쓸 수 있게 별도 온보딩 문서를 마련해둠.

---

## 시각화 — 과거 유사도 네트워크는 재사용 안 함

Heritage Archive의 "사람-사람 유사도 그래프"는 이 데이터엔 안 맞음 — task-discovery는
**사람 간 유사도**가 아니라 **카테고리별 준비도·시간축·관계** 구조라서.

대신 같은 카테고리 데이터를 **두 가지 뷰**로 본다 (아래 슬라이드, 더미 데이터 예시):

1. **매트릭스뷰** — 카테고리를 시간축 × 준비도 위에 배치
2. **온톨로지 그래프뷰** — 카테고리 간 관계(`broader`/`related`)를 노드-엣지로

**오늘 회의에서 이 방향으로 갈지 확정 필요.**

---

## 시각화 예시 ① — 매트릭스뷰 (더미 데이터)

<svg viewBox="0 0 640 340" width="100%" height="340" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="640" height="340" fill="#fcfcfb" rx="8"/>
  <line x1="60" y1="20" x2="60" y2="300" stroke="#8b93a3" stroke-width="1"/>
  <line x1="60" y1="300" x2="600" y2="300" stroke="#8b93a3" stroke-width="1"/>
  <text x="330" y="325" font-size="14" fill="#545c6b" text-anchor="middle">시간축(horizon) — 단기 → 장기</text>
  <line x1="60" y1="110" x2="600" y2="110" stroke="#e2e2e2" stroke-dasharray="4 4"/>
  <line x1="60" y1="210" x2="600" y2="210" stroke="#e2e2e2" stroke-dasharray="4 4"/>
  <text x="52" y="65" font-size="12" fill="#0ca30c" text-anchor="end">이미 함</text>
  <text x="52" y="165" font-size="12" fill="#fab219" text-anchor="end">갭만 있음</text>
  <text x="52" y="265" font-size="12" fill="#6b7280" text-anchor="end">선행 신호</text>

  <circle cx="150" cy="70" r="28" fill="#0ca30c" fill-opacity="0.78"/>
  <text x="150" y="74" font-size="11" fill="white" text-anchor="middle">ATE 운영</text>
  <circle cx="430" cy="80" r="32" fill="#0ca30c" fill-opacity="0.78"/>
  <text x="430" y="84" font-size="11" fill="white" text-anchor="middle">AX 지능화</text>
  <circle cx="260" cy="160" r="22" fill="#fab219" fill-opacity="0.82"/>
  <text x="260" y="164" font-size="10" fill="white" text-anchor="middle">Yield 최적화</text>
  <circle cx="490" cy="180" r="18" fill="#fab219" fill-opacity="0.82"/>
  <text x="490" y="184" font-size="10" fill="white" text-anchor="middle">BIB 관리</text>
  <circle cx="190" cy="260" r="12" fill="#6b7280" stroke="#6b7280" stroke-dasharray="3 2" fill-opacity="0.6"/>
  <text x="190" y="282" font-size="10" fill="#545c6b" text-anchor="middle">벤더 종속 탈피</text>
  <circle cx="390" cy="250" r="12" fill="#6b7280" stroke="#6b7280" stroke-dasharray="3 2" fill-opacity="0.6"/>
  <text x="390" y="272" font-size="10" fill="#545c6b" text-anchor="middle">설비 예방정비</text>
</svg>

버블 크기 = 인원수, 색 = 준비도(이미 함 / 갭만 있음 / 선행 신호)

---

## 시각화 예시 ② — 온톨로지 그래프뷰 (더미 데이터)

<svg viewBox="0 0 640 360" width="100%" height="360" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="640" height="360" fill="#fcfcfb" rx="8"/>
  <line x1="320" y1="170" x2="150" y2="75"  stroke="#f3cc73" stroke-width="2.5"/>
  <line x1="320" y1="170" x2="480" y2="85"  stroke="#f3cc73" stroke-width="2.5"/>
  <line x1="320" y1="170" x2="220" y2="285" stroke="#f3cc73" stroke-width="2.5"/>
  <line x1="150" y1="75"  x2="480" y2="85"  stroke="#9aa3b2" stroke-width="1.5" stroke-dasharray="5 4"/>
  <line x1="220" y1="285" x2="420" y2="310" stroke="#9aa3b2" stroke-width="1.5" stroke-dasharray="5 4"/>

  <circle cx="320" cy="170" r="46" fill="#0ca30c" fill-opacity="0.85"/>
  <text x="320" y="166" font-size="12" fill="white" text-anchor="middle">AX 기반</text>
  <text x="320" y="182" font-size="12" fill="white" text-anchor="middle">테스트 지능화</text>

  <circle cx="150" cy="75" r="30" fill="#fab219" fill-opacity="0.85"/>
  <text x="150" y="79" font-size="10" fill="white" text-anchor="middle">D1b Yield</text>

  <circle cx="480" cy="85" r="30" fill="#fab219" fill-opacity="0.85"/>
  <text x="480" y="80" font-size="10" fill="white" text-anchor="middle">설비 예방보전</text>
  <text x="480" y="93" font-size="10" fill="white" text-anchor="middle">자동화</text>

  <circle cx="220" cy="285" r="26" fill="#6b7280" fill-opacity="0.8"/>
  <text x="220" y="289" font-size="10" fill="white" text-anchor="middle">BIB 관리</text>

  <circle cx="420" cy="310" r="22" fill="#6b7280" fill-opacity="0.8"/>
  <text x="420" y="314" font-size="9" fill="white" text-anchor="middle">Burn-in 신뢰성</text>

  <line x1="40" y1="345" x2="80" y2="345" stroke="#f3cc73" stroke-width="2.5"/>
  <text x="86" y="349" font-size="11" fill="#545c6b">broader (상위개념)</text>
  <line x1="260" y1="345" x2="300" y2="345" stroke="#9aa3b2" stroke-width="1.5" stroke-dasharray="5 4"/>
  <text x="306" y="349" font-size="11" fill="#545c6b">related (연관)</text>
</svg>

이 관계는 taxonomy 생성 시 LLM이 같이 뽑고, 코드가 댕글링·자기참조는 자동으로 걸러낸다

---

## 지금 상태

**됨**
- 파이프라인 전체 코드 완성, 테스트 87개 통과
- 사내망에서 taxonomy(카테고리) 생성 1차 확인 — 그룹핑이 적절해 보임

**아직 안 됨 / 열려 있음**
- 실데이터로 끝까지(배정 → 집계 → 최종 문서) 돌려서 확인
- 아래 3가지 미결 사항 확정

---

## 오늘 정해야 할 것

1. **Layer 2(해석) 컨셉** — 팀 총평만? 카테고리별 서사 페이지까지?
2. **시각화 방향** — 매트릭스뷰 + 온톨로지 그래프뷰로 갈지
3. **실명 표기 정책** — 회고 인용에 실명을 쓸지, 익명 처리할지
4. **"우리 팀" 범위** — 부서 전체인지, 특정 조직 단위인지
5. **산출물 형태 · 기한** — 워크숍 자료 한 번인지, 반복 산출인지

3~5는 **렌더(정리) 단계만 교체**하면 되는 구조라, 지금 정해도 앞단 코드는 안 바뀐다.
1~2는 이번에 새로 만들 부분이라 **컨셉부터 여기서 맞추고 들어가야** 함.

---

# 다음 단계

- 위 5가지 미결 확정 (오늘)
- Layer 2(해석) + 시각화, 컨셉대로 구현
- 실데이터로 전체 파이프라인 실행 → 최종 워크숍 자료 확인
- 카테고리 관계(온톨로지) 초안을 워크숍에서 사람이 검토

---

# 부록 — ① 추출 단계, 더 자세히

---

## 추출 단계가 뽑는 JSON 속성

| 필드 | 타입 | 위치 | 의미 |
|---|---|---|---|
| `signal_present` | bool | 최상위 | 이 회고에 뽑을 내용이 있는지 |
| `future_task[]` | item 배열 | 최상위 | 앞으로 하고 싶은/해야 할 과제 |
| `future_task[].horizon` | 단기\|장기\|불명 | future_task 항목에만 | 시간축 |
| `capability_have[]` | item 배열 | 최상위 | "이미 갖고 있다"고 말한 역량 |
| `capability_gap[]` | item 배열 | 최상위 | "부족하다/필요하다"고 말한 역량 |
| `direction` | item 또는 null | 최상위 (단수) | 전반적 지향 방향 한 문장 |

네 축 안의 **item 공통 구조**: `text`(서술) + `quotes[]`(원문 발췌)

---

## 간단히 적은 프롬프트 (실제 로직 축약)

```
다음은 김민준(CL2, HFT/양산기술)의 근원경쟁력 회고다.
미래과제·보유역량·필요역량·지향방향을 추출하라.

JSON으로만 답하라:
{
  "signal_present": true/false,
  "future_task": [{"text": "...", "horizon": "단기|장기|불명", "quotes": ["원문 그대로"]}],
  "capability_have": [{"text": "...", "quotes": ["..."]}],
  "capability_gap": [{"text": "...", "quotes": ["..."]}],
  "direction": {"text": "...", "quotes": ["..."]} 또는 null
}

규칙:
- quotes는 원문에서 글자 그대로 발췌 (창작·의역 금지)
- text는 quotes의 서술이지, 그대로 베낀 게 아니어야 함
- 내용 없으면 빈 배열 / 신호 없으면 signal_present=false + 전부 비움

원문:
<회고 텍스트 그대로>
```

---

## `quote`가 뭔가

`text`는 LLM이 **요약한 문장**, `quotes`는 그 요약의 **증거로 삼은 원문 그대로**

- **원문 대조** — quote가 실제로 회고 원문 안에 있는지 확인(공백·개행 무시).
  없으면 그 항목 통째로 폐기 → 지어낸 인용 차단
- **복붙 방지** — text가 quotes를 그대로 베낀 건 아닌지 확인.
  베낀 거면 폐기 → "서술 없는 복붙"을 강제로 막음

두 검증 중 하나라도 실패하면 **그 항목만** 버려진다 — 그 사람 회고 전체가 아니라.
