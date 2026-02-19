# Documentation-Driven Build System
## Making Sure We Actually USE the 57 Docs

**The Problem**: 850KB of docs that sit unused while we code from memory.

**The Solution**: Build system that FORCES doc consultation before any code is written.

---

## The Build Protocol (Mandatory)

### Rule: NO CODE WITHOUT DOCS CHECK

Every build task follows this protocol:

```yaml
Step 1: IDENTIFY
  question: "What am I building?"
  output: "Feature name + component"
  
Step 2: FIND RELEVANT DOCS
  question: "Which docs cover this?"
  action: "Search /mnt/project/ for relevant docs"
  output: "List of 3-5 most relevant docs"
  
Step 3: READ DOCS
  action: "Actually read the relevant sections"
  output: "Notes on key principles, patterns, constraints"
  
Step 4: CHECK FOR CONFLICTS
  question: "Does my approach violate any documented principles?"
  action: "Cross-reference with architecture docs"
  
Step 5: DESIGN
  action: "Design based on doc principles"
  output: "Technical design that references docs"
  
Step 6: CODE
  action: "Write code following design"
  constraint: "Must match doc patterns"
  
Step 7: VERIFY
  action: "Check code against docs"
  question: "Did I follow the documented approach?"
```

---

## Practical Example: Building Lore Editor

### Step 1: Identify
```yaml
building: "Lore rich text editor with AI assist"
components: ["Frontend editor", "API endpoints", "AI integration"]
```

### Step 2: Find Relevant Docs
```bash
# Search project docs
grep -r "editor" /mnt/project/*.md
grep -r "frontend" /mnt/project/*.md
grep -r "ai integration" /mnt/project/*.md

# Result: Relevant docs found
- /mnt/project/ADAMUS_ARCHITECTURE.md (AI integration patterns)
- /mnt/project/DEVELOPMENT_STANDARDS.md (frontend patterns)
- /mnt/project/DATA_GOVERNANCE_FRAMEWORK.md (data validation)
- /mnt/project/ZERO_TRUST_ARCHITECTURE.md (credential management)
- /mnt/project/PROMPT_INJECTION_DEFENSE.md (AI safety)
```

### Step 3: Read Docs (Extract Key Points)
```yaml
from_adamus_architecture:
  - "AI calls must go through AI Firewall"
  - "Never expose raw LLM to frontend"
  - "Log all AI interactions"

from_development_standards:
  - "React with TypeScript"
  - "Tailwind for styling"
  - "Error boundaries required"

from_data_governance:
  - "Validate all user input"
  - "Tag data before storage"
  - "Track data lineage"

from_zero_trust:
  - "Never hardcode credentials"
  - "JIT access for AI calls"
  - "All API calls authenticated"

from_prompt_defense:
  - "Filter user input for injection"
  - "Sanitize before sending to LLM"
  - "Validate LLM output"
```

### Step 4: Check for Conflicts
```yaml
question: "Can I build editor that sends user text directly to OpenAI?"
answer: "NO - violates multiple docs"
  - Zero Trust: "Never expose credentials to frontend"
  - Prompt Defense: "Must filter input first"
  - Data Governance: "Must validate and tag"

correct_approach:
  - Frontend → Backend API
  - Backend validates input (Data Governance)
  - Backend filters for injection (Prompt Defense)
  - Backend calls AI through firewall (Zero Trust)
  - Backend logs interaction (Adamus Architecture)
```

### Step 5: Design
```typescript
// DESIGN (references docs in comments)

// Frontend (following DEVELOPMENT_STANDARDS.md)
interface EditorProps {
  initialContent: string;
  onSave: (content: string) => void;
}

// Backend API (following ZERO_TRUST_ARCHITECTURE.md)
POST /api/lore/ai-assist
Headers: {
  Authorization: "Bearer <JWT>" // Never hardcoded
}
Body: {
  text: string,
  requestType: "complete" | "suggest" | "edit"
}

// AI Integration (following PROMPT_INJECTION_DEFENSE.md)
1. Receive user text
2. Filter for injection patterns
3. Validate safe to send to LLM
4. Call LLM through AI Firewall
5. Validate LLM response
6. Return to user

// Data Storage (following DATA_GOVERNANCE_FRAMEWORK.md)
1. Validate schema
2. Tag: { source: "user", type: "lore_content", ai_assisted: true }
3. Store with lineage tracking
```

### Step 6: Code (Following Design)
```typescript
// This code MATCHES the design which MATCHES the docs

// frontend/components/LoreEditor.tsx
import { useState } from 'react';
import { aiAssist } from '@/lib/api'; // Follows pattern from docs

export function LoreEditor({ initialContent, onSave }: EditorProps) {
  // Implementation follows DEVELOPMENT_STANDARDS.md patterns
  // Error boundary at parent level (as documented)
  // Tailwind for styling (as documented)
  
  const handleAIAssist = async (text: string) => {
    // Don't call AI directly - goes through backend
    // (follows ZERO_TRUST_ARCHITECTURE.md)
    const result = await aiAssist(text);
    return result;
  };
}

// backend/routes/lore.ts
import { filterPromptInjection } from '@/lib/security';
import { validateSchema } from '@/lib/data-governance';
import { aiFirewall } from '@/lib/ai-firewall';

router.post('/api/lore/ai-assist', async (req, res) => {
  // 1. Authenticate (ZERO_TRUST_ARCHITECTURE.md)
  const user = await authenticateRequest(req);
  
  // 2. Filter injection (PROMPT_INJECTION_DEFENSE.md)
  const filteredText = filterPromptInjection(req.body.text);
  
  // 3. Validate (DATA_GOVERNANCE_FRAMEWORK.md)
  const valid = validateSchema(filteredText, 'lore_content');
  if (!valid) return res.status(400).json({ error: 'Invalid input' });
  
  // 4. Call AI through firewall (ADAMUS_ARCHITECTURE.md)
  const result = await aiFirewall.complete({
    prompt: filteredText,
    user: user.id,
    type: 'lore_assist'
  });
  
  // 5. Log (ADAMUS_ARCHITECTURE.md)
  await logAIInteraction({
    user: user.id,
    input: filteredText,
    output: result,
    timestamp: Date.now()
  });
  
  // 6. Return
  res.json({ result });
});
```

### Step 7: Verify
```yaml
checklist:
  - follows_zero_trust: ✅ "No hardcoded credentials"
  - follows_prompt_defense: ✅ "Input filtered"
  - follows_data_governance: ✅ "Schema validated, tagged"
  - follows_adamus_arch: ✅ "Goes through AI Firewall, logged"
  - follows_dev_standards: ✅ "React + TypeScript + Tailwind"

conflicts: none
approved: true
```

---

## Enforcing Doc Usage with Claude Code

### The Build Command
```bash
# Custom build command that enforces protocol

genre-build "Lore rich text editor"

# This script:
# 1. Asks Claude Code: "What are you building?"
# 2. Searches /mnt/project/ for relevant docs
# 3. Shows doc excerpts to Claude Code
# 4. Asks: "Does your approach match these docs?"
# 5. Only proceeds if Claude Code confirms
```

### Implementation
```bash
#!/bin/bash
# genre-build command

FEATURE=$1

echo "Building: $FEATURE"
echo ""

# Step 1: Find relevant docs
echo "Step 1: Finding relevant docs..."
DOCS=$(grep -l "$FEATURE" /mnt/project/*.md)
echo "Found: $DOCS"
echo ""

# Step 2: Extract key principles
echo "Step 2: Key principles from docs:"
for doc in $DOCS; do
  echo "From $doc:"
  # Show relevant sections
  grep -A 5 "$FEATURE" "$doc"
done
echo ""

# Step 3: Confirm with Claude Code
echo "Step 3: Design following these principles"
echo "Run: claude-code with context from docs above"
echo ""

# Step 4: Verify
echo "Step 4: After coding, verify against docs"
echo "Checklist:"
echo "[ ] Follows documented patterns"
echo "[ ] No conflicts with architecture"
echo "[ ] Security requirements met"
```

---

## Doc Categories & When to Use

### Always Check These (Every Build)
```yaml
core_architecture:
  - ADAMUS_ARCHITECTURE.md: "How AI/agents work"
  - DEVELOPMENT_STANDARDS.md: "Code patterns"
  - ZERO_TRUST_ARCHITECTURE.md: "Security basics"

before_any_code:
  - Read relevant sections
  - Note constraints
  - Design accordingly
```

### Check for Specific Features
```yaml
ai_features:
  - PROMPT_INJECTION_DEFENSE.md
  - LLM_OPTIMIZATION_FRAMEWORK.md
  - EXPLAINABLE_AI_FRAMEWORK.md

data_features:
  - DATA_GOVERNANCE_FRAMEWORK.md
  - LOGGING_INFRASTRUCTURE.md

multi_step_workflows:
  - MULTI_METHOD_AGENT_ARCHITECTURE.md

user_facing_decisions:
  - BIAS_DETECTION_FRAMEWORK.md
  - AUGUSTUS_COACHING_FRAMEWORK.md
```

### Check During Refactoring
```yaml
improving_existing_code:
  - PERFORMANCE_OPTIMIZATION.md
  - HALLUCINATION_PREVENTION_PROTOCOL.md
  
security_hardening:
  - THREAT_MODEL.md
  - VULNERABILITY_MANAGEMENT.md
```

---

## Living Documentation Strategy

### Docs Are Not Static
```yaml
every_build:
  - if_doc_unclear: "Update doc with clarification"
  - if_pattern_changes: "Update doc immediately"
  - if_new_pattern: "Document it"

weekly_review:
  - check: "Are docs still accurate?"
  - update: "Reflect actual implementation"
  - prune: "Remove outdated sections"
```

### Doc Update Protocol
```yaml
when_you_learn_something:
  1. note_it: "Write down the learning"
  2. find_doc: "Which doc should this go in?"
  3. update_doc: "Add the learning"
  4. commit: "Git commit with clear message"

example:
  learning: "AI Firewall adds 150ms latency"
  doc: "ZERO_TRUST_ARCHITECTURE.md"
  update: "Add performance note to AI Firewall section"
  commit: "docs: note AI Firewall latency impact"
```

---

## Integration with War Room

### War Room Tracks Doc Usage
```yaml
metrics:
  - doc_consultation_rate: "% of builds that checked docs first"
  - doc_violations: "Code that didn't follow documented patterns"
  - doc_updates: "How often docs are kept current"

alerts:
  - low_consultation: "Team not checking docs (< 80%)"
  - high_violations: "Code not matching architecture"
  - stale_docs: "Doc not updated in 30+ days"
```

---

## The Point of All This

**Question**: "What's the point of all these docs?"

**Answer**: 
1. **Consistency**: Everyone (including Adamus) builds the same way
2. **Quality**: Patterns are proven, not improvised
3. **Speed**: Don't re-design every time, follow pattern
4. **Security**: Critical requirements documented, not forgotten
5. **Onboarding**: New people (or AI agents) can read and understand
6. **Maintenance**: Future you knows why decisions were made

**But ONLY if we actually use them.**

**This build protocol ensures we do.**

---

## Week 1 Action: Prove the Pattern

### Monday: Set Up Build System
```bash
# 1. Create genre-build command
# 2. Test with one feature
# 3. Verify Claude Code can follow it
```

### Tuesday-Friday: Build 3 Features Using Protocol
```yaml
feature_1: "Lore editor"
  - Find docs ✓
  - Read principles ✓
  - Design ✓
  - Code ✓
  - Verify ✓

feature_2: "Saga payments"
  - Find docs ✓
  - Read principles ✓
  - Design ✓
  - Code ✓
  - Verify ✓

feature_3: "Bible collaboration"
  - Find docs ✓
  - Read principles ✓
  - Design ✓
  - Code ✓
  - Verify ✓
```

### End of Week: Evaluate
```yaml
question: "Did protocol work?"
metrics:
  - did_we_follow_docs: true/false
  - code_quality_improved: true/false
  - build_speed_impact: "+/- X%"
  
decision: "Keep protocol? Adjust? Abandon?"
```

---

## Bottom Line

**The docs are only valuable if we USE them.**

**This protocol FORCES usage:**
1. No code without doc check
2. Design must reference docs
3. Code must match design
4. Verify against docs before commit

**Start Monday: Implement genre-build command, test with one feature.**

**If it works: Keep using it. Every build. No exceptions.**
