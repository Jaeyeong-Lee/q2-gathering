import json

import generate_dummy
import tags


def test_parse_tags_from_messy_llm_response():
    response = '결과입니다:\n```json\n["문제해결형", " 데이터드리븐 ", "문제해결형"]\n```\n이상입니다.'
    assert tags.parse_tags(response) == ["문제해결형", "데이터드리븐"]


def test_normalize_merges_synonyms():
    synonyms = {"데이터 드리븐": "데이터드리븐", "문제 해결형": "문제해결형"}
    # 동의어는 대표형으로, 병합 후 중복은 하나로
    result = tags.normalize(["데이터 드리븐", "문제해결형", "문제 해결형"], synonyms)
    assert result == ["데이터드리븐", "문제해결형"]


def test_failed_call_retries_only_that_person():
    persons = [{"id": i, "text": f"회고텍스트{i}", "tags": []} for i in range(3)]
    calls = []
    fail_once = ["회고텍스트1"]

    def flaky(prompt):
        calls.append(prompt)
        for marker in fail_once:
            if marker in prompt:
                fail_once.remove(marker)
                raise RuntimeError("호출 실패")
        return '["협업리더"]'

    by_id, failed = tags.extract_all(persons, flaky, retries=1)
    assert failed == []
    assert by_id == {0: ["협업리더"], 1: ["협업리더"], 2: ["협업리더"]}
    # 실패했던 1번만 2회 호출, 나머지는 각 1회 (전체 배치 재실행 없음)
    assert sum("회고텍스트1" in c for c in calls) == 2
    assert sum("회고텍스트0" in c for c in calls) == 1
    assert sum("회고텍스트2" in c for c in calls) == 1


def test_exhausted_retries_reports_failure_without_killing_batch():
    persons = [{"id": 0, "text": "정상", "tags": []}, {"id": 7, "text": "불량", "tags": []}]

    def call(prompt):
        if "불량" in prompt:
            raise RuntimeError("호출 실패")
        return '["공정통"]'

    by_id, failed = tags.extract_all(persons, call, retries=1)
    assert failed == [7]
    assert by_id == {0: ["공정통"]}


def test_consolidate_pool_unifies_spelling_across_persons():
    by_id = {0: ["데이터 드리븐", "협업리더"], 1: ["Data-driven", "공정통"]}
    seen = []

    def call(prompt):
        seen.append(prompt)
        return '{"데이터 드리븐": "데이터드리븐", "Data-driven": "데이터드리븐"}'

    result = tags.consolidate_pool(by_id, call)
    assert result == {0: ["데이터드리븐", "협업리더"], 1: ["데이터드리븐", "공정통"]}
    assert len(seen) == 1  # 풀 전체를 1회 호출로 정리
    assert "협업리더" in seen[0] and "Data-driven" in seen[0]  # 프롬프트에 전체 풀 포함


def test_main_fills_tags_field_in_persons_json(tmp_path):
    data_dir = tmp_path / "data"
    generate_dummy.main(out_dir=data_dir)
    persons_path = data_dir / "persons.json"
    before = {p["id"]: p for p in json.loads(persons_path.read_text())}

    def call(prompt):
        if "회고:" in prompt:  # 인당 추출 호출
            if before[1]["text"] in prompt:
                raise RuntimeError("호출 실패")  # 1번은 항상 실패
            return '["신기술탐구", "멘토형"]'
        return "{}"  # 풀 정리 호출: 병합 없음

    failed = tags.main(persons_path=persons_path, call=call, retries=0)
    assert failed == [1]

    after = {p["id"]: p for p in json.loads(persons_path.read_text())}
    assert set(after) == set(before)
    assert after[0]["tags"] == ["신기술탐구", "멘토형"]
    assert after[1]["tags"] == before[1]["tags"]  # 실패자는 기존 태그 유지
    assert after[0]["text"] == before[0]["text"]  # tags 외 필드 불변
