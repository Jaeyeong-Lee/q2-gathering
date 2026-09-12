"""deck.md → 발표 화면 문구, NEBULA_STORY → story 후보. 오타는 빈 슬라이드가 아니라 빌드 오류가 된다."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from nebula.demo import FakeClient, source
from nebula.model import ValidationError
from nebula.pipeline import run
from nebula.render import DECK_BEATS, build, parse_deck

DECK = Path(__file__).resolve().parents[1] / "nebula" / "templates" / "deck.md"


class DeckCopy(unittest.TestCase):
    def test_committed_deck_covers_every_beat(self):
        self.assertEqual(set(parse_deck(DECK.read_text())), set(DECK_BEATS))

    def test_repeated_keys_become_lines_and_notes(self):
        sections = []
        for beat in DECK_BEATS:
            body = "화면: 첫 줄\n화면: 둘째 줄\n보조: 라벨\n멘트: 하나\n멘트: 둘\n" if beat == "1-0" else ""
            sections.append(f"## {beat} 이름\n{body}")
        copy = parse_deck("# 머리말은 무시\n> 안내\n\n" + "\n".join(sections))
        self.assertEqual(
            copy["1-0"], {"screen": ["첫 줄", "둘째 줄"], "sub": "라벨", "note": "하나\n둘"}
        )
        self.assertEqual(copy["1-1"], {"screen": [], "sub": None, "note": None})

    def test_typos_stop_the_build(self):
        text = DECK.read_text()
        broken = {
            "unknown beat": text.replace("## 1-3", "## 1-9", 1),
            "duplicate beat": text.replace("## 1-8", "## 1-7", 1),
            "missing beat": text.split("## scene-3")[0],
            "unknown key": text.replace("화면:", "제목:", 1),
            "unknown placeholder": text.replace("화면: {people}", "화면: {persons}", 1),
        }
        for case, deck in broken.items():
            with self.subTest(case), self.assertRaises(ValidationError):
                parse_deck(deck)


class StoryAndCopyInlining(unittest.TestCase):
    def test_build_inlines_deck_copy_and_the_chosen_story(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            story = root / "candidate.js"
            story.write_text("window.storyMarker = '__PAYLOAD__';")
            with mock.patch.dict(os.environ, {"NEBULA_STORY": str(story)}):
                build(run(source()[:2], root / "out", FakeClient()), root / "out")
            page = (root / "out" / "nebula.html").read_text()
        self.assertIn("window.storyMarker = '__PAYLOAD__';", page)
        self.assertNotIn("__COPY__", page)
        self.assertIn(parse_deck(DECK.read_text())["1-0"]["screen"][0], page)

    def test_bad_story_override_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = run(source()[:1], root / "out", FakeClient())
            closing = root / "closing.js"
            closing.write_text("document.write('</script>')")
            for path in (root / "missing.js", closing):
                with self.subTest(path.name), mock.patch.dict(
                    os.environ, {"NEBULA_STORY": str(path)}
                ), self.assertRaises(ValidationError):
                    build(data, root / "out")


if __name__ == "__main__":
    unittest.main()
