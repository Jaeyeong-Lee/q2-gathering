# 실험 브리프 — Hyperframes로 nebula 장면 하나를 결정적 MP4로 렌더

## 배경 (왜 이걸 하는가)

q3 발표 라이브 데모(`nebula.html`)는 브라우저에서 **실시간** 렌더된다. 실측된 문제:

> "전환 프레임 11→7개로 줄여도 **50ms 넘는 프레임이 7개**나 남아 있다. 320명 픽스처 기준 성능 목표: **50ms 프레임 3개 이하**"
> — q2-gathering `docs/engine-layout-round2-summary.md`

즉 무대에서 프레임 드랍 위험이 남아 있고, 발표장 네트워크 단절 시 폰트 CDN이 무용지물이 되는 문제도 별도로 있다.

Hyperframes는 HTML+CSS+GSAP 컴포지션을 **프레임 단위로 캡처해 MP4로 굽는다**. 애니메이션 구간을 미리 구워두면 무대 재생은 그냥 동영상 파일 재생이 되어 프레임 타임 문제가 구조적으로 사라진다. 이 실험이 답할 질문은 하나다:

**"그게 이 장면에서 실제로 되는가, 얼마나 걸리는가, 무엇이 깨지는가."**

## 이 저장소

scratch 저장소다. **q2-gathering 본 저장소가 아니다 — 그쪽은 절대 열지 마라.**

- `reference/nebula.template.html` — 원본 템플릿(빌드 전, `__PAYLOAD__` 플레이스홀더). 시각 언어와 장면 로직의 원본.
- `fixtures/synthetic-payload.json` — 합성 payload. 사람 64 / 과제 96 / 분류 6 / 사람 엣지 152. **전부 합성 데이터**(이름이 "합성 인물 001" 형태).
- `render/`, `video/` — 산출물을 여기에 만든다.

## 만들 장면 (하나만)

nebula 원본의 **장면 2 = 성운**. 전체 인터랙션 재현이 아니라 이 장면의 **motion**만이다.

1. 64명이 각자 자기 과제 별(작은 원 + 글로우)을 가진 상태에서 시작
2. 별들이 PJT별 격자 칸으로 **해쳐모인다** (2개 PJT → 2칸)
3. 한 칸이 강조된 뒤
4. 그 칸의 별들이 **과제군(카테고리) 클러스터로 다시 모여 성운**을 이룬다

총 ~8초. 시작·중간·끝이 한눈에 읽혀야 한다.

## 시각 언어 (원본에서 그대로 가져온다)

- 배경 `#0e1225`, 우주 영역에 radial-gradient 강조 `#25223f99`
- 강조색: `--violet #b8a3ed`, `--mint #a1dfd0`, `--rose #eeb3ce`
- 별 = 원 + `feGaussianBlur stdDeviation=3` 글로우. PJT 색은 payload `pjts[].color`
- 폰트: `"Apple SD Gothic Neo"`, `"Avenir Next"`
- 모션 감각: 느리고 부드럽게. 원본 전환은 `cubic-bezier(.22,.75,.18,1)` 계열, 1.65~2s
- 한국어 라벨을 쓸 경우 **합성 데이터에 있는 문구만** 쓴다

## 기술 요구 (Hyperframes 규약 — 어기면 렌더가 깨진다)

- 컴포지션마다 타임라인 등록: `window.__timelines["<composition-id>"] = tl`
- `gsap.timeline({ paused: true })` — 재생은 엔진이 제어한다
- `repeat: -1` 금지(유한 반복만), `Math.random()` / `Date.now()` 금지(결정적이어야 함), 타임라인을 async/setTimeout으로 만들지 말 것
- **hero frame 먼저**: GSAP 없이 정적 HTML+CSS로 가장 많은 요소가 동시에 보이는 순간을 먼저 완성 → 그 다음 `gsap.from()` 진입 / `gsap.to()` 퇴장
- `npx hyperframes lint` 통과
- 렌더: `npx hyperframes render --quality high --fps 30 --output render/nebula-scene2.mp4`

## 산출물

1. `video/` — Hyperframes 프로젝트 (`npx hyperframes init`)
2. `render/nebula-scene2.mp4` — 1920x1080, 30fps, 약 8초
3. `render/still-t4s.png` — t=4초 스틸 프레임 (검수용, ffmpeg로 추출)
4. `REPORT.md` — 아래 항목

## 검증 (직접 실행하고 결과를 REPORT.md에 붙인다)

```
ffprobe -v error -show_entries stream=width,height,r_frame_rate,duration \
  -of default=nw=1 render/nebula-scene2.mp4
```
- **결정성 확인: 같은 설정으로 두 번 렌더해서 duration이 동일한가**
- 렌더 wall time (1회차/2회차, `time` 으로 측정)
- `ls -la render/`

## REPORT.md에 담을 것

1. 산출물 경로 + ffprobe 결과 원문
2. 렌더 wall time (1회차/2회차)
3. 원본 장면 대비 **재현 못 한 것 / 달라진 것** — 솔직하게. 미화하지 마라.
4. 실제 payload(사람 320, 과제 수백)로 갈 때 예상 걸림돌
5. 이 용도(무대 발표용 장면 사전 렌더)에 Hyperframes가 맞는지 한 단락 판단
6. 설치/실행 중 막힌 것과 우회법 (다음 사람이 같은 데서 막히지 않게)

## 금지

- **q2-gathering 본 저장소에 접근하지 마라.** 다른 경로의 파일을 읽지 말고, 이 저장소 안에서만 작업한다.
- **실데이터 금지**: `fixtures/synthetic-payload.json` 외의 데이터를 쓰지 마라.
- 새 서비스 가입, 외부 API 키 발급, 네트워크 스토리지 업로드 금지.
- 이 저장소 밖으로 파일을 쓰지 마라(`/tmp` 정도는 허용).

## 커밋

작업이 끝나면 현재 브랜치에 커밋한다(`git add -A && git commit`). 푸시하지 마라. 커밋 메시지에 무엇을 검증했는지 남긴다.
