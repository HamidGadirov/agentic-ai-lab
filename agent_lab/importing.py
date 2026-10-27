"""Import a flat vLLM benchmark result with explicit experimental metadata."""
import hashlib

from .contracts import RUN, strict_json, validate


def import_vllm(source, metadata):
    raw = source.read_bytes()
    report = strict_json(raw.decode())
    meta = strict_json(metadata.read_text())
    allowed = {"run_id", "model", "precision", "workload"}
    if set(meta) != allowed:
        raise ValueError("Metadata must contain run_id, model, precision, and workload only.")
    mapping = {"completed": "completed", "failed": "failed", "p95_ttft_ms": "p95_ttft_ms",
               "p95_tpot_ms": "p95_tpot_ms", "output_tokens_per_second": "output_throughput"}
    if any(field not in report for field in mapping.values()):
        raise ValueError("Required flat benchmark metrics are missing; adapt the importer explicitly for this report format.")
    row = {"schema_version": 1, **meta, "synthetic": False,
           "source_sha256": hashlib.sha256(raw).hexdigest(),
           "metrics": {key: report[value] for key, value in mapping.items()}}
    validate(row, RUN)
    return row
