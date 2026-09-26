# Prompt Evaluation Scoring Rubric & Guide

This document defines the scoring rubric across all three parameters for evaluating written prompts.
Total Marks Available: **250 Marks**.

---

## 1. Prompt Clarity (0 – 100 Marks)

| Sub-Criterion | Max Marks | Exceptional (90-100%) | Moderate (60-89%) | Poor (<60%) |
|---|---|---|---|---|
| **Role & Persona Definition** | 20 | Role, expertise level, goal, and context are explicitly defined and tailored. | Role is stated but generic (e.g. "You are an assistant"). | No role or identity specified. |
| **Task Specificity & Negative Constraints** | 25 | Crystal-clear task definition with explicit negative rules ("Never do X"). | Clear primary task, but negative constraints are absent. | Vague or underspecified task; open to misinterpretation. |
| **Instruction Structure & Delimiters** | 20 | Uses clean headings, XML tags (`<instructions>`, `<context>`), or markdown sections. | Uses some bullet points, but instructions blend into context. | Unstructured wall of plain text with poor readability. |
| **Tone, Style & Audience** | 15 | Explicitly dictates vocabulary level, tone, format, and perspective. | Mentions tone loosely (e.g., "be friendly"). | No style or tone guidance provided. |
| **Unambiguous Language** | 20 | Direct, imperative verbs. No contradictory directives or fuzzy language. | Minor ambiguity or slightly vague wording in secondary instructions. | Contradictory instructions or vague directives ("do a good job"). |

---

## 2. Output Quality & Schema Compliance (0 – 100 Marks)

| Sub-Criterion | Max Marks | Exceptional (90-100%) | Moderate (60-89%) | Poor (<60%) |
|---|---|---|---|---|
| **Output Format & Schema Enforcement** | 30 | Exact output schema provided (JSON keys, markdown template, character limits). | Format requested loosely (e.g. "return JSON"), but schema missing. | No output structure specified; model chooses arbitrarily. |
| **Few-Shot Examples & In-Context Demos** | 25 | Curated input/output exemplars covering happy path and edge cases. | One basic example with minimal nuance. | Zero examples provided. |
| **Edge Cases & Fallbacks** | 25 | Explicit handling for empty, malformed, contradictory, or unanswerable inputs. | Mentions fallback loosely (e.g. "if unsure, ask"). | No guidance on error states; risk of hallucinated fallback. |
| **Factuality & Hallucination Prevention** | 20 | Strict grounding constraint (e.g. "answer only using context; state if missing"). | Generic instruction to be accurate. | No factual constraints or hallucination guardrails. |

---

## 3. Efficiency & Token Economy (0 – 50 Marks)

| Sub-Criterion | Max Marks | Exceptional (90-100%) | Moderate (60-89%) | Poor (<60%) |
|---|---|---|---|---|
| **Conciseness & Fluff Elimination** | 15 | Zero pleasantries ("please", "kindly"), zero redundant rules, crisp language. | Some conversational filler or repeated rules. | Heavy fluff, wordiness, and redundant instructions throughout. |
| **Token Economy & Context Footprint** | 15 | Maximizes impact per token; compact instructions that leave room for context. | Slightly verbose, could be trimmed by 20–30% without loss. | Excessively bloated instructions wasting context window. |
| **Dynamic Parameterization** | 10 | Clear variable placeholders (`{query}`, `<context>`) separated from fixed prompt. | Inconsistent variable placeholders. | Variables embedded confusingly inside text. |
| **Signal-to-Noise Ratio** | 10 | High information density; instructions are easy for the model attention heads to weight. | Moderate density; key constraints buried in lengthy paragraphs. | Low density; critical rules get lost in irrelevant text. |

---

## Scoring Summary Table

| Parameter | Maximum Marks | Passing Benchmark | Production Standard |
|---|---|---|---|
| **Prompt Clarity** | 100 | 60 | 85+ |
| **Output Quality** | 100 | 60 | 85+ |
| **Efficiency** | 50 | 30 | 42+ |
| **Total Score** | **250** | **150** | **212+** |
