"""A small validation-and-repair layer for local coding models."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import json
import re
from typing import Callable, Protocol
from urllib import request


SYSTEM_PROMPT = """You are a precise Python coding assistant.
Return only the requested Python source. Do not include analysis, explanations,
Markdown fences, examples, tests, or duplicate definitions. Think internally and
finish with the shortest correct implementation that satisfies every requirement.
"""


class ChatClient(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> str: ...


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    feedback: str = ""


@dataclass(frozen=True)
class CodingResult:
    source: str
    passed: bool
    attempts: int
    feedback: str


class OllamaChatClient:
    """Minimal local-only Ollama client with explicit generation controls."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: int = 120,
    ) -> None:
        if base_url.rstrip("/") not in {
            "http://127.0.0.1:11434",
            "http://localhost:11434",
            "http://host.docker.internal:11434",
        }:
            raise ValueError("coding assistant requires a local Ollama endpoint")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def chat(self, messages: list[dict[str, str]]) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "think": False,
                "options": {
                    "num_ctx": 8192,
                    "num_predict": 1024,
                    "temperature": 0,
                    "top_k": 20,
                    "top_p": 0.95,
                    "min_p": 0,
                    "presence_penalty": 0,
                    "repeat_penalty": 1,
                    "seed": 42,
                },
            }
        ).encode()
        req = request.Request(
            self.base_url + "/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout_seconds) as response:
            payload = json.load(response)
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        return payload.get("message", {}).get("content", "")


def extract_python(text: str) -> str:
    """Accept plain source or exactly one Python fence, rejecting surrounding prose."""
    stripped = text.strip()
    fences = re.fullmatch(r"```(?:python)?\s*\n(.*?)\n?```", stripped, re.DOTALL)
    source = fences.group(1).strip() if fences else stripped
    ast.parse(source)
    return source


def syntax_validator(source: str) -> ValidationResult:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return ValidationResult(False, f"SyntaxError on line {exc.lineno}: {exc.msg}")
    if not tree.body or any(not isinstance(node, ast.FunctionDef) for node in tree.body):
        return ValidationResult(False, "Define functions only; remove prose and top-level code.")
    return ValidationResult(True)


class CodingAssistant:
    """Generate code, validate it, then use concise failures for bounded repair."""

    def __init__(self, client: ChatClient, max_repairs: int = 2) -> None:
        if max_repairs < 0 or max_repairs > 3:
            raise ValueError("max_repairs must be between 0 and 3")
        self.client = client
        self.max_repairs = max_repairs

    def solve(
        self,
        task: str,
        validator: Callable[[str], ValidationResult] = syntax_validator,
    ) -> CodingResult:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task.strip()},
        ]
        last_source = ""
        last_feedback = ""
        for attempt in range(1, self.max_repairs + 2):
            raw = self.client.chat(messages)
            try:
                source = extract_python(raw)
                validation = validator(source)
            except (SyntaxError, ValueError) as exc:
                source = raw.strip()
                validation = ValidationResult(False, f"Invalid Python output: {exc}")
            if validation.passed:
                return CodingResult(source, True, attempt, "")
            last_source = source
            last_feedback = validation.feedback[:4000]
            if attempt <= self.max_repairs:
                messages.extend(
                    [
                        {"role": "assistant", "content": source},
                        {
                            "role": "user",
                            "content": (
                                "The candidate failed validation. Fix only the defects below and "
                                "return the complete corrected Python source, with no prose.\n\n"
                                + last_feedback
                            ),
                        },
                    ]
                )
        return CodingResult(last_source, False, self.max_repairs + 1, last_feedback)
