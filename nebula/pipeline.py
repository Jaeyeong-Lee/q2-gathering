"""Sequential, resumable stages. Independent PJTs retain independent taxonomies."""

from typing import Any
import json
from collections import defaultdict
from pathlib import Path
from . import prompts
from .model import (
    persons,
    extraction,
    taxonomy,
    assignments,
    digest,
    need,
    ValidationError,
)
from .storage import Store, write_json, output_lock
from .network import normalize_network


def batches(items, size, max_chars):
    group: list[dict[str, Any]] = []
    total = 0
    for item in items:
        length = len(json.dumps(item, ensure_ascii=False))
        need(length <= max_chars, "one item exceeds batch character budget")
        if group and (len(group) >= size or total + length > max_chars):
            yield group
            group, total = [], 0
        group.append(item)
        total += length
    if group:
        yield group


def run(
    source, out, client, batch_size=24, max_chars=24000, corrections=None, network=None
):
    with output_lock(out):
        return _run(source, out, client, batch_size, max_chars, corrections, network)


def _run(source, out, client, batch_size, max_chars, corrections, network):
    need(type(batch_size) is int and batch_size > 0, "batch size must be positive")
    need(type(max_chars) is int and max_chars > 0, "max chars must be positive")
    ps = persons(source)
    normalized_network = normalize_network(network, ps) if network is not None else None
    corrections = corrections or {"persons": []}
    need(
        isinstance(corrections, dict) and set(corrections) <= {"persons", "taxonomies"},
        "corrections fields invalid",
    )
    need(
        isinstance(corrections.get("persons", []), list),
        "corrections persons list required",
    )
    overrides = {}
    source_by_id = {p["id"]: p for p in ps}
    for entry in corrections.get("persons", []):
        need(
            isinstance(entry, dict)
            and set(entry) == {"person_id", "source_hash", "extraction"},
            "person correction fields invalid",
        )
        pid = entry["person_id"]
        need(
            pid in source_by_id and pid not in overrides,
            "unknown/duplicate corrected person",
        )
        need(
            entry["source_hash"] == digest(source_by_id[pid]["text"]),
            "correction source changed; inspect current text",
        )
        overrides[pid] = entry["extraction"]
    taxonomy_overrides = {}
    need(
        isinstance(corrections.get("taxonomies", []), list),
        "taxonomy corrections list required",
    )
    for entry in corrections.get("taxonomies", []):
        need(
            isinstance(entry, dict)
            and set(entry) == {"pjt", "input_hash", "categories"},
            "taxonomy correction fields invalid",
        )
        need(
            isinstance(entry["pjt"], str) and entry["pjt"] not in taxonomy_overrides,
            "duplicate taxonomy correction",
        )
        taxonomy_overrides[entry["pjt"]] = entry
    store = Store(out)
    # Retain last HTML with an explicit previous filename, never at the current path.
    for name in ("matrix", "review"):
        current = store.out / (name + ".html")
        if current.exists():
            current.replace(store.out / (name + ".previous.html"))
    write_json(
        store.out / "status.json", {"state": "running", "input_hash": digest(ps)}
    )
    try:
        extracted, correction_entries = [], []
        for i, p in enumerate(ps):
            need(
                len(p["text"]) <= max_chars,
                f"person index {i}: source too large; adjust character budget",
            )
            holder = {}

            def validate(raw):
                result = extraction(raw, p)
                holder["raw"] = raw
                return result

            if p["id"] in overrides:
                result = validate(overrides[p["id"]])
            else:
                result = store.call(
                    client,
                    "extract",
                    prompts.EXTRACT,
                    {"person_id": p["id"], "text": p["text"]},
                    validate,
                )
            extracted.append(result)
            correction_entries.append(
                {
                    "person_id": p["id"],
                    "source_hash": digest(p["text"]),
                    "extraction": holder["raw"],
                }
            )
        write_json(
            store.out / "corrections-template.json", {"persons": correction_entries}
        )
        tasks = [t for e in extracted for t in e["tasks"]]
        caps = [c for e in extracted for c in e["capabilities"]]
        links = [l for e in extracted for l in e["links"]]
        groups = defaultdict(list)
        for task in tasks:
            groups[task["pjt"]].append(task)
        need(
            set(taxonomy_overrides) <= set(groups),
            "taxonomy correction has no task-bearing PJT",
        )
        categories, assigned, taxonomy_templates = [], [], []
        for pjt in sorted(groups):
            local: list[dict[str, Any]] = []
            minimal = [
                {"id": t["id"], "label": t["label"], "quote": t["quote"]}
                for t in groups[pjt]
            ]
            task_hash = digest(minimal)
            write_json(
                store.out / "task-inputs" / (digest(pjt)[:24] + ".json"),
                {"pjt": pjt, "input_hash": task_hash, "tasks": minimal},
            )
            if pjt in taxonomy_overrides:
                override = taxonomy_overrides[pjt]
                need(
                    override["input_hash"] == task_hash,
                    "taxonomy correction tasks changed; inspect current tasks",
                )
                local = taxonomy({"additions": override["categories"]}, pjt, [])
            else:
                for batch in batches(minimal, batch_size, max_chars):
                    payload = {"pjt": pjt, "existing": local, "tasks": batch}
                    need(
                        len(json.dumps(payload, ensure_ascii=False)) <= max_chars * 3,
                        "taxonomy registry too large; review PJT scope or increase budget",
                    )
                    additions = store.call(
                        client,
                        "taxonomy",
                        prompts.TAXONOMY,
                        payload,
                        lambda raw, pjt=pjt, local=local: taxonomy(raw, pjt, local),
                    )
                    local.extend(additions)
                write_json(
                    store.out / "taxonomy-drafts" / (digest(pjt)[:24] + ".json"),
                    {
                        "pjt": pjt,
                        "input_hash": task_hash,
                        "categories": [
                            {
                                k: c[k]
                                for k in ("name", "definition", "includes", "excludes")
                            }
                            for c in local
                        ],
                    },
                )
                if local:
                    # Bound the final pass; no silent truncation of a large registry.
                    representatives = [
                        minimal[i]
                        for i in range(
                            0, len(minimal), max(1, len(minimal) // batch_size)
                        )
                    ][:batch_size]
                    final_payload = {
                        "pjt": pjt,
                        "drafts": local,
                        "representative_tasks": representatives,
                    }
                    need(
                        len(json.dumps(final_payload, ensure_ascii=False))
                        <= max_chars * 3,
                        "taxonomy consolidation too large; supply reviewed taxonomy corrections",
                    )
                    local = store.call(
                        client,
                        "consolidate",
                        prompts.CONSOLIDATE,
                        final_payload,
                        lambda raw, pjt=pjt: taxonomy(raw, pjt, []),
                    )
                    need(bool(local), "nonempty taxonomy drafts consolidated to empty")
            taxonomy_templates.append(
                {
                    "pjt": pjt,
                    "input_hash": task_hash,
                    "categories": [
                        {
                            k: c[k]
                            for k in ("name", "definition", "includes", "excludes")
                        }
                        for c in local
                    ],
                }
            )
            categories.extend(local)
            for batch in batches(minimal, batch_size, max_chars):
                payload = {"pjt": pjt, "categories": local, "tasks": batch}
                need(
                    len(json.dumps(payload, ensure_ascii=False)) <= max_chars * 3,
                    "assignment request too large",
                )
                assigned.extend(
                    store.call(
                        client,
                        "assign",
                        prompts.ASSIGN,
                        payload,
                        lambda raw, batch=batch, local=local: assignments(
                            raw, batch, local
                        ),
                    )
                )
        data = {
            "schema_version": 1,
            "synthetic": client.cache_identity.get("provider") == "fake",
            "persons": ps,
            "tasks": tasks,
            "capabilities": caps,
            "links": links,
            "categories": categories,
            "assignments": assigned,
            "provider": client.cache_identity,
            "review": {},
            "network": normalized_network,
            "corrections_template": {
                "persons": correction_entries,
                "taxonomies": taxonomy_templates,
            },
        }
        data["run_id"] = digest(data)
        write_json(store.out / "result.json", data)
        write_json(
            store.out / "status.json",
            {
                "state": "complete",
                "run_id": data["run_id"],
                "persons": len(ps),
                "tasks": len(tasks),
                "calls": store.calls,
                "cache_hits": store.hits,
            },
        )
        return data
    except Exception:
        write_json(
            store.out / "status.json",
            {
                "state": "failed",
                "input_hash": digest(ps),
                "completed_calls": store.calls,
                "cache_hits": store.hits,
                "stage": store.stage,
                "call_key": store.call_key,
            },
        )
        raise


def with_review(data, review):
    need(
        digest({k: v for k, v in data.items() if k != "run_id"}) == data["run_id"],
        "result artifact changed; use corrections and rerun instead of editing result.json",
    )
    need(
        isinstance(review, dict) and review.get("run_id") == data["run_id"],
        "review is for a different run; re-review changed data",
    )
    decisions = review.get("decisions")
    need(isinstance(decisions, dict), "review decisions object required")
    task_ids = {t["id"] for t in data["tasks"]}
    tasks = {t["id"]: t for t in data["tasks"]}
    categories = {c["id"]: c for c in data["categories"]}
    assignments_by_id = {a["task_id"]: dict(a) for a in data["assignments"]}
    for tid, decision in decisions.items():
        need(tid in task_ids and isinstance(decision, dict), "review has unknown task")
        need(
            decision.get("status") in ("approved", "rejected", "pending"),
            "review status invalid",
        )
        need(isinstance(decision.get("note", ""), str), "review note must be text")
        need(
            set(decision) <= {"status", "note", "category_id"},
            "review decision fields invalid",
        )
        if "category_id" in decision:
            cid = decision["category_id"]
            need(
                cid is None
                or cid in categories
                and categories[cid]["pjt"] == tasks[tid]["pjt"],
                "review category belongs to another PJT or is unknown",
            )
            if cid != assignments_by_id[tid]["category_id"]:
                need(
                    bool(decision.get("note", "").strip()),
                    "category correction requires a review note",
                )
                assignments_by_id[tid] = {
                    "task_id": tid,
                    "category_id": cid,
                    "reason": decision["note"],
                }
    return {
        **data,
        "review": decisions,
        "assignments": list(assignments_by_id.values()),
    }
