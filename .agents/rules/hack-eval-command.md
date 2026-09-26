---
trigger: model_decision
description: Triggers the AI Agent Hackathon Evaluation when the user types /hack-eval or /eval-agent or asks to evaluate an agent.
---

# Command: /hack-eval

When the user enters `/hack-eval [problem_statement]`, `/eval-agent [problem_statement]`, or requests an evaluation:

1. **Problem Statement Resolution:**
   - If the user supplied the problem statement in the command argument (e.g. `/hack-eval "..."`), adopt it directly as the target problem statement.
   - Otherwise, inspect `.agents/skills/hack-eval/SKILL.md` to see if `[PROBLEM_STATEMENT]` has been set.
   - If not set, halt and ask the user:
     > "Please provide the hackathon problem statement to begin the AI agent evaluation."
2. **Skill Invocation:**
   - Execute the instructions in `.agents/skills/hack-eval/SKILL.md`.
   - Strictly adhere to read-only evaluation (only `hack_evaluation.md` may be created/modified).
   - Score the 5 parameters totaling **450 marks**.
3. **Commit & Response:**
   - Commit `hack_evaluation.md` with: `chore: add AI agent hackathon evaluation`.
   - Reply in chat with strictly: `File created`.
