import unittest
from nebula.network import normalize_network
from nebula.model import ValidationError


class NetworkContract(unittest.TestCase):
    def test_existing_neighbors_become_undirected_edges_without_recomputing_scores(
        self,
    ):
        ps = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        network = normalize_network(
            {
                "1": [{"id": 2, "similarity": 0.81}],
                "2": [{"id": 1, "similarity": 0.81}],
            },
            ps,
        )
        self.assertEqual(network["edges"], [{"a": "1", "b": "2", "similarity": 0.81}])
        self.assertEqual(len(network["nodes"]), 3)
        self.assertFalse(network["has_layout"])

    def test_preserves_supplied_coordinates_and_rejects_unknown_join(self):
        ps = [{"id": "1"}, {"id": "2"}]
        raw = {
            "nodes": [{"id": 1, "x": 0.2, "y": 0.7}, {"id": 2, "x": 0.8, "y": 0.4}],
            "edges": [{"a": 1, "b": 2, "similarity": 0.6}],
        }
        self.assertTrue(normalize_network(raw, ps)["has_layout"])
        raw["edges"][0]["b"] = 999
        with self.assertRaises(ValidationError):
            normalize_network(raw, ps)
