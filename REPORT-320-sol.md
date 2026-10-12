# 320명 실규모 확장 렌더 보고서

## 0. 결론 요약

- 입력은 합성 fixture `fixtures/payload-320-slim.json`: **320명 / 456과제 / 24분류 / 8 PJT / 832 엣지**다.
- 최종 as-is 영상은 **1920×1080 / 30fps / 240프레임 / 8.000000초 / 4,562,410 bytes**다.
- 8 PJT의 원본 `COLS=4` 배치는 **4×2로 성립**하며, 별 중심과 반지름 기준으로 셀 밖으로 넘친 과제 별은 없다.
- 다만 320명에서는 **개별 별을 읽을 수 없다**. PJT·과제군의 색/밀도/형태는 읽히지만 사람이나 과제 하나씩 구분하는 화면은 아니다.
- 성운 연기 필터를 사전 래스터 배경 1장으로 바꾼 nofilter는 캡처+인코드 평균을 **1.8초(2.9%)** 줄였다. 따라서 **성운 연기 필터가 주 병목이라는 가설은 기각**한다.
- 정확성 우선 최종 경로의 장면당 wall time은 평균 **63.95초**다. 발표 4장면 직렬 사전 렌더는 약 **4.26분**, 여유를 포함해 **5분 내외**로 노트북 1대에서 감당 가능하다.
- 자동 5워커 경로에서는 정확히 4.0초인 프레임 120에서 텍스트가 한 프레임 빠지는 결함을 발견했다. 최종 산출물은 **1 worker + `HF_STATIC_DEDUP=false` + fast capture off**로 다시 렌더해 해당 결함이 없음을 확인했다.

## 1. 산출물

- `render/nebula-scene2-320.mp4` — as-is, 원본 SVG 필터 유지
- `render/nebula-scene2-320-nofilter.mp4` — 성운 연기를 `video/assets/nebula-gas-320.png` 한 요소로 사전 래스터화
- `render/still-320-t2s.png`
- `render/still-320-t4s.png`
- `render/still-320-t6s.png`
- `REPORT-320.md`

구현 소스:

- `video/scripts/build-320.mjs`
- `video/compositions/nebula-scene2-320.html`
- `video/compositions/nebula-scene2-320-nofilter.html`
- `video/assets/nebula-gas-320.svg`
- `video/assets/nebula-gas-320.png`

렌더 조건은 Hyperframes `0.8.72`, 1920×1080, 30fps, quality high, hardware GPU, 1 worker다. 프로젝트의 1차 결과와 CLI 재현성을 유지하기 위해 저장소에 고정된 `0.8.72`를 사용했다.

## 2. 렌더 wall time

최종 산출물은 정확성 우선 경로로 각각 2회 렌더했다.

| 변형 | 회차 | wall time (`time real`) | Hyperframes total | setup | capture + streaming encode | assemble | 파일 크기 |
|---|---:|---:|---:|---:|---:|---:|---:|
| as-is | 1 | 66.82s | 65.1s | 0.4s | 64.5s | 0.1s | 4,562,410 bytes |
| as-is | 2 | 61.07s | 59.2s | 0.4s | 58.5s | 0.1s | 4,562,410 bytes |
| nofilter | 1 | 63.99s | 62.3s | 0.2s | 61.9s | 0.1s | 4,559,168 bytes |
| nofilter | 2 | 59.54s | 57.9s | 0.2s | 57.5s | 0.1s | 4,559,168 bytes |
| **as-is 평균** |  | **63.95s** | **62.15s** | **0.40s** | **61.50s** | **0.10s** |  |
| **nofilter 평균** |  | **61.77s** | **60.10s** | **0.20s** | **59.70s** | **0.10s** |  |

1워커 경로는 프레임 캡처와 H.264 인코드를 스트리밍으로 겹쳐 수행한다. 따라서 CLI가 `encode (during capture)`로 보고하며 capture와 encode를 별도 숫자로 분리할 수 없다. 표의 capture는 인코드가 포함된 값이다.

### 결정성

| 변형 | 두 렌더 duration | 두 렌더 파일 크기 | SHA-256 | 판정 |
|---|---:|---:|---|---|
| as-is | 8.000000s / 8.000000s | 4,562,410 / 4,562,410 bytes | 두 파일 모두 `adbcbdf4f4d39b281ee4bc1b5d8cb36be9d0b749045f7d61177647c5a96c3cf1` | 완전 동일 |
| nofilter | 8.000000s / 8.000000s | 4,559,168 / 4,559,168 bytes | 두 파일 모두 `8bd614c2179f867ac28e416c624419f5e007481c3107ae60dc103d70b2ee7cae` | 완전 동일 |

두 변형 모두 컨테이너 바이트뿐 아니라 디코딩한 240개 프레임의 `framemd5`도 일치했다.

## 3. 1차 64명 대비 배율

| 항목 | 1차 | 이번 | 데이터 배율 |
|---|---:|---:|---:|
| 사람 | 64 | 320 | 5.00× |
| 과제 | 96 | 456 | 4.75× |
| PJT | 2 | 8 | 4.00× |
| as-is 파일 크기 | 1,868,740 bytes | 4,562,410 bytes | 2.44× |

1차의 wall time은 32.6s / 23.9s, 평균 **28.25s**였다. 이번 정확성 우선 최종 as-is는 66.82s / 61.07s, 평균 **63.95s**로 **2.26×**다. 노드 수는 약 5배가 됐지만 wall time은 2.26배에 그쳤다.

단, 이 비교에는 중요한 조건 차이가 있다. 1차는 5워커였고 이번 최종 산출물은 1워커다. 이번에도 자동 5워커 성능만 보면 as-is wall time은 49.63s / 47.48s, 평균 **48.56s**, 즉 1차 평균의 **1.72×**였다. 하지만 5워커 결과는 프레임 120에서 텍스트가 한 프레임 누락되어 최종 산출물로 채택하지 않았다.

1차의 대표 capture 11.4s와 최종 as-is capture+encode 평균 61.5s를 단순 비교하면 **5.39×**지만, 이것도 5워커 대 1워커 차이를 포함하므로 데이터 증가만의 배율로 해석하면 안 된다. 같은 자동 5워커 경로에서는 총 시간이 1.72배였다는 쪽이 규모 확장 자체를 더 잘 보여준다.

## 4. 필터 비용 분리

nofilter는 런타임의 `feTurbulence + feDisplacementMap + feGaussianBlur` 성운 연기를 제거하고, 동일한 세 성운 모양을 투명 PNG 한 장으로 사전 래스터화했다. 별의 `starGlow`와 보조 성운의 일반 `blur`는 그대로 유지했다.

| 지표 | as-is 평균 | nofilter 평균 | nofilter 절감 |
|---|---:|---:|---:|
| wall time | 63.95s | 61.77s | **2.18s / 3.4%** |
| capture + streaming encode | 61.50s | 59.70s | **1.80s / 2.9%** |
| Hyperframes total | 62.15s | 60.10s | **2.05s / 3.3%** |

**판정: “성운 연기 필터가 병목”이라는 가설은 맞지 않았다.** 제거 효과는 측정되지만 3% 안팎이다. 이 장면에서 더 큰 비용은 320명 사람 노드와 456개 과제 노드, 그리고 이들에 반복 적용되는 776개의 `starGlow` 및 전체 프레임 스크린샷 캡처 쪽으로 보는 것이 타당하다. 다만 이것은 로그와 구조를 바탕으로 한 추론이며, 이번 nofilter는 의도대로 성운 연기만 분리했기 때문에 `starGlow` 전체의 비용까지 측정한 실험은 아니다.

## 5. 8 PJT 4×2 격자 레이아웃

원본 수식 `COLS=4`, `width=1040/4`, `height=480/2`를 그대로 사용했다.

- 셀 크기: **260×240 SVG px**
- 배치: **4열×2행**
- 셀별 과제 수: 92, 62, 46, 45, 38, 82, 28, 63
- 반지름 9인 과제 별까지 포함한 최악의 셀 경계 여유: 좌 25.0px / 우 26.2px / 상 63.9px / 하 20.3px
- 결론: **셀 밖으로 넘치는 별은 없다.** 4×2 레이아웃 자체는 성립한다.

하지만 “안 넘친다”와 “안 겹친다”는 다르다. 가장 조밀한 `기술 기획` 셀은 92개 과제가 들어가며 최근접 거리 중앙값이 6.52px다. 과제 별의 글로우 원 지름은 18px이므로 92개 중 **96.7%가 최근접 별과 18px 미만**이고, 시각적으로 대부분 겹친다. 셀 경계는 지키지만 내부 밀집은 심하다.

## 6. 가독성 판정

### `still-320-t2s.png`

- 8개 PJT의 색 영역과 전체 분포는 구분된다.
- 사람 별과 과제 별의 크기 차이는 보이지만, 320명과 456과제가 겹쳐 개별 별을 추적하거나 수를 세는 것은 불가능하다.
- 판정: **전체 구조는 읽힘 / 개별 데이터는 읽히지 않음**.

### `still-320-t4s.png`

- 4×2 셀과 8개 PJT 라벨은 읽힌다.
- 강조 셀 `기술 기획`은 테두리와 밝기로 즉시 구분된다.
- 비강조 셀은 의도적으로 어둡지만 PJT 이름과 별 무리는 식별 가능하다.
- 강조 셀 내부 92개 과제는 여러 덩어리로 뭉개져 하나씩 읽을 수 없다.
- 판정: **PJT 선택 상태는 명확 / 셀 내부 개별 과제 가독성은 부족**.

### `still-320-t6s.png`

- 강조 PJT의 세 과제군 라벨은 읽힌다.
- 각 과제군은 32개, 31개, 29개 과제를 가지며 성운과 글로우가 겹쳐 개별 별의 수나 소속 경계를 정확히 읽기는 어렵다.
- 성운 연기가 라벨 근처까지 올라와 지역 대비를 낮추지만, 세 라벨 자체는 식별 가능하다.
- 판정: **과제군 3개의 존재와 위치는 읽힘 / 과제 단위 읽기는 불가능**.

종합하면 이 장면은 발표에서 “많은 기록이 PJT와 과제군으로 모인다”는 서사를 전달하는 데는 성공한다. 그러나 320명 전체를 화면에서 검수하거나 개별 별의 의미를 읽는 용도로는 실패한다. 확대, 샘플링, 라벨 온디맨드, 또는 밀도 기반 표현이 별도 필요하다.

## 7. 무대 준비 시간 추정

- as-is 장면 1개 평균 wall time: **63.95초**
- 4장면 직렬 렌더: `63.95 × 4 = 255.8초 = 4.26분`
- 관측된 느린 회차 기준: `66.82 × 4 = 267.3초 = 4.46분`
- 파일 크기 단순 추정: `4.56MB × 4 ≈ 18.2MB`

**판정: 노트북 1대로 감당 가능하다.** 리허설 직전 즉석 생성보다 발표 전 미리 렌더하는 방식이 안전하며, 4장면 전체에 약 5분을 잡으면 된다. 1워커 직렬 경로라 CPU/GPU 메모리 압박도 낮다.

## 8. 원본의 50ms 프레임 목표와의 관계

이번 수치는 브라우저 실시간 프레임 시간이 아니라 Hyperframes의 오프라인 스크린샷 캡처+인코드 시간이다. 1워커 as-is capture+encode 평균을 240프레임으로 나누면 약 256ms/출력 프레임이지만, 여기에 CDP 스크린샷과 H.264 인코드가 포함되므로 원본의 “50ms 초과 프레임 3개 이하” 목표와 직접 비교할 수 없다.

따라서 이번 실험이 증명한 것은 **실시간 50ms 목표 달성 여부가 아니라, 그 목표를 못 맞추더라도 320명 장면을 약 1분에 결정적으로 사전 렌더해 무대에서는 30fps MP4로 재생할 수 있다는 것**이다. 50ms 목표 자체는 실제 브라우저 앱에서 Performance trace와 프레임 타임 계측을 별도로 해야 한다.

## 9. 실데이터로 갈 때 남은 걸림돌

1. **PJT·분류 불균형**: 합성 fixture는 PJT당 28~92개 과제, 강조 PJT당 3분류로 비교적 통제돼 있다. 실데이터에서 한 PJT나 한 분류로 쏠리면 현재 고정 반경 클러스터는 더 심하게 뭉개진다.
2. **긴 라벨과 실제 문구**: 실제 PJT명·분류명이 더 길거나 줄바꿈을 포함하면 셀 라벨과 성운 라벨이 겹칠 수 있다. slim fixture는 이름이 짧다.
3. **좌표 결측·이상치**: 이번 fixture는 `has_layout=true`, x/y가 0~1에 정규화돼 있다. 실데이터의 null, 범위 밖 좌표, 동일 좌표 중복은 별도 방어가 필요하다.
4. **폰트 환경**: 현재 로컬 `Apple SD Gothic Neo`에 의존한다. 발표 노트북이 바뀌면 폰트 메트릭과 줄바꿈이 달라질 수 있으므로 폰트 파일 내장이 안전하다.
5. **데이터 품질과 식별자**: 사람-과제-PJT-분류 참조가 끊기거나 중복 ID가 있으면 노드 생성과 클러스터 배치가 실패할 수 있다.
6. **엣지와 상호작용**: fixture의 832개 엣지는 이번 1차 장면 계승 구현에서도 표시하지 않았다. 실데이터에서 관계선을 동시에 보여주면 DOM과 시각 혼잡이 크게 늘어난다.
7. **실시간 목표 미검증**: 실제 앱의 hover, 클릭, 검색, 패널, 접근성 요소까지 포함한 50ms 프레임 목표는 별도 브라우저 프로파일링이 필요하다.
8. **Hyperframes 병렬 캡처 결함**: 자동 5워커에서 프레임 120의 텍스트가 한 프레임 누락됐다. 최종은 1워커로 우회했지만, 빠른 병렬 렌더를 운영 경로로 쓰려면 Hyperframes 버전 업 후 재검증이 필요하다.

## 10. 검증 원문

### Hyperframes lint

```text
$ npx --yes hyperframes@0.8.72 lint --verbose
◆  Linting video/3 files

  ⚠ [.../video/index.html:23:3] nested_structure_needs_subcomposition [nebula-scene]: <div id="nebula-scene"> is a timeline element that contains nested <div>.

◇  0 error(s), 1 warning(s)
```

경고는 1차부터 존재한 기존 `video/index.html` 구조 권고다. 새 320 컴포지션에는 lint error가 없다. 두 변형 모두 `check --at 2,4,6`에서 runtime 0, layout 0, motion 0, contrast 17/17 통과했다.

### 요구된 ffprobe

```text
$ ffprobe -v error -show_entries stream=width,height,r_frame_rate,nb_frames -show_entries format=duration,size \
  -of default=nw=1 render/nebula-scene2-320.mp4
width=1920
height=1080
r_frame_rate=30/1
nb_frames=240
duration=8.000000
size=4562410
```

### 요구된 디코드 무결성

```text
$ ffmpeg -v error -i render/nebula-scene2-320.mp4 -f null -
```

출력 없음, exit code 0 — 정상.

### nofilter ffprobe 및 디코드

```text
$ ffprobe -v error -show_entries stream=width,height,r_frame_rate,nb_frames -show_entries format=duration,size \
  -of default=nw=1 render/nebula-scene2-320-nofilter.mp4
width=1920
height=1080
r_frame_rate=30/1
nb_frames=240
duration=8.000000
size=4559168

$ ffmpeg -v error -i render/nebula-scene2-320-nofilter.mp4 -f null -
```

디코드 출력 없음, exit code 0 — 정상.
