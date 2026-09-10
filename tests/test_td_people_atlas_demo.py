"""Synthetic build contract: provenance, counts and corpus-derived similarity."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from td_people_atlas_demo import build_payload, text_vectors
from similarity import top_k_neighbors
from td_render_common import render


class AtlasContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = build_payload()

    def test_every_facet_has_source_evidence_and_unique_identity(self):
        d = self.payload
        self.assertEqual(len(d["people"]), 200)
        self.assertEqual(len({p["id"] for p in d["people"]}), 200)
        self.assertEqual(len({p["pjt"] for p in d["people"]}), 8)
        facet_ids = []
        for p in d["people"]:
            for f in p["facets"]:
                self.assertIn(f["quote"], p["text"])
                facet_ids.append(f["id"])
        self.assertEqual(len(facet_ids), len(set(facet_ids)))

    def test_counts_are_unique_people_with_matching_axes(self):
        for t in self.payload["topics"]:
            for axis, key in [("future_task", "future"), ("capability_have", "have")]:
                expected = [p["id"] for p in self.payload["people"]
                            if any(f["axis"] == axis and f["category"] == t["id"] for f in p["facets"])]
                self.assertEqual(t[key], expected)
            self.assertEqual(t["spread"], len({p["pjt"] for p in self.payload["people"] if p["id"] in t["future"]}))
        self.assertTrue(any(not p["signal"] for p in self.payload["people"]))

    def test_similarity_uses_text_not_categories(self):
        people = [{"id": 1, "text": "공통 데이터를 정리하고 분석한다."},
                  {"id": 2, "text": "공통 데이터를 정리하고 분석한다."},
                  {"id": 3, "text": "장시간 신뢰성 시험으로 수명을 검증한다."}]
        nbs = top_k_neighbors(text_vectors(people), k=2)
        self.assertEqual(nbs["1"][0], {"id": 2, "similarity": 1.0})
        self.assertLess(nbs["1"][1]["similarity"], 1)
        self.assertFalse(any(e["a"] == e["b"] for e in self.payload["edges"]))

    def test_payload_is_safe_to_embed_and_has_no_external_assets(self):
        root = Path(__file__).resolve().parents[1]
        template = (root / "templates" / "td_people_atlas.html").read_text()
        html = render(template, {"text": "</script><img src=x onerror=alert(1)>"})
        self.assertIn("\\u003c/script\\u003e", html)
        self.assertNotIn("<img src=x", html)
        self.assertNotIn('src="https://', template)
        self.assertNotIn('href="https://', template)


if __name__ == "__main__":
    unittest.main()
