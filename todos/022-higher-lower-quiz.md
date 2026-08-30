---
id: 022
title: Higher / Lower 퀴즈 — 설계만 있고 코드가 없는 것
status: ready
blocked_by: [016]
labels: [ready-for-agent, decision-needed]
---

## Parent

docs/PRD-heritage-archive.md US16~20 (미구현) · docs/deliverable-candidates-fable-2026-08-30.html 후보 ⑦

## What to build

두 단어 중 어느 쪽이 더 많이 나왔는지 관객이 맞히는 퀴즈. 형태소 빈도 산출물을 그대로 쓰므로
추가 계산이 없다. 원래 PRD가 약속한 네 코너 중 유일하게 코드가 없는 구간이다.

**착수 전 결정 필요**: 발표 형식이 원래 설계 당시(분기회 10분 세그먼트)와 같다는 보장이 없다.
형식이 다르면 무대 없는 소품이 된다. 발표회 형식이 확정된 뒤에 착수한다.

## Acceptance criteria

- [ ] (게이트) 발표회 형식이 확정되고 이 코너가 들어갈 자리가 있음을 확인한 뒤 착수
- [ ] 빈도 산출물만 읽어 문제를 생성한다 (추가 계산·LLM 0)
- [ ] 정답 공개 시 실제 빈도 수치가 함께 표시된다
- [ ] 같은 seed면 같은 문제 순서가 나온다
- [ ] 헤드리스 크롬 스크린샷 + pytest 통과
