# Validation scope

Release: 0.1.0. Validation environment: Python 3.12, jsonschema 4.26.0.

- All 17 unittest tests passed.
- All three scripted fixture cases passed: an eligible winner, no eligible run,
  and no matching workload.
- A complete multi-turn tool exchange passed through the actual HTTP client
  against a local scripted chat-completions server.
- The project built and installed through pip; its installed package, run outside
  the source directory, passed the demo and all three fixture cases. This checks
  that the fixture files are included in the distribution.

The tests cover strict JSON and schema validation, local evidence boundaries,
incomplete candidate sets, forged comparison identifiers, incorrect decisions,
tool errors and recovery, execution budgets, trace behavior, and the explicit
vLLM report importer. They use temporary directories and synthetic evidence.

No live language model, GPU inference server, or real benchmark dataset was used
for this validation. The offline evaluation measures workflow correctness; it is
not a model intelligence, prompt-injection robustness, or performance benchmark.
Time limits are cooperative and are not a process-level resource sandbox.

To reproduce the workflow checks:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m agent_lab demo
python -m agent_lab evaluate
```

Choose a new `--output` directory when repeating either command; existing output
directories are intentionally preserved.
