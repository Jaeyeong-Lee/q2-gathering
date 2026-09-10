"""Real HTTP adapter integration against a loopback OpenAI-compatible server."""

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from nebula.demo import FakeClient, source
from nebula.llm import OpenAICompatible, LLMError
from nebula.pipeline import run


class HTTPContract(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.failures = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                owner.requests.append(
                    (self.path, body, self.headers.get("Authorization"))
                )
                if owner.failures:
                    code = owner.failures.pop(0)
                    self.send_response(code)
                    self.end_headers()
                    self.wfile.write(b"PRIVATE ERROR BODY")
                    return
                system = body["messages"][0]["content"]
                stage = (
                    "extract"
                    if system.startswith("You extract")
                    else (
                        "taxonomy"
                        if system.startswith("Build local")
                        else (
                            "consolidate"
                            if system.startswith("Consolidate")
                            else "assign"
                        )
                    )
                )
                result = FakeClient().complete(
                    stage, system, json.loads(body["messages"][1]["content"])
                )
                response = {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {
                                "content": json.dumps(result, ensure_ascii=False)
                            },
                        }
                    ]
                }
                encoded = json.dumps(response).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}/v1"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_all_pipeline_stages_use_chat_completions_json(self):
        client = OpenAICompatible(
            self.base, "internal-model", "test-key", sleep=lambda _: None
        )
        with tempfile.TemporaryDirectory() as out:
            result = run(source()[:2], out, client)
        self.assertEqual(len(result["tasks"]), 3)
        self.assertEqual(
            len(self.requests), 5
        )  # two people, taxonomy, consolidate, assign
        for path, body, auth in self.requests:
            self.assertEqual(path, "/v1/chat/completions")
            self.assertEqual(body["response_format"], {"type": "json_object"})
            self.assertEqual(auth, "Bearer test-key")
            self.assertEqual(body["model"], "internal-model")

    def test_transient_retry_is_bounded_and_error_does_not_leak_body(self):
        self.failures = [429, 503, 503]
        client = OpenAICompatible(self.base, "model", attempts=3, sleep=lambda _: None)
        with self.assertRaises(LLMError) as caught:
            client.complete("extract", "You extract", {"text": source()[0]["text"]})
        self.assertEqual(len(self.requests), 3)
        self.assertNotIn("PRIVATE", str(caught.exception))

    def test_nonretryable_auth_error_and_json_mode_fallback(self):
        self.failures = [401]
        client = OpenAICompatible(
            self.base, "model", response_format="none", sleep=lambda _: None
        )
        with self.assertRaises(LLMError):
            client.complete("extract", "You extract", {"text": source()[0]["text"]})
        self.assertEqual(len(self.requests), 1)
        self.assertNotIn("response_format", self.requests[0][1])
