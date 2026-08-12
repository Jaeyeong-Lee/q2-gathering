# HTML 리포트 톤앤매너 — 다른 세션에 줄 지시문

아래를 그대로 붙여넣으면 같은 톤의 리포트가 나온다.

---

## 지시문 (여기부터 복사)

자체 완결형 HTML 파일 하나로 리포트를 써라. 아래 규칙을 지켜라.

### 기술

- Tailwind는 CDN(`https://cdn.tailwindcss.com`), Mermaid는 ESM CDN(`mermaid@11`)으로
  불러온다. 빌드 스텝 없음. 커스텀 CSS는 `<style>`에 5줄 이하로만.
- `mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose",
  flowchart: { curve: "basis" } })`
- 본문은 `<main class="mx-auto max-w-5xl space-y-14 px-6 py-12">`.

### 타이포 — 이게 시그니처다

| 용도 | 스타일 |
|---|---|
| 제목(h1/h2/h3) | **`font-serif`** — 본문과 대비되는 세리프 |
| 본문 | 기본 sans |
| 파일경로·심볼·수치 | `font-mono text-xs` |
| 섹션 눈썹 라벨 | `.lbl` = `font-size:10px; letter-spacing:.12em; text-transform:uppercase` + `text-slate-500` |

`.lbl`을 아낌없이 써라. 모든 카드·구역 위에 작은 대문자 라벨이 하나씩 붙는 게
이 리포트의 리듬이다.

### 색 — 의미 있는 곳에만

- 바탕 `bg-stone-50`, 글자 `text-slate-900`, 카드 `bg-white border-slate-200`
- **emerald** = 강한 추천 / 좋은 상태
- **amber** = 주의 · 기존 결정과 충돌
- **red** = 문제 · 유출 · 실측된 버그
- 그 외엔 슬레이트 무채색. 장식용 색은 쓰지 마라.

### 구조

1. **헤더** — `.lbl` 눈썹 + 세리프 h1 + 오른쪽에 날짜·규모 수치(테스트 수, 파일별 줄 수).
   아래에 `border-b`.
2. **범례** — 그림에서 쓸 기호를 인라인 SVG로 4칸 그리드. (실선=X, 점선=Y …)
3. **실측 박스** — 빨간 테두리 박스에 **직접 확인한 사실 하나**를 숫자와 함께.
   추측이 아니라 재현한 것만. 이게 리포트 전체의 신뢰를 만든다.
4. **번호 붙은 항목들** — `<article id="c1">` … 각각:
   - 세리프 h2 `1 · 제목` + 강도 배지(emerald `Strong` / slate `Worth exploring`)
   - `font-mono text-xs`로 관련 파일:라인 한 줄
   - **Before / After 나란히** — `grid gap-4 md:grid-cols-2`, 각 카드에 `.lbl` 제목
   - 마지막에 `✦`로 시작하는 이득 목록 `grid sm:grid-cols-2`
5. **Top recommendation** — `border-2 border-slate-900`으로 확실히 무겁게. 세리프 3xl.
6. **푸터** — 사용한 어휘를 `font-mono`로 나열. 무엇을 안 다뤘는지도 한 줄.

### 그림

- **관계가 그래프면 Mermaid** — 호출 흐름, 의존, 시퀀스.
  문제 노드는 `classDef leak stroke:#dc2626,fill:#fef2f2`, 얇은 모듈은
  `fill:#f8fafc,stroke:#cbd5e1`, 좋은 모듈은 `fill:#0f172a,color:#fff`.
- **비유·질량·단면이면 손으로 그린 div/SVG.** Mermaid로 다 하지 마라 — 7:3 정도로
  섞어야 편집물처럼 보인다.
- Before/After는 **반드시 쌍으로**. 하나만 있으면 개선이 안 보인다.

### 글쓰기

- **수치와 파일:라인을 문장 안에 넣어라.** "탭은 30대인데 칸은 0건", "23개 파라미터",
  "`web.py:313`". 형용사 대신 숫자.
- 짧은 평서문. 완충 표현("~일 수도 있습니다", "고려해볼 만합니다") 금지.
- 기존 결정과 충돌하면 amber 박스로 **명시하고**, 그 결정이 맞는지 코드가 맞는지
  분명히 말해라.
- 도메인 용어는 프로젝트 용어집 그대로. 새로 지어내지 마라.
- 한국어 본문에 영어 기술어가 섞이는 건 괜찮다. 억지로 번역하지 마라.

### 하지 말 것

- 그라디언트 배경, 아이콘 폰트, 애니메이션, 이모지 불릿
- 내용 없는 요약 카드("총 6개 항목" 같은)
- 같은 정보를 표와 그림으로 두 번
- 색으로만 구분되는 정보 (라벨을 같이 달아라)

## 지시문 끝

---

## 원본

`docs/reports/architecture-review-2026-08-09.html` — 25KB, 항목 6개,
mermaid 7 · 손그림 SVG 3. 이 문서의 규칙은 전부 그 파일에서 뽑은 것이다.

**CDN을 쓰므로 오프라인/내부망에서는 스타일 없이 뜬다.** 그 환경에서 새 리포트를
만들 거라면 Tailwind·Mermaid를 인라인하거나, 애초에 마크다운으로 쓰는 게 낫다 —
이 톤의 핵심은 타이포 대비와 `.lbl` 리듬이라 CSS가 안 오면 남는 게 없다.
