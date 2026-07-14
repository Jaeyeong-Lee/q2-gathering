import json

import llm_review as lr


def test_review_all_skips_already_done():
    persons = [
        {"id": 0, "name": "A", "cl_level": "CL3", "text": "A 원문"},
        {"id": 1, "name": "B", "cl_level": "CL3", "text": "B 원문"},
    ]
    results = {"1": "이미 있음"}
    calls = []

    def call(prompt):
        calls.append(prompt)
        return "리뷰 결과"

    failed = lr.review_all(persons, results, call, retries=0)
    assert failed == []
    assert len(calls) == 1  # id=1은 스킵, id=0만 호출
    assert results == {"0": "리뷰 결과", "1": "이미 있음"}


def test_review_all_retries_only_failed_person():
    persons = [
        {"id": 0, "name": "A", "cl_level": "CL3", "text": "A 원문"},
        {"id": 1, "name": "B", "cl_level": "CL3", "text": "B 원문"},
    ]
    fail_once = ["A 원문"]

    def flaky(prompt):
        for marker in fail_once:
            if marker in prompt:
                fail_once.remove(marker)
                raise RuntimeError("실패")
        return "리뷰 결과"

    results = {}
    failed = lr.review_all(persons, results, flaky, retries=1, delay=0)
    assert failed == []
    assert results == {"0": "리뷰 결과", "1": "리뷰 결과"}


def test_review_all_exhausted_retry_keeps_batch_alive():
    persons = [
        {"id": 0, "name": "bad", "cl_level": "CL3", "text": "불량 원문"},
        {"id": 1, "name": "ok", "cl_level": "CL3", "text": "정상 원문"},
    ]

    def call(prompt):
        if "불량" in prompt:
            raise RuntimeError("실패")
        return "리뷰 결과"

    results = {}
    failed = lr.review_all(persons, results, call, retries=1, delay=0)
    assert failed == [0]
    assert results == {"1": "리뷰 결과"}


def test_review_all_picks_prompt_by_cl_level(monkeypatch):
    monkeypatch.setattr(lr, "PROMPTS", {"CL2": "주니어용: {text}", "CL4": "시니어용: {text}"})
    persons = [
        {"id": 0, "name": "A", "cl_level": "CL2", "text": "A 원문"},
        {"id": 1, "name": "B", "cl_level": "CL4", "text": "B 원문"},
    ]
    prompts = []

    def call(prompt):
        prompts.append(prompt)
        return "리뷰 결과"

    results = {}
    failed = lr.review_all(persons, results, call, retries=0, delay=0)
    assert failed == []
    assert prompts == ["주니어용: A 원문", "시니어용: B 원문"]


def test_review_all_unknown_cl_level_raises(monkeypatch):
    monkeypatch.setattr(lr, "PROMPTS", {"CL2": "{text}"})
    persons = [{"id": 0, "name": "A", "cl_level": "CL9", "text": "A 원문"}]
    try:
        lr.review_all(persons, {}, lambda p: "결과", retries=0, delay=0)
        assert False, "미등록 cl_level이면 즉시 KeyError가 나야 함"
    except KeyError:
        pass


def test_main_writes_progress_even_if_crashed_midway(tmp_path, monkeypatch):
    # 2번째 사람에서 미등록 cl_level(KeyError)로 죽어도 1번째 사람의 결과는 out_path에 남아야 함
    monkeypatch.setattr(lr, "PROMPTS", {"CL2": "{text}"})
    persons_path = tmp_path / "persons.json"
    persons_path.write_text(json.dumps([
        {"id": 0, "name": "A", "cl_level": "CL2", "text": "A 원문"},
        {"id": 1, "name": "B", "cl_level": "CL9", "text": "B 원문"},
    ], ensure_ascii=False), encoding="utf-8")
    out_path = tmp_path / "llm_review.json"

    try:
        lr.main(persons_path=persons_path, out_path=out_path, call=lambda p: "리뷰 결과", retries=0, delay=0)
        assert False, "미등록 cl_level이면 KeyError가 전파되어야 함"
    except KeyError:
        pass

    results = json.loads(out_path.read_text())
    assert results == {"0": "리뷰 결과"}  # 죽기 전 진행분 보존, B는 다음 실행에서 재시도 대상


def test_main_does_not_mutate_persons_json(tmp_path):
    persons_path = tmp_path / "persons.json"
    before = [{"id": 0, "name": "A", "cl_level": "CL3", "text": "A 원문"}]
    persons_path.write_text(json.dumps(before, ensure_ascii=False), encoding="utf-8")
    out_path = tmp_path / "llm_review.json"

    failed = lr.main(persons_path=persons_path, out_path=out_path, call=lambda p: "리뷰 결과", retries=0, delay=0)
    assert failed == []
    assert json.loads(persons_path.read_text()) == before  # persons.json 불변
    assert json.loads(out_path.read_text()) == {"0": "리뷰 결과"}


def test_main_resumes_from_existing_out_path(tmp_path):
    persons_path = tmp_path / "persons.json"
    persons_path.write_text(json.dumps([
        {"id": 0, "name": "A", "cl_level": "CL3", "text": "A 원문"},
        {"id": 1, "name": "B", "cl_level": "CL3", "text": "B 원문"},
    ], ensure_ascii=False), encoding="utf-8")
    out_path = tmp_path / "llm_review.json"
    out_path.write_text(json.dumps({"0": "기존 리뷰"}, ensure_ascii=False), encoding="utf-8")
    calls = []

    def call(prompt):
        calls.append(prompt)
        return "새 리뷰"

    failed = lr.main(persons_path=persons_path, out_path=out_path, call=call, retries=0, delay=0)
    assert failed == []
    assert len(calls) == 1  # id=0은 스킵, id=1만 새로 호출
    assert json.loads(out_path.read_text()) == {"0": "기존 리뷰", "1": "새 리뷰"}
