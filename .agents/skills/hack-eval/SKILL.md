---
name: hack-eval
description: Evaluates an AI agent's complete implementation and harness against a defined hackathon problem statement across 5 core parameters (Problem Statement Alignment, Code Quality, Innovation, Security, Grounding and Evals - 450 marks total), generates hack_evaluation.md, commits it to Git with a specific commit message, and outputs 'File created'.
---

# AI Agent Hackathon Evaluation Skill

This skill governs the end-to-end evaluation of an AI agent's implementation and harness against a hackathon problem statement. It inspects the codebase objectively, gathers concrete evidence, scores 5 defined parameters totaling **450 marks**, generates a comprehensive report in `hack_evaluation.md`, commits the report to Git, and returns a strict chat response.

---

## 1. Problem Statement Configuration

```text
# 🧳 Hackathon Challenge: Build an AI Travel Agent

### Problem Statement

Build an **AI Travel Agent** that can understand a user's travel preferences and constraints, use relevant tools/data, and create a **personalized, practical, and adaptive travel plan**.

The agent should be able to handle requests such as:

> “Plan a 5-day trip from Delhi for 2 people under ₹50K, focused on nature and food, with a relaxed itinerary.”

**Your agent should demonstrate:**
Intent & constraint understanding • Tool/API usage • Planning & reasoning • Personalization • Itinerary generation • Re-planning when requirements change • Safe handling of untrusted inputs

### 🏆 Judging Criteria — 450 Marks

| Criteria                        |         Marks |
| ------------------------------- | ------------: |
| **Problem Statement Alignment** | **100 marks** |
| **Code Quality**                | **100 marks** |
| **Innovation**                  | **100 marks** |
| **Security**                    | **100 marks** |
| **Grounding & Evals**           |  **50 marks** |
| **Total**                       | **450 marks** |

**Grounding & Evals:** Are recommendations grounded in reliable sources, and does the team have meaningful tests/evaluations demonstrating agent quality and reliability?

**💡 Judge on outcomes, not complexity:** More agents, tools, or frameworks ≠ better solution.
```

### Pre-Execution Problem Statement Validation (CRITICAL FIRST STEP)

When this skill is executed, the evaluator agent **MUST** perform this check before any other action:

1. **Inspect the Problem Statement Placeholder Above:**
   - Check whether `[PROBLEM_STATEMENT]` has been replaced with a concrete, meaningful problem statement.
2. **If NOT Replaced (or contains only placeholder/whitespace/generic text):**
   - **HALT IMMEDIATELY.**
   - Do **NOT** inspect repository files.
   - Do **NOT** run tests or build commands.
   - Do **NOT** generate `hack_evaluation.md`.
   - Do **NOT** initialize Git or make any Git commit.
   - Respond in chat asking the user for the problem statement:
     > "Please provide the hackathon problem statement to begin the AI agent evaluation."
   - Await user response. Do not proceed until the problem statement is provided.
3. **If Replaced (Meaningful Problem Statement Present):**
   - Use the provided problem statement as the **sole authoritative reference** for evaluating Problem Statement Alignment.
   - **Do NOT invent missing requirements.**
   - **Do NOT infer an alternative problem statement.**
   - Evaluate strictly what was requested versus what was built.

---

## 2. Read-Only Evaluation Restriction (STRICT GUARDRAIL)

The evaluation MUST be strictly non-destructive. The evaluator agent acts as an impartial auditor, NOT a developer on the target project.

### Permitted Actions
- Reading and inspecting repository files across the entire harness.
- Running safe, non-destructive, existing tests (e.g., `pytest`, `npm test`) if practical and existing.
- Checking Git history and status (`git status`, `git log`).
- Reviewing existing logs, traces, evaluation outputs, or benchmarks.
- Creating and modifying **ONLY** the evaluation report: `hack_evaluation.md`.

### Prohibited Actions
- **DO NOT** modify any source code files.
- **DO NOT** refactor code or fix discovered bugs.
- **DO NOT** modify existing test files.
- **DO NOT** modify configuration files, environment files, or package manifests.
- **DO NOT** install new global or project dependencies that alter the repository.
- **DO NOT** create evaluation scripts, test harnesses, or scratch files inside the evaluated repository.
- **DO NOT** modify documentation or README files.
- **DO NOT** create any file other than `hack_evaluation.md`.

> **STRICT RULE:** Only `hack_evaluation.md` may be created or modified during the evaluation.

---

## 3. Evaluation Parameters & Scoring System

The evaluation is scored out of **450 total marks**. The primary score must **NEVER** be normalized to 100.

| # | Parameter | Maximum Score | Scoring Range |
|---|---|---|---|
| 1 | Problem Statement Alignment | 100 | 0 – 100 |
| 2 | Code Quality | 100 | 0 – 100 |
| 3 | Innovation | 100 | 0 – 100 |
| 4 | Security | 100 | 0 – 100 |
| 5 | Grounding and Evals | 50 | 0.0 – 50.0 |
| | **Total Score** | **450** | **0.0 – 450.0** |

```text
Total Score = Problem Statement Alignment + Code Quality + Innovation + Security + Grounding and Evals
```

All arithmetic in the final report must be mathematically consistent.

---

### Parameter 1: Problem Statement Alignment (0 – 100 Marks)

Evaluate how comprehensively and accurately the AI agent implementation solves the given problem statement.

#### Key Assessment Criteria
- **Understanding of Requirements:** Comprehension of core user needs, domain constraints, and input/output contracts.
- **Functional Completeness:** Proportion of requested features actually implemented and working.
- **Coverage of Core Use Cases:** End-to-end execution paths addressing the primary user scenarios.
- **Agent Behavior & Workflow Alignment:** Agent decision-making, planning, and task execution matches expected workflows.
- **Output Correctness:** Quality, accuracy, schema compliance, and format adherence of agent outputs.
- **Edge Case Handling:** Resiliency when handling unexpected, empty, malformed, or boundary inputs.
- **Alignment vs Gaps:** Explicitly document gaps between the problem statement requirements and the codebase.

#### Scoring Brackets
- **90–100 (Exceptional):** Full functional completeness; handles all core and edge cases; workflows perfectly mirror requirements.
- **75–89 (Strong):** Covers primary use cases thoroughly; minor edge case gaps or minor feature omissions.
- **50–74 (Moderate):** Core workflow partially implemented; key requirements missing or partially stubbed.
- **25–49 (Deficient):** Major disconnect with problem statement; core functionality non-operational or mismatched.
- **0–24 (Inadequate):** Little to no alignment; does not solve the stated problem.

---

### Parameter 2: Code Quality (0 – 100 Marks)

Evaluate the quality, architecture, robustness, and maintainability of the complete codebase and agent harness. Evaluate **actual code**, not claimed capabilities.

#### Key Assessment Criteria
- **Architecture & Modularity:** Clean separation of concerns, domain vs infrastructure separation, modular agent components.
- **Readability & Maintainability:** Google style guide adherence, clean naming, single-responsibility functions, type safety (type hints, TypeScript strict).
- **Error Handling & Resilience:** Explicit exception handling, graceful degradation, circuit breakers, retry policies with backoff/jitter.
- **Input Validation & Sanitization:** Strict schema validation (Pydantic, Zod), defensive parsing of untrusted inputs.
- **Configuration & Secrets Management:** 12-factor config, `.env.example`, environment variables, no hardcoded configuration.
- **Dependency Management:** Clean package manifests (`pyproject.toml`, `package.json`), pinned versions, no unnecessary dependencies.
- **Testing Practices:** Unit tests, integration tests, mock strategies for LLMs/tools, test coverage on core domain logic.
- **Logging & Observability:** Structured logging, correlation IDs, agent trajectory logging, tracing (OpenTelemetry, LangSmith).
- **Code Duplication & Hygiene:** DRY compliance, dead code elimination, absence of hardcoded magic values.
- **Resource Management:** Connection pooling, async I/O for network calls, streaming responses, timeout handling on external calls.
- **Production Readiness:** Health endpoints, containerization (Dockerfile), readiness for deployment.

#### Scoring Brackets
- **90–100 (Production-Grade):** Exemplary architecture, strict typing, comprehensive error handling, robust tests, zero hardcoding.
- **75–89 (Clean & Robust):** Well-structured, good separation of concerns, solid error handling, good test coverage.
- **50–74 (Acceptable / Prototype):** Functional but contains architectural flaws, sparse tests, occasional hardcoding or loose typing.
- **25–49 (Fragile):** Poor structure, monolithic design, missing error handling, no tests, widespread magic values.
- **0–24 (Broken / Spaghetti):** Unmaintainable, unhandled exceptions, syntax/import errors, anti-patterns throughout.

---

### Parameter 3: Innovation (0 – 100 Marks)

Evaluate meaningful technical innovation, architectural sophistication, and practical differentiation beyond a generic LLM wrapper.

> **CRITICAL RULE:** Do NOT award marks solely for using multiple frameworks or complex architecture. Innovation must be **implemented**, **relevant**, **technically meaningful**, and **demonstrably useful**.

#### Key Assessment Criteria
- **Novel Agent Architecture:** Hierarchical multi-agent teams, supervisor-worker graphs, reflection/self-correction loops, dynamic delegation.
- **Creative Orchestration:** State machines (LangGraph, custom DAGs), event-driven execution, dynamic replanning.
- **Advanced LLM Usage:** Structured outputs, schema enforcement, multi-modal integration, dynamic temperature/sampling, task-specific prompt engineering.
- **Tool Calling & Execution:** Autonomous tool selection, composite tool chains, intelligent schema generation, sandbox execution.
- **MCP & Skills Integration:** Integration with Model Context Protocol (MCP) servers, reusable skills, modular tool providers.
- **Memory & Context Strategies:** Hierarchical memory, entity extraction, rolling context summarization, semantic memory search.
- **RAG Improvements:** Hybrid search (dense + sparse/BM25), query rewriting, multi-hop reasoning, re-ranking (Cross-Encoders, Cohere), semantic chunking.
- **Adaptive Behavior:** Dynamic routing based on query complexity, self-healing tool retry on schema mismatch.
- **Differentiation:** Clear technical departure from a standard single-prompt LLM wrapper.

#### Scoring Brackets
- **90–100 (Groundbreaking):** Novel, highly differentiated architecture; advanced self-healing or multi-agent orchestration; deeply practical value.
- **75–89 (Innovative):** Strong technical differentiation; well-crafted memory or multi-agent patterns; clearly transcends basic wrappers.
- **50–74 (Moderate Innovation):** Standard agent patterns (basic ReAct, simple tool-calling); some customization but mostly off-the-shelf.
- **25–49 (Minimal Innovation):** Thin wrapper around standard LLM API; minimal or trivial tool calling; no creative architecture.
- **0–24 (Zero Innovation):** Direct API call with static prompt; zero agentic behavior.

---

### Parameter 4: Security (0 – 100 Marks)

Perform a comprehensive, rigorous security audit of the AI agent and its complete harness.

#### Core Security Dimensions

1. **Prompt Injection & Adversarial Robustness:**
   - Direct prompt injection defenses (delimiters, system instruction reinforcement).
   - Indirect prompt injection defenses (treating retrieved content, tool outputs, and scraped web content as untrusted data).
   - Instruction boundary enforcement (strict separation of system prompt, user prompt, and tool results).
   - Data and instruction separation (XML tags, Markdown framing, structured JSON).

2. **Tool Security & Execution Boundaries:**
   - Tool permissions & least privilege (read-only tools vs destructive tools).
   - Tool input validation (regex checks, path traversal prevention, command injection prevention).
   - Excessive agency mitigation (human-in-the-loop approvals for sensitive actions: payments, deletes, emails).
   - Unsafe code/command execution (`eval()`, `exec()`, `shell=True`, unsanitized subshells).
   - Tool output sanitization before re-injecting into agent context.

3. **Secrets, Credentials & Data Privacy:**
   - Hardcoded secrets check (API keys, tokens, DB credentials, private keys in code or Git history).
   - Environment variable management (use of `.env` without checking into VCS).
   - Sensitive data exposure in logs, error messages, or agent responses.
   - PII masking and data isolation.

4. **RAG & Retrieval Security:**
   - Unauthorized retrieval / multi-tenant data leakage.
   - Unsafe document ingestion (XXE in XML parsers, PDF exploits, SSRF in web scrapers).
   - Data exfiltration risks via prompt injection into RAG context.

5. **Application Security & Agentic Denial-of-Service:**
   - Authentication & authorization on API endpoints (JWT, OAuth, API key validation).
   - Uncontrolled agent loops / recursion limits (preventing infinite LLM calls and token drainage).
   - Resource exhaustion limits (timeouts on external calls, payload size limits).
   - Error disclosure (avoiding stack traces leaking to end users).

#### Security Rules for Evaluator
- **Distinguish confirmed vulnerabilities from potential risks:** Mark as `[CONFIRMED]` only when verified in code; mark speculative issues as `[POTENTIAL]`.
- **Avoid fabricating vulnerabilities:** Only report security flaws backed by specific file and line evidence.
- **NEVER expose discovered secrets in the report:** Redact all API keys and credentials (e.g., `sk-ant-...[REDACTED]`, `AIzaSy...[REDACTED]`).
- **Perform ONLY non-destructive validation:** Never attempt active exploitation.
- **Never modify source code to fix security issues.**

#### Scoring Brackets
- **90–100 (Hardened):** Robust prompt injection boundaries, strict tool sandboxing, zero hardcoded secrets, recursion limits, sanitized inputs.
- **75–89 (Secure):** Good security practices, no exposed secrets, standard input validation, minor gaps in indirect injection hardening.
- **50–74 (Moderate Risk):** Missing indirect injection defenses, loose tool input validation, or missing agent recursion limits.
- **25–49 (High Risk):** Hardcoded credentials, unsafe execution (`eval`/`exec`/shell injection), or excessive autonomous agency.
- **0–24 (Critical Exposure):** Widespread confirmed critical vulnerabilities, publicly exposed secrets, remote code execution vulnerabilities.

---

### Parameter 5: Grounding and Evals (0 – 50.0 Marks Total)

> **CRITICAL SCORING RULE:** This parameter is scored out of **50.0 marks total** (NOT 100).
> It consists of two subcategories:
> - **Grounding:** 0.0 – 25.0 Marks
> - **Evals:** 0.0 – 25.0 Marks
> Total = `Grounding Score + Evals Score` (Maximum: 50.0).

#### 5.1 Grounding (0.0 – 25.0 Marks)
Evaluate how the agent grounds its outputs in authoritative knowledge, avoids hallucination, and maintains factual traceability.

> *Note:* Do not assume RAG is mandatory for every problem. If a problem does not require retrieval, evaluate grounding based on domain constraints, data validation, and factual adherence.

- **Knowledge Source Reliability (5.0 pts):** Authoritative, verified data sources, clean ingestion.
- **Retrieval Relevance & Context Precision (5.0 pts):** Relevant chunk retrieval, minimal context noise, sensible chunking.
- **Citation & Source Attribution (5.0 pts):** Traceable citations, metadata references, clear origin of facts in answers.
- **Hallucination Prevention & Faithfulness (5.0 pts):** Prompts enforcing strict grounding, refusal to answer when facts are absent.
- **Handling Missing/Conflicting Information (5.0 pts):** Graceful fallback when information is unavailable or contradictory.

#### 5.2 Evals (0.0 – 25.0 Marks)
Evaluate the sophistication, coverage, and reproducibility of the evaluation harness used to measure agent performance.

> *Note:* Do not award marks simply because an eval framework (Ragas, DeepEval, etc.) is listed in `requirements.txt`. Evaluate whether it is **meaningfully implemented and executed**.

- **Deterministic & Unit Evaluations (5.0 pts):** Assertions on agent outputs, tool call schemas, state transitions.
- **LLM-as-a-Judge / Semantic Metrics (5.0 pts):** Implemented rubrics for faithfulness, answer relevance, context recall.
- **Agent Trajectory & Tool Call Evals (5.0 pts):** Testing tool calling accuracy, step sequences, recovery from errors.
- **Benchmark / Dataset & Failure-Case Testing (5.0 pts):** Golden evaluation datasets, adversarial test cases, edge case test suites.
- **Eval Automation & Reproducibility (5.0 pts):** Reproducible eval runner script (`run_evals.py` or CI integration), logged metrics.

---

## 4. Complete Harness Inspection Methodology

The evaluator must inspect the complete AI agent harness before scoring. **Evaluate actual code implementation rather than relying on README claims.**

### Components to Inspect

1. **Agent Architecture & Entrypoint:**
   - Entrypoint scripts (`main.py`, `app.py`, `src/index.ts`, `cli.py`).
   - Agent loops, state machines, supervisor/worker graphs.
2. **LLM Configuration & Prompts:**
   - Model providers (OpenAI, Anthropic, Gemini, local models).
   - System prompts, user templates, few-shot examples, JSON schemas.
   - Temperature, top_p, token limits, fallback models.
3. **Tools & Function Calling:**
   - Tool definitions, schemas, arguments, docstrings.
   - Sandboxing, error handling during tool execution.
4. **MCP Integrations & Skills:**
   - Model Context Protocol server configurations (`mcp_config.json`, servers).
   - Reusable agent skills, tools, or runbooks.
5. **Memory & State Management:**
   - State classes, context windows, checkpointing, vector stores, session persistence.
6. **RAG Pipeline (if applicable):**
   - Embeddings, chunking strategies, vector database, similarity metrics, re-ranking.
7. **Testing & Eval Suites:**
   - Test files (`tests/`, `*_test.py`, `*.spec.ts`), evaluation scripts (`eval/`, `benchmarks/`).
   - Recorded evaluation results, benchmark metrics, test logs.
8. **Security Controls:**
   - Injection guards, input sanitizers, auth middlewares, secret masking.
9. **Configuration & Dependencies:**
   - `.env.example`, config loaders, dependency manifests (`requirements.txt`, `pyproject.toml`, `package.json`).
10. **Logging & Observability:**
    - Log formats, tracing integrations (LangSmith, Phoenix, OpenTelemetry).

### Evidence-Based Validation Protocol
For every parameter, the evaluator MUST document:
1. Exact file paths and line ranges inspected.
2. Concrete code snippets or configuration lines as evidence.
3. Actual test/eval outputs if existing tests were run.
4. Clear classification:
   - **[IMPLEMENTED]:** Feature is fully written, functional, and verifiable in code.
   - **[PARTIALLY IMPLEMENTED]:** Feature is started or incomplete, with stubbed methods or partial coverage.
   - **[PLANNED / STUB]:** Placeholder function, empty class, or `pass`/`TODO` comments.
   - **[CLAIMED BUT UNVERIFIED]:** Mentioned in README/docs but absent in actual codebase.

> **PROHIBITION:** The evaluator must NEVER fabricate test results, fake benchmark numbers, or make unsupported claims.

---

## 5. Evaluation Report Generation (`hack_evaluation.md`)

All evaluation results must be written to a single Markdown file at the project root named:

```text
hack_evaluation.md
```

### Report Structural Template

The report **MUST** follow this exact structure:

```markdown
# AI Agent Hackathon Evaluation Report

## 1. Overall Score

| Parameter | Maximum Marks | Awarded Marks | Percentage |
|---|---|---|---|
| Problem Statement Alignment | 100 | [SCORE] | [PCT]% |
| Code Quality | 100 | [SCORE] | [PCT]% |
| Innovation | 100 | [SCORE] | [PCT]% |
| Security | 100 | [SCORE] | [PCT]% |
| Grounding and Evals | 50 | [SCORE] | [PCT]% |
| **Total Score** | **450** | **[TOTAL_SCORE]** | **[TOTAL_PCT]%** |

---

## 2. Executive Summary
- **Overall Assessment:** [Concise 2-3 paragraph summary of the submission]
- **Main Strengths:** [Bullet points of top 3-5 technical achievements]
- **Significant Weaknesses:** [Bullet points of top 3-5 limitations or gaps]
- **Key Technical Observations:** [Observations on architecture, agent loop, tools]
- **Important Security Concerns:** [Summary of security posture and vulnerabilities]
- **Alignment with Problem Statement:** [High-level verdict on requirements coverage]

---

## 3. Detailed Parameter Evaluations

### 3.1 Problem Statement Alignment (Awarded: [SCORE] / 100)
- **Assessment:** [Detailed analysis of alignment against requirements]
- **Evidence:**
  - Files Inspected: `[path/to/file:L10-L50]`
  - Implementation Findings: [Specific code evidence]
- **Strengths:**
  - [Strength 1 with reference]
- **Weaknesses & Gaps:**
  - [Gap 1 with reference]
- **Recommendations:**
  - [Concrete actionable advice]

### 3.2 Code Quality (Awarded: [SCORE] / 100)
- **Assessment:** [Architecture, readability, maintainability, tests]
- **Evidence:**
  - Files Inspected: `[path/to/file:L10-L50]`
  - Implementation Findings: [Specific code evidence]
- **Strengths:**
  - [Strength 1 with reference]
- **Weaknesses & Gaps:**
  - [Gap 1 with reference]
- **Recommendations:**
  - [Concrete actionable advice]

### 3.3 Innovation (Awarded: [SCORE] / 100)
- **Assessment:** [Novelty, orchestration, differentiation from basic wrapper]
- **Evidence:**
  - Files Inspected: `[path/to/file:L10-L50]`
  - Implementation Findings: [Specific code evidence]
- **Strengths:**
  - [Strength 1 with reference]
- **Weaknesses & Gaps:**
  - [Gap 1 with reference]
- **Recommendations:**
  - [Concrete actionable advice]

### 3.4 Security (Awarded: [SCORE] / 100)
- **Assessment:** [Prompt injection, tool boundaries, secrets, RAG, app security]
- **Evidence:**
  - Files Inspected: `[path/to/file:L10-L50]`
  - Findings: [Specific security findings, redacted secrets]
- **Strengths:**
  - [Strength 1 with reference]
- **Weaknesses & Gaps:**
  - [Gap 1 with reference]
- **Recommendations:**
  - [Concrete actionable advice]

### 3.5 Grounding and Evals (Awarded: [TOTAL_50] / 50.0)
- **Subcategory Breakdown:**
  - **Grounding Score:** [SCORE_G] / 25.0
  - **Evals Score:** [SCORE_E] / 25.0
  - **Total Grounding and Evals:** [TOTAL_50] / 50.0
- **Assessment:**
  - Grounding: [Reliability, citations, hallucination guards]
  - Evals: [Deterministic tests, trajectory evals, benchmark datasets]
- **Evidence:**
  - Files Inspected: `[path/to/file:L10-L50]`
  - Implementation Findings: [Specific code evidence]
- **Strengths:**
  - [Strength 1 with reference]
- **Weaknesses & Gaps:**
  - [Gap 1 with reference]
- **Recommendations:**
  - [Concrete actionable advice]

---

## 4. Cross-Cutting Findings
- **Architecture & Modularity:** [System-level architecture observations]
- **Reliability & Resilience:** [Error recovery, fallback mechanisms]
- **Security Posture:** [Holistic security review]
- **Evaluation Maturity:** [Level of automated testing and validation]
- **Maintainability & Extensibility:** [Ease of future feature addition]
- **Reproducibility:** [Clarity of setup instructions and environment reproduction]

---

## 5. Critical Issues & Vulnerabilities

| Issue | Severity (Critical/High/Medium/Low) | Affected Component | Confirmation Status (Confirmed/Potential) | Evidence | Potential Impact |
|---|---|---|---|---|---|
| [Issue Description] | [Severity] | `[file:line]` | [Confirmed/Potential] | [Brief code evidence - REDACT SECRETS] | [Impact] |

---

## 6. Final Summary & Judging Verdict
- **Final Score Breakdown:**
  - Problem Statement Alignment: [SCORE] / 100
  - Code Quality: [SCORE] / 100
  - Innovation: [SCORE] / 100
  - Security: [SCORE] / 100
  - Grounding and Evals: [SCORE] / 50.0
  - **Total Score: [TOTAL] / 450.0**
- **Strongest Aspects:** [Key highlights]
- **Major Gaps:** [Key deficits]
- **Improvement Priorities:** [Top 3 items team should address next]
- **Evaluation Limitations:** [Any environment constraints during evaluation]
```

---

## 6. Git Staging & Immediate Commit Protocol (MANDATORY)

Immediately after `hack_evaluation.md` has been generated and verified, the evaluator agent **MUST** commit it to Git.

### Step-by-Step Git Procedure

1. **Check Git Initialization:**
   - Run `git rev-parse --is-inside-work-tree` or `git status`.
   - **Case A: Git is already initialized:**
     - Run `git status` to see the working directory state.
     - **DO NOT** stage pre-existing modified or untracked files.
     - Stage **ONLY** `hack_evaluation.md`:
       ```bash
       git add hack_evaluation.md
       ```
   - **Case B: Git is NOT initialized:**
     - Check whether a parent repository exists (`git rev-parse --show-toplevel`).
     - If no parent repository exists, initialize Git at the evaluated project root:
       ```bash
       git init
       ```
     - Stage **ONLY** `hack_evaluation.md`:
       ```bash
       git add hack_evaluation.md
       ```
2. **Execute Commit:**
   - Commit with the exact commit message:
     ```bash
     git commit -m "chore: add AI agent hackathon evaluation"
     ```
   - **Do NOT ask the user for confirmation before committing.**
3. **Verify Git Commit:**
   - Run `git log -1 --stat` or `git status` to verify `hack_evaluation.md` was successfully committed.
4. **Git Safety Invariants:**
   - **NEVER** run `git add .` or `git add -A`.
   - **NEVER** stage or commit source code files, dependencies, or user files.
   - **NEVER** commit secrets, `.env` files, or API credentials.
   - **NEVER** run `git reset --hard` or discard existing user work.
   - If a Git commit fails due to an environmental issue (e.g. read-only filesystem, missing git binary), document the failure clearly. Do not falsely claim success.

---

## 7. Chat Output Requirement (EXACT RESPONSE)

After the evaluation report has been generated, verified, and committed to Git, the evaluator agent **MUST** respond in chat with **EXACTLY**:

```text
File created
```

### Strict Output Constraints
- **DO NOT** output the score or summary in chat.
- **DO NOT** provide explanations, findings, or highlights in chat.
- **DO NOT** add conversational filler (e.g., "The evaluation is complete. File created.").
- **EXACT STRING ONLY:** `File created`.
- If the problem statement was missing and requested from the user, output the clarification request instead.
- If report generation or Git commit failed, report the error honestly; do NOT output `File created`.

---

## 8. Evaluator Execution Checklist

Before finishing the evaluation session, verify:
- [ ] Problem statement placeholder was verified (or user was prompted).
- [ ] Entire harness was inspected (architecture, prompts, tools, memory, RAG, evals, security, configs).
- [ ] All 5 parameters scored objectively with evidence.
- [ ] Grounding & Evals scored out of 50.0 (Grounding 25.0 + Evals 25.0).
- [ ] Total score calculated out of 450.0 (NOT normalized to 100).
- [ ] All sensitive secrets redacted in report.
- [ ] No source code or existing project files were modified (read-only restriction obeyed).
- [ ] `hack_evaluation.md` generated at root following the required structure.
- [ ] Git checked/initialized and `hack_evaluation.md` selectively staged and committed.
- [ ] Commit message is exactly `chore: add AI agent hackathon evaluation`.
- [ ] Chat response is strictly `File created`.
