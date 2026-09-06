---
id: 021
title: 항해 — 딥링크 자동 시퀀스
status: done # scripts/td_gallery.py에 발표 모드로 통합 — 캡션은 지어낸 서사 없이 실측 수치만
blocked_by: [012]
labels: [ready-for-agent]
---

## Parent

docs/deliverable-candidates-2026-08-28.html 후보 H · docs/deliverable-candidates-fable-2026-08-30.html 후보 ⑥

## What to build

장면 순서를 코드에 박아 발표자가 키 하나로 넘기는 모드. 전체 지도 → 한 사람 → 단어 → AX 렌즈처럼
장면 목록을 정의하고, 각 장면은 이미 있는 딥링크로 이동한다.

무대 리스크의 대부분은 라이브 클릭이다. 시퀀스가 고정되면 발표자는 말만 하면 된다. 어떤 후보를
고르든 발표회가 있는 한 마지막에 이게 필요해진다.

## Acceptance criteria

- [x] 장면 목록이 한 곳에 정의되고 순서 변경이 그 한 곳 수정으로 끝난다
- [x] 키 입력으로 앞뒤 이동이 되고, 중간에서 수동 조작으로 빠져나올 수 있다
- [x] 각 장면이 기존 딥링크를 재사용한다 (별도 상태 관리 추가 없음)
- [x] 헤드리스 크롬으로 장면별 스크린샷을 뽑아 순서를 확인
