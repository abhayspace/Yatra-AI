"""Exception types shared across the agent package."""


class ToolError(Exception):
    """A tool refused its input or could not complete; safe to show to the user."""


class LLMError(RuntimeError):
    """The Azure AI Foundry call failed or returned something unusable."""


class GraphLimitError(RuntimeError):
    """The explicit step cap for a graph run was exceeded."""
