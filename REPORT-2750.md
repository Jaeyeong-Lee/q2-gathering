# REPORT — 2750 실규모 렌더 + noglow 최적화

측정: 2026-09-25, 로컬 Mac(Apple Silicon), `npx hyperframes render --quality high --fps 30`, 240프레임(8초).

## 1. 결과물
| 컴포지션 | 출력 | wall time | capture 모드 | worker | 파일 |
|---|---|---|---|---|---|
| `expand` (사람→과제 전개) | `nebula-expand-2750.mp4` | **2분 23초** | `drawelement` 스트리밍 | 1 | 5.99MB |
| `scene2` (성운, glow 전체) | `nebula-scene2-2750.mp4` | **1분 59초** | `screenshot` | 2 | 5.99MB |
| `scene2-noglow` (강조 노드만 glow) | `nebula-scene2-2750-noglow.mp4` | **46.8초** | `screenshot` | **5** | 8.09MB |

- lint: 세 컴포지션 모두 **0 error / 1 warning**.
- 디스크: 1차 시도에서 `scene2`가 3.0초 만에 죽었다(디스크 부족). 공간 확보 후 재실행.

## 2. 핵심 개선 — noglow가 2.5배 빠르다
- `scene2`(전체 glow) **119초** → `scene2-noglow` **46.8초**. **−73초, 2.5배**.
- 차이는 두 가지가 같이 움직였다: ① glow를 강조 노드로만 제한 ② 파이프라인이 **worker 2 → 5**로 올라가 capture 113초 → **40.7초**.
- 즉 이득은 "그림을 가볍게" + "병렬 캡처" 두 요인이 합쳐진 결과다(어느 쪽이 얼마인지는 미분리 — 다음 실험 과제).
- 반면 `expand`는 glow를 건드리지 않아 여전히 143초대이고, **captureStream이 아니라 drawelement 스트리밍** 경로를 탄다(worker 1). 이 경로가 병목 후보다.

## 3. 파이프라인 관찰 (Phase별 소요, expand 기준)
| 단계 | 소요 |
|---|---|
| browser_probe | 0.14초 |
| video_extract(사전 점검) | ~0.002초 |
| capture_calibration | **13.3초** |
| capture_streaming (240프레임) | **127.0초** ← 지배적 |
| encode | 3.4초 |
| assemble | 0.1초 |
| **총** | **141.0초** |

- 캡처가 전체의 90%다. 렌더 단축은 **캡처 경로**에서만 나온다.
- 캘리브레이션 13.3초는 고정비라 짧은 영상에서 비중이 크다(프레임 240 기준 9%).

## 4. 산출물 위치
- 컴포지션 원본: `video-2750/{expand,scene2,scene2-noglow}/` (index.html + hyperframes.json + meta.json)
- 스틸: `video-2750/*/snapshots/*.png` — 프레임 캡처 + `finding-*`(콘텐츠 겹침 지적 스틸)
- 렌더 하네스: `render-2750.sh`(3종 순차) · `render-2750b.sh`(남은 2종 재시도)
- 원시 로그: `render/results.txt` · `render/results2.txt` · `render-2750*.log`

## 5. 확인 못 한 것
- noglow 이득 중 **glow 축소 vs worker 증가**의 기여도 분리 (worker를 5로 고정한 glow 전체 렌더가 필요).
- 2750 과제 전개가 **실데이터**인지 합성 fixture인지 — `fixtures/`는 합성으로 보이나 대조 미실시.
- Mesil·다른 장면(1부) 은 이번 측정 범위 밖.
