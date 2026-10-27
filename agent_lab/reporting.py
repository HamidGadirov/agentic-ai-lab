"""Render verified numbers directly; model-generated prose is not used as evidence."""
import json


def escape(value):
    result = str(value).replace("\n", " ")
    for char in "\\`*_{}[]()#+!|<>":
        result = result.replace(char, "\\" + char)
    return result


def markdown(decision):
    workload, limits = decision["task"]["workload"], decision["task"]["limits"]
    chosen = decision["selected_run_id"]
    synthetic = any(row["synthetic"] for row in decision["results"])
    lines = ["# Benchmark recommendation", "", f"Status: **{escape(decision['status'])}**.", "",
             f"Selected run: **{escape(chosen) if chosen is not None else 'none'}**.", "",
             "Selection maximizes reported output throughput among runs meeting every limit.",
             "This verifies the policy and arithmetic, not the truth or statistical reliability of the input measurements.", ""]
    if synthetic:
        lines += ["**Synthetic demonstration data. These are not measured model or GPU performance results.**", ""]
    lines += ["## Workload and limits", "", "```json", json.dumps({"workload": workload, "limits": limits}, indent=2), "```", "",
              "## Compared runs", "", "| Run | Model | Eligible | TTFT P95 ms | TPOT P95 ms | Error rate | Output tokens/s |",
              "| --- | --- | --- | ---: | ---: | ---: | ---: |"]
    for row in decision["results"]:
        lines.append(f"| {escape(row['run_id'])} | {escape(row['model'])} | {'yes' if row['eligible'] else 'no'} | "
                     f"{row['p95_ttft_ms']:.2f} | {row['p95_tpot_ms']:.2f} | {row['error_rate']:.2%} | {row['output_tokens_per_second']:.2f} |")
    lines += ["", "## Rejections", ""]
    failures = [row for row in decision["results"] if row["failures"]]
    lines += [f"- {escape(row['run_id'])}: {', '.join(escape(value) for value in row['failures'])}." for row in failures] or ["None."]
    lines += ["", "## Evidence", "", "Comparison: `" + decision["comparison_id"] + "`.", ""]
    for source in decision["sources"]:
        lines.append(f"- {escape(source['path'])}; canonical record SHA-256: `{source['sha256']}`.")
    lines += ["", "A point comparison does not establish significance or generalization to another workload.",
              "Provider: `" + decision["execution"]["provider"] + "`.", ""]
    return "\n".join(lines)
