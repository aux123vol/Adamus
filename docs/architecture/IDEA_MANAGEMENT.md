# Idea Management
## How Adamus Captures, Evaluates, and Implements Ideas

---

## Idea Capture

```yaml
sources:
  augustus: "Direct input during work sessions"
  users: "Feedback from Genre users"
  cambi_ai: "Trend detection"
  business_ai: "Competitor gaps"
  openclaw: "Implementation discoveries"
  adamus: "Self-improvement ideas"
```

## Evaluation Matrix

```yaml
for_every_idea:
  mrr_impact: "High/Medium/Low"
  effort: "Hours to implement"
  strategic_fit: "Aligns with sovereignty/creator focus"
  user_demand: "Confirmed by user conversations"
  score: "(mrr_impact * 3 + strategic_fit * 2) / effort"
```

## Idea States

```yaml
states:
  captured: "Logged, not evaluated"
  evaluated: "Scored, prioritized"
  approved: "Augustus approved"
  in_progress: "OpenClaw/Claude building"
  shipped: "Live in product"
  killed: "Not worth building"
```

## Storage

```yaml
location: "~/adamus/data/ideas.json"
war_room: "Ideas panel showing top 5"
weekly_review: "Augustus reviews backlog every Monday"
```

**Status**: ACTIVE — Adamus captures ideas 24/7
