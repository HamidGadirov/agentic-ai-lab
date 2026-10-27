# Benchmark recommendation

Status: **selected**.

Selected run: **fast**.

Selection maximizes reported output throughput among runs meeting every limit.
This verifies the policy and arithmetic, not the truth or statistical reliability of the input measurements.

**Synthetic demonstration data. These are not measured model or GPU performance results.**

## Workload and limits

```json
{
  "workload": {
    "workload_id": "synthetic-chat-v1",
    "input_tokens": 1024,
    "output_tokens": 128,
    "concurrency": 8,
    "accelerator": "synthetic-accelerator",
    "accelerator_count": 1
  },
  "limits": {
    "p95_ttft_ms": 350,
    "p95_tpot_ms": 25,
    "max_error_rate": 0.02
  }
}
```

## Compared runs

| Run | Model | Eligible | TTFT P95 ms | TPOT P95 ms | Error rate | Output tokens/s |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| balanced | demo-model-a | yes | 260.00 | 18.00 | 0.00% | 900.00 |
| bulk | demo-model-c | no | 480.00 | 30.00 | 0.00% | 2000.00 |
| fast | demo-model-b | yes | 330.00 | 20.00 | 1.00% | 1250.00 |
| unreliable | demo-model-d | no | 220.00 | 15.00 | 5.00% | 1500.00 |

## Rejections

- bulk: p95\_ttft\_ms\_exceeded, p95\_tpot\_ms\_exceeded.
- unreliable: error\_rate\_exceeded.

## Evidence

Comparison: `comparison:9d9e60c7e53fcb92`.

- runs/balanced.json; canonical record SHA-256: `916223f9d64fc99dd45a59a57c22dea32650c6c115449b5afbdaa759e76d777d`.
- runs/bulk.json; canonical record SHA-256: `9307333fa222f38ca6c94f6b50c23c7725edbf0ce3d13811ae19469174e2598e`.
- runs/fast.json; canonical record SHA-256: `1ee0db4abc8da03dd1142757cbed78b1937a61d12f80995ef8626ddd344c942c`.
- runs/unreliable.json; canonical record SHA-256: `5edd40a980e627bac45b71f4111e3323ec33f9788eccc5b8f9690ba1b4253edc`.

A point comparison does not establish significance or generalization to another workload.
Provider: `scripted_demo`.
