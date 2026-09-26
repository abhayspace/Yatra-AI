# Detailed Scoring Rubric & Marking Guide

This document defines the detailed scoring rubrics across all five evaluation parameters for the AI Agent Hackathon Evaluation.
Total Marks Available: **450 Marks**.

---

## 1. Problem Statement Alignment (0 – 100 Marks)

Measures fidelity, completeness, and correctness in solving the defined problem statement.

| Score Band | Classification | Criteria & Expectations |
|---|---|---|
| **90 – 100** | **Exceptional** | Comprehensive implementation covering 100% of primary requirements and major edge cases. The agent workflow exactly maps to user needs, produces correct structured outputs, gracefully recovers from malformed inputs, and has zero critical requirement gaps. |
| **75 – 89** | **Strong** | Covers 80–90% of core requirements. The primary user flow is completely functional and demonstrable. Minor edge cases or secondary requirements may be incomplete or stubbed, but the core objective is unquestionably achieved. |
| **50 – 74** | **Moderate** | Core functionality is partially implemented (~50–70%). Basic happy path functions, but significant requirement gaps exist, such as missing key agent tools, incomplete data processing, or brittle execution paths. |
| **25 – 49** | **Deficient** | Major requirements are unfulfilled (<50%). High discrepancy between what was requested and what was built. Only trivial or preliminary components work. |
| **0 – 24** | **Inadequate** | Severe failure to align with the problem statement. The agent does not execute the target task, solves an unrelated problem, or contains only non-functional boilerplate. |

### Assessment Dimension Weights (Guideline for scoring):
- **Core Functional Requirements Coverage:** 35 Marks
- **Workflow & Agent Trajectory Alignment:** 25 Marks
- **Output Correctness & Schema Adherence:** 20 Marks
- **Edge Case & Error Condition Handling:** 10 Marks
- **Domain Constraints Adherence:** 10 Marks

---

## 2. Code Quality (0 – 100 Marks)

Measures software engineering rigor, architectural cleanliness, maintainability, and testing.

| Score Band | Classification | Criteria & Expectations |
|---|---|---|
| **90 – 100** | **Production-Grade** | Clean architecture (domain logic cleanly separated from external infrastructure/LLM calls). Strict typing throughout (Python type hints / TypeScript strict). Clear single-responsibility functions. 12-factor configuration with environment variables. Comprehensive test suite (unit + integration). Structured logging with correlation IDs. Zero hardcoded secrets/magic numbers. |
| **75 – 89** | **Clean & Robust** | Well-structured codebase with clear modules and good readability. Proper error handling across external calls. Solid test coverage for core components. Good configuration management. Minor code duplication or minor type annotation gaps. |
| **50 – 74** | **Prototype Quality** | Functional code with working components, but lacks architectural separation. Sparse tests (or only placeholder tests). Inconsistent error handling (e.g. broad `except Exception:` with print statements). Some hardcoded configurations or magic strings. |
| **25 – 49** | **Fragile** | Monolithic or chaotic design. Lack of modularity, missing error handling, unhandled promise rejections / uncaught exceptions. Zero tests. Unpinned dependencies, duplicate code blocks. |
| **0 – 24** | **Spaghetti / Broken** | Syntax errors, broken imports, missing dependencies preventing startup, completely unmaintainable spaghetti code. |

### Assessment Dimension Weights:
- **Architecture, Modularity & Separation of Concerns:** 25 Marks
- **Readability, Style & Type Safety:** 15 Marks
- **Error Handling, Circuit Breaking & Resilience:** 20 Marks
- **Testing Practices & Coverage:** 15 Marks
- **Configuration & Dependency Management:** 15 Marks
- **Logging, Observability & Resource Management:** 10 Marks

---

## 3. Innovation (0 – 100 Marks)

Measures meaningful technical innovation, architectural differentiation, and practical problem-solving sophistication.

> **Important Rule:** Do NOT award marks solely for stacking multiple libraries or frameworks. Innovation must be actually implemented, functional, technically sound, and clearly useful.

| Score Band | Classification | Criteria & Expectations |
|---|---|---|
| **90 – 100** | **Groundbreaking** | Novel agent architecture (e.g., dynamic multi-agent collaboration with specialized roles, self-reflection and automatic recovery loops, novel memory consolidation). Deep technical differentiation from standard tutorials or boilerplate wrappers. Demonstrably delivers superior performance, speed, or accuracy. |
| **75 – 89** | **Innovative** | Thoughtful technical design that clearly goes beyond basic LLM calls. Advanced tool orchestration, custom state machines (LangGraph / custom DAG), dynamic context routing, or sophisticated hybrid RAG pipelines with re-ranking. |
| **50 – 74** | **Moderate** | Standard agent patterns (e.g., standard ReAct loop or out-of-the-box framework tutorial). Uses tool calling, but with standard schemas and minimal adaptation. Some custom logic, but mostly relies on default library behavior. |
| **25 – 49** | **Minimal** | Basic LLM API wrapper with a static system prompt. Trivial or non-agentic tool usage (e.g., hardcoded tool calls without dynamic LLM selection). |
| **0 – 24** | **Zero Innovation** | Generic prompt copied from boilerplate with no agentic capabilities or technical differentiation. |

### Assessment Dimension Weights:
- **Agent Architecture & Multi-Agent / Orchestration Novelty:** 30 Marks
- **Intelligent Tooling, MCP & Protocol Integrations:** 25 Marks
- **Context, Memory & State Innovations:** 20 Marks
- **Differentiation from Standard Boilerplate / LLM Wrappers:** 15 Marks
- **Practical Utility & Elegance of Solution:** 10 Marks

---

## 4. Security (0 – 100 Marks)

Measures resilience against LLM-specific vulnerabilities, safe tool execution, credential management, and application security.

| Score Band | Classification | Criteria & Expectations |
|---|---|---|
| **90 – 100** | **Hardened** | Multi-layered defense: strict instruction/data separation with delimiters, indirect prompt injection guards on all retrieved/external content, strict least-privilege tool execution with sandboxing, zero hardcoded credentials, safe environment configuration, recursion limits on agent loops, input sanitization and output validation. |
| **75 – 89** | **Secure** | Solid security posture: no hardcoded secrets, environment variable configuration, good input validation, safe command execution. Minor gaps in indirect prompt injection defenses or missing human-in-the-loop controls for high-impact actions. |
| **50 – 74** | **Moderate Risk** | Basic security hygiene observed (no obvious public API keys), but significant agentic vulnerabilities exist: no defenses against indirect prompt injection in RAG context, missing recursion limits on agent loops (risk of infinite token drainage), or unsanitized tool inputs. |
| **25 – 49** | **High Risk** | Dangerous patterns present: hardcoded API keys or database passwords, unsafe code execution (`eval()`, `exec()`, `shell=True` on raw user inputs), excessive agency allowing unconstrained file system or network writes. |
| **0 – 24** | **Critical Vulnerability** | Severe security failures: publicly exposed production credentials, active remote code execution (RCE) vulnerabilities, arbitrary untrusted code execution without validation. |

### Assessment Dimension Weights:
- **Prompt Injection Defenses (Direct & Indirect):** 25 Marks
- **Tool Execution Security & Sandboxing (Least Privilege, No Unsafe Eval):** 25 Marks
- **Secrets, API Keys & Credential Management (No Hardcoding, Redaction):** 20 Marks
- **RAG & Data Isolation Security (Access Control, Ingestion Safety):** 15 Marks
- **Application Security & Agentic Loop / DoS Protection:** 15 Marks

---

## 5. Grounding and Evals (0 – 50.0 Marks Total)

> **STRICT MAXIMUM: 50.0 MARKS TOTAL.**
> Split into two subcategories of 25 marks each:
> - **Grounding:** 0.0 – 25.0 Marks
> - **Evals:** 0.0 – 25.0 Marks

### 5.1 Grounding (0.0 – 25.0 Marks)
Measures factual grounding, context fidelity, source attribution, and hallucination prevention.

| Points | Criteria |
|---|---|
| **5.0 pts** | **Knowledge Source Reliability & Ingestion:** Uses authoritative, reliable data sources with clean parsing and preprocessing. |
| **5.0 pts** | **Retrieval Relevance & Precision:** High precision retrieval, context filtering, minimal irrelevancy or noise in prompt context. |
| **5.0 pts** | **Citation & Source Attribution:** Generates verifiable citations, references source documents, and maintains provenance in responses. |
| **5.0 pts** | **Hallucination Mitigation & Faithfulness:** Prompting and constraints enforce strict adherence to ground truth; explicitly refrains from answering when context is insufficient. |
| **5.0 pts** | **Missing & Conflicting Data Handling:** Robust fallback handling when source documents conflict or data is unavailable. |

*Note on Grounding without RAG:* If the problem statement does not require external retrieval (e.g. pure code generation or mathematical logic), evaluate grounding based on domain constraints, data validation, and factual adherence.

### 5.2 Evals (0.0 – 25.0 Marks)
Measures the sophistication, coverage, and reproducibility of the agent evaluation suite.

| Points | Criteria |
|---|---|
| **5.0 pts** | **Deterministic & Unit Evaluations:** Assertions verifying tool calling schemas, state machine transitions, and output JSON schemas. |
| **5.0 pts** | **LLM-Based / Semantic Metrics:** Implemented evaluations assessing faithfulness, answer relevance, context recall, or task goal completion. |
| **5.0 pts** | **Agent Trajectory & Step Evaluation:** Evaluating agent decision sequences, tool call arguments, recovery from errors, and execution paths. |
| **5.0 pts** | **Test Datasets & Adversarial Cases:** A curated golden evaluation set, edge cases, failure cases, and adversarial prompt tests. |
| **5.0 pts** | **Reproducibility & Automation:** An executable eval script (e.g., `python run_evals.py` or `npm run eval`) with structured metric logging. |

*Note on Eval Frameworks:* Merely having `ragas`, `deepeval`, or `truera` in `requirements.txt` receives 0 marks if no test scripts actually run them. Marks are awarded solely for implemented, working evaluations.
