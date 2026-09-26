---
trigger: model_decision
description: Triggers the AI Prompt Evaluation when the user types /prompt-eval or asks to evaluate, audit, or score a prompt.
---

# Command: /prompt-eval

When the user enters `/prompt-eval [prompt_or_file]`, `/eval-prompt`, or requests prompt evaluation:

1. **Target Identification:**
   - Extract the prompt text or target file path passed as argument.
   - If missing, check `.agents/skills/prompt-eval/SKILL.md` or prompt the user:
     > *"Please provide the prompt text or the path to the prompt file you would like to evaluate."*
2. **Execute Evaluation:**
   - Refer to [.agents/skills/prompt-eval/SKILL.md](file:///f:/globalai/eval_skill/.agents/skills/prompt-eval/SKILL.md).
   - Evaluate across Prompt Clarity (/100), Output Quality (/100), and Efficiency (/50) totaling **250 marks**.
   - Generate `prompt_eval.md` including detailed criteria breakdown, actionable recommendations, and an **optimized prompt rewrite**.
3. **Commit & Response:**
   - Commit `prompt_eval.md` with: `chore: add prompt evaluation report`.
   - Provide a brief summary of the score and top recommendations in chat.
