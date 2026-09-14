"""python -m nebula.stability OUT OUT2 [OUT3 ...]

Compares how runs of the same extraction grouped each PJT's tasks. Scores are label-free, so
renamed categories with the same grouping agree fully. Prints PJT indices and counts only —
PJT and category names never reach the console.
"""

import itertools
import json
import sys
from collections import Counter, defaultdict
from math import comb
from pathlib import Path


def _labels(out):
    data = json.loads((Path(out) / "result.json").read_text())
    pjt = {t["id"]: t["pjt"] for t in data["tasks"]}
    labels: dict[str, dict[str, str | None]] = defaultdict(dict)
    for a in data["assignments"]:
        labels[pjt[a["task_id"]]][a["task_id"]] = a["category_id"]
    return labels


def _group(labels, task):
    # Unassigned tasks are not a shared category: each stands alone.
    return labels[task] if labels[task] is not None else ("unassigned", task)


def ari(xs, ys):
    """Adjusted Rand Index of two labelings of the same items (needs at least two)."""
    pairs = lambda counts: sum(comb(c, 2) for c in counts.values())
    index = pairs(Counter(zip(xs, ys)))
    rows, cols = pairs(Counter(xs)), pairs(Counter(ys))
    expected = rows * cols / comb(len(xs), 2)
    top = (rows + cols) / 2
    if top == expected:  # both all-singleton or both one group: identical partitions
        return 1.0
    return (index - expected) / (top - expected)


def compare(outs):
    runs = [_labels(out) for out in outs]
    rows = []
    for index, name in enumerate(sorted(runs[0]), 1):
        per_run = [run.get(name, {}) for run in runs]
        common = sorted(set.intersection(*(set(r) for r in per_run)))
        pairs = [
            {
                "runs": (i, j),
                "ari": ari([_group(a, t) for t in common], [_group(b, t) for t in common])
                if len(common) > 1
                else None,
                "to_assigned": sum(a[t] is None and b[t] is not None for t in common),
                "to_unassigned": sum(a[t] is not None and b[t] is None for t in common),
            }
            for (i, a), (j, b) in itertools.combinations(enumerate(per_run), 2)
        ]
        rows.append(
            {
                "pjt": index,
                "tasks": len(common),
                "unassigned": [sum(r[t] is None for t in common) for r in per_run],
                "pairs": pairs,
            }
        )
    return rows


def main(outs):
    if len(outs) < 2:
        raise SystemExit("usage: python -m nebula.stability OUT OUT2 [OUT3 ...]")
    for row in compare(outs):
        print(f"PJT#{row['pjt']}  과제 {row['tasks']}  미분류 {' / '.join(map(str, row['unassigned']))}")
        for p in row["pairs"]:
            score = "-" if p["ari"] is None else f"{p['ari']:.2f}"
            print(
                f"  실행{p['runs'][0]}↔실행{p['runs'][1]}  ARI {score}"
                f"  미분류→배정 {p['to_assigned']}  배정→미분류 {p['to_unassigned']}"
            )


if __name__ == "__main__":
    main(sys.argv[1:])
