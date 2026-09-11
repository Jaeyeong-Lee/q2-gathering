"""Minimal OpenAI-compatible chat client. One retry layer, no provider SDK needed."""

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler


class LLMError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    # Do not forward Authorization to a redirected host.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OpenAICompatible:
    def __init__(
        self,
        base_url,
        model,
        api_key="",
        timeout=120,
        attempts=3,
        response_format="json_object",
        max_tokens=8192,
        sleep=time.sleep,
    ):
        parsed = urlsplit(base_url)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise LLMError(
                "NEBULA_BASE_URL must be an HTTP(S) base URL without credentials/query"
            )
        if not model or response_format not in ("json_object", "none"):
            raise LLMError("model and valid JSON response mode required")
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model, self.api_key = model, api_key
        self.timeout, self.attempts = timeout, attempts
        self.mode, self.max_tokens, self.sleep = response_format, max_tokens, sleep
        self.opener = build_opener(NoRedirect())
        self.cache_identity = {
            "provider": "openai-compatible",
            "base_url": base_url,
            "model": model,
            "mode": response_format,
            "max_tokens": max_tokens,
        }

    @classmethod
    def from_env(cls):
        base, model = os.getenv("NEBULA_BASE_URL"), os.getenv("NEBULA_MODEL")
        if not base or not model:
            raise LLMError(
                "Set NEBULA_BASE_URL and NEBULA_MODEL; no external endpoint is selected by default"
            )
        return cls(
            base,
            model,
            os.getenv("NEBULA_API_KEY", ""),
            timeout=float(os.getenv("NEBULA_TIMEOUT", "120")),
            response_format=os.getenv("NEBULA_JSON_MODE", "json_object"),
            max_tokens=int(os.getenv("NEBULA_MAX_TOKENS", "8192")),
        )

    def complete(self, stage, system, payload):
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "max_tokens": self.max_tokens,
        }
        if self.mode != "none":
            body["response_format"] = {"type": "json_object"}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        request = Request(
            self.url, data=json.dumps(body).encode(), headers=headers, method="POST"
        )
        for attempt in range(self.attempts):
            try:
                with self.opener.open(request, timeout=self.timeout) as response:
                    envelope = json.loads(response.read())
                choice = envelope["choices"][0]
                if choice.get("finish_reason") == "length":
                    raise LLMError(
                        "LLM output truncated; increase max tokens or reduce batch size"
                    )
                content = choice["message"]["content"]
                if not isinstance(content, str):
                    raise LLMError("LLM returned no text content")
                text = content.strip()
                if text.startswith("```") and text.endswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                return json.loads(text)
            except HTTPError as exc:
                retry = exc.code in (408, 429) or 500 <= exc.code < 600
                if not retry or attempt + 1 == self.attempts:
                    raise LLMError(
                        f"LLM HTTP {exc.code}; response body omitted"
                    ) from None
            except (URLError, TimeoutError, OSError):
                if attempt + 1 == self.attempts:
                    raise LLMError(
                        "LLM network/timeout failure; request details omitted"
                    ) from None
            except (ValueError, KeyError, IndexError, TypeError):
                raise LLMError(
                    "LLM response is not a valid JSON chat completion; body omitted"
                ) from None
            self.sleep(min(2**attempt, 8))
        raise LLMError("LLM attempts exhausted")


class AgentClient:
    """No endpoint. The agent driving the run answers each stage itself.

    Stages are handed off through the output directory and validated exactly like a
    model's response; see docs/nebula-agent-run.md.
    """

    agent_turn = True
    cache_identity = {"provider": "agent", "version": 1}

    def complete(self, stage, system, payload):
        raise LLMError("AgentClient answers through the output directory, not a call")
