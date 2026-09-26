"""Tests are hermetic: they never read real credentials from .env or the shell.

Set YATRA_LIVE=1 to run the live tests against the configured Azure AI Foundry deployment.
"""
import os

if os.environ.get("YATRA_LIVE") != "1":
    for _name in (
        "AZURE_AI_FOUNDRY_ENDPOINT", "AZURE_AI_FOUNDRY_API_KEY", "AZURE_AI_FOUNDRY_DEPLOYMENT_NAME",
        "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
    ):
        os.environ[_name] = ""
    os.environ["CORS_ORIGINS"] = "http://localhost:3000"
