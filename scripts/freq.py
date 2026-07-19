"""회고 텍스트 → 명사 빈도 freq.json 집계 (todos/003, kiwipiepy).

불용어는 scripts/stopwords.txt (한 줄 한 단어) — 워드클라우드 품질 튜닝은 이 파일만 편집.
"""
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
STOPWORDS_PATH = Path(__file__).parent / "stopwords.txt"

_kiwi = None  # Kiwi 로딩이 느려서 최초 사용 시 1회 생성


def load_stopwords(path=STOPWORDS_PATH):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return {w for w in (l.strip() for l in lines) if w and not w.startswith("#")}


def word_freq(text, stopwords=None):
    """텍스트 → {명사: 횟수}. NNG/NNP 기준, 뒤따르는 XSN 병합(자동+화→자동화), 2자 이상."""
    global _kiwi
    if _kiwi is None:
        from kiwipiepy import Kiwi
        _kiwi = Kiwi()
    if stopwords is None:
        stopwords = load_stopwords()

    words = []
    prev_noun = False  # XSN은 직전 토큰이 명사일 때만 병합 (자동+화→자동화), 복수 들은 버림
    for token in _kiwi.tokenize(text):
        if token.tag in ("NNG", "NNP"):
            words.append(token.form)
            prev_noun = True
        else:
            if token.tag == "XSN" and token.form != "들" and prev_noun:
                words[-1] += token.form
            prev_noun = False
    return Counter(w for w in words if len(w) >= 2 and w not in stopwords)


def main(persons_path=ROOT / "data" / "persons.json", out_path=ROOT / "data" / "freq.json"):
    persons = json.loads(Path(persons_path).read_text(encoding="utf-8"))
    stopwords = load_stopwords()
    counts = {str(p["id"]): dict(word_freq(p["text"], stopwords)) for p in persons}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(counts, ensure_ascii=False, indent=1), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    print(main(*sys.argv[1:]))
