"""python -m nebula demo|run|build"""

import argparse
import json
import sys
from pathlib import Path
from .demo import source, FakeClient, network as demo_network
from .llm import OpenAICompatible, LLMError, AgentClient
from .model import ValidationError, digest, need
from .pipeline import run, with_review
from .render import build
from .storage import write_json, output_lock, begin_run, mark_failed, AgentTurn


def main():
    parser = argparse.ArgumentParser(
        description="PJT-local future-task extraction and capability matrix"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "demo", "build"):
        p = sub.add_parser(name)
        p.add_argument("--out", type=Path, required=True)
        p.add_argument("--review", type=Path)
        p.add_argument("--approved-only", action="store_true")
        if name != "build":
            p.add_argument("--network", type=Path)
            p.add_argument("--corrections", type=Path)
            p.add_argument("--reset-corrections", action="store_true")
        if name == "run":
            p.add_argument("--input", type=Path, required=True)
        if name != "build":
            p.add_argument("--agent", action="store_true")
            p.add_argument("--batch-size", type=int, default=24)
            p.add_argument("--max-chars", type=int, default=24000)
    args = parser.parse_args()
    try:
        with output_lock(args.out):
            if args.command != "build":
                begin_run(args.out)
            try:
                if args.command == "build":
                    status = json.loads((args.out / "status.json").read_text())
                    if status.get("state") != "complete":
                        raise ValidationError(
                            "last pipeline run incomplete; finish it before rebuilding"
                        )
                    data = json.loads((args.out / "result.json").read_text())
                    need(
                        digest({k: v for k, v in data.items() if k != "run_id"})
                        == data["run_id"],
                        "result artifact modified; use correction workflow",
                    )
                else:
                    inputs = (
                        source()
                        if args.command == "demo"
                        else json.loads(args.input.read_text())
                    )
                    client = (
                        AgentClient()
                        if args.agent
                        else (
                            FakeClient()
                            if args.command == "demo"
                            else OpenAICompatible.from_env()
                        )
                    )
                    corrections = (
                        json.loads(args.corrections.read_text())
                        if args.corrections
                        else None
                    )
                    network = (
                        json.loads(args.network.read_text())
                        if args.network
                        else demo_network(inputs) if args.command == "demo" else None
                    )
                    data = run(
                        inputs,
                        args.out,
                        client,
                        args.batch_size,
                        args.max_chars,
                        corrections,
                        network,
                        args.reset_corrections,
                    )
                    if args.command == "demo":
                        write_json(args.out / "synthetic-persons.json", inputs)
                        write_json(args.out / "synthetic-network.json", network)
                if args.review:
                    data = with_review(data, json.loads(args.review.read_text()))
                output = build(data, args.out, args.approved_only)
                print(
                    f'Completed: persons={len(data["persons"])} tasks={len(data["tasks"])} categories={len(data["categories"])}'
                )
                print(output)
            except Exception:
                if args.command != "build":
                    mark_failed(args.out)
                raise
    except AgentTurn as error:
        print(str(error), file=sys.stderr)
        return 2
    except (ValidationError, LLMError) as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError):
        print(
            "Input/artifact error; verify JSON structure, paths, and configuration. Contents omitted.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
