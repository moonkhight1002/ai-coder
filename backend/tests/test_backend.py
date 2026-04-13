from __future__ import annotations

import json
import threading
import time
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
import os

from backend.app import LeetCodeCopilotApp
from backend.models import ProblemSnapshot, SolveDraft
from backend.providers import BaseProvider, OpenAIResponsesProvider, RuleBasedProvider, create_provider_from_settings, default_provider_settings
from backend.server import ApiHandler
from backend import providers as providers_module


class FakeProvider(BaseProvider):
    name = "fake"

    def generate(self, problem: ProblemSnapshot) -> SolveDraft:
        return SolveDraft(
            provider=self.name,
            code="class Solution:\n    pass\n",
            analysis=f"Generated for {problem.slug}",
            complexity="O(n)",
            warnings=[],
        )


class ProviderTests(unittest.TestCase):
    def test_rule_based_provider_uses_starter_code(self) -> None:
        provider = RuleBasedProvider()
        problem = ProblemSnapshot(
            platform="leetcode",
            title="Two Sum",
            slug="two-sum",
            url="https://leetcode.com/problems/two-sum/",
            statement="Find two numbers that add up to target.",
            language="python3",
            starter_code="class Solution:\n    def twoSum(self, nums, target):\n        pass\n",
        )

        draft = provider.generate(problem)

        self.assertEqual(draft.provider, "rule_based")
        self.assertIn("NotImplementedError", draft.code)
        self.assertIn("Two Sum", draft.code)
        self.assertTrue(draft.warnings)

    def test_openai_provider_can_be_created_from_settings(self) -> None:
        provider = create_provider_from_settings(
            {
                "provider": "openai",
                "apiKey": "test-key",
                "model": "gpt-4.1-mini",
                "apiUrl": "https://api.openai.com/v1/responses",
            }
        )

        self.assertIsInstance(provider, OpenAIResponsesProvider)

    def test_default_provider_settings_prefers_openai_when_key_present(self) -> None:
        previous_openai_key = os.environ.get("OPENAI_API_KEY")
        previous_leetbot_provider = os.environ.get("LEETBOT_PROVIDER")
        try:
            os.environ["OPENAI_API_KEY"] = "test-key"
            if "LEETBOT_PROVIDER" in os.environ:
                del os.environ["LEETBOT_PROVIDER"]
            settings = default_provider_settings()
            self.assertEqual(settings["provider"], "openai")
            self.assertEqual(settings["apiKey"], "test-key")
        finally:
            if previous_openai_key is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = previous_openai_key
            if previous_leetbot_provider is None:
                os.environ.pop("LEETBOT_PROVIDER", None)
            else:
                os.environ["LEETBOT_PROVIDER"] = previous_leetbot_provider

    def test_default_provider_settings_respects_local_model_and_api_url(self) -> None:
        original_loader = providers_module._load_local_provider_config
        previous_model = os.environ.get("LEETBOT_MODEL")
        previous_api_url = os.environ.get("LEETBOT_API_URL")
        try:
            os.environ.pop("LEETBOT_MODEL", None)
            os.environ.pop("LEETBOT_API_URL", None)
            providers_module._load_local_provider_config = lambda: {
                "provider": "openai",
                "apiKey": "local-key",
                "model": "llama3.2",
                "apiUrl": "http://127.0.0.1:11434/v1/chat/completions",
            }
            settings = default_provider_settings()
            self.assertEqual(settings["model"], "llama3.2")
            self.assertEqual(settings["apiUrl"], "http://127.0.0.1:11434/v1/chat/completions")
        finally:
            providers_module._load_local_provider_config = original_loader
            if previous_model is None:
                os.environ.pop("LEETBOT_MODEL", None)
            else:
                os.environ["LEETBOT_MODEL"] = previous_model
            if previous_api_url is None:
                os.environ.pop("LEETBOT_API_URL", None)
            else:
                os.environ["LEETBOT_API_URL"] = previous_api_url

    def test_rule_based_provider_ignores_plain_text_starter(self) -> None:
        provider = RuleBasedProvider()
        problem = ProblemSnapshot(
            platform="leetcode",
            title="Zigzag Conversion",
            slug="zigzag-conversion",
            url="https://leetcode.com/problems/zigzag-conversion/",
            statement="Convert a string to zigzag format.",
            language="python3",
            starter_code='"PAYPALISHIRING"',
        )

        draft = provider.generate(problem)

        self.assertIn("class Solution", draft.code)
        self.assertNotEqual(draft.code.strip(), '"PAYPALISHIRING"')

    def test_create_provider_from_settings_keeps_default_key_when_override_is_blank(self) -> None:
        provider = create_provider_from_settings(
            {
                "provider": "openai",
                "apiKey": "",
                "model": "gpt-4.1-mini",
                "apiUrl": "https://api.openai.com/v1/responses",
            }
        )

        self.assertIsInstance(provider, OpenAIResponsesProvider)

    def test_create_provider_from_settings_allows_local_url_without_api_key(self) -> None:
        provider = create_provider_from_settings(
            {
                "provider": "openai",
                "apiKey": "",
                "model": "llama3.2",
                "apiUrl": "http://127.0.0.1:11434/v1/chat/completions",
            }
        )

        self.assertIsInstance(provider, OpenAIResponsesProvider)

    def test_chat_completions_payload_text_is_extracted(self) -> None:
        provider = OpenAIResponsesProvider(
            api_key="",
            model="llama3.2",
            api_url="http://127.0.0.1:11434/v1/chat/completions",
        )

        text = provider._extract_text_payload(
            endpoint_kind="chat_completions",
            payload={
                "choices": [
                    {
                        "message": {
                            "content": '{"code":"pass","analysis":"ok","complexity":"O(1)","warnings":[]}'
                        }
                    }
                ]
            },
        )

        self.assertIn('"code":"pass"', text)


class ApiTests(unittest.TestCase):
    def test_solve_round_trip(self) -> None:
        from backend import server as server_module

        original_app = server_module.APP
        server_module.APP = LeetCodeCopilotApp(provider=FakeProvider())
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            time.sleep(0.1)
            try:
                port = httpd.server_address[1]
                payload = {
                    "problem": {
                        "platform": "leetcode",
                        "title": "Two Sum",
                        "slug": "two-sum",
                        "url": "https://leetcode.com/problems/two-sum/",
                        "statement": "Given an array and a target.",
                        "language": "python3",
                    },
                    "autoSolve": True,
                    "autoAdvance": False,
                }
                request = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/solve",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=5) as response:
                    body = json.loads(response.read().decode("utf-8"))

                self.assertEqual(body["status"], "draft_ready")
                self.assertEqual(body["draft"]["provider"], "fake")
                self.assertEqual(body["state"]["current_problem"]["slug"], "two-sum")
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=2)
        finally:
            server_module.APP = original_app

    def test_configure_provider_preserves_default_api_key_when_payload_key_is_blank(self) -> None:
        app = LeetCodeCopilotApp()

        response = app.configure_provider(
            {
                "provider": "openai",
                "apiKey": "",
                "model": "gpt-4.1-mini",
                "apiUrl": "https://api.openai.com/v1/responses",
            }
        )

        self.assertEqual(response["provider"], "openai")
        self.assertTrue(response["hasApiKey"])


if __name__ == "__main__":
    unittest.main()
