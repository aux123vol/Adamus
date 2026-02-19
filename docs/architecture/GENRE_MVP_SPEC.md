# Genre MVP Specification
## What to Build First (Security-First, Privacy-First)

**Goal**: Ship Genre MVP that demonstrates core value while establishing secure foundation.

**Timeline**: 4-6 weeks  
**You + Claude Code**: Building together  
**Adamus**: Builds itself while helping build Genre

---

## MVP Definition: The Minimum Lovable Product

### What MVP Is NOT
```yaml
not_mvp:
  - "All three products (Lore/Saga/Bible) fully featured"
  - "Perfect UI/UX"
  - "Enterprise-scale infrastructure"
  - "Every feature you can imagine"
```

### What MVP IS
```yaml
mvp:
  - "ONE product with ONE core workflow"
  - "Proves the value hypothesis"
  - "Gets first paying users"
  - "Foundation for iteration"
  
specifically_for_genre:
  core_product: "Lore (story creation tool)"
  core_workflow: "Create → AI Assist → Save → Share"
  core_value: "Writers can create better stories faster with AI help"
  foundation: "Secure, private, self-improving from day 1"
```

---

## Lore MVP: The Core Features

### Week 1-2: Foundation + Editor

**Feature 1: Rich Text Editor**
```yaml
what:
  - "Create and edit story content"
  - "Basic formatting (bold, italic, headings)"
  - "Save automatically"
  
tech_stack:
  - frontend: "React + TypeScript"
  - editor: "Tiptap (or similar)"
  - storage: "PostgreSQL"
  
must_have_from_docs:
  - data_governance: "Validate all input"
  - zero_trust: "Never hardcode credentials"
  - logging: "Track all user actions"
  
estimated_time: "3-4 days with Claude Code"
```

**Feature 2: User Authentication**
```yaml
what:
  - "Sign up / Sign in"
  - "Email verification"
  - "Password reset"
  
tech_stack:
  - auth: "NextAuth.js or Supabase Auth"
  - storage: "PostgreSQL"
  
must_have_from_docs:
  - zero_trust: "JIT access tokens"
  - data_governance: "PII handling"
  
estimated_time: "2-3 days with Claude Code"
```

**Feature 3: Basic Dashboard**
```yaml
what:
  - "List of user's stories"
  - "Create new story"
  - "Open existing story"
  
tech_stack:
  - frontend: "React + Tailwind"
  - backend: "Next.js API routes"
  
estimated_time: "2 days with Claude Code"
```

### Week 3-4: AI Assistance (The Core Value)

**Feature 4: AI Writing Assist**
```yaml
what:
  - "Select text → Ask AI to improve"
  - "Commands: 'Continue', 'Expand', 'Rewrite'"
  - "AI suggestions appear inline"
  
tech_stack:
  - ai: "Claude API (via Anthropic)"
  - integration: "Through AI Firewall"
  
must_have_from_docs:
  - prompt_injection_defense: "Filter user input"
  - ai_firewall: "Never expose API key to frontend"
  - llm_optimization: "Start with prompt engineering"
  - explainability: "Log what AI did and why"
  
estimated_time: "4-5 days with Claude Code"
```

**Feature 5: AI Context Management**
```yaml
what:
  - "AI knows story context (characters, plot)"
  - "AI suggestions are coherent with story"
  
tech_stack:
  - rag: "Vector DB (Weaviate or Pinecone)"
  - embeddings: "OpenAI embeddings"
  
must_have_from_docs:
  - data_governance: "Tag data before vectorizing"
  - rag_system: "Short-term memory for AI"
  
estimated_time: "3-4 days with Claude Code"
```

### Week 5-6: Sharing + Monetization

**Feature 6: Share Stories**
```yaml
what:
  - "Generate shareable link"
  - "View-only mode for readers"
  - "Optional: Comments from readers"
  
tech_stack:
  - links: "UUID-based URLs"
  - permissions: "Public vs private toggle"
  
estimated_time: "2 days with Claude Code"
```

**Feature 7: Basic Payments**
```yaml
what:
  - "Free tier: 5 stories"
  - "Pro tier: Unlimited stories + advanced AI"
  - "Stripe integration"
  
tech_stack:
  - payments: "Stripe Checkout"
  - webhooks: "Handle subscription events"
  
must_have_from_docs:
  - zero_trust: "Webhook validation"
  - data_governance: "Track payment data"
  
estimated_time: "3-4 days with Claude Code"
```

---

## Technical Architecture for MVP

### Stack
```yaml
frontend:
  - framework: "Next.js 14 (App Router)"
  - language: "TypeScript"
  - styling: "Tailwind CSS"
  - editor: "Tiptap"
  
backend:
  - runtime: "Next.js API Routes"
  - database: "PostgreSQL (Supabase)"
  - auth: "NextAuth.js"
  - ai: "Anthropic Claude API"
  
infrastructure:
  - hosting: "Vercel (frontend + API)"
  - database: "Supabase (PostgreSQL + Auth)"
  - vector_db: "Weaviate Cloud"
  - monitoring: "Vercel Analytics + Sentry"
```

### Project Structure
```
/genre-lore-mvp/
  /app/                  # Next.js app directory
    /api/               # API routes
      /ai/              # AI endpoints
      /auth/            # Auth endpoints
      /stories/         # Story CRUD
    /dashboard/         # Dashboard pages
    /editor/            # Editor pages
    /shared/            # Shared story views
    
  /components/          # React components
    /editor/            # Editor components
    /ui/                # UI primitives
    
  /lib/                 # Utilities
    /ai-firewall.ts     # AI security layer
    /data-validation.ts # Input validation
    /db.ts              # Database client
    
  /docs/                # PUBLIC docs only
    architecture.md
    api.md
    
  .env.example          # Example env vars (no real values)
  .gitignore            # Ignore .env, secrets/
```

---

## Security Requirements (From 8 Systems)

### Must-Have Security (MVP)
```yaml
from_data_governance:
  - [ ] All input validated at API boundary
  - [ ] User data tagged (type, owner, timestamp)
  - [ ] Change tracking for story edits
  
from_zero_trust:
  - [ ] No credentials in code
  - [ ] API keys in .env (gitignored)
  - [ ] JWT authentication for all API calls
  
from_prompt_injection_defense:
  - [ ] User input filtered before AI
  - [ ] AI responses validated before display
  - [ ] Rate limiting on AI endpoints
  
from_llm_optimization:
  - [ ] Prompt engineering (no fine-tuning yet)
  - [ ] Cost monitoring (alert if >$100/day)
```

### Nice-to-Have Security (Post-MVP)
```yaml
from_bias_detection:
  - "Monitor AI suggestions for bias (can wait)"
  
from_explainable_ai:
  - "Full decision tracing (basic logging OK for MVP)"
  
from_multi_method_agents:
  - "Advanced agent coordination (overkill for MVP)"
```

---

## MVP Success Metrics

### Week 4 Check-In
```yaml
metrics:
  - can_user_create_story: "YES/NO"
  - can_user_get_ai_help: "YES/NO"
  - is_data_secure: "YES/NO"
  - are_costs_tracked: "YES/NO"
  
if_all_yes: "Continue to payments"
if_any_no: "Fix before proceeding"
```

### Week 6 Check-In (Launch)
```yaml
metrics:
  - 5_beta_users_trying: "YES/NO"
  - ai_suggestions_helpful: "User feedback"
  - no_security_issues: "YES/NO"
  - costs_under_budget: "<$50/day"
  
if_all_yes: "Open to more users"
if_any_no: "Fix before scaling"
```

### Month 3 Check-In (PMF Signal)
```yaml
metrics:
  - 50+_active_users: "YES/NO"
  - 10+_paying_users: "YES/NO"
  - >70%_retention: "YES/NO"
  - $1K+_MRR: "YES/NO"
  
if_all_yes: "Scaling phase, build Saga next"
if_any_no: "Iterate on Lore, don't expand yet"
```

---

## What NOT to Build in MVP

### Tempting But NOT MVP
```yaml
dont_build_yet:
  - saga_products: "Wait until Lore has PMF"
  - bible_infrastructure: "Wait until 2+ products"
  - mobile_apps: "Web first, mobile later"
  - collaboration: "Single-user first"
  - advanced_ai: "Prompt engineering only, no fine-tuning"
  - analytics_dashboard: "Basic metrics only"
  - admin_panel: "Manual admin for now"
  - seo_optimization: "Focus on product first"
  - internationalization: "English only for MVP"
  
why_not: "Each feature adds weeks. Ship fast, iterate."
```

---

## Build Schedule (You + Claude Code)

### Week 1: Foundation
```yaml
monday:
  - setup_project: "Next.js + PostgreSQL"
  - setup_claude_code: "Local development"
  
tuesday:
  - build_auth: "Sign up / Sign in"
  - test_auth: "Can users authenticate?"
  
wednesday:
  - build_dashboard: "List stories"
  - test_dashboard: "Can users see their stories?"
  
thursday:
  - build_editor_basic: "Create/edit stories"
  - test_editor: "Can users write?"
  
friday:
  - integrate_all: "Auth → Dashboard → Editor"
  - test_flow: "End-to-end user flow works?"
  
deliverable: "Users can sign up and create stories"
```

### Week 2: AI Integration
```yaml
monday:
  - build_ai_firewall: "Security layer for AI calls"
  - test_firewall: "Blocks malicious input?"
  
tuesday:
  - integrate_claude_api: "Call Anthropic API"
  - test_basic_ai: "Can get AI response?"
  
wednesday:
  - build_ai_commands: "Continue, Expand, Rewrite"
  - test_commands: "Do they work?"
  
thursday:
  - integrate_with_editor: "AI suggestions in editor"
  - test_ux: "Is experience smooth?"
  
friday:
  - cost_monitoring: "Track API costs"
  - test_limits: "Proper rate limiting?"
  
deliverable: "Users can get AI writing help"
```

### Week 3: RAG for Context
```yaml
monday:
  - setup_weaviate: "Vector database"
  - test_vectorization: "Can store embeddings?"
  
tuesday:
  - build_context_extraction: "Extract characters, plot"
  - test_extraction: "Accurate?"
  
wednesday:
  - integrate_rag: "AI uses story context"
  - test_coherence: "Suggestions coherent?"
  
thursday:
  - optimize_performance: "Fast enough?"
  - test_at_scale: "Works with long stories?"
  
friday:
  - polish_ux: "Smooth experience"
  - user_testing: "Get 3 friends to try"
  
deliverable: "AI understands story context"
```

### Week 4: Sharing
```yaml
monday:
  - build_share_links: "Generate URLs"
  - test_sharing: "Can non-users view?"
  
tuesday:
  - build_view_mode: "Read-only display"
  - test_viewing: "Looks good?"
  
wednesday:
  - permissions: "Public vs private"
  - test_permissions: "Privacy works?"
  
thursday:
  - polish: "Final touches"
  - staging_deploy: "Deploy to staging"
  
friday:
  - final_testing: "Full QA pass"
  - fix_bugs: "Address issues"
  
deliverable: "Users can share stories"
```

### Week 5: Payments
```yaml
monday:
  - stripe_setup: "Create Stripe account"
  - pricing_page: "Show tiers"
  
tuesday:
  - stripe_checkout: "Integration"
  - test_payment: "Can process payment?"
  
wednesday:
  - subscription_logic: "Free vs Pro features"
  - test_logic: "Limits enforced?"
  
thursday:
  - webhooks: "Handle Stripe events"
  - test_webhooks: "Subscription updates?"
  
friday:
  - billing_portal: "Users manage subscription"
  - test_portal: "Can cancel/upgrade?"
  
deliverable: "Users can pay"
```

### Week 6: Launch Prep
```yaml
monday:
  - security_audit: "Review all security measures"
  - fix_issues: "Address vulnerabilities"
  
tuesday:
  - performance_testing: "Load test"
  - optimize: "Fix slow endpoints"
  
wednesday:
  - error_handling: "Graceful failures"
  - monitoring: "Set up Sentry"
  
thursday:
  - production_deploy: "Go live"
  - smoke_tests: "Verify production works"
  
friday:
  - invite_beta_users: "First 10 users"
  - monitor_closely: "Watch for issues"
  
deliverable: "MVP LIVE"
```

---

## Using Claude Code to Build

### Daily Workflow
```bash
# Morning: Check what to build today
# You: Read MVP doc, see today's tasks

# Start Claude Code session
cd genre-lore-mvp
claude-code

# Give Claude Code clear instructions
# (Based on today's task from schedule above)

# Example: Tuesday of Week 1
claude-code "Build authentication system:
- NextAuth.js with email provider
- PostgreSQL for user storage
- Sign up, sign in, sign out flows
- Email verification
Follow patterns from /docs/zero-trust.md for security"

# Claude Code builds
# You review code
# You test locally
# You commit if good

git add .
git commit -m "feat: add authentication system"
```

### References to Docs
```bash
# When Claude Code needs guidance, reference docs

claude-code "Build AI writing assist feature.
Read /docs/prompt-injection-defense.md first.
Implement input filtering before AI calls."

# Claude Code reads doc, implements correctly
```

---

## After MVP: What's Next

### Month 2-3: Iterate to PMF
```yaml
based_on_user_feedback:
  - improve_ai_quality
  - add_requested_features
  - optimize_performance
  - reduce_costs
  
goal: "10+ paying users, $1K+ MRR, >70% retention"
```

### Month 4-6: Build Saga
```yaml
once_lore_has_pmf:
  - build_saga_mvp: "Monetization layer"
  - integrate_with_lore: "Sell stories"
  - test_with_lore_users: "Do they want this?"
```

### Month 7-12: Build Bible
```yaml
once_2_products_working:
  - build_bible_mvp: "Format standards"
  - ecosystem_play: "Get external adoption"
  - positioning: "Infrastructure provider"
```

---

## The Bottom Line

**MVP Scope**: Lore only, 7 features, 6 weeks  
**Tech Stack**: Next.js + PostgreSQL + Claude API  
**Security**: Data Gov + Zero Trust + Prompt Defense (basics)  
**Launch**: Week 6, 10 beta users  
**Goal**: Prove AI writing assistance has value

**You + Claude Code**: Build together, ship fast, stay secure

**Start Monday**: Setup project, build auth

**Success**: Users love it, pay for it, tell friends about it
