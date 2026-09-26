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
    front = ROOT / "frontend"
    pkg = json.loads((front / "package.json").read_text())
    source = "\n".join(
        p.read_text() for d in ("app", "components", "lib") for p in (front / d).rglob("*") if p.suffix in {".ts", ".tsx", ".css"}
    )
    # consumed by the build/lint toolchain (or loaded by the framework) instead of being imported from source
    toolchain = {
        "tailwindcss": lambda: '@import "tailwindcss"' in (front / "app/globals.css").read_text(),
        "@tailwindcss/postcss": lambda: "@tailwindcss/postcss" in (front / "postcss.config.mjs").read_text(),
        "typescript": lambda: (front / "tsconfig.json").exists(),
        "eslint": lambda: (front / "eslint.config.mjs").exists(),
        "eslint-config-next": lambda: "eslint-config-next" in (front / "eslint.config.mjs").read_text(),
        "@types/node": lambda: (front / "tsconfig.json").exists(),
        "@types/react": lambda: (front / "tsconfig.json").exists(),
        "@types/react-dom": lambda: (front / "tsconfig.json").exists(),
        "react-dom": lambda: "next" in pkg["dependencies"],  # required peer of next
    }
    for name in {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}:
        if name in toolchain:
            assert toolchain[name](), f"{name} is declared but its tool is not configured"
        else:
            assert re.search(rf"""["']{re.escape(name)}(?:/[^"']*)?["']""", source), f"frontend dependency {name} is never imported"
