"""OpenRouter client used by both red-team and triage agents.

OpenRouter exposes an OpenAI-compatible API, so we use the official `openai`
Python SDK with a custom `base_url`. This keeps the agent code identical to
what you'd write against OpenAI proper, and lets you swap models per-call.

Default model is Nous Hermes 3 70B — strong tool calling and structured JSON.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelChoice:
    """One model option, used by the eval harness for A/B comparison."""

    slug: str
    display_name: str
    family: str  # hermes, claude, gpt, qwen, etc.


# Curated list of models worth comparing in the eval harness.
# Add/remove freely; the eval harness iterates this.
MODEL_OPTIONS: tuple[ModelChoice, ...] = (
    ModelChoice("nousresearch/hermes-3-llama-3.1-70b", "Hermes 3 70B", "hermes"),
    ModelChoice("nousresearch/hermes-3-llama-3.1-405b", "Hermes 3 405B", "hermes"),
    ModelChoice("anthropic/claude-haiku-4.5", "Claude Haiku 4.5", "claude"),
    ModelChoice("openai/gpt-4o-mini", "GPT-4o mini", "gpt"),
    ModelChoice("qwen/qwen-2.5-72b-instruct", "Qwen 2.5 72B", "qwen"),
    ModelChoice("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B", "llama"),
)


class OpenRouterClient:
    """Thin wrapper over the OpenAI SDK pointed at OpenRouter.

    Adds:
      - JSON-mode helper with Pydantic validation
      - Default model from env
      - Spend-cap guard rail (warns; the real cap is enforced server-side
        in OpenRouter account settings — we just refuse to call if we've
        seen too many calls without it being set)
      - Standard headers OpenRouter likes (HTTP-Referer + X-Title)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str | None = None,
    ) -> None:
        api_key = api_key or os.environ["OPENROUTER_API_KEY"]
        base_url = base_url or os.environ.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        )
        self.default_model = default_model or os.environ.get(
            "OPENROUTER_DEFAULT_MODEL",
            "nousresearch/hermes-3-llama-3.1-70b",
        )
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/justinkok28/project-ouroboros-oss",
                "X-Title": "Project Ouroboros",
            },
        )

        # Soft warning if no spend cap configured. The real cap lives in
        # OpenRouter account settings — this is a paranoia second layer.
        cap = os.environ.get("OPENROUTER_MONTHLY_USD_CAP")
        if not cap:
            logger.warning(
                "OPENROUTER_MONTHLY_USD_CAP not set. Set a spend cap in your "
                "OpenRouter account settings AND this env var as a reminder."
            )

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> ChatCompletion:
        """Plain chat completion."""
        return self._client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
        )

    def chat_json[T: BaseModel](
        self,
        messages: list[dict[str, Any]],
        schema: type[T],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        max_retries: int = 2,
    ) -> T:
        """Chat completion that returns a validated Pydantic instance.

        Uses JSON-mode (`response_format={"type": "json_object"}`). If the model
        returns malformed JSON or fails schema validation, we retry up to
        `max_retries` times, prepending the validation error to the conversation.
        """
        # Inject a strict system message reinforcing JSON-only output
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        system_msg = {
            "role": "system",
            "content": (
                "You must respond with a single JSON object that strictly conforms "
                "to the following JSON Schema. Do not include any prose, markdown, "
                "code fences, or commentary outside the JSON.\n\n"
                f"Schema:\n{schema_json}"
            ),
        }
        full_messages: list[dict[str, Any]] = [system_msg, *messages]

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            response = self.chat(
                full_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or ""
            try:
                parsed = schema.model_validate_json(raw)
                return parsed
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                logger.warning(
                    "Validation failed on attempt %d/%d: %s",
                    attempt + 1,
                    max_retries + 1,
                    e,
                )
                full_messages.append({"role": "assistant", "content": raw})
                full_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response failed schema validation. "
                            f"Error: {e}\n\n"
                            "Reply with ONLY a corrected JSON object."
                        ),
                    }
                )

        raise RuntimeError(
            f"OpenRouter chat_json failed after {max_retries + 1} attempts: {last_error}"
        )
