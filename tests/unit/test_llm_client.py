import pytest
from pydantic import BaseModel

from agent import llm_client
from agent.errors import LLMError
from agent.llm_client import AzureFoundryLLM, _extract_json, foundry_base_url
from agent.settings import ConfigError, Settings


def settings(**kw):
    base = dict(
        azure_ai_foundry_endpoint="https://res.services.ai.azure.com/api/projects/proj",
        azure_ai_foundry_api_key="k",
        azure_ai_foundry_deployment_name="claude-sonnet",
        _env_file=None,
    )
    base.update(kw)
    return Settings(**base)


def test_project_endpoint_maps_to_anthropic_route():
    assert foundry_base_url("https://res.services.ai.azure.com/api/projects/proj") == "https://res.services.ai.azure.com/anthropic"
    assert foundry_base_url("https://res.services.ai.azure.com/anthropic/") == "https://res.services.ai.azure.com/anthropic"


@pytest.mark.parametrize("bad", ["http://res.services.ai.azure.com", "not a url", "", "ftp://x"])
def test_non_https_endpoint_rejected(bad):
    with pytest.raises(ConfigError):
        foundry_base_url(bad)


@pytest.mark.parametrize("missing", ["azure_ai_foundry_endpoint", "azure_ai_foundry_api_key", "azure_ai_foundry_deployment_name"])
def test_client_refuses_to_start_without_foundry_settings(missing):
    with pytest.raises(ConfigError):
        AzureFoundryLLM(settings(**{missing: ""}))


def test_client_targets_foundry_only():
    llm = AzureFoundryLLM(settings())
    assert str(llm._client.base_url).startswith("https://res.services.ai.azure.com/anthropic")
    assert llm._model == "claude-sonnet"


def test_no_direct_anthropic_endpoint_or_key_in_source():
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    for path in list((root / "agent").rglob("*.py")) + list((root / "backend").rglob("*.py")):
        text = path.read_text()
        assert "api.anthropic.com" not in text, path
        assert "ANTHROPIC_API_KEY" not in text, path


def test_llm_client_is_only_constructed_in_llm_client_module():
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    offenders = [
        str(p) for p in list((root / "agent").rglob("*.py")) + list((root / "backend").rglob("*.py"))
        if p.name != "llm_client.py" and ("AnthropicFoundry(" in p.read_text() or "anthropic.Anthropic(" in p.read_text())
    ]
    assert offenders == []


def test_extract_json_handles_fences_and_noise():
    assert _extract_json('sure:\n```json\n{"a": 1}\n```') == {"a": 1}
    assert _extract_json('{"a": {"b": 2}} trailing') == {"a": {"b": 2}}
    for bad in ("no json here", "{broken", "[1,2]"):
        with pytest.raises(LLMError):
            _extract_json(bad)


class Out(BaseModel):
    x: int


class FakeResp:
    def __init__(self, content):
        self.content = content


class Block:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_structured_call_reads_tool_use_block():
    llm = AzureFoundryLLM(settings())
    seen = {}

    def create(**kw):
        seen.update(kw)
        return FakeResp([Block(type="tool_use", name="submit", input={"x": 3})])

    llm._client.messages.create = create
    assert llm.complete_structured("t", "sys", "user", Out).x == 3
    assert seen["model"] == "claude-sonnet" and seen["tool_choice"] == {"type": "tool", "name": "submit"}
    assert "temperature" not in seen


def test_structured_call_falls_back_to_text_json_and_validates():
    llm = AzureFoundryLLM(settings())
    llm._client.messages.create = lambda **kw: FakeResp([Block(type="text", text='{"x": 5}')])
    assert llm.complete_structured("t", "s", "u", Out).x == 5
    llm._client.messages.create = lambda **kw: FakeResp([Block(type="text", text='{"x": "abc"}')])
    with pytest.raises(LLMError):
        llm.complete_structured("t", "s", "u", Out)


def test_get_llm_without_config_raises(monkeypatch):
    for name in ("AZURE_AI_FOUNDRY_ENDPOINT", "AZURE_AI_FOUNDRY_API_KEY", "AZURE_AI_FOUNDRY_DEPLOYMENT_NAME"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(llm_client, "get_settings", lambda: Settings(_env_file=None))
    llm_client.get_llm.cache_clear()
    with pytest.raises(ConfigError):
        llm_client.get_llm()
    llm_client.get_llm.cache_clear()


def _status_error(cls, status, message):
    import httpx

    req = httpx.Request("POST", "https://res.services.ai.azure.com/anthropic/v1/messages")
    return cls(message, response=httpx.Response(status, request=req), body=None)


def test_forced_tool_choice_rejection_retries_with_auto():
    import anthropic

    llm = AzureFoundryLLM(settings())
    calls = []

    def create(**kw):
        calls.append(kw["tool_choice"])
        if len(calls) == 1:
            raise _status_error(anthropic.BadRequestError, 400, 'tool_choice: type "tool" is not supported')
        return FakeResp([Block(type="tool_use", name="submit", input={"x": 1})])

    llm._client.messages.create = create
    assert llm.complete_structured("t", "s", "u", Out).x == 1
    assert calls == [{"type": "tool", "name": "submit"}, {"type": "auto"}]


@pytest.mark.parametrize("status,cls_name", [(401, "AuthenticationError"), (404, "NotFoundError"), (429, "RateLimitError"), (500, "InternalServerError")])
def test_api_errors_become_llm_errors_without_leaking_details(status, cls_name):
    import anthropic

    llm = AzureFoundryLLM(settings())

    def create(**kw):
        raise _status_error(getattr(anthropic, cls_name), status, "secret-detail-abc")

    llm._client.messages.create = create
    with pytest.raises(LLMError) as exc:
        llm.complete_structured("t", "s", "u", Out)
    assert "secret-detail-abc" not in str(exc.value)


def test_unknown_model_error_explains_the_fix():
    import anthropic

    llm = AzureFoundryLLM(settings(azure_ai_foundry_deployment_name="gpt-4.1-mini"))

    def create(**kw):
        err = _status_error(anthropic.BadRequestError, 400, "Unknown model: gpt-4.1-mini")
        err.body = {"error": {"code": "unknown_model", "message": "Unknown model"}}
        raise err

    llm._client.messages.create = create
    with pytest.raises(LLMError, match="Claude Sonnet deployment"):
        llm.complete_structured("t", "s", "u", Out)


def test_missing_deployment_error_names_the_setting():
    import anthropic

    llm = AzureFoundryLLM(settings())

    def create(**kw):
        raise _status_error(anthropic.NotFoundError, 404, "DeploymentNotFound")

    llm._client.messages.create = create
    with pytest.raises(LLMError, match="AZURE_AI_FOUNDRY_DEPLOYMENT_NAME"):
        llm.complete_structured("t", "s", "u", Out)
