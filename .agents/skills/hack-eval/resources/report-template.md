# AI Agent Hackathon Evaluation Report Template

This template defines the exact structure and formatting required for `hack_evaluation.md`. The evaluator agent should copy and populate this document.

---

```markdown
# AI Agent Hackathon Evaluation Report

## 1. Overall Score

| Parameter | Maximum Marks | Awarded Marks | Percentage |
|---|---|---|---|
| Problem Statement Alignment | 100 | {{SCORE_ALIGNMENT}} | {{PCT_ALIGNMENT}}% |
| Code Quality | 100 | {{SCORE_CODE_QUALITY}} | {{PCT_CODE_QUALITY}}% |
| Innovation | 100 | {{SCORE_INNOVATION}} | {{PCT_INNOVATION}}% |
| Security | 100 | {{SCORE_SECURITY}} | {{PCT_SECURITY}}% |
| Grounding and Evals | 50 | {{SCORE_GROUNDING_EVALS}} | {{PCT_GROUNDING_EVALS}}% |
| **Total Score** | **450** | **{{TOTAL_SCORE}}** | **{{TOTAL_PCT}}%** |

*Note: Total score is out of 450 marks. Scores are calculated objectively based on verified codebase evidence.*

---

## 2. Executive Summary

- **Overall Assessment:**
  {{EXECUTIVE_SUMMARY_TEXT}}

- **Main Strengths:**
  - {{STRENGTH_1}}
  - {{STRENGTH_2}}
  - {{STRENGTH_3}}

- **Significant Weaknesses:**
  - {{WEAKNESS_1}}
  - {{WEAKNESS_2}}
  - {{WEAKNESS_3}}

- **Key Technical Observations:**
  - {{TECHNICAL_OBSERVATION_1}}
  - {{TECHNICAL_OBSERVATION_2}}

- **Important Security Concerns:**
  - {{SECURITY_CONCERN_1}}
  - {{SECURITY_CONCERN_2}}

- **Alignment with Problem Statement:**
  {{PROBLEM_ALIGNMENT_SUMMARY}}

---

## 3. Detailed Parameter Evaluations

### 3.1 Problem Statement Alignment (Awarded: {{SCORE_ALIGNMENT}} / 100)

- **Assessment:**
  {{ALIGNMENT_ASSESSMENT}}

- **Evidence:**
  - Files Inspected: `{{ALIGNMENT_FILES}}`
  - Findings: {{ALIGNMENT_EVIDENCE}}

- **Strengths:**
  - {{ALIGNMENT_STRENGTH_1}}
  - {{ALIGNMENT_STRENGTH_2}}

- **Weaknesses and Gaps:**
  - {{ALIGNMENT_GAP_1}}
  - {{ALIGNMENT_GAP_2}}

- **Recommendations:**
  - {{ALIGNMENT_REC_1}}
  - {{ALIGNMENT_REC_2}}

---

### 3.2 Code Quality (Awarded: {{SCORE_CODE_QUALITY}} / 100)

- **Assessment:**
  {{CODE_QUALITY_ASSESSMENT}}

- **Evidence:**
  - Files Inspected: `{{CODE_QUALITY_FILES}}`
  - Findings: {{CODE_QUALITY_EVIDENCE}}

- **Strengths:**
  - {{CODE_QUALITY_STRENGTH_1}}
  - {{CODE_QUALITY_STRENGTH_2}}

- **Weaknesses and Gaps:**
  - {{CODE_QUALITY_GAP_1}}
  - {{CODE_QUALITY_GAP_2}}

- **Recommendations:**
  - {{CODE_QUALITY_REC_1}}
  - {{CODE_QUALITY_REC_2}}

---

### 3.3 Innovation (Awarded: {{SCORE_INNOVATION}} / 100)

- **Assessment:**
  {{INNOVATION_ASSESSMENT}}

- **Evidence:**
  - Files Inspected: `{{INNOVATION_FILES}}`
  - Findings: {{INNOVATION_EVIDENCE}}

- **Strengths:**
  - {{INNOVATION_STRENGTH_1}}
  - {{INNOVATION_STRENGTH_2}}

- **Weaknesses and Gaps:**
  - {{INNOVATION_GAP_1}}
  - {{INNOVATION_GAP_2}}

- **Recommendations:**
  - {{INNOVATION_REC_1}}
  - {{INNOVATION_REC_2}}

---

### 3.4 Security (Awarded: {{SCORE_SECURITY}} / 100)

- **Assessment:**
  {{SECURITY_ASSESSMENT}}

- **Evidence:**
  - Files Inspected: `{{SECURITY_FILES}}`
  - Findings: {{SECURITY_EVIDENCE}}

- **Strengths:**
  - {{SECURITY_STRENGTH_1}}
  - {{SECURITY_STRENGTH_2}}

- **Weaknesses and Gaps:**
  - {{SECURITY_GAP_1}}
  - {{SECURITY_GAP_2}}

- **Recommendations:**
  - {{SECURITY_REC_1}}
  - {{SECURITY_REC_2}}

---

### 3.5 Grounding and Evals (Awarded: {{SCORE_GROUNDING_EVALS}} / 50.0)

- **Subcategory Breakdown:**
  - **Grounding Score:** {{SCORE_GROUNDING}} / 25.0
  - **Evals Score:** {{SCORE_EVALS}} / 25.0
  - **Total Grounding and Evals:** {{SCORE_GROUNDING_EVALS}} / 50.0

- **Assessment:**
  - **Grounding (Factual fidelity, citations, hallucination guards):**
    {{GROUNDING_ASSESSMENT}}
  - **Evals (Test harness, deterministic checks, benchmark metrics):**
    {{EVALS_ASSESSMENT}}

- **Evidence:**
  - Files Inspected: `{{GROUNDING_EVALS_FILES}}`
  - Findings: {{GROUNDING_EVALS_EVIDENCE}}

- **Strengths:**
  - {{GE_STRENGTH_1}}
  - {{GE_STRENGTH_2}}

- **Weaknesses and Gaps:**
  - {{GE_GAP_1}}
  - {{GE_GAP_2}}

- **Recommendations:**
  - {{GE_REC_1}}
  - {{GE_REC_2}}

---

## 4. Cross-Cutting Findings

- **Architecture:** {{CROSS_ARCHITECTURE}}
- **Reliability:** {{CROSS_RELIABILITY}}
- **Security:** {{CROSS_SECURITY}}
- **Evaluation Maturity:** {{CROSS_EVAL_MATURITY}}
- **Maintainability:** {{CROSS_MAINTAINABILITY}}
- **Reproducibility:** {{CROSS_REPRODUCIBILITY}}

---

## 5. Critical Issues & Vulnerabilities

| Issue | Severity | Affected Component | Confirmation Status | Evidence | Potential Impact |
|---|---|---|---|---|---|
| {{ISSUE_1_TITLE}} | {{SEVERITY_1}} | `{{COMPONENT_1}}` | {{STATUS_1}} | {{EVIDENCE_1}} | {{IMPACT_1}} |
| {{ISSUE_2_TITLE}} | {{SEVERITY_2}} | `{{COMPONENT_2}}` | {{STATUS_2}} | {{EVIDENCE_2}} | {{IMPACT_2}} |

*Severity levels: Critical, High, Medium, Low.*
*Status levels: Confirmed (verified in code), Potential (speculative or deployment-dependent).*
*Note: All discovered secrets and sensitive values are redacted above.*

---

## 6. Final Summary & Judging Verdict

- **Final Score Breakdown:**
  - Problem Statement Alignment: {{SCORE_ALIGNMENT}} / 100
  - Code Quality: {{SCORE_CODE_QUALITY}} / 100
  - Innovation: {{SCORE_INNOVATION}} / 100
  - Security: {{SCORE_SECURITY}} / 100
  - Grounding and Evals: {{SCORE_GROUNDING_EVALS}} / 50.0
  - **Total Score: {{TOTAL_SCORE}} / 450.0**

- **Strongest Aspects:**
  - {{FINAL_STRONG_1}}
  - {{FINAL_STRONG_2}}

- **Major Gaps:**
  - {{FINAL_GAP_1}}
  - {{FINAL_GAP_2}}

- **Improvement Priorities:**
  1. {{PRIORITY_1}}
  2. {{PRIORITY_2}}
  3. {{PRIORITY_3}}

- **Evaluation Limitations:**
  {{EVAL_LIMITATIONS}}
```
