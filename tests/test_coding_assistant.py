from coding_assistant import (
    CodingAssistant,
    OllamaChatClient,
    ValidationResult,
    extract_python,
    syntax_validator,
)


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.messages = []

    def chat(self, messages):
        self.messages.append(messages)
        return next(self.responses)


def test_extracts_plain_source_and_single_fence():
    assert extract_python("def f():\n    return 1") == "def f():\n    return 1"
    assert extract_python("```python\ndef f():\n    return 1\n```").startswith("def f")


def test_repairs_failed_candidate_with_concise_feedback():
    client = FakeClient(["def add(a, b):\n    return a - b", "def add(a, b):\n    return a + b"])

    def validate(source):
        namespace = {}
        exec(source, {"__builtins__": {}}, namespace)
        return ValidationResult(namespace["add"](2, 3) == 5, "add(2, 3) returned -1; expected 5")

    result = CodingAssistant(client).solve("Define add(a, b).", validate)
    assert result.passed
    assert result.attempts == 2
    assert "returned -1" in client.messages[1][-1]["content"]


def test_stops_after_repair_limit():
    client = FakeClient(["def f():\n    return 0"] * 3)
    result = CodingAssistant(client, max_repairs=2).solve(
        "Define f.", lambda _: ValidationResult(False, "expected 1")
    )
    assert not result.passed
    assert result.attempts == 3


def test_syntax_validator_requires_functions_only():
    assert syntax_validator("def f():\n    return 1").passed
    assert not syntax_validator("print('hello')").passed


def test_ollama_client_rejects_remote_endpoint():
    try:
        OllamaChatClient("qwen3.5:4b", "http://example.com:11434")
    except ValueError as exc:
        assert "local" in str(exc)
    else:
        raise AssertionError("remote endpoint should be rejected")


def test_ollama_client_allows_host_bridge():
    client = OllamaChatClient("qwen3.5:4b", "http://host.docker.internal:11434")
    assert client.base_url == "http://host.docker.internal:11434"
