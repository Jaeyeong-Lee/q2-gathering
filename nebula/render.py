"""Build presentation and review payload, with provenance-preserving aggregates."""

import json
from collections import defaultdict
from pathlib import Path
from .model import digest, need
from .storage import Store, write_json, write_text, output_lock


def build_view(data, approved_only=False):
    assignments = {a["task_id"]: a for a in data["assignments"]}
    caps = {c["id"]: c for c in data["capabilities"]}
    linked = defaultdict(list)
    for link in data["links"]:
        linked[link["task_id"]].append(
            {**caps[link["capability_id"]], "relation_quote": link["relation_quote"]}
        )
    tasks = []
    for t in data["tasks"]:
        review = data.get("review", {}).get(t["id"], {"status": "pending", "note": ""})
        if (
            review["status"] == "rejected"
            or approved_only
            and review["status"] != "approved"
        ):
            continue
        tasks.append(
            {
                **t,
                **{k: assignments[t["id"]][k] for k in ("category_id", "reason")},
                "skills": linked[t["id"]],
                "review": review,
            }
        )
    grouped = defaultdict(list)
    for task in tasks:
        for kind in ("have", "need"):
            if any(s["kind"] == kind for s in task["skills"]):
                grouped[
                    (task["pjt"], task["category_id"], task["horizon"], kind)
                ].append(task)
    bubbles = []
    categories = {c["id"]: c for c in data["categories"]}
    for key, members in sorted(grouped.items(), key=lambda pair: str(pair[0])):
        pjt, cid, h, kind = key
        bubbles.append(
            {
                "id": digest(key)[:20],
                "pjt": pjt,
                "category_id": cid,
                "name": categories[cid]["name"] if cid else "미분류",
                "horizon": h,
                "kind": kind,
                "people": len({t["person_id"] for t in members}),
                "task_ids": [t["id"] for t in members],
            }
        )
    linked_cap_ids = {l["capability_id"] for l in data["links"]}
    return {
        "run_id": data["run_id"],
        "synthetic": data["synthetic"],
        "approved_only": approved_only,
        "network": data.get("network"),
        "persons": data["persons"],
        "tasks": tasks,
        "categories": data["categories"],
        "bubbles": bubbles,
        "unlinked_capabilities": [
            c for c in data["capabilities"] if c["id"] not in linked_cap_ids
        ],
        "excluded_tasks": len(data["tasks"]) - len(tasks),
        "no_task_person_ids": sorted(
            {p["id"] for p in data["persons"]} - {t["person_id"] for t in data["tasks"]}
        ),
    }


def encoded(data):
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def build(data, out, approved_only=False):
    with output_lock(out):
        out = Store(out).out
        status_path = out / "status.json"
        if status_path.exists():
            status = json.loads(status_path.read_text())
            need(
                status.get("state") == "complete"
                and status.get("run_id") == data["run_id"],
                "output run changed or incomplete; reload result before building",
            )
        return _build(data, out, approved_only)


def _build(data, out, approved_only):
    view = build_view(data, approved_only)
    root = Path(__file__).parent / "templates"
    html = (root / "matrix.html").read_text().replace("__PAYLOAD__", encoded(view))
    review = (root / "review.html").read_text().replace("__PAYLOAD__", encoded(data))
    write_text(out / "matrix.html", html)
    write_text(out / "review.html", review)
    write_json(out / "view.json", view)
    return out / "matrix.html"
