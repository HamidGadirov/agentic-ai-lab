# Task and evidence formats

## Workspace layout

```text
workspace/
  runs/
    candidate-a.json
    candidate-b.json
  notes/
    experiment-context.md
```

The caller chooses the workspace. The agent chooses known run IDs rather than
arbitrary file paths. At most 16 top-level JSON run files and 16 top-level Markdown
notes are supported. Files over 64 KiB, symlinks, invalid records, and duplicate
run IDs are rejected. Invalid evidence stops loading; it is not silently omitted.

## Normalized run

```json
{
  "schema_version": 1,
  "run_id": "candidate-a",
  "model": "your-model-and-revision",
  "precision": "bf16",
  "synthetic": false,
  "workload": {
    "workload_id": "your-fixed-dataset-and-protocol",
    "input_tokens": 1024,
    "output_tokens": 128,
    "concurrency": 8,
    "accelerator": "your-accelerator",
    "accelerator_count": 1
  },
  "metrics": {
    "completed": 100,
    "failed": 1,
    "p95_ttft_ms": 300,
    "p95_tpot_ms": 20,
    "output_tokens_per_second": 1000
  }
}
```

These numbers illustrate the schema; they are not measured results. The
`synthetic` field distinguishes fabricated demonstration measurements from
imported measurements, not random synthetic prompts from natural-language
traffic. A measured vLLM random-token benchmark is still a measurement.

All workload fields must match the task exactly. Model and precision may differ.
Encode the dataset/prompt distribution, tokenizer-length protocol, sampling,
cache warmup protocol, and other fixed experimental conditions in the workload
identifier or maintain that provenance externally. Matching labels alone does
not prove experimentally comparable runs.

TTFT means time to first token, TPOT means time per output token, and throughput
is aggregate output tokens per second. Latencies must be positive milliseconds;
throughput must be positive. At least one completed request is required. Error
rate is `failed / (completed + failed)`, and every limit is inclusive. The policy
uses reported percentiles directly; it does not recompute or validate their
sampling uncertainty.

## Task

The task has `question`, `workload`, and `limits`. The structured limits are
`p95_ttft_ms`, `p95_tpot_ms`, and `max_error_rate`, where error rate is a fraction
such as 0.02, not a percentage such as 2. See `examples/task.json`.
The question is explanatory; numeric constraints are not extracted from prose.

## Import a vLLM report

`import-vllm` expects the flat metrics `completed`, `failed`, `p95_ttft_ms`,
`p95_tpot_ms`, and `output_throughput`, matching the reviewed vLLM benchmark
format. It maps throughput to `output_tokens_per_second`, records the source
file's SHA-256, and validates the resulting record. Missing failure/percentile
fields cause an error. Other versions or nested formats need an explicit adapter.

`examples/run-metadata.json` supplies `run_id`, `model`, `precision`, and
`workload`; edit it for the actual experiment. This metadata is supplied by the
caller and is not independently inferred or authenticated. Do not invent zero
failures or copy P50 values into P95 fields to satisfy validation.

For older logs that lack required fields, re-run a suitable benchmark or extend
the data model and decision policy explicitly. Do not claim identical evidence
quality when the required measurement is unavailable.
