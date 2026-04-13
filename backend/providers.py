from __future__ import annotations

import json
import os
import textwrap
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse

from .models import ProblemSnapshot, SolveDraft


class BaseProvider(ABC):
    name = "base"

    @abstractmethod
    def generate(self, problem: ProblemSnapshot) -> SolveDraft:
        raise NotImplementedError


class RuleBasedProvider(BaseProvider):
    name = "rule_based"

    def generate(self, problem: ProblemSnapshot) -> SolveDraft:
        language = problem.language.lower()
        code = self._draft_code(problem, language)
        analysis = (
            f"Draft generated locally for '{problem.title or problem.slug or 'untitled problem'}'. "
            "This is a study-oriented starter and should be reviewed before running or submitting."
        )
        complexity = "Complexity is not inferred reliably in fallback mode. Review the algorithm manually."
        warnings = [
            "Fallback provider is active, so the draft may be incomplete for arbitrary problems.",
            "Hidden test cases are not available from the page and cannot be validated locally.",
        ]
        return SolveDraft(
            provider=self.name,
            code=code,
            analysis=analysis,
            complexity=complexity,
            warnings=warnings,
        )

    def _draft_code(self, problem: ProblemSnapshot, language: str) -> str:
        starter = (problem.starter_code or "").strip()
        if starter and not self._looks_like_code(starter):
            starter = ""
        if language.startswith("python"):
            if starter:
                return self._python_from_starter(problem, starter)
            return self._python_template(problem)
        if language.startswith("java"):
            return self._java_template(problem, starter)
        if "c++" in language or language == "cpp":
            return self._cpp_template(problem, starter)
        if "javascript" in language or language == "js":
            return self._javascript_template(problem, starter)
        return starter or self._plain_template(problem)

    def _python_from_starter(self, problem: ProblemSnapshot, starter: str) -> str:
        header = textwrap.dedent(
            f'''\
            # Draft generated for: {problem.title or "LeetCode Problem"}
            # Review the algorithm, edge cases, and complexity before submitting.

            '''
        )
        if "pass" in starter:
            return header + starter.replace(
                "pass",
                textwrap.dedent(
                    """\
                    # TODO: implement the optimal algorithm for this problem.
                    # Consider:
                    # 1. the core data structure
                    # 2. boundary inputs and empty cases
                    # 3. time and space complexity
                    raise NotImplementedError("Replace this draft with a reviewed solution")
                    """
                ).rstrip(),
                1,
            )
        return header + starter

    def _python_template(self, problem: ProblemSnapshot) -> str:
        prompt_hint = (problem.statement or "").splitlines()
        first_line = prompt_hint[0].strip() if prompt_hint else "Implement the required logic."
        return textwrap.dedent(
            f'''\
            # Draft generated for: {problem.title or "LeetCode Problem"}
            # Problem hint: {first_line}

            class Solution:
                def solve(self, *args, **kwargs):
                    # TODO: replace this fallback draft with the correct LeetCode method.
                    raise NotImplementedError("Implement the solution for this problem")
            '''
        )

    def _java_template(self, problem: ProblemSnapshot, starter: str) -> str:
        if starter:
            return starter
        return textwrap.dedent(
            f'''\
            // Draft generated for: {problem.title or "LeetCode Problem"}
            class Solution {{
                public Object solve() {{
                    throw new UnsupportedOperationException("Implement the solution for this problem");
                }}
            }}
            '''
        )

    def _cpp_template(self, problem: ProblemSnapshot, starter: str) -> str:
        if starter:
            return starter
        return textwrap.dedent(
            f'''\
            // Draft generated for: {problem.title or "LeetCode Problem"}
            class Solution {{
            public:
                int solve() {{
                    throw "Implement the solution for this problem";
                }}
            }};
            '''
        )

    def _javascript_template(self, problem: ProblemSnapshot, starter: str) -> str:
        if starter:
            return starter
        return textwrap.dedent(
            f'''\
            // Draft generated for: {problem.title or "LeetCode Problem"}
            var solve = function() {{
                throw new Error("Implement the solution for this problem");
            }};
            '''
        )

    def _plain_template(self, problem: ProblemSnapshot) -> str:
        return f"// Draft generated for: {problem.title or 'LeetCode Problem'}"

    def _looks_like_code(self, text: str) -> bool:
        lowered = text.lower()
        signals = [
            "class ",
            "def ",
            "return ",
            "public ",
            "#include",
            "function ",
            "var ",
            "let ",
            "const ",
            "=>",
            "{",
            "}",
            ";",
            "\n",
        ]
        return any(signal in lowered for signal in signals)


class OpenAIResponsesProvider(BaseProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, api_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.api_url = api_url

    def generate(self, problem: ProblemSnapshot) -> SolveDraft:
        raw = self._request_completion(problem)
        payload = self._parse_json(raw)
        warnings = list(payload.get("warnings", []))
        warnings.append(
            "Model-generated drafts should be reviewed locally before being run or submitted."
        )
        return SolveDraft(
            provider=self.name,
            code=str(payload.get("code", "")).strip(),
            analysis=str(payload.get("analysis", "")).strip(),
            complexity=str(payload.get("complexity", "")).strip(),
            warnings=warnings,
        )

    def _request_completion(self, problem: ProblemSnapshot) -> str:
        system_prompt = (
            "You are a coding study assistant. Produce a careful draft solution for the visible problem only. "
            "Do not claim hidden tests passed. Return strict JSON with keys code, analysis, complexity, warnings."
        )
        user_prompt = json.dumps(problem.to_dict(), ensure_ascii=False)
        endpoint_kind = _detect_api_style(self.api_url)
        request_body = json.dumps(
            self._build_request_payload(
                endpoint_kind=endpoint_kind,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.api_url,
            data=request_body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = ""
            try:
                details = exc.read().decode("utf-8").strip()
            except OSError:
                details = ""
            if details:
                raise RuntimeError(f"Model provider returned HTTP {exc.code}: {details}") from exc
            raise RuntimeError(f"Model provider returned HTTP {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Unable to reach model provider: {exc}") from exc

        return self._extract_text_payload(endpoint_kind=endpoint_kind, payload=payload)

    def _build_request_payload(self, endpoint_kind: str, system_prompt: str, user_prompt: str) -> dict[str, object]:
        if endpoint_kind == "chat_completions":
            return {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
        return {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
        }

    def _extract_text_payload(self, endpoint_kind: str, payload: dict[str, object]) -> str:
        if endpoint_kind == "chat_completions":
            choices = payload.get("choices", [])
            if isinstance(choices, list):
                for choice in choices:
                    if not isinstance(choice, dict):
                        continue
                    message = choice.get("message", {})
                    if not isinstance(message, dict):
                        continue
                    content = message.get("content", "")
                    text = _coerce_message_text(content)
                    if text:
                        return text
            raise RuntimeError("Model response did not include a chat completion message.")

        if payload.get("output_text"):
            return str(payload["output_text"])

        parts: list[str] = []
        output = payload.get("output", [])
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content", [])
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    text = block.get("text")
                    if text:
                        parts.append(str(text))
        joined = "\n".join(parts).strip()
        if not joined:
            raise RuntimeError("Model response did not include any text output.")
        return joined

    def _parse_json(self, raw: str) -> dict[str, object]:
        candidate = raw.strip()
        if candidate.startswith("```"):
            candidate = candidate.strip("`")
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Model response was not valid JSON.") from exc
        if not isinstance(data, dict):
            raise RuntimeError("Model response JSON must be an object.")
        return data


def default_provider_settings() -> dict[str, str]:
    config = _load_local_provider_config()
    api_key = (
        os.getenv("LEETBOT_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
        or str(config.get("apiKey", "")).strip()
    )
    provider = (
        os.getenv("LEETBOT_PROVIDER", "").strip().lower()
        or str(config.get("provider", "")).strip().lower()
        or ("openai" if api_key else "rule_based")
    )
    return {
        "provider": provider,
        "apiKey": api_key,
        "model": (
            os.getenv("LEETBOT_MODEL", "").strip()
            or str(config.get("model", "")).strip()
            or "gpt-4.1-mini"
        ),
        "apiUrl": (
            os.getenv("LEETBOT_API_URL", "").strip()
            or str(config.get("apiUrl", "")).strip()
            or "https://api.openai.com/v1/responses"
        ),
    }


def _load_local_provider_config() -> dict[str, str]:
    config_path = Path(__file__).resolve().parent / "provider_config.local.json"
    if not config_path.exists():
        return {}
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): str(value) for key, value in payload.items() if value is not None}


def create_provider_from_settings(settings: dict[str, str] | None = None) -> BaseProvider:
    resolved = default_provider_settings()
    if settings:
        resolved.update(
            {
                key: value
                for key, value in settings.items()
                if value is not None and (not isinstance(value, str) or value.strip())
            }
        )

    provider_name = str(resolved.get("provider", "rule_based")).strip().lower()
    if provider_name == "openai":
        api_key = str(resolved.get("apiKey", "")).strip()
        model = str(resolved.get("model", "gpt-4.1-mini")).strip()
        api_url = str(resolved.get("apiUrl", "https://api.openai.com/v1/responses")).strip()
        if api_key or _is_local_api_url(api_url):
            return OpenAIResponsesProvider(api_key=api_key, model=model, api_url=api_url)
    return RuleBasedProvider()


def create_provider() -> BaseProvider:
    return create_provider_from_settings()


def _detect_api_style(api_url: str) -> str:
    path = urlparse(api_url).path.rstrip("/").lower()
    if path.endswith("/chat/completions"):
        return "chat_completions"
    return "responses"


def _is_local_api_url(api_url: str) -> bool:
    host = (urlparse(api_url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "0.0.0.0", "::1"}


def _coerce_message_text(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") in {"text", "output_text"} and item.get("text"):
                parts.append(str(item["text"]))
        return "\n".join(parts).strip()
    return ""
