# Universal Agent Configuration & Custom Commands

This repository defines the **AI Agent Hackathon Evaluator Skill**. All agents operating in this workspace (Antigravity, Claude Code, GitHub Copilot, OpenCode, Cursor, etc.) must follow these instructions.

---

## Slash Commands

### `/hack-eval [problem_statement]` (or `/eval-agent`)

**Intent:** Execute a complete, read-only hackathon evaluation of this project against the given problem statement using the `hack-eval` skill.

**Execution Protocol:**
1. **Extract Problem Statement:**
   - If argument `[problem_statement]` is provided in the slash command (e.g., `/hack-eval Build an AI Travel Agent...`), use it as the ground truth.
   - If no problem statement is provided in the command, check if [.agents/skills/hack-eval/SKILL.md](file:///f:/globalai/eval_skill/.agents/skills/hack-eval/SKILL.md) has had its problem statement configured.
   - If still missing, **HALT** and prompt the user: *"Please provide the hackathon problem statement to begin the AI agent evaluation."*
2. **Execute Evaluation Skill:**
   - Refer to [.agents/skills/hack-eval/SKILL.md](file:///f:/globalai/eval_skill/.agents/skills/hack-eval/SKILL.md).
   - Perform a complete, read-only inspection of the codebase harness.
   - Score the 5 parameters totaling **450 marks** (Alignment 100, Code Quality 100, Innovation 100, Security 100, Grounding & Evals 50).
   - Write the comprehensive judging report to `hack_evaluation.md`.
3. **Commit:**
   - Selectively stage `hack_evaluation.md` and commit with message: `chore: add AI agent hackathon evaluation`.
4. **Chat Response:**
   - Respond in chat with strictly: `File created`.

---

### `/prompt-eval [prompt_or_file]` (or `/eval-prompt`)

**Intent:** Execute a complete prompt evaluation of any written prompt or prompt file across Prompt Clarity (/100), Output Quality (/100), and Efficiency (/50) totaling **250 marks**, outputting to `prompt_eval.md`.

**Execution Protocol:**
1. **Extract Target Prompt:**
   - Use the prompt text or file path provided as argument.
   - If missing, check [.agents/skills/prompt-eval/SKILL.md](file:///f:/globalai/eval_skill/.agents/skills/prompt-eval/SKILL.md) or prompt user: *"Please provide the prompt text or the path to the prompt file you would like to evaluate."*
2. **Execute Evaluation Skill:**
   - Refer to [.agents/skills/prompt-eval/SKILL.md](file:///f:/globalai/eval_skill/.agents/skills/prompt-eval/SKILL.md).
   - Score the 3 criteria (Prompt Clarity /100, Output Quality /100, Efficiency /50) totaling **250 marks**.
   - Generate `prompt_eval.md` including a production-ready optimized rewrite.
3. **Commit:**
   - Selectively stage `prompt_eval.md` and commit with message: `chore: add prompt evaluation report`.
4. **Chat Response:**
   - Output score summary and key recommendations in chat.
