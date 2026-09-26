---
name: prompt-eval
description: Evaluates any written prompt or prompt template against 3 core parameters (Prompt Clarity /100, Output Quality /100, Efficiency /50 - 250 marks total), generates a comprehensive evaluation report in prompt_eval.md, provides an optimized prompt refactor, commits to Git, and reports completion.
---

# Prompt Evaluation Skill (`prompt-eval`)

This skill evaluates any prompt, prompt template, system instruction, or prompt file across three core criteria totaling **250 marks**:
1. **Prompt Clarity** (100 Marks)
2. **Output Quality & Schema Guidance** (100 Marks)
3. **Efficiency & Token Economy** (50 Marks)

The evaluation results, detailed findings, sub-score breakdowns, and an **optimized rewrite** of the prompt are written to `prompt_eval.md`.

---

## 1. Input Prompt Target

The prompt to be evaluated can be provided via:
1. **Direct argument in chat or slash command:**
   ```text
   /prompt-eval "You are a customer support agent. Help the user with their issues politely."
   ```
2. **File path in the repository:**
   ```text
   /prompt-eval path/to/prompt.txt (or prompts.py, system_prompt.md)
   ```
3. **Configured in this skill below:**

```text
[PROMPT_TO_EVALUATE]
```

### Pre-Execution Validation Check
When executed:
1. Check whether a prompt or target file was provided in the user request or replaced in `[PROMPT_TO_EVALUATE]`.
2. If no prompt or file path is provided:
   - Prompt the user in chat:
     > *"Please provide the prompt text or the path to the prompt file you would like to evaluate."*
   - Await user input before proceeding.
3. If provided, extract the prompt text and begin evaluation.

---

## 2. Evaluation Parameters & Scoring System

The evaluation is scored out of **250 total marks**:

| # | Parameter | Maximum Marks | Description |
|---|---|---|---|
| 1 | **Prompt Clarity** | 100 | Specificity, role definition, boundary conditions, formatting delimiters, lack of ambiguity. |
| 2 | **Output Quality** | 100 | Format/schema enforcement, few-shot examples, edge case handling, hallucination prevention. |
| 3 | **Efficiency** | 50 | Token economy, fluff elimination, signal-to-noise ratio, parameterization. |
| | **Total Score** | **250** | Sum of all three criteria. |

```text
Total Score = Prompt Clarity (100) + Output Quality (100) + Efficiency (50)
```

---

### Parameter 1: Prompt Clarity (0 – 100 Marks)

Measures how clear, unambiguous, structured, and well-bounded the prompt instructions are.

- **Role & Persona Definition (20 pts):**
  - Is the agent's identity, expertise, perspective, and core objective clearly articulated?
- **Task Specificity & Negative Constraints (25 pts):**
  - Are specific tasks clearly defined?
  - Are explicit negative constraints present ("what NOT to do", out-of-scope boundaries)?
- **Instruction Structure & Delimiters (20 pts):**
  - Does the prompt use clear structural separation (Markdown headings, XML tags like `<context>`, `<rules>`, `<instructions>`, bullet points)?
  - Are instruction blocks cleanly distinguished from dynamic data slots?
- **Tone, Style & Target Audience (15 pts):**
  - Does it specify the desired tone (e.g., professional, concise, empathetic) and target reader level?
- **Unambiguous Language (20 pts):**
  - Is the phrasing direct, deterministic, and free of vague directives (e.g., "be good", "do your best", "handle nicely")?

---

### Parameter 2: Output Quality & Schema Compliance (0 – 100 Marks)

Measures how effectively the prompt steers the model to produce accurate, consistent, and well-structured outputs.

- **Output Format & Schema Enforcement (30 pts):**
  - Are explicit output constraints defined (JSON schema, markdown headings, specific key-value pairs, length/table requirements)?
  - Does it specify strict formatting rules (e.g., "Return only valid JSON without markdown wrapping")?
- **Few-Shot Examples & In-Context Demonstrations (25 pts):**
  - Are realistic input/output examples provided to demonstrate desired formatting, style, and tone?
  - Do examples showcase edge cases and expected failure behaviors?
- **Edge Cases & Fallback Instructions (25 pts):**
  - Does the prompt instruct how to handle missing data, ambiguous user queries, contradictory inputs, or errors?
  - Does it define graceful refusal criteria for out-of-bounds requests?
- **Factuality & Hallucination Prevention (20 pts):**
  - Are there strict constraints requiring the model to rely only on provided facts and avoid speculation?
  - Does it instruct the model to state "I do not know" rather than fabricating information?

---

### Parameter 3: Efficiency & Token Economy (0 – 50 Marks)

Measures whether the prompt achieves maximum effectiveness with minimal token waste and clean maintainability.

- **Conciseness & Fluff Elimination (15 pts):**
  - Are polite filler phrases ("Please", "Kindly", "Thank you"), redundant explanations, and duplicate rules removed?
- **Token Economy & Context Footprint (15 pts):**
  - Is the prompt density high? Does every word contribute to guiding the model's output?
- **Dynamic Parameterization (10 pts):**
  - Are variable injection points clearly delineated (e.g. `{query}`, `{{context}}`, `<user_input>`)?
- **Signal-to-Noise Ratio (10 pts):**
  - Are instructions prioritized logically so critical constraints receive high attention without token waste?

---

## 3. Evaluation Report Generation (`prompt_eval.md`)

All evaluation results must be written to a single Markdown file at the project root named:

```text
prompt_eval.md
```

### Required Report Content:
1. **Overall Score Table:** Breakdown of Prompt Clarity (/100), Output Quality (/100), Efficiency (/50), and Total (/250).
2. **Executive Summary:** High-level summary of prompt strengths and key areas for improvement.
3. **Evaluated Prompt Analysis:** The prompt text evaluated, estimated token count, and structural overview.
4. **Detailed Parameter Breakdown:**
   - Score and specific point allocations per criterion.
   - Identified strengths with concrete quotes.
   - Identified weaknesses, ambiguities, or gaps with line/phrase quotes.
5. **Actionable Recommendations:** Bulleted list of prioritized improvements.
6. **Optimized Prompt Rewrite (Production-Ready):** A fully rewritten, enhanced version of the prompt incorporating all recommendations (structural XML tags, schema definitions, edge case handling, and token optimization).

---

## 4. Git Staging & Commit Protocol

Immediately after `prompt_eval.md` has been generated and verified:
1. Check Git status:
   ```bash
   git add prompt_eval.md
   git commit -m "chore: add prompt evaluation report"
   ```
2. If Git is uninitialized, initialize Git, stage `prompt_eval.md`, and commit.

---

## 5. Chat Output

Upon successful completion and commit, report a brief summary in chat:
- Total score (X / 250) and parameter breakdown.
- Top 2 strengths and top 2 areas to improve.
- Inform the user that the full evaluation and **optimized prompt rewrite** have been written to `prompt_eval.md`.
