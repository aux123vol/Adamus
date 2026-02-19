# Hallucination Prevention Protocol
## How Adamus Avoids AI Hallucinations

---

## The Problem

```yaml
hallucination_risks:
  - inventing_apis: "AI says function exists, it doesn't"
  - false_facts: "AI makes up data or stats"
  - inconsistent_behavior: "Different answer same question"
  - confident_wrong: "High confidence, completely wrong"
```

## Prevention Strategies

```yaml
strategy_1_ground_in_docs:
  rule: "Every claim must cite a specific document"
  implementation: "Prompt includes 'cite your source'"
  validation: "Check citation exists"
  
strategy_2_test_before_commit:
  rule: "All code must run before committing"
  implementation: "OpenClaw always executes code"
  validation: "Tests pass = no hallucinated APIs"
  
strategy_3_low_confidence_escalation:
  rule: "If < 80% confident, ask Augustus"
  implementation: "Confidence score in every response"
  validation: "Flagged items get human review"
  
strategy_4_multi_verification:
  rule: "Important facts verified by 2+ sources"
  implementation: "Cross-reference documents"
  validation: "Sources match = proceed"
```

## Detection System

```yaml
red_flags:
  - "I think" / "I believe" (uncertainty without asking)
  - "Usually" / "Typically" (vague instead of specific)
  - Long confident explanations with no citations
  - Code that doesn't match actual installed packages
  
if_red_flag_detected:
  action: "Flag for Augustus review"
  never: "Deploy flagged code autonomously"
```

**Status**: ACTIVE — Applied to all brain outputs
