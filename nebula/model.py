"""Input and LLM-result contracts. Pure validators; never log document text."""

from typing import Any
import hashlib
import json
import re

HORIZONS = ("short", "mid", "long", "unknown")


class ValidationError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def need(condition, code):
    if not condition:
        raise ValidationError(code)


def fields(value, keys, code):
    need(isinstance(value, dict) and set(value) == set(keys), code)


def string(value, code):
    need(isinstance(value, str) and bool(value.strip()), code)
    return value


def persons(value):
    need(
        isinstance(value, list) and bool(value), "input must be a nonempty person list"
    )
    out, seen = [], set()
    for i, p in enumerate(value):
        need(isinstance(p, dict), f"person[{i}]: object required")
        need(
            isinstance(p.get("id"), (str, int)) and not isinstance(p.get("id"), bool),
            f"person[{i}]: id required",
        )
        pid = str(p["id"]).strip()
        need(pid and pid not in seen, f"person[{i}]: empty or duplicate id")
        seen.add(pid)
        for key in ("pjt", "text"):
            string(p.get(key), f"person[{i}]: {key} required")
        name = p.get("name", pid)
        string(name, f"person[{i}]: name must be text")
        out.append({"id": pid, "name": name, "pjt": p["pjt"], "text": p["text"]})
    return sorted(out, key=lambda p: p["id"])


def evidence(quote, source, code):
    string(quote, code)
    need(quote in source, code + ": quote not in source")
    return quote


def extraction(raw, person):
    fields(raw, ("tasks", "capabilities", "links"), "extract fields")
    for key in raw:
        need(isinstance(raw[key], list), "extract list required")
    source = person["text"]
    tasks, caps, links, refs, identities = [], [], [], {}, set()
    for t in raw["tasks"]:
        fields(
            t,
            ("ref", "label", "quote", "occurrence", "horizon", "time_quote"),
            "task fields",
        )
        string(t["ref"], "task ref")
        string(t["label"], "task label")
        need(t["ref"] not in refs, "duplicate extract ref")
        evidence(t["quote"], source, "task evidence")
        n = t["occurrence"]
        need(
            type(n) is int and 1 <= n <= source.count(t["quote"]),
            "task occurrence invalid",
        )
        need(t["horizon"] in HORIZONS, "task horizon invalid")
        if t["horizon"] == "unknown":
            need(t["time_quote"] is None, "unknown horizon must have null time_quote")
        else:
            evidence(t["time_quote"], source, "time evidence")
            marker = {"short": "단기", "mid": "중기", "long": "장기"}[t["horizon"]]
            need(
                marker in t["time_quote"] and t["quote"] in t["time_quote"],
                "time quote must connect task and explicit horizon",
            )
        ident = digest([person["id"], "task", t["quote"], n])[:24]
        need(ident not in identities, "duplicate task evidence")
        identities.add(ident)
        refs[t["ref"]] = ("task", ident, t["quote"])
        tasks.append(
            {
                "id": ident,
                "person_id": person["id"],
                "pjt": person["pjt"],
                "ax_mentioned": bool(
                    re.search(r"\b(?:AI|AX|LLM)\b|인공지능|머신러닝", t["quote"], re.I)
                ),
                **{
                    k: t[k]
                    for k in ("label", "quote", "occurrence", "horizon", "time_quote")
                },
            }
        )
    for c in raw["capabilities"]:
        fields(c, ("ref", "kind", "label", "quote", "occurrence"), "capability fields")
        string(c["ref"], "capability ref")
        string(c["label"], "capability label")
        need(
            c["ref"] not in refs and c["kind"] in ("have", "need"),
            "capability ref/kind invalid",
        )
        evidence(c["quote"], source, "capability evidence")
        need(
            type(c["occurrence"]) is int
            and 1 <= c["occurrence"] <= source.count(c["quote"]),
            "capability occurrence invalid",
        )
        ident = digest([person["id"], c["kind"], c["quote"], c["occurrence"]])[:24]
        need(ident not in identities, "duplicate capability evidence")
        identities.add(ident)
        refs[c["ref"]] = ("capability", ident, c["quote"])
        caps.append(
            {
                "id": ident,
                "person_id": person["id"],
                **{k: c[k] for k in ("kind", "label", "quote", "occurrence")},
            }
        )
    seen_links = set()
    for link in raw["links"]:
        fields(link, ("task_ref", "capability_ref", "relation_quote"), "link fields")
        tr, cr = refs.get(link["task_ref"]), refs.get(link["capability_ref"])
        need(
            tr is not None
            and tr[0] == "task"
            and cr is not None
            and cr[0] == "capability",
            "link ref invalid",
        )
        assert tr is not None and cr is not None
        q = evidence(link["relation_quote"], source, "link evidence")
        need(
            tr[2] in q and cr[2] in q,
            "link evidence must contain both task and capability quotes",
        )
        need("\n\n" not in q, "link evidence must be one passage, not distant sections")
        pair = (tr[1], cr[1])
        need(pair not in seen_links, "duplicate link")
        seen_links.add(pair)
        links.append({"task_id": tr[1], "capability_id": cr[1], "relation_quote": q})
    return {"tasks": tasks, "capabilities": caps, "links": links}


def stage_items(raw, key, prefix, person):
    """Validate one extraction stage on its own; refs are ours, so stages can't collide."""
    fields(raw, (key,), key + " fields")
    need(isinstance(raw[key], list), key + " list required")
    for item in raw[key]:
        need(isinstance(item, dict), key + " item object required")
    items = [{**item, "ref": prefix + str(i)} for i, item in enumerate(raw[key], 1)]
    extraction({"tasks": [], "capabilities": [], "links": [], key: items}, person)
    return items


def stage_links(raw, tasks, capabilities, person):
    """Links are judged after the fact, against already validated tasks and capabilities."""
    fields(raw, ("links",), "links fields")
    need(isinstance(raw["links"], list), "links list required")
    extraction(
        {"tasks": tasks, "capabilities": capabilities, "links": raw["links"]}, person
    )
    return raw["links"]


def taxonomy(raw, pjt, existing):
    fields(raw, ("additions",), "taxonomy fields")
    need(isinstance(raw["additions"], list), "taxonomy additions must be list")
    names = {c["name"].strip().casefold() for c in existing}
    out = []
    for c in raw["additions"]:
        fields(c, ("name", "definition", "includes", "excludes"), "category fields")
        for key in c:
            string(c[key], "category text required")
        for key in ("name", "definition"):
            # A Korean category may carry equipment/standard abbreviations, so the
            # test is "has Hangul", not "is ASCII-free".
            need(
                re.search(r"[가-힣]", c[key]),
                "category name/definition must be written in Korean"
                "; rerun taxonomy instead of reusing an older-contract correction",
            )
        name = c["name"].strip().casefold()
        need(name not in names, "duplicate category name")
        names.add(name)
        out.append({"id": digest([pjt, c])[:24], "pjt": pjt, **c})
    return out


def assignments(raw, tasks, categories):
    fields(raw, ("assignments",), "assignment fields")
    need(isinstance(raw["assignments"], list), "assignments list required")
    expected = {t["id"] for t in tasks}
    allowed = {c["id"] for c in categories}
    found, out = set(), []
    for row in raw["assignments"]:
        fields(row, ("task_id", "category_id", "reason"), "assignment row fields")
        need(
            row["task_id"] in expected and row["task_id"] not in found,
            "unknown/duplicate assignment task",
        )
        need(
            row["category_id"] is None or row["category_id"] in allowed,
            "unknown assignment category",
        )
        string(row["reason"], "assignment reason required")
        found.add(row["task_id"])
        out.append(row)
    need(found == expected, "assignment response omitted tasks")
    return out
