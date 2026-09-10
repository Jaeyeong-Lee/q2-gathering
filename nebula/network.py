"""Read existing similarity artifacts; never infer similarity from taxonomy."""

from typing import Any
import math
from .model import need


def normalize_network(raw, persons):
    need(isinstance(raw, dict), "network object required")
    known = {p["id"] for p in persons}
    provided_nodes = raw.get("nodes")
    if provided_nodes is None:
        nodes = [{"id": pid} for pid in sorted(known)]
    else:
        need(isinstance(provided_nodes, list), "network nodes list required")
        nodes, seen = [], set()
        for node in provided_nodes:
            need(isinstance(node, dict) and "id" in node, "network node id required")
            pid = str(node["id"])
            need(pid in known and pid not in seen, "unknown/duplicate network person")
            seen.add(pid)
            n = {"id": pid}
            need(("x" in node) == ("y" in node), "network coordinate pair required")
            if "x" in node:
                for key in ("x", "y"):
                    value = node[key]
                    need(
                        type(value) in (int, float) and math.isfinite(value),
                        "network coordinates must be finite",
                    )
                    n[key] = value
            nodes.append(n)
        need(
            seen == known,
            "network nodes must match input persons; supply missing isolated nodes too",
        )
    coordinates = sum("x" in n for n in nodes)
    need(
        coordinates in (0, len(nodes)), "network layout must include all people or none"
    )
    rows = raw.get("edges")
    if rows is None:
        neighbors = raw.get("neighbors", raw)
        need(isinstance(neighbors, dict), "network neighbors object required")
        rows = []
        for pid, entries in neighbors.items():
            if pid == "nodes":
                continue
            need(
                str(pid) in known and isinstance(entries, list),
                "network neighbor source invalid",
            )
            for entry in entries:
                need(
                    isinstance(entry, dict) and "id" in entry and "similarity" in entry,
                    "network neighbor fields invalid",
                )
                rows.append(
                    {"a": pid, "b": entry["id"], "similarity": entry["similarity"]}
                )
    need(isinstance(rows, list), "network edges list required")
    unique: dict[tuple[str, str], float] = {}
    for row in rows:
        need(
            isinstance(row, dict) and all(k in row for k in ("a", "b", "similarity")),
            "network edge fields invalid",
        )
        a, b, score = str(row["a"]), str(row["b"]), row["similarity"]
        need(
            a in known and b in known and a != b,
            "network edge has unknown person or self-link",
        )
        need(
            type(score) in (int, float) and math.isfinite(score) and -1 <= score <= 1,
            "network similarity must be finite in [-1,1]",
        )
        edge_key = (min(a, b), max(a, b))
        need(
            edge_key not in unique or abs(unique[edge_key] - score) < 0.00001,
            "conflicting similarity for one pair",
        )
        unique[edge_key] = score
    return {
        "nodes": nodes,
        "edges": [
            {"a": a, "b": b, "similarity": s} for (a, b), s in sorted(unique.items())
        ],
        "has_layout": bool(nodes) and coordinates == len(nodes),
    }
