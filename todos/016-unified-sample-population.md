---
id: 016
title: 합성 인구 단일화 — 한 인구로 두 지도를 먹인다
status: ready
blocked_by: [010]
labels: [ready-for-agent]
---

## Parent

docs/deliverable-candidates-2026-08-28.html 후보 A · docs/deliverable-candidates-fable-2026-08-30.html 후보 ④의 전제

## What to build

지금 합성 인구가 두 벌이다. 사람 지도(heritage) 쪽 더미 생성기와 task-discovery 쪽 합성 코퍼스가
서로 다른 사람들을 만든다. 그래서 "이 사람의 별과 이 사람의 과제"를 나란히 놓을 수가 없다.

task-discovery 합성 코퍼스의 인구를 **하나의 진실**로 삼아, 그 인구로 사람 지도 샘플 HTML까지
빌드한다. 임베딩·유사도·형태소 빈도·조립 네 단계를 샘플 입출력 경로로 돌린다. 이게 되면 017의
개인 카드 조인이 성립하고, 두 지도가 같은 사람을 가리킨다.

**heritage 더미 생성기는 실행하지 않는다.** 그 스크립트는 실데이터가 놓인 파일을 덮어쓴다.
이 티켓의 어떤 단계도 실데이터 파일에 쓰기를 하지 않는다.

## Acceptance criteria

- [ ] 합성 코퍼스 인구로 사람 지도 샘플 HTML이 빌드되고 브라우저에서 열린다
- [ ] 사람 지도의 인물 식별자와 과제 카드의 인물 식별자가 서로 매칭된다
- [ ] 실행 전후로 실데이터 파일의 수정 시각이 변하지 않는다 (무접촉 확인)
- [ ] 샘플 HTML이 공개 배포 디렉터리가 아닌 샘플 경로에 생성된다
- [ ] 헤드리스 크롬(--headless=new) 스크린샷으로 렌더 확인
