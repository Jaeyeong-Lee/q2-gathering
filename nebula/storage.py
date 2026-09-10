"""Atomic stage cache. A failed/invalid call is never cached as completed."""

import json
import os
import tempfile
from pathlib import Path
from .model import digest
from contextlib import contextmanager


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

    root = Store(out).out
    with (root / ".run.lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValidationError("output directory is in use by another run") from None
        try:
            yield
        finally:
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
                "contract": 1,
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
        raw = client.complete(stage, prompt, payload)
        result = validate(raw)
        write_json(path, raw)
        self.calls += 1
        return result
