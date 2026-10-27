"""Strict JSON contracts shared by inputs, tools, and decision verification."""
import hashlib
import json

from jsonschema import Draft202012Validator


def object_schema(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


STRING = {"type": "string", "minLength": 1, "maxLength": 160}
POSITIVE = {"type": "number", "exclusiveMinimum": 0}
NONNEGATIVE = {"type": "number", "minimum": 0}
INTEGER = {"type": "integer", "minimum": 1}
WORKLOAD = object_schema({"workload_id": STRING, "input_tokens": INTEGER, "output_tokens": INTEGER,
                          "concurrency": INTEGER, "accelerator": STRING, "accelerator_count": INTEGER})
TASK = object_schema({"question": {"type": "string", "minLength": 1, "maxLength": 2000},
                      "workload": WORKLOAD,
                      "limits": object_schema({"p95_ttft_ms": POSITIVE, "p95_tpot_ms": POSITIVE,
                                               "max_error_rate": {"type": "number", "minimum": 0, "maximum": 1}})})
RUN = object_schema({"schema_version": {"const": 1}, "run_id": STRING, "model": STRING,
                     "precision": STRING, "synthetic": {"type": "boolean"}, "workload": WORKLOAD,
                     "metrics": object_schema({"completed": INTEGER, "failed": {"type": "integer", "minimum": 0},
                                                "p95_ttft_ms": POSITIVE, "p95_tpot_ms": POSITIVE,
                                                "output_tokens_per_second": POSITIVE})})
RUN["properties"]["source_sha256"] = {"type": "string", "pattern": "^[a-f0-9]{64}$"}


def validate(value, schema):
    errors = list(Draft202012Validator(schema).iter_errors(value))
    if errors:
        path = ".".join(str(x) for x in errors[0].absolute_path) or "root"
        raise ValueError(f"Schema validation failed at {path}.")


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key.")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("Nonfinite JSON constants are not allowed.")

    value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    # Also reject exponent overflow such as 1e999.
    json.dumps(value, allow_nan=False)
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
