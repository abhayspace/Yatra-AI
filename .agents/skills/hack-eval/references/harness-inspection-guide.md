# AI Agent Harness Inspection Guide

This guide provides systematic commands and inspection patterns for analyzing an AI agent codebase and its complete harness.

---

## 1. Initial Project Reconnaissance

### Step 1: Detect Project Type & Dependencies
Identify languages, frameworks, and architecture:
- **Python:** Inspect `pyproject.toml`, `requirements.txt`, `Pipfile`, `setup.py`, `conda.yaml`.
  - Look for agent libraries: `langchain`, `langgraph`, `crewai`, `autogen`, `llamaindex`, `google-genai`, `anthropic`, `openai`, `pydantic-ai`, `smolagents`.
  - Look for eval libraries: `ragas`, `deepeval`, `truera`, `pytest`, `pytest-asyncio`.
- **TypeScript / Node.js:** Inspect `package.json`, `pnpm-lock.yaml`, `yarn.lock`.
  - Look for: `@langchain/core`, `langgraph`, `ai` (Vercel AI SDK), `@modelcontextprotocol/sdk`.
- **Configuration & Environment:**
  - Check `.env.example`, `config.yaml`, `settings.py`, `docker-compose.yml`.

### Step 2: Identify Entrypoints & Agent Loops
Find where the agent starts execution:
- Common entrypoints: `main.py`, `app.py`, `server.py`, `src/index.ts`, `src/main.ts`, `cli.py`, `agent.py`.
- Search for agent instantiation patterns:
  - `Agent(`, `create_react_agent(`, `StateGraph(`, `Workflow(`, `ChatOpenAI(`, `genai.Client(`.

---

## 2. Deep Dive by Component

### Component A: Agent Architecture & State Machine
1. Check how agent state is maintained:
   - Is it a linear ReAct loop, a directed acyclic graph (DAG), a state machine (LangGraph), or multi-agent supervisor?
   - How is conversation history persisted across turns? (In-memory, SQLite, Redis, Postgres).
2. Check loop boundaries:
   - Is there a `max_iterations`, `recursion_limit`, or timeout on the agent loop?

### Component B: Prompts & LLM Configuration
1. Inspect prompt templates:
   - System prompts: Check for role instructions, constraints, output schemas, few-shot examples.
   - User prompts: Check how dynamic inputs are formatted and whether delimiters/tags are used.
2. Inspect model parameters:
   - Temperature, top_p, max_tokens, presence_penalty.
   - Structured output enforcement (e.g. `response_format={"type": "json_object"}` or `.with_structured_output(Schema)`).

### Component C: Tools & Model Context Protocol (MCP)
1. Inspect tool declarations:
   - Tool decorators (`@tool`, `@function`, schema definitions).
   - Tool input validation: Are parameter types and ranges strictly validated?
   - Tool execution safety: Does any tool execute shell commands, file modifications, or network calls?
2. Inspect MCP integrations:
   - Look for `mcp_config.json`, client connections, SSE transports, or stdio transports.
   - Check authorization and scoping on MCP tools.

### Component D: RAG & Grounding Pipelines (if present)
1. Ingestion:
   - How are source documents loaded, parsed, cleaned, and chunked?
   - Chunk size, chunk overlap, splitting strategy (character, recursive, semantic).
2. Retrieval:
   - Vector database: Chroma, Pinecone, Qdrant, Weaviate, FAISS, PGVector.
   - Retrieval strategy: Dense embeddings, hybrid search (BM25 + vector), re-ranking (Cohere, Cross-Encoder).
3. Grounding & Attribution:
   - Are source citations passed to the prompt and required in the final output?
   - Is there a check for context relevance before generation?

### Component E: Evaluation & Testing Harness
1. Locate tests and evals:
   - Look in `tests/`, `eval/`, `evals/`, `benchmarks/`, `evaluation/`.
2. Determine eval execution:
   - Are evals deterministic assertions, LLM-as-a-judge evaluations, or synthetic datasets?
   - Check if evaluation scripts actually run and produce output metrics.
   - Note: Do NOT assume evals exist without verifying working test code!

### Component F: Security Controls & Secrets
1. Scan for hardcoded credentials:
   - Search for API key patterns (`sk-`, `key=`, `token=`, `api_key=`).
2. Scan for dangerous functions:
   - Search for `eval(`, `exec(`, `os.system(`, `subprocess.Popen(..., shell=True)`.
3. Check error disclosure:
   - Look for global exception handlers; ensure raw traceback is logged rather than returned to client.

---

## 3. Evidence Documentation Format

When recording findings in `hack_evaluation.md`, use exact citations:
- Format: `[src/agent/orchestrator.py:L45-L68]`
- State the verification status:
  - `[IMPLEMENTED]`
  - `[PARTIALLY IMPLEMENTED]`
  - `[PLANNED / STUB]`
  - `[CLAIMED BUT UNVERIFIED]`
