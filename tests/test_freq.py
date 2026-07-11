import json

import build
import freq
import generate_dummy


def test_noun_freq_known_sentence():
    # 사람이 판단한 명사 목록이 기준 (파생명사 자동화·개선 포함, 조사·어미 제외)
    text = "용접 로봇을 도입해 공정 자동화를 진행했고, 용접 품질이 개선되었습니다."
    assert freq.word_freq(text, stopwords=set()) == {
        "용접": 2,
        "로봇": 1,
        "도입": 1,
        "공정": 1,
        "자동화": 1,
        "진행": 1,
        "품질": 1,
        "개선": 1,
    }


def test_plural_suffix_folds_into_base_noun():
    # 동료들 → 동료 (들을 붙이면 동료/동료들이 따로 집계됨), 파생접미사 화는 병합 유지
    counts = freq.word_freq("동료들과 협업하며 설비 자동화를 개선했다.", stopwords=set())
    assert counts == {"동료": 1, "협업": 1, "설비": 1, "자동화": 1, "개선": 1}


def test_stopwords_filtered():
    text = "용접 업무를 담당하며 품질 개선 프로젝트를 수행했습니다."
    # 명시적 불용어
    assert "용접" not in freq.word_freq(text, stopwords={"용접"})
    # 기본값: scripts/stopwords.txt 적용 (업무·담당·프로젝트·수행은 템플릿 공통어)
    default = freq.word_freq(text)
    assert "업무" not in default and "프로젝트" not in default
    assert default["품질"] == 1 and default["개선"] == 1


def test_persons_text_through_build(tmp_path):
    # 더미 persons.json의 text → freq.main → freq.json 교체 → 001 빌드 조립까지 관통
    data_dir = tmp_path / "data"
    generate_dummy.main(out_dir=data_dir)
    persons = json.loads((data_dir / "persons.json").read_text())

    out = freq.main(persons_path=data_dir / "persons.json", out_path=data_dir / "freq.json")
    counts = json.loads(out.read_text())
    assert set(counts) == {str(p["id"]) for p in persons}
    for per_person in counts.values():
        assert per_person, "빈 빈도 딕셔너리 금지"
        for word, n in per_person.items():
            assert isinstance(n, int) and n >= 1
            assert len(word) >= 2

    html = build.build(data_dir=data_dir, out_path=tmp_path / "archive.html").read_text()
    assert "__FREQ__" not in html
