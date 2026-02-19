# Version Control System
## Git Workflow for Adamus + Genre

---

## Repository Structure

```yaml
repositories:
  adamus: "github.com/[username]/adamus"
  genre: "github.com/[username]/genre"
  genre_dsb: "github.com/[username]/genre-dsb"
```

## Branch Strategy

```yaml
main: "Production — only merge tested code"
develop: "Integration — PRs merge here first"
feature_branches:
  format: "feature/[description]"
  openclaw: "openclaw/[feature-name]"
  hotfix: "hotfix/[issue]"
```

## Commit Convention

```yaml
format: "[Component] [Brain] Description"
examples:
  - "[Coordinator] [Claude] Add multi-brain routing"
  - "[OpenClaw] [Auto] Implement data governance v0.1"
  - "[Genre] [Claude] Add user authentication"
  - "[Security] [Manual] Update zero trust rules"
```

## PR Rules

```yaml
all_prs:
  - tests_must_pass: true
  - description_required: true
  - augustus_review: "Required for main"
  - openclaw_prs: "Always draft until reviewed"
  - never_push_to_main: "Always PR"
```

## .gitignore (Critical)

```gitignore
.env
.env.*
*.key
*.pem
credentials/
.adamus/memory/
__pycache__/
*.pyc
node_modules/
.DS_Store
logs/
*.log
```

**Status**: ACTIVE — All work in Git always
