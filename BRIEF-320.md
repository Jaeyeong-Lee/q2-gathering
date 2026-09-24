# 실험 브리프 2 — 320명 실규모 확장 렌더

## 배경

1차 실험(같은 저장소, 이전 커밋)은 **64명 / 96과제 / 2 PJT** 합성 payload로 성운 장면 하나를 8초에 구웠고, 결과는 `render/nebula-scene2.mp4` (1920×1080, 30fps, 8.0s, 1.87MB), 렌더 wall time 32.6s / 23.9s, 2회 렌더 완전 동일(결정성 확인)이었다. 상세는 `REPORT.md`.

이번 목표는 **실데이터 규모로 확장했을 때 무너지는지**를 보는 것이다. q3 발표의 실제 규모는 **320명 / 과제 수백 / 8 PJT**이고, 원본 문서의 성능 목표는 "320명 픽스처 기준 50ms 프레임 3개 이하"다.

**실데이터는 쓰지 않는다** — 아래 합성 fixture가 그 규모를 그대로 만든 것이다.

## 이 저장소

- `reference/nebula.template.html` — 원본 템플릿(시각 언어·장면 로직의 원본)
- `fixtures/payload-320-slim.json` — **이번에 쓸 것.** 합성 320명 / 456과제 / 24분류 / 8 PJT / 엣지 832. 사람은 `id,pjt,x,y,name`, 과제는 `id,person,pjt,category,seq,seed,horizon`.
- `fixtures/payload-320.json` — 같은 payload의 전체본(636KB). 라벨·문구가 더 필요할 때만 열어라. **통째로 cat 하지 마라**(컨텍스트를 태운다). 필요하면 파이썬으로 필요한 키만 뽑아라.
- `video/` — 1차에서 만든 Hyperframes 프로젝트. **이걸 확장해서 재사용하는 걸 우선 고려**하라(사람 수만 바뀌는 구조라면 그게 맞다). 새로 만들어도 되지만, 1차 산출물 `render/nebula-scene2.mp4`와 `REPORT.md`는 **덮어쓰지 말고 그대로 둬라.**
- `render/` — 새 산출물

## 만들 것

1차와 **같은 성운 장면**을 320명 규모로: 별들이 8개 PJT 격자로 해쳐모이기 → 한 칸 강조 → 그 칸의 별들이 과제군 클러스터 성운으로 모이기. 8초, 1920×1080, 30fps.

원본의 PJT 격자는 `COLS=4`다 — 8개 PJT면 4×2가 된다. 320명에서 이 레이아웃이 성립하는지 확인하라.

## 산출물 (4개)

1. `render/nebula-scene2-320.mp4` — 원본 구성 그대로(모든 SVG 필터 유지)
2. `render/nebula-scene2-320-nofilter.mp4` — **필터 비용 분리 측정용.** 성운 연기(`feTurbulence`+`feDisplacementMap`+`feGaussianBlur`)를 장면 전체에 반복 적용하지 말고, 장면당 1개 요소(또는 배경 1장)로 줄인 버전. 나머지 모션·색은 동일하게.
3. `render/still-320-t2s.png`, `render/still-320-t4s.png`, `render/still-320-t6s.png` — 가독성 검수용 스틸 3장
4. `REPORT-320.md`

## REPORT-320.md에 담을 것 (숫자 중심)

1. **렌더 wall time 표** — as-is / nofilter 각 2회. 가능하면 setup · capture · encode 단계 분리해서.
2. **1차(64명) 대비 배율** — 사람 5배, 과제 4.75배가 렌더 시간에 어떻게 반영됐나.
3. **필터가 캡처 시간에 미친 영향** — as-is vs nofilter 차이를 초 단위로. "필터가 병목"이라는 가설이 맞았는지 판정.
4. **8 PJT 격자 레이아웃** — 4×2가 성립했는지, 셀 안 별이 넘치지 않는지.
5. **가독성 판정** — 320명 별이 뭉개지는지. 스틸 3장을 근거로. 좋게 말하지 말고 실제로 읽히는지 판단하라.
6. **무대 준비 시간 추정** — 8초 장면 1개당 X초면, 발표 4장면을 사전 렌더하면 총 몇 분인가. 노트북 1대로 감당 가능한가.
7. **실데이터로 갈 때 남은 걸림돌** — 이번에도 합성이므로 실데이터에서만 나타날 문제를 따로 적어라.

## 검증 (직접 실행하고 원문을 붙여라)

```
ffprobe -v error -show_entries stream=width,height,r_frame_rate,nb_frames -show_entries format=duration,size \
  -of default=nw=1 render/nebula-scene2-320.mp4
ffmpeg -v error -i render/nebula-scene2-320.mp4 -f null -   # 디코드 무결성 (출력 없으면 정상)
```
- **결정성**: 같은 설정 2회 렌더의 duration·파일 크기가 동일한가

## 기술 규약 (1차와 동일 — 어기면 렌더가 깨진다)

- `window.__timelines["<id>"] = tl` 등록, `gsap.timeline({paused:true})`
- `repeat: -1` 금지, `Math.random()`/`Date.now()` 금지(결정적), async로 타임라인 생성 금지
- `npx hyperframes lint` 통과
- 렌더: `npx hyperframes render --quality high --fps 30 --output <경로>`

## 금지

- **q2-gathering 본 저장소에 접근하지 마라.** 이 저장소 안에서만 작업한다.
- 실데이터 금지: `fixtures/`의 합성 payload 외 데이터를 쓰지 마라.
- 외부 업로드·서비스 가입 금지.
- 1차 산출물(`render/nebula-scene2.mp4`, `render/still-t4s.png`, `REPORT.md`)을 덮어쓰지 마라.

## 커밋

끝나면 현재 브랜치에 커밋한다. 푸시하지 마라.
