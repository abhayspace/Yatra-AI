"""The only place a language-model client is constructed.

Claude Sonnet is reached through an Azure AI Foundry deployment. Configuration comes from
AZURE_AI_FOUNDRY_ENDPOINT, AZURE_AI_FOUNDRY_API_KEY and AZURE_AI_FOUNDRY_DEPLOYMENT_NAME;
if any is missing the client refuses to start rather than falling back to another provider.
Other modules depend on the LLMClient interface, so tests can supply a scripted stand-in and
the provider stays swappable.
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, TypeVar
from urllib.parse import urlparse

import anthropic
from pydantic import BaseModel, ValidationError

from agent.errors import LLMError
from agent.settings import ConfigError, Settings, get_settings

T = TypeVar("T", bound=BaseModel)

SUBMIT_TOOL = "submit"


class LLMClient(ABC):
    """What the agent needs from a language model."""

    @abstractmethod
    def complete_structured(self, task: str, system: str, user: str, schema: type[T]) -> T:
        """Return an instance of `schema`. `task` names the call site (parse_intent, compose_reply, ...)."""


def foundry_base_url(endpoint: str) -> str:
    """Anthropic-compatible base URL for an Azure AI Foundry project or resource endpoint.

    https://<resource>.services.ai.azure.com/api/projects/<project>  ->  https://<resource>.services.ai.azure.com/anthropic
    """
    parsed = urlparse(endpoint.strip())
    if parsed.scheme != "https" or not parsed.netloc:
        raise ConfigError("AZURE_AI_FOUNDRY_ENDPOINT must be an https URL.")
    return f"https://{parsed.netloc}/anthropic"


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced:
        text = fenced.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise LLMError("The model did not return structured output.")
    try:
        obj = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError("The model returned malformed structured output.") from exc
    if not isinstance(obj, dict):
        raise LLMError("The model returned an unexpected structure.")
    return obj


class AzureFoundryLLM(LLMClient):
    def __init__(self, settings: Settings):
        settings.require_llm()
        self._model = settings.azure_ai_foundry_deployment_name
        self._max_tokens = settings.llm_max_tokens
        self._client = anthropic.AnthropicFoundry(
            api_key=settings.azure_ai_foundry_api_key.get_secret_value(),
            base_url=foundry_base_url(settings.azure_ai_foundry_endpoint),
            timeout=settings.llm_timeout_seconds,
            max_retries=2,
        )
        self._forced_tool_ok = True

    def _call(self, system: str, user: str, schema: type[BaseModel]) -> dict[str, Any]:
        tool = {
            "name": SUBMIT_TOOL,
            "description": "Submit the final structured result.",
            "input_schema": schema.model_json_schema(),
        }
        kwargs: dict[str, Any] = dict(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            tools=[tool],
        )
        kwargs["tool_choice"] = {"type": "tool", "name": SUBMIT_TOOL} if self._forced_tool_ok else {"type": "auto"}
        try:
            try:
                resp = self._client.messages.create(**kwargs)
            except anthropic.BadRequestError as exc:
                # some deployments reject forced tool use; retry once letting the model choose
                if self._forced_tool_ok and "tool_choice" in str(exc):
                    self._forced_tool_ok = False
                    kwargs["tool_choice"] = {"type": "auto"}
                    kwargs["system"] = system + f"\nYou must respond by calling the {SUBMIT_TOOL} tool."
                    resp = self._client.messages.create(**kwargs)
                else:
                    raise
        except anthropic.APIConnectionError as exc:
            raise LLMError("Could not reach the Azure AI Foundry endpoint.") from exc
        except anthropic.AuthenticationError as exc:
            raise LLMError("Azure AI Foundry rejected the API key.") from exc
        except anthropic.NotFoundError as exc:
            raise LLMError("The Azure AI Foundry deployment name was not found.") from exc
        except anthropic.RateLimitError as exc:
            raise LLMError("The Azure AI Foundry deployment is rate limited; try again shortly.") from exc
        except anthropic.APIStatusError as exc:
            raise LLMError(f"Azure AI Foundry returned an error (HTTP {exc.status_code}).") from exc

        for block in resp.content:
            if getattr(block, "type", None) == "tool_use" and block.name == SUBMIT_TOOL and isinstance(block.input, dict):
                return block.input
        texts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        return _extract_json("\n".join(texts))

    def complete_structured(self, task: str, system: str, user: str, schema: type[T]) -> T:
        try:
            return schema.model_validate(self._call(system, user, schema))
        except ValidationError as exc:
            raise LLMError(f"The model's {task} output did not match the expected shape.") from exc


@lru_cache
def get_llm() -> LLMClient:
    """The production client. Raises ConfigError if Azure AI Foundry is not configured."""
    return AzureFoundryLLM(get_settings())
