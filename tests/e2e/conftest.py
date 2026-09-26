import httpx
import pytest

from agent.graph import Deps, build_graph
from agent.settings import Settings
from tests.fakes import TODAY, ScriptedLLM, weather_transport


@pytest.fixture
def settings():
    return Settings(_env_file=None)


@pytest.fixture
def make_graph(settings):
    def factory(llm=None, rainy_offsets=None, hot=False, weather_fail=False, settings_override=None):
        transport = weather_transport(rainy_offsets, hot, weather_fail)
        deps = Deps(
            llm=llm or ScriptedLLM(), settings=settings_override or settings,
            http_client=httpx.Client(transport=transport), today=lambda: TODAY,
        )
        graph = build_graph(deps)
        graph.weather_calls = transport.calls  # type: ignore[attr-defined]
        graph.deps = deps  # type: ignore[attr-defined]
        return graph

    return factory
