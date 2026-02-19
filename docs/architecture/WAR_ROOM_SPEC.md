# War Room Specification
## Daily Steering System for Genre

**Purpose**: Give Augustus omniscient view of Genre's health, so he can steer daily instead of quarterly.

**Analogy**: Fighter jet cockpit - HUD shows speed, altitude, threats, targets all at once.

---

## War Room Philosophy

### Traditional Company Management
```yaml
problems:
  - quarterly_reports: "Too slow for startup"
  - spreadsheets: "Static, outdated instantly"
  - gut_feeling: "No data backing decisions"
  - blind_steering: "Don't know if going off cliff until too late"
  
result: "React to problems weeks after they start"
```

### War Room Management
```yaml
solution:
  - real_time_data: "Updated every minute"
  - visual_dashboard: "See everything at once"
  - automated_alerts: "Know about problems immediately"
  - daily_steering: "Adjust course every day"
  
result: "Prevent problems before they become crises"
```

---

## War Room: Three Synchronized Layers

### Layer 1: Internal Vitals (Your Company)
```yaml
what_to_track:
  survival_metrics:
    - burn_rate: "$X/month"
    - runway: "X months until out of money"
    - cash_reserves: "$X in bank"
    
  pmf_pulse:
    - users_total: "All users"
    - users_active: "Used in last 7 days"
    - users_paying: "Paid subscriptions"
    - mrr: "Monthly recurring revenue"
    - churn: "% users who left"
    - retention: "% users who stayed"
    
  productivity:
    - features_shipped: "Last 7 days"
    - velocity: "Features/week trend"
    - bugs_open: "Unresolved issues"
    - deploy_frequency: "How often shipping"
    
  adamus_health:
    - capabilities_built: "X/100 systems"
    - self_improvement_rate: "Systems/week"
    - security_score: "X/10"
    - cost_efficiency: "$ saved via optimization"

why_it_matters:
  - "Tells you if engine overheating (burn too high)"
  - "Tells you if product working (PMF metrics)"
  - "Tells you if team productive (velocity)"
  - "Tells you if foundation solid (Adamus health)"
```

### Layer 2: External Radar (Competition + Environment)
```yaml
what_to_track:
  competitor_activity:
    - feature_launches: "What did they ship?"
    - pricing_changes: "Did they drop prices?"
    - funding_news: "Did they raise?"
    - user_sentiment: "What are people saying?"
    
  moat_tracking:
    - infrastructure_costs: "Are AWS costs rising?"
    - api_dependencies: "Are vendors reliable?"
    - data_rights: "Do we own our data?"
    
  threat_landscape:
    - vertical_threats: "AWS/Google building similar?"
    - horizontal_threats: "New startups in space?"
    - shadow_threats: "Open source alternatives?"
    - bottom_up_threats: "Indie builders?"
    
  environment_signals:
    - geopolitical: "GPU bans, IP law changes"
    - compliance: "New regulations"
    - market_shifts: "AI hype cooling?"

why_it_matters:
  - "See where competitors moving"
  - "Know where battlefield tilting"
  - "Anticipate threats before they hit"
```

### Layer 3: Strategic Horizon (Future Steering)
```yaml
what_to_track:
  unicorn_index:
    - valuation_signals: "What's company worth?"
    - believer_growth: "How many people believe?"
    - arr_trajectory: "Path to $1B valuation"
    
  monopoly_index:
    - rails_adoption: "External builders using Genre?"
    - lock_in_strength: "Hard to switch away?"
    - network_effects: "More users = more value?"
    
  civilization_index:
    - protocol_adoption: "Standards, not just features"
    - ecosystem_health: "Independent builders thriving?"
    - cultural_impact: "Changing how creators work?"
    
  ai_general_suggestions:
    - pivots: "AI sees opportunities"
    - expansions: "Adjacent markets"
    - threats: "Risks you might miss"

why_it_matters:
  - "Not just 'where you are' but 'where to fly next'"
  - "Anticipate unicorn path"
  - "Build monopoly, not just company"
```

---

## War Room MVP: What to Build First

### Phase 1: Basic Dashboard (Week 1-2)
```yaml
goal: "See key metrics at a glance"

metrics_to_track:
  survival:
    - cash_in_bank: "$X"
    - burn_rate: "$X/month"
    - runway: "X months"
    
  pmf:
    - total_users: "X users"
    - paying_users: "X paying"
    - mrr: "$X/month"
    - churn: "X%"
    
tech_stack:
  - frontend: "React dashboard"
  - backend: "PostgreSQL queries"
  - charts: "Recharts or Chart.js"
  
update_frequency: "Once per day (morning)"
```

### Phase 2: Real-Time Updates (Week 3-4)
```yaml
goal: "Live data, not daily snapshots"

add:
  - websocket_updates: "Push new data to browser"
  - minute_by_minute: "Users, revenue, errors"
  - alerts: "Email/SMS when threshold crossed"
  
tech_stack:
  - websockets: "Socket.io or Pusher"
  - background_jobs: "Calculate metrics every minute"
  
update_frequency: "Every 1-5 minutes"
```

### Phase 3: Competitor Tracking (Week 5-6)
```yaml
goal: "Know what competitors are doing"

add:
  - competitor_scraper: "Monitor their websites"
  - feature_diff: "What's new since last week?"
  - pricing_tracker: "Price changes"
  
tech_stack:
  - scraping: "Puppeteer or Playwright"
  - storage: "PostgreSQL"
  - alerts: "When competitor ships something"
```

---

## War Room Technical Architecture

### Data Collection Layer
```typescript
// /lib/war-room/collectors/

// Internal metrics collector
class InternalMetricsCollector {
  async collect() {
    const metrics = {
      cash: await this.getCashBalance(),
      burn: await this.calculateBurnRate(),
      users: await this.getUserStats(),
      mrr: await this.calculateMRR(),
      churn: await this.calculateChurn()
    };
    
    await this.saveMetrics(metrics);
    await this.checkAlerts(metrics);
    
    return metrics;
  }
  
  private async getCashBalance() {
    // Query bank API or manual input
  }
  
  private async calculateBurnRate() {
    // Last 30 days of expenses
  }
  
  // ... other methods
}

// Competitor metrics collector
class CompetitorCollector {
  async collect() {
    for (const competitor of COMPETITORS) {
      const data = await this.scrapeCompetitor(competitor);
      await this.detectChanges(data);
      await this.alertIfNeeded(data);
    }
  }
}

// Adamus health collector
class AdamusHealthCollector {
  async collect() {
    const health = {
      capabilities: await this.countCapabilities(),
      velocity: await this.calculateVelocity(),
      security: await this.calculateSecurityScore(),
      cost: await this.calculateCostSavings()
    };
    
    return health;
  }
}
```

### Metrics Storage
```sql
-- /db/schema/war_room.sql

CREATE TABLE internal_metrics (
  id UUID PRIMARY KEY,
  timestamp TIMESTAMP NOT NULL,
  
  -- Survival
  cash_balance DECIMAL,
  burn_rate DECIMAL,
  runway_months INT,
  
  -- PMF
  total_users INT,
  active_users INT,
  paying_users INT,
  mrr DECIMAL,
  churn_rate DECIMAL,
  
  -- Productivity
  features_shipped INT,
  velocity DECIMAL,
  bugs_open INT,
  
  -- Adamus
  adamus_capabilities INT,
  adamus_velocity DECIMAL,
  security_score DECIMAL
);

CREATE TABLE competitor_snapshots (
  id UUID PRIMARY KEY,
  competitor_name VARCHAR(255),
  timestamp TIMESTAMP NOT NULL,
  
  features JSONB,  -- List of features detected
  pricing JSONB,   -- Pricing tiers
  metadata JSONB   -- Other data
);

CREATE TABLE alerts (
  id UUID PRIMARY KEY,
  timestamp TIMESTAMP NOT NULL,
  severity VARCHAR(50),  -- 'critical', 'warning', 'info'
  category VARCHAR(50),  -- 'survival', 'pmf', 'competitor'
  message TEXT,
  resolved BOOLEAN DEFAULT false
);
```

### Dashboard Frontend
```typescript
// /app/war-room/page.tsx

export default function WarRoomDashboard() {
  const metrics = useWarRoomMetrics(); // Real-time via WebSocket
  
  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Layer 1: Internal Vitals */}
      <div className="col-span-3">
        <h2>Internal Vitals</h2>
        
        <div className="grid grid-cols-3 gap-4">
          <SurvivalMetrics data={metrics.survival} />
          <PMFMetrics data={metrics.pmf} />
          <ProductivityMetrics data={metrics.productivity} />
        </div>
      </div>
      
      {/* Layer 2: External Radar */}
      <div className="col-span-3">
        <h2>External Radar</h2>
        
        <CompetitorActivity data={metrics.competitors} />
        <ThreatLandscape data={metrics.threats} />
      </div>
      
      {/* Layer 3: Strategic Horizon */}
      <div className="col-span-3">
        <h2>Strategic Horizon</h2>
        
        <UnicornIndex data={metrics.unicorn} />
        <MonopolyIndex data={metrics.monopoly} />
        <AIGeneralSuggestions data={metrics.suggestions} />
      </div>
      
      {/* Alerts */}
      <div className="col-span-3">
        <AlertsFeed alerts={metrics.alerts} />
      </div>
    </div>
  );
}
```

---

## War Room Daily Workflow

### 6:00 AM: Automated Report Generation
```yaml
what_happens:
  - metrics_collected: "From all sources"
  - report_generated: "Daily brief"
  - email_sent: "To Augustus's inbox"
  
report_contains:
  - headline_metrics: "Cash, users, MRR"
  - changes_from_yesterday: "What moved?"
  - alerts: "Anything critical?"
  - top_3_priorities: "What to focus on today"
```

### 8:00 AM: Augustus Review (15 min)
```yaml
augustus_opens_war_room:
  - scans_vitals: "Is anything red?"
  - reads_alerts: "Critical issues?"
  - reviews_competitors: "What did they do?"
  - checks_priorities: "What's most important?"
  
augustus_decides:
  - approve_priorities: "Yes, focus on these 3 things"
  - adjust_priorities: "No, actually do X instead"
  - escalate: "Red alert needs immediate attention"
  - delegate: "Adamus, handle this please"
```

### Throughout Day: Real-Time Monitoring
```yaml
war_room_updates:
  - every_5_minutes: "Refresh metrics"
  - push_alerts: "If threshold crossed"
  - augustus_checks: "Whenever he wants"
  
examples:
  - 11am: "MRR just crossed $1K - celebration!"
  - 2pm: "Error rate spiking - investigate"
  - 4pm: "Competitor launched new feature - react"
```

### 6:00 PM: End of Day Summary
```yaml
adamus_reports:
  - what_shipped: "Features/fixes deployed"
  - what_changed: "Metrics delta from morning"
  - what_learned: "Insights from the day"
  - tomorrow_priorities: "Based on today's data"
  
augustus_reviews:
  - 10_minutes: "Quick scan"
  - adjustments: "Change course if needed"
  - sleep_well: "Knowing nothing on fire"
```

---

## Alert Thresholds

### Critical Alerts (Immediate Action)
```yaml
survival:
  - cash_below: "$10K"
  - burn_rate_increase: ">50% from baseline"
  - runway_below: "3 months"
  
pmf:
  - churn_spike: ">20% in one day"
  - mrr_drop: ">$1K in one day"
  - zero_signups: "24 hours without new user"
  
technical:
  - error_rate: ">5%"
  - uptime: "<95%"
  - security_breach: "Any breach"
```

### Warning Alerts (Monitor Closely)
```yaml
survival:
  - burn_increase: ">25% from baseline"
  - runway_below: "6 months"
  
pmf:
  - churn_high: ">10%"
  - growth_stalling: "Flat for 7 days"
  
technical:
  - slow_response: ">3s average"
  - cost_spike: ">$50/day on APIs"
```

### Info Alerts (Good to Know)
```yaml
growth:
  - new_milestone: "100 users, $1K MRR, etc."
  - viral_moment: "Mentioned on Twitter/HN"
  
competitor:
  - new_feature: "Competitor shipped something"
  - funding: "Competitor raised"
```

---

## War Room Integration with Adamus

### Adamus Uses War Room Data
```yaml
for_self_improvement:
  - sees_cost_spike: "Optimize LLM calls"
  - sees_slow_response: "Improve performance"
  - sees_security_issue: "Build defense system"
  
for_genre_building:
  - sees_churn_high: "Focus on retention features"
  - sees_competitor_feature: "Clone and improve"
  - sees_growth_opportunity: "Suggest expansion"
```

### War Room Tracks Adamus
```yaml
adamus_metrics:
  - capabilities_built: "How complete is Adamus?"
  - self_improvement_rate: "How fast learning?"
  - security_score: "How protected?"
  - cost_efficiency: "How much $ saved?"
  
display:
  - separate_section: "Adamus Health"
  - trends: "Is Adamus getting better?"
  - compare_to_goals: "On track for Week 16?"
```

---

## Advanced War Room Features (Post-MVP)

### AI General Integration
```yaml
what:
  - ai_analyzes_data: "Pattern recognition"
  - ai_suggests_moves: "Pivots, expansions"
  - ai_predicts_future: "Trend forecasting"
  
example:
  - pattern: "Users who try Feature X convert 3x more"
  - suggestion: "Focus marketing on Feature X"
  - prediction: "At current rate, $10K MRR in 47 days"
```

### Scenario Planning
```yaml
what:
  - what_if_analysis: "If we raise prices 20%?"
  - sensitivity_testing: "How much churn can we handle?"
  - path_planning: "What sequence gets to $100K MRR fastest?"
  
implementation:
  - monte_carlo: "Simulate 1000 scenarios"
  - show_paths: "Visual roadmap"
```

### Team Dashboards (When You Hire)
```yaml
role_specific_views:
  - engineering: "Velocity, bugs, uptime"
  - marketing: "CAC, LTV, conversion"
  - customer_success: "Churn, satisfaction, support"
  
all_feed_into:
  - augustus_view: "Strategic overview"
```

---

## Building War Room with Claude Code

### Week 1: Basic Dashboard
```bash
claude-code "Build War Room dashboard:

Phase 1 (this week):
- Dashboard showing: cash, burn, users, MRR, churn
- Update once per day
- Simple React interface

Follow /docs/development-standards.md for frontend patterns."
```

### Week 2: Real-Time Updates
```bash
claude-code "Add real-time updates to War Room:

- WebSocket connection
- Update metrics every 5 minutes
- Push notifications for alerts

Integrate with existing dashboard."
```

### Week 3: Alerts
```bash
claude-code "Add alert system to War Room:

- Define thresholds (critical, warning, info)
- Check metrics against thresholds
- Send email/SMS when crossed
- Show alert feed in dashboard

Integrate with existing real-time system."
```

---

## The Bottom Line

**War Room Purpose**: Daily steering, not quarterly surprises

**MVP Scope**: Internal vitals + basic alerts (Week 1-3)

**Tech**: React + PostgreSQL + WebSockets

**Result**: Augustus spends 15 min/day steering, knows everything

**Start**: After Genre MVP has users (need data to track)

**Then**: Expand to competitor tracking, strategic horizon, AI suggestions

**Eventually**: Full cockpit with AI General analyzing and suggesting moves

**This is how Augustus stays omniscient while Adamus handles execution.**
