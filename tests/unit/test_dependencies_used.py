"""Every declared dependency must actually be used."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# distribution name -> how it is used
PYTHON_IMPORT_NAMES = {
    "fastapi": "fastapi", "pydantic": "pydantic", "pydantic-settings": "pydantic_settings", "langgraph": "langgraph",
    "anthropic": "anthropic", "supabase": "supabase", "httpx": "httpx",
}
RUNTIME_ONLY = {"uvicorn": "backend/Dockerfile"}  # started as a server process, never imported


def _python_source() -> str:
    return "\n".join(p.read_text() for d in ("agent", "backend") for p in (ROOT / d).rglob("*.py"))


def test_every_requirement_is_imported_or_run():
    names = [re.split(r"[<>=\[!~ ]", line.strip(), maxsplit=1)[0].lower() for line in (ROOT / "requirements.txt").read_text().splitlines()
             if line.strip() and not line.startswith("#")]
    source = _python_source()
    for name in names:
        if name in RUNTIME_ONLY:
            assert name in (ROOT / RUNTIME_ONLY[name]).read_text()
        else:
            module = PYTHON_IMPORT_NAMES[name]
            assert re.search(rf"^\s*(?:from|import)\s+{module}\b", source, re.M), f"{name} is listed but never imported"


def test_dev_requirements_only_add_test_tools():
    lines = [l.strip() for l in (ROOT / "requirements-dev.txt").read_text().splitlines() if l.strip()]
    assert lines[0] == "-r requirements.txt" and [re.split(r"[<>=]", l)[0] for l in lines[1:]] == ["pytest"]


def test_every_frontend_dependency_is_used():
    pkg = json.loads((ROOT / "frontend" / "package.json").read_text())
    used_text = "\n".join(
        p.read_text() for d in ("app", "components", "lib") for p in (ROOT / "frontend" / d).rglob("*") if p.suffix in {".ts", ".tsx", ".css"}
    ) + "\n".join(p.read_text() for p in (ROOT / "frontend").glob("*.mjs")) + (ROOT / "frontend/next.config.ts").read_text()
    tooling = {  # consumed by the build/lint toolchain rather than imported from source
        "tailwindcss": "@import \"tailwindcss\"", "@tailwindcss/postcss": "postcss.config.mjs", "typescript": "tsconfig.json",
        "eslint": "eslint.config.mjs", "eslint-config-next": "eslint.config.mjs", "@types/node": None, "@types/react": None, "@types/react-dom": None,
        "react-dom": None,  # required peer of next, loaded by the framework
    }
    for name in {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}:
        if name in tooling:
            hint = tooling[name]
            if hint:
                haystack = used_text if hint.startswith("@import") else (ROOT / "frontend" / hint).read_text() if (ROOT / "frontend" / hint).exists() else ""
                assert hint.split("/")[0].strip('"') in haystack or hint in haystack or name.split("/")[-1] in haystack, name
            continue
        assert re.search(rf"""["']{re.escape(name)}(?:/[^"']*)?["']""", used_text), f"frontend dependency {name} is never imported"
