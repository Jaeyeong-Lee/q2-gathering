"""Build presentation and review payload, with provenance-preserving aggregates."""

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from .model import digest, need
from .layout import place_people
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


# Eight hues reused from the previous synthetic atlas; index falls back by modulo
# so a corpus with more PJTs still renders instead of failing.
PALETTE = [
    "#7dcfff",
    "#a7a4ff",
    "#f0afce",
    "#eeb78c",
    "#e5d688",
    "#9bd4bd",
    "#9fb8f0",
    "#cebcf4",
]


def _seed(value):
    """Stable 0..1 jitter so a rerun places the same star in the same spot."""
    return int(digest(value)[:8], 16) / 0xFFFFFFFF


def _coordinates(people):
    """Scale supplied layout into 0..1; the template maps that onto its viewport.

    Coordinates may arrive normalized or in arbitrary pixels, so the range is
    derived rather than assumed. Absent layout stays absent: the template then
    says so and falls back to a deterministic ring.
    """
    points = [p for p in people if p["x"] is not None]
    if not points:
        return
    for key in ("x", "y"):
        values = [p[key] for p in points]
        low, span = min(values), (max(values) - min(values)) or 1
        for p in points:
            p[key] = round((p[key] - low) / span, 6)


def build_nebula(view):
    """Reshape build_view output for the four-scene presentation.

    The scenes address people and PJTs by position, so stable ids are indexed
    here and the original ids ride along for evidence display. Unclassified
    tasks get a per-PJT placeholder category instead of disappearing.
    """
    network = view.get("network") or {}
    nodes = {n["id"]: n for n in network.get("nodes", [])}
    pjt_names = sorted({p["pjt"] for p in view["persons"]})
    pjt_at = {name: i for i, name in enumerate(pjt_names)}

    people, person_at = [], {}
    for i, person in enumerate(sorted(view["persons"], key=lambda p: p["id"])):
        person_at[person["id"]] = i
        node = nodes.get(person["id"], {})
        people.append(
            {
                "id": i,
                "pid": person["id"],
                "name": person["name"],
                "pjt": pjt_at[person["pjt"]],
                "text": person["text"],
                "x": node.get("x"),
                "y": node.get("y"),
            }
        )
    edges = [
        {"a": person_at[e["a"]], "b": person_at[e["b"]], "w": e["similarity"]}
        for e in network.get("edges", [])
    ]
    layout_source = "supplied" if network.get("has_layout") else "absent"
    if layout_source == "absent" and edges:
        place_people(people, edges, len(pjt_names))
        layout_source = "computed"
    _coordinates(people)

    loose = {t["pjt"] for t in view["tasks"] if not t["category_id"]}
    by_pjt = defaultdict(list)
    for category in view["categories"]:
        by_pjt[category["pjt"]].append(category)
    categories, category_at = [], {}
    for name in pjt_names:
        entries = sorted(by_pjt.get(name, []), key=lambda c: c["name"])
        if name in loose:
            entries.append({"id": f"unclassified:{name}", "name": "미분류"})
        for index, category in enumerate(entries):
            category_at[category["id"]] = index
            categories.append(
                {
                    "id": category["id"],
                    "pjt": pjt_at[name],
                    "name": category["name"],
                    "definition": category.get("definition", ""),
                }
            )

    tasks, written = [], Counter[int]()
    for task in sorted(view["tasks"], key=lambda t: (t["person_id"], t["id"])):
        cid = task["category_id"] or f"unclassified:{task['pjt']}"
        owner = person_at[task["person_id"]]
        tasks.append(
            {
                "id": task["id"],
                "person": owner,
                "pjt": pjt_at[task["pjt"]],
                "category": cid,
                "cat_index": category_at[cid],
                "seq": written[owner],
                "horizon": task["horizon"],
                "quote": task["quote"],
                "time_quote": task["time_quote"],
                "review": task["review"],
                "reason": task["reason"],
                "skills": [
                    {
                        "kind": "have" if s["kind"] == "have" else "gap",
                        "label": s["label"],
                        "quote": s["quote"],
                        "relation_quote": s["relation_quote"],
                    }
                    for s in task["skills"]
                ],
                "seed": _seed(task["id"]),
            }
        )
        written[owner] += 1

    per_pjt = Counter(p["pjt"] for p in people)
    return {
        "run_id": view["run_id"],
        "synthetic": view["synthetic"],
        "approved_only": view["approved_only"],
        "has_layout": layout_source != "absent",
        "layout_source": layout_source,
        "people": people,
        "tasks": tasks,
        "categories": categories,
        "pjts": [
            {"name": name, "color": PALETTE[i % len(PALETTE)], "count": per_pjt[i]}
            for i, name in enumerate(pjt_names)
        ],
        "edges": edges,
    }


DECK_BEATS = [f"1-{i}" for i in range(9)] + [f"scene-{i}" for i in range(4)]
DECK_KEYS = {"화면": "screen", "보조": "sub", "멘트": "note"}
DECK_PLACEHOLDERS = {"people", "tasks", "pjts"}


def parse_deck(text):
    """deck.md → {beat: {screen: [lines], sub, note}}.

    A typo stops the build: a silently blank slide is worse on stage than an error
    at build time. Lines before the first "## " heading are the file's own notes.
    """
    copy: dict[str, dict] = {}
    beat = None
    for number, line in enumerate(text.splitlines(), 1):
        where = f"deck.md line {number}"
        if line.startswith("## "):
            beat = (line[3:].split() or [""])[0]
            need(beat in DECK_BEATS and beat not in copy, f"{where}: unknown or duplicate beat")
            copy[beat] = {"screen": [], "sub": None, "note": None}
        elif beat is not None and line.strip():
            key, sep, value = line.partition(":")
            need(bool(sep) and key.strip() in DECK_KEYS, f"{where}: expected 화면/보조/멘트")
            value = value.strip()
            for name in re.findall(r"\{(\w*)\}", value):
                need(name in DECK_PLACEHOLDERS, f"{where}: unknown placeholder")
            entry, field = copy[beat], DECK_KEYS[key.strip()]
            if field == "screen":
                entry["screen"].append(value)
            elif field == "note" and entry["note"]:
                entry["note"] += "\n" + value
            else:
                need(entry[field] is None, f"{where}: 보조 appears twice")
                entry[field] = value
    missing = [b for b in DECK_BEATS if b not in copy]
    need(not missing, "deck.md missing beats: " + ", ".join(missing))
    return copy


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
    # NEBULA_STORY picks a story candidate to preview without touching templates/.
    override = os.environ.get("NEBULA_STORY")
    story_path = Path(override) if override else root / "story.js"
    need(not override or story_path.is_file(), "NEBULA_STORY file not found")
    story = story_path.read_text() if story_path.is_file() else ""
    need("</script" not in story.lower(), "story.js must not contain a closing script tag")
    copy = encoded(parse_deck((root / "deck.md").read_text()))
    for name, payload in (
        ("nebula", build_nebula(view)),
        ("matrix", view),
        ("review", data),
    ):
        parts = {"PAYLOAD": encoded(payload), "STORY": story, "COPY": copy}
        # One pass, so text inserted for one placeholder is never re-scanned for another.
        page = re.sub(
            r"__(PAYLOAD|STORY|COPY)__",
            lambda m: parts[m.group(1)],
            (root / f"{name}.html").read_text(),
        )
        write_text(out / f"{name}.html", page)
    write_json(out / "view.json", view)
    return out / "nebula.html"
