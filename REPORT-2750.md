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

## 2. 정정 — `noglow`는 최적화가 아니다 (같은 것을 두 번 돌린 것)
**`scene2-noglow`와 `scene2`의 컴포지션은 사실상 동일하다.** 실측:

```
$ cmp video-2750/scene2/index.html video-2750/scene2-noglow/index.html
differ: char 446921, line 50            ← 7바이트만 다름
$ cmp -l ... | head -6
446921  42  55    # B → -
446922  73 156    # s → n
446923  12 157    # \n → o        = "Bs…" vs "-noglow…" (이름 문자열)
```
`hyperframes.json`도 동일하고 둘 다 같은 fixture(`payload-2750-slim.json`)를 쓴다.
`meta.json`은 `id`만 `nebula-scene2-2750` / `nebula-scene2-noglow-2750`로 다르다.

**따라서 119초 → 46.8초 차이는 "glow를 줄여서"가 아니다.** 차이는 렌더 파이프라인이 잡은 전략이었다:

| | `scene2` (1차) | `scene2-noglow` (2차) |
|---|---|---|
| capture | `screenshot`, **worker 2**, 113.5초 | `screenshot`, **worker 5**, 40.7초 |
| encode | 3.4초 | 4.1초 |
| 총 | **119초** | **46.8초** |

즉 **같은 입력에 대해 파이프라인의 캡처 병렬도가 2 → 5로 달라졌고, 그게 2.5배 차이를 만들었다.**
1차는 디스크 부족으로 `scene2`가 3.0초 만에 죽은 직후의 런이고, 2차는 14시간 뒤(디스크 확보 후)의 런이다.
**환경 상태가 파이프라인 휴리스틱을 바꿨을 가능성이 크다.**

**이게 내부망 벤치마크에서 참고할 진짜 발견이다**: 컴포지션이 같아도 캡처 전략에 따라 **2.5배**가 갈린다 →
벤치마크를 하려면 **worker/캡처 모드를 명시적으로 고정**하고, 같은 조건에서 **반복 측정**해야 한다.

**고정 방법은 CLI에 있다** (`hyperframes render --help`, v0.8.149 실측):
- `-w, --workers=<n|auto>` — **기본값이 auto**다. 그래서 같은 입력에서 2와 5로 갈렸다. 벤치마크에선 `-w 5`처럼 **숫자로 못 박아라.**
- `--docker` — "Use Docker for deterministic render". 결정론이 필요하면 이걸 쓴다.
- 참고: `-q, --quality`의 기본은 `looks`(CRF 16)이고 `delivery`가 high다 — 이 하네스가 쓴 `--quality high`는 delivery 프로파일이다.



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
