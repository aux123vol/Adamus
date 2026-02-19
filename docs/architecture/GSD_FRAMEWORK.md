# GSD Framework (Get Stuff Done)
## Adamus Execution Protocol — No Excuses, Ship It

**GSD Principle**: Decisions in 2 minutes, implementations same day, no task older than 48 hours.

---

## The GSD Rules

```yaml
rule_1_two_minute_decisions:
  if_decision_takes_less_than_2min: "Make it NOW"
  if_decision_takes_more: "Schedule a 15-min block, make it then"
  never: "Leave decisions in limbo"

rule_2_same_day_shipping:
  small_features: "Design, build, test, ship — same day"
  medium_features: "Ship MVP same day, iterate tomorrow"
  large_features: "Ship skeleton same day, flesh out this week"

rule_3_no_zombie_tasks:
  max_age: "48 hours in backlog without progress"
  if_older: "Either do it now, delegate to OpenClaw, or delete it"
  zombie_review: "Every Monday morning"
```

---

## Daily GSD Protocol

```yaml
8:00am: "Review overnight OpenClaw PRs (30 min max)"
8:30am: "Pick top 3 MRR tasks"
8:35am: "Start task 1 — no email, no social"
12:00pm: "Lunch + quick metrics check"
1:00pm: "Task 2"
3:30pm: "Task 3 or continue task 2"
4:45pm: "Brief OpenClaw for tonight"
5:00pm: "Ship whatever is done, leave"
```

---

## Blockers Protocol

```yaml
if_blocked:
  first: "Can OpenClaw unblock this autonomously?"
  second: "Can I solve it in < 15 min?"
  third: "Do I need another person?"
  
  if_yes_openclaw: "Add to tonight's backlog"
  if_yes_15min: "Do it now"
  if_need_person: "Send message, move to next task"
  
never: "Sit blocked for more than 15 minutes without action"
```

---

## Weekly GSD Review

```yaml
every_monday_8am:
  - shipped_last_week: "Count actual shipped items"
  - mrr_delta: "Did shipping move MRR?"
  - zombie_tasks: "Kill anything >48hrs stale"
  - this_week_top_3: "Set the 3 that matter most"
```

---

**Status**: ACTIVE — Enforced by Adamus daily
