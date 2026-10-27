"""CLI for the scripted demo, live tool-use agent, evaluation, and report import."""
import argparse
import json
import os
from pathlib import Path

from .contracts import strict_json
from .engine import AgentError, Budget, Trace, run_agent
from .importing import import_vllm
from .providers import ChatProvider, DemoProvider, ProviderError
from .reporting import markdown
from .tools import EvidenceStore

FIXTURES = Path(__file__).parent / "fixtures"


def execute(provider, workspace, task, output, budget=Budget()):
    store = EvidenceStore(workspace, task)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    trace = Trace(output / "trace.jsonl")
    try:
        result = run_agent(provider, store, trace, budget)
        (output / "decision.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        (output / "report.md").write_text(markdown(result))
        return result
    finally:
        trace.close()


def make_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Scripted offline workflow; no model or API key.")
    demo.add_argument("--task", choices=["interactive", "strict", "unseen"], default="interactive")
    demo.add_argument("--output", type=Path, default=Path("outputs/demo"))
    run = sub.add_parser("run", help="Use an actual tool-calling model via a chat-completions endpoint.")
    run.add_argument("--workspace", type=Path, default=FIXTURES)
    run.add_argument("--task", type=Path, default=FIXTURES / "tasks/interactive.json")
    run.add_argument("--base-url", default=os.environ.get("AGENT_BASE_URL", "http://127.0.0.1:8000/v1"))
    run.add_argument("--model", default=os.environ.get("AGENT_MODEL"))
    run.add_argument("--output", type=Path, default=Path("outputs/live"))
    run.add_argument("--max-turns", type=int, default=8)
    run.add_argument("--max-tool-calls", type=int, default=24)
    run.add_argument("--max-seconds", type=float, default=120)
    evaluation = sub.add_parser("evaluate", help="Run deterministic fixture cases; this is not a live-model benchmark.")
    evaluation.add_argument("--output", type=Path, default=Path("outputs/evaluation"))
    imported = sub.add_parser("import-vllm", help="Normalize a benchmark report without inventing missing metrics.")
    imported.add_argument("source", type=Path)
    imported.add_argument("--metadata", type=Path, required=True)
    imported.add_argument("--output", type=Path, required=True)
    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()
    try:
        if args.command == "import-vllm":
            row = import_vllm(args.source, args.metadata)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x") as stream:
                stream.write(json.dumps(row, indent=2, allow_nan=False) + "\n")
            print(f"Imported {row['run_id']} into {args.output}")
            return
        if args.command == "evaluate":
            args.output.mkdir(parents=True, exist_ok=False)
            cases = strict_json((FIXTURES / "cases.json").read_text())
            scores = []
            for case in cases:
                task = strict_json((FIXTURES / "tasks" / (case["task"] + ".json")).read_text())
                result = execute(DemoProvider(), FIXTURES, task, args.output / case["task"])
                passed = result["selected_run_id"] == case["selected_run_id"] and result["status"] == case["status"]
                scores.append({"task": case["task"], "passed": passed})
            report = {"provider": "scripted_demo", "cases": scores, "passed": sum(c["passed"] for c in scores), "total": len(scores)}
            (args.output / "evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report, indent=2))
            if not all(c["passed"] for c in scores):
                raise SystemExit(1)
            return
        if args.command == "demo":
            provider, workspace = DemoProvider(), FIXTURES
            task = strict_json((FIXTURES / "tasks" / (args.task + ".json")).read_text())
            budget = Budget()
        else:
            if not args.model:
                parser.error("Provide --model or export AGENT_MODEL.")
            provider, workspace = ChatProvider(args.model, args.base_url), args.workspace
            task = strict_json(args.task.read_text())
            budget = Budget(turns=args.max_turns, tool_calls=args.max_tool_calls, seconds=args.max_seconds)
        result = execute(provider, workspace, task, args.output, budget)
        print(json.dumps({"provider": provider.label, "status": result["status"],
                          "selected_run_id": result["selected_run_id"], "output": str(args.output)}, indent=2))
    except FileExistsError:
        parser.exit(1, "Output already exists; choose a new --output directory or filename.\n")
    except (AgentError, ProviderError, ValueError, OSError) as error:
        parser.exit(1, f"{type(error).__name__}: {error}\n")
