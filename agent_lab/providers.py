"""A real tool-calling HTTP client and a clearly labelled deterministic demo."""
import json
import os
import time
import urllib.error
import urllib.request

from .contracts import digest, strict_json


class ProviderError(RuntimeError):
    pass


def tool_reply(calls):
    return {"message": {"role": "assistant", "content": None, "tool_calls": [
        {"id": f"demo-{name}-{index}-{digest(arguments)[:8]}", "type": "function",
         "function": {"name": name, "arguments": json.dumps(arguments)}}
        for index, (name, arguments) in enumerate(calls)]}, "finish_reason": "tool_calls", "usage": {}}


class DemoProvider:
    """Scripted tool selection for testing plumbing; this is not a language model."""
    label = "scripted_demo"

    def complete(self, messages, tools, timeout):
        observations = [strict_json(m["content"]) for m in messages if m["role"] == "tool"]
        seen = {row["tool"] for row in observations if row["ok"]}
        if "list_runs" not in seen:
            return tool_reply([("list_runs", {})])
        listed = next(row["result"] for row in observations if row["tool"] == "list_runs" and row["ok"])
        ids = listed["matching_run_ids"]
        if ids and "read_run" not in seen:
            return tool_reply([("read_run", {"run_id": run_id}) for run_id in ids])
        if "search_notes" not in seen:
            return tool_reply([("search_notes", {"query": "latency throughput", "limit": 2})])
        if "compare_runs" not in seen:
            return tool_reply([("compare_runs", {"run_ids": ids})])
        result = next(row["result"] for row in reversed(observations) if row["tool"] == "compare_runs" and row["ok"])
        return tool_reply([("submit_decision", {"comparison_id": result["comparison_id"],
                                                "selected_run_id": result["selected_run_id"]})])


class ChatProvider:
    label = "live_chat_model"

    def __init__(self, model, base_url="http://127.0.0.1:8000/v1", max_tokens=1024, max_attempts=2):
        if not base_url.startswith(("http://", "https://")) or not model:
            raise ValueError("Provide a model alias and an HTTP(S) API base URL.")
        self.model, self.base_url = model, base_url.rstrip("/")
        self.max_tokens, self.max_attempts = max_tokens, max_attempts

    def complete(self, messages, tools, timeout):
        body = json.dumps({"model": self.model, "messages": messages, "tools": tools,
                           "tool_choice": "auto", "temperature": 0, "max_tokens": self.max_tokens}, allow_nan=False).encode()
        headers = {"Content-Type": "application/json"}
        if os.environ.get("AGENT_API_KEY"):
            headers["Authorization"] = "Bearer " + os.environ["AGENT_API_KEY"]
        request = urllib.request.Request(self.base_url + "/chat/completions", data=body, headers=headers)
        deadline = time.monotonic() + timeout
        for attempt in range(self.max_attempts):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProviderError("Model request time budget exhausted.")
            try:
                with urllib.request.urlopen(request, timeout=remaining) as response:
                    raw = response.read(262145)
                if len(raw) > 262144:
                    raise ProviderError("Model response exceeds 256 KiB.")
                payload = strict_json(raw.decode())
                choice = payload["choices"][0]
                message = choice["message"]
                if message.get("role") != "assistant":
                    raise ProviderError("Expected an assistant response.")
                # Preserve returned reasoning fields for models whose templates need them,
                # but the agent never writes those fields into its execution trace.
                allowed = {key: message[key] for key in ["role", "content", "tool_calls", "reasoning", "reasoning_content"] if key in message}
                usage = {key: value for key, value in (payload.get("usage") or {}).items()
                         if key in {"prompt_tokens", "completion_tokens", "total_tokens"} and type(value) is int}
                return {"message": allowed, "finish_reason": choice.get("finish_reason"), "usage": usage}
            except urllib.error.HTTPError as error:
                if error.code in {429, 502, 503, 504} and attempt + 1 < self.max_attempts:
                    time.sleep(min(0.25, max(0, deadline - time.monotonic())))
                    continue
                raise ProviderError(f"Model endpoint returned HTTP {error.code}.") from error
            except (urllib.error.URLError, TimeoutError) as error:
                raise ProviderError("Model endpoint is unavailable or timed out.") from error
            except (KeyError, IndexError, TypeError, ValueError, UnicodeError) as error:
                raise ProviderError("Model endpoint returned an invalid response.") from error
        raise ProviderError("Model request failed.")
