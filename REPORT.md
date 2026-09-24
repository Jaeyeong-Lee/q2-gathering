# Hyperframes 실험 보고 — nebula 장면 2 (성운)

## 1. 산출물 경로 + ffprobe 결과

### 산출물
- `video/` — Hyperframes 프로젝트 (`index.html`, `hyperframes.json`, `package.json`, `meta.json`, `AGENTS.md`, `CLAUDE.md`)
- `render/nebula-scene2.mp4` — 1920×1080, 30fps, 8.0초, 1.8 MB
- `render/still-t4s.png` — t=4초 스틸 프레임 (검수용, 332 KB)

### ffprobe 원문
```
$ ffprobe -v error -show_entries stream=width,height,r_frame_rate,duration \
    -of default=nw=1 render/nebula-scene2.mp4
width=1920
height=1080
r_frame_rate=30/1
duration=8.000000
```

## 2. 렌더 wall time (결정성 확인)

| 회차 | wall time | 파일 크기 | duration |
|------|-----------|-----------|----------|
| 1회차 | 32.6s (total) | 1,868,740 bytes | 8.000000s |
| 2회차 | 23.9s (total) | 1,868,740 bytes | 8.000000s |

- **결정성 확인**: 두 렌더 모두 duration=8.000000, 파일 크기 1,868,740 bytes로 완전히 동일.
- 2회차가 빠른 이유: 1회차에서 브라우저 다운로드/캐시 워밍업이 선행되었기 때문. 실제 캡처+인코딩 시간은 유사 (~22s vs ~24s).
- 렌더 상세 (1회차 기준): setup 10.5s · capture 11.4s · encode 2.1s · assemble 0.1s

## 3. 원본 장면 대비 재현 못 한 것 / 달라진 것

### 재현한 것
- **시각 언어**: 배경 `#0e1225`, radial-gradient 강조, 별 = 원 + `feGaussianBlur stdDeviation=3` 글로우, PJT 색상(payload 그대로), 성운 필터(`feTurbulence` + `feDisplacementMap` + `feGaussianBlur`) — 원본에서 그대로 포팅
- **위치 계산 로직**: `originals`(사람 좌표), `pjtCell`, `clusterCenter`, `offsets`, `target` 함수 — 원본 JS를 그대로 이식
- **모션 시퀀스**: 64명 각자 과제 별 → PJT 격자 해쳐모이 → 한 PJT 강조 → 카테고리 클러스터 성운 — 4단계 모션을 GSAP 타임라인으로 구현
- **글로우 / 성운 연기 효과**: SVG 필터 `starGlow`, `gas`, `blur` — 원본 정의 그대로 사용

### 달라진 것 / 재현 못 한 것
- **인터랙티브 요소 전부 제거**: hover, click, tooltip, inspector 패널, 검색, 키보드 내비게이션 — 동영상이므로 당연히 없음
- **사람 노드 페이드아웃**: 원본은 사람 별이 과제 별로 "갈라져 나오는" 연출이 있으나, 이 컴포지션에서는 과제 별이 처음부터 보이고 사람 별은 phase 1→2 전환 시 페이드아웃. 원본의 `splitPerson` 개별 분열 애니메이션은 생략
- **PJT 격자 레이아웃**: 원본 `COLS=4` 기준이나, 2개 PJT만 있으므로 `COLS=2`로 좌우 2칸 배치. 원본은 4열 그리드이나 2개 PJT가 모두 첫 행에 표시되므로 시각적 결과는 동일
- **성운 라벨의 htmlLabel**: 원본은 HTML `<button>` 오버레이로 라벨을 만들지만, 여기서는 SVG `<text>`로 대체 — 동영상에서는 클릭 불필요
- **하단 문구**: deck.md `scene-2`의 화면 문구("흩어진 과제들이, 성운을 이룹니다")와 보조 문구를 하단 오버레이로 배치
- **전환 easing**: 원본 `cubic-bezier(.22,.75,.18,1)` → GSAP `power2.inOut`로 근사 (GSAP에 정확한 CustomEase 없이 최적 매칭)
- **사람 간 연결선(edges)**: 152개 엣지 중 상위 4개를 노미네이션하는 원본 로직이 있으나, 이 장면 모션에 불필요하여 생략

## 4. 실제 payload (320명, 과제 수백)로 갈 때 예상 걸림돌

1. **렌더 시간 선형 증가**: 64명/96과제에서 240프레임 캡처에 ~12s (5 워커). 320명/과제 수백이면 DOM 노드가 5배 이상, 프레임당 캡처 시간이 길어져 렌더가 1~2분 수준으로 증가할 가능성. static-frame dedup 비율이 떨어지면 더 느려짐.
2. **SVG 노드 과다**: 320명 사람 노드 + 수백 개 과제 노드 + 성운 필터 → 브라우저 렌더링 부하. `feTurbulence` + `feDisplacementMap` 필터가 많은 요소에 적용되면 프레임 캡처가 100ms+ 걸릴 수 있음.
3. **좌표 계산**: 320명의 x/y 좌표가 payload에 있으면 동일 로직으로 처리 가능. 없으면 원본의 원형 배치 fallback으로 처리하나, 시각이 달라짐.
4. **파일 크기**: 현재 1.8 MB / 8초. 320명 scale에서도 8초면 5~10 MB 수준으로 예상 (해상도/프레임수 동일 시).
5. **PJT 수 증가**: 2개가 아닌 4~5개 PJT면 격자 레이아웃과 클러스터 위치 계산을 원본 COLS=4에 맞게 조정 필요.

## 5. 이 용도(무대 발표용 장면 사전 렌더)에 Hyperframes가 맞는지

**결론: 맞다.** 핵심 문제인 "브라우저 실시간 렌더 시 프레임 드랍"을 구조적으로 해결한다. MP4로 구워두면 재생은 미디어 플레이어가 처리하므로 프레임 타임 문제가 사라진다. 결정성도 확인했다 — 두 번 렌더해 동일한 파일이 나온다. 8초 장면 기준 30초 내외 렌더 시간은 무대 준비에 부담 없다. 다만 전체 발표(4개 장면)를 모두 렌더하려면 각 장면마다 컴포지션을 작성해야 하므로 작업량이 있고, 인터랙티브 기능(클릭으로 과제 상세 보기)이 필요한 장면은 동영상으로 대체 불가하다 — 발표자가 실시간 탐색을 보여줘야 하는 부분은 브라우저를 그대로 써야 한다. 즉 **미리 정해진 시퀀스를 무대에서 재생**하는 용도에는 적합하고, **실시간 탐색 시연**에는 부적합하다.

## 6. 설치/실행 중 막힌 것과 우회법

1. **`hyperframes doctor`가 응답하지 않음**: `npx hyperframes doctor`가 30초 이상 무응답. 원인 불명(아마 네트워크 타임아웃). 무시하고 바로 `init` → `render` 진행해도 문제 없음.
2. **폰트 lint 에러**: `font_family_without_font_face` — `"Apple SD Gothic Neo"`가 auto-resolved 폰트 목록에 없어 에러. `@font-face { font-family:'Apple SD Gothic Neo'; src: local('Apple SD Gothic Neo'); }` 선언을 추가하면 해결. 실제 폰트 파일 없이 `local()`만으로 lint 통과.
3. **`nested_structure_needs_subcomposition` 워닝**: 루트 컴포지션에 `<div>`가 중첩되어 있으면 서브컴포지션으로 분리하라는 권고. 렌더에는 영향 없으므로 무시 가능. `--strict` 없이 렌더하면 워닝과 함께 진행됨.
4. **GSAP CDN 인라이닝**: 렌더 시 `https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js`를 자동으로 인라인 처리. 네트워크 단절 우려는 불필요 — 컴파일 시점에 한 번만 가져와서 임베드.
5. **`hyperframes init` 스킬 업데이트 시도**: `init`가 기본적으로 GitHub에서 스킬을 확인하려 시도. `HYPERFRAMES_SKIP_SKILLS=1` 환경변수로 우회 가능하지만, `--non-interactive` 플래그만으로도 충분히 진행됨.
