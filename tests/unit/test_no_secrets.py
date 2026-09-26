"""Guards against committing credentials: tracked files must not contain key-like strings,
and .env.example must only hold placeholders."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLACEHOLDER_HINTS = ("your-", "replace-with", "claude-sonnet", "localhost", "127.0.0.1", "my-", "30", "4", "20", "http://")
PATTERNS = {
    "JWT": re.compile(r"eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    "Supabase secret key": re.compile(r"\bsb_secret_[A-Za-z0-9_-]{10,}"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    "long hex/base64 assignment to a KEY/SECRET/TOKEN": re.compile(r"(?i)\b\w*(?:api_key|secret|token|password)\w*\s*[=:]\s*['\"]?(?![0-9a-fA-F]{8}-[0-9a-fA-F]{4}-)[A-Za-z0-9+/_-]{32,}['\"]?"),  # GUIDs (role ids) are not secrets
}


def tracked_files() -> list[Path]:
    if not shutil.which("git") or not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    return [ROOT / f for f in out if (ROOT / f).is_file() and not f.endswith(("package-lock.json", ".png", ".ico", ".json.map"))]


def test_no_credentials_in_tracked_files():
    problems = []
    for path in tracked_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                problems.append(f"{path.relative_to(ROOT)}: looks like a {name}")
    assert not problems, "\n".join(problems)


def test_env_is_ignored_and_example_holds_only_placeholders():
    assert ".env" in (ROOT / ".gitignore").read_text().splitlines()
    tracked = {p.relative_to(ROOT).as_posix() for p in tracked_files()}
    assert ".env" not in tracked and ".env.example" in tracked
    for line in (ROOT / ".env.example").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            key, _, value = line.partition("=")
            assert any(h in value for h in PLACEHOLDER_HINTS) or value.isdigit(), f"{key} does not look like a placeholder"
            assert len(value) < 90 and not PATTERNS["JWT"].search(value), key
