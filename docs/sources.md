# Public interfaces and references

Reviewed on 27 October 2026.

- [vLLM tool calling](https://docs.vllm.ai/en/latest/features/tool_calling/):
  parser selection, automatic calls, tool schemas, and gpt-oss parser configuration.
- [vLLM serving benchmark CLI](https://docs.vllm.ai/en/latest/cli/bench/serve/):
  benchmark workload controls and output metrics.
- [vLLM 0.32.0 benchmark implementation](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/benchmarks/serve.py):
  flat metric names used by the explicit importer.
- [JSON Schema validation](https://python-jsonschema.readthedocs.io/en/stable/):
  the validation library used for local contracts.
- [Python urllib.request](https://docs.python.org/3/library/urllib.request.html):
  HTTP requests in the small compatible-endpoint client.

Application logic, fixture values, ranking policy, and documentation were written
for this project. No model implementation or agent framework is vendored.
No model weights or external datasets are included. The selected vLLM integration
is a documented interface, not a claim that every tool-capable model has passed
this project's live acceptance tests.
