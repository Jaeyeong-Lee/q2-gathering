"""Atomic stage cache. A failed/invalid call is never cached as completed."""

import json
import os
import tempfile
import threading
from pathlib import Path
from .model import digest, ValidationError
from contextlib import contextmanager

_held = threading.local()


class AgentTurn(Exception):
    """Not a failure: the run needs the agent driving it to answer one stage.

    `answer` is the only live handoff. Older request files may still sit unanswered
    after an input change, so a driver follows this path instead of scanning.
    """

    def __init__(self, message, answer):
        super().__init__(message)
        self.answer = Path(answer)
        self.request = Path(str(answer).replace(".answer.json", ".json"))


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2))


@contextmanager
def output_lock(out):
    """OS releases advisory lock after termination; no stale-lock deletion needed (POSIX)."""
    import fcntl
    from .model import ValidationError

    root = Store(out).out.resolve()
    held: set[Path] = getattr(_held, "paths", set())
    if root in held:
        yield
        return
    with (root / ".run.lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValidationError("output directory is in use by another run") from None
        _held.paths = held
        held.add(root)
        try:
            yield
        finally:
            held.remove(root)
            fcntl.flock(stream, fcntl.LOCK_UN)


class Store:
    def __init__(self, out):
        self.out = Path(out)
        if "dist" in self.out.resolve().parts:
            raise ValueError("Output under dist is not allowed")
        self.out.mkdir(parents=True, exist_ok=True)
        self.hits = self.calls = 0
        self.stage = "input"
        self.call_key = None

    def call(self, client, stage, prompt, payload, validate):
        key = digest(
            {
                "contract": 2,  # 2: extract split into tasks/capabilities/links
                "client": client.cache_identity,
                "stage": stage,
                "prompt": prompt,
                "payload": payload,
            }
        )
        self.stage, self.call_key = stage, key
        write_json(
            self.out / "status.json",
            {
                "state": "running",
                "stage": stage,
                "call_key": key,
                "completed_calls": self.calls,
                "cache_hits": self.hits,
            },
        )
        path = self.out / "cache" / stage / (key + ".json")
        if path.exists():
            raw = json.loads(path.read_text())
            result = validate(raw)  # Still enforce current validator on resume.
            self.hits += 1
            return result
        if getattr(client, "agent_turn", False):
            return self.handoff(stage, key, prompt, payload, validate, path)
        raw = client.complete(stage, prompt, payload)
        result = validate(raw)
        write_json(path, raw)
        self.calls += 1
        return result

    def handoff(self, stage, key, prompt, payload, validate, cache_path):
        """Stop, let the agent answer this one stage, resume on the next run.

        The answer lands outside cache/ and is promoted only after it validates, so an
        agent's malformed answer never becomes a completed call.
        """
        folder = self.out / "agent-requests" / stage
        answer = folder / (key + ".answer.json")
        if answer.exists():
            try:
                raw = json.loads(answer.read_text())
            except ValueError:
                raise ValidationError(
                    "agent answer is not valid JSON: " + str(answer)
                ) from None
            result = validate(raw)
            write_json(cache_path, raw)
            answer.unlink()
            self.calls += 1
            return result
        write_json(
            folder / (key + ".json"),
            {
                "stage": stage,
                "answer_path": str(answer),
                "instructions": prompt,
                "input": payload,
            },
        )
        raise AgentTurn("agent turn: answer " + stage + " at " + str(answer), answer)


def begin_run(out):
    root = Store(out).out
    for name in ("nebula", "matrix", "review"):
        current = root / (name + ".html")
        if current.exists():
            current.replace(root / (name + ".previous.html"))
    write_json(root / "status.json", {"state": "running", "stage": "input"})


def mark_failed(out):
    root = Store(out).out
    status = json.loads((root / "status.json").read_text())
    status["state"] = "failed"
    write_json(root / "status.json", status)
