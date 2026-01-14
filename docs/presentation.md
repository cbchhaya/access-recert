---
marp: true
theme: default
paginate: true
header: 'Access Recertification Assurance System (ARAS)'
footer: 'Confidential | January 2025'
style: |
  section {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  h1 {
    color: #1a365d;
  }
  h2 {
    color: #2c5282;
  }
  table {
    font-size: 0.8em;
  }
  .highlight {
    background-color: #ebf8ff;
    padding: 1em;
    border-radius: 8px;
  }
---

<!-- _class: lead -->
# Access Recertification Assurance System
## AI-Assisted Risk-Based Access Certification

**Transforming compliance theater into meaningful security**

January 2025

---

# The Problem We're Solving

## Access certification has become security theater

| What Should Happen | What Actually Happens |
|-------------------|----------------------|
| Managers thoughtfully review each entitlement | Managers approve everything to clear their queue |
| Inappropriate access is identified and revoked | 97-99% of access is approved unchanged |
| Security posture improves after each campaign | Nothing changes; the same issues persist |

**Result**: Compliance checkbox exercise that provides false assurance

---

# The Evidence is Clear

## Industry data on certification failure

| Metric | Value | Source |
|--------|-------|--------|
| Typical approval rate | **97-99%** | Industry benchmarks |
| Typical revocation rate | **2-3%** | Pathlock, Gartner |
| Employees with unneeded access | **50%** | IBM, Ponemon |
| Average permissions per user | **96,000** | Veza 2025 Report |

> "Access review fatigue is one of the most common causes of audit failure"
> — IDPro Body of Knowledge

---

# Why Does This Happen?

## Root causes of rubber-stamping

**Volume overload**
- Managers review 50-200 items per direct report
- Multiple campaigns per year
- Limited time, competing priorities

**Lack of context**
- "User X has Role Y" — but what does that mean?
- No indication of whether access is appropriate
- No comparison to peers or usage data

**Misaligned incentives**
- Revoking access → potential disruption, complaints
- Approving access → no immediate consequence

---

# The Opportunity

## AI can transform this process

What if we could:

- **Identify** which access is typical vs. unusual for each user
- **Detect** dormant access that's never actually used
- **Prioritize** reviewer attention on items that matter
- **Automate** low-risk certifications with full audit trail
- **Explain** why access is flagged to help decision-making

**The technology exists. The question is: how do we implement it responsibly?**

---

# Our Approach: Assurance Scoring

## A single score representing confidence in access appropriateness

```
Assurance Score = f(Peer Typicality, Sensitivity, Usage)
```

| Component | What It Measures | Score Impact |
|-----------|------------------|--------------|
| **Peer Typicality** | How common is this access among similar users? | Higher typicality → higher score |
| **Resource Sensitivity** | How critical/sensitive is the resource? | Higher sensitivity → **ceiling on score** |
| **Usage Activity** | Is the access actually being used? | Dormant access → lower score |

---

# Key Innovation #1: Sensitivity as a Ceiling

## Typical ≠ Safe

**The problem with weighted scores:**
If 80% of a department has excessive access to a critical system, a weighted approach would auto-approve it.

**Our solution:**
Sensitivity acts as an **absolute ceiling**, not a weight.

| Sensitivity | Max Possible Score | Auto-Cert Eligible |
|-------------|-------------------|-------------------|
| Public | 100 | Yes |
| Internal | 85 | Yes (if graduated) |
| Confidential | 50 | No |
| **Critical** | **0** | **Never** |

---

# Key Innovation #2: Convergence-Based Graduation

## Auto-certification must be earned, not configured

**Traditional approach:**
Admin sets threshold → auto-certification enabled → hope it works

**Our approach:**

```
Observation → Metrics Tracking → Eligibility → Human Approval → Graduation → Monitoring
     ↑                                                                           │
     └─────────────────── Automatic Rollback if thresholds breached ─────────────┘
```

Categories graduate to auto-certification only when:
- **>90% recommendation acceptance** over 3+ campaigns
- **<10% override rate**
- **<15% false positive rate**
- **Human governance sign-off**

---

# Key Innovation #3: Multi-Algorithm Clustering

## Different algorithms, different insights

We don't trust a single algorithm to define "peers"

| Algorithm | Approach | Strength |
|-----------|----------|----------|
| K-means | Distance to centroid | Fast, interpretable |
| Hierarchical | Tree-based grouping | Captures org structure |
| DBSCAN | Density-based | Natural outlier detection |
| Graph Community | Network relationships | Actual collaboration patterns |

**When algorithms disagree significantly → flag for human review**

---

# Key Innovation #4: Three Lines of Defense

## Built-in governance, not bolted on

| Line | Actor | Capability |
|------|-------|------------|
| **First** | Manager / Resource Owner | Review recommendations, make decisions |
| **Second** | Risk / Compliance | Sample auto-approved items, challenge decisions |
| **Third** | Audit | Full trail, explanation for any decision |

**Every auto-certified item:**
- Logged with full score breakdown
- Available for second-line sampling (min 5%)
- Explainable on demand

---

# How It Works: The User Experience

## For the Reviewer

**Before (Traditional):**
```
☐ John Smith - AWS-Prod-Admin-Role     [Approve] [Revoke]
☐ John Smith - GitHub-Repo-Access      [Approve] [Revoke]
☐ John Smith - Salesforce-Standard     [Approve] [Revoke]
... 47 more items ...
```

**After (ARAS):**
```
⚠️ HIGH PRIORITY (3 items need your attention)

John Smith - AWS-Prod-Admin-Role       Score: 23
├─ Only 8% of peers have this access
├─ Last used: 14 months ago
├─ Sensitivity: Critical (requires review)
└─ [Certify with justification] [Revoke]

✅ AUTO-CERTIFIED (47 items) - Click to review
```

---

# How It Works: Scoring Example

## Real scenario breakdown

| User | Access | Peer % | Sensitivity | Usage | Score | Action |
|------|--------|--------|-------------|-------|-------|--------|
| Alice (Engineer) | GitHub team repo | 95% | Internal | Daily | **85** | Auto-certify |
| Bob (Engineer) | AWS Prod Admin | 8% | Critical | Never | **0** | Review required |
| Carol (Analyst) | Salesforce Reports | 72% | Confidential | Weekly | **42** | Review recommended |
| Dave (Manager) | HR Portal Read | 88% | Confidential | Monthly | **38** | Review recommended |

**Note:** Bob's access scores 0 despite any typicality because Critical sensitivity = ceiling of 0

---

# Competitive Differentiation

## What makes ARAS different

| Capability | Market Status | ARAS |
|------------|---------------|------|
| Peer analysis | Common (SailPoint, Saviynt) | ✓ Multi-algorithm |
| Risk weighting | Common | ✓ **Sensitivity ceiling** |
| Auto-certification | Common | ✓ **Convergence-based graduation** |
| Usage analytics | Emerging | ✓ Dormancy as primary signal |
| Governance guardrails | Rare | ✓ **Automatic rollback** |
| Multi-algorithm consensus | None | ✓ **Disagreement detection** |

**No vendor offers convergence-based graduation with automatic rollback**

---

# Expected Outcomes

## Measurable improvement

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| Time per decision | 30 sec | 15 sec | **50% reduction** |
| Items requiring human review | 100% | 30-40% | **60-70% reduction** |
| Revocation rate | 2-3% | 10-15% | **5x increase** |
| Campaign completion time | 4 weeks | 1 week | **75% reduction** |
| Identity-related audit findings | Baseline | -80% | **Significant reduction** |

---

# Regulatory Alignment

## This approach has support

**FFIEC IT Examination Handbook:**
> "The frequency and depth of each area's audit will vary according to the risk assessment of that area."

**IDPro Body of Knowledge:**
> "Rather than reviewing all access indiscriminately, organizations should focus on high-risk permissions."

**SR 11-7 (Financial Services):**
Provides framework for AI/ML model governance that we follow

**Key:** Risk-based certification is accepted when properly governed with full audit trail

---

# Implementation Phases

## Measured, phased approach

| Phase | Duration | Mode | Outcome |
|-------|----------|------|---------|
| **1. Shadow** | 3-6 months | AI recommends, humans decide everything | Baseline metrics, model tuning |
| **2. Assisted** | 3-6 months | Recommendations visible, tracked | Measure acceptance, build trust |
| **3. Graduated** | Ongoing | Auto-cert for qualifying categories | Efficiency gains with governance |
| **4. Optimization** | Ongoing | Expand categories, refine model | Continuous improvement |

**No auto-certification until demonstrated performance + human approval**

---

# Architecture Overview

## System components

```
┌─────────────────────────────────────────────────────────────────┐
│                      Data Sources                               │
│  HR System │ Azure AD │ AWS │ GitHub │ Activity Logs │ Sentinel │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Analytics Engine                              │
│  Peer Clustering │ Assurance Scoring │ Anomaly Detection        │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API / Backend                                │
│  Campaign Mgmt │ Review Queue │ Audit Trail │ Graduation Logic  │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    User Interfaces                              │
│  Reviewer Dashboard │ Admin Console │ Compliance View │ Chat    │
└─────────────────────────────────────────────────────────────────┘
```

---

# Conversational Interface

## Natural language access to insights

**Reviewer:** "Show me my highest priority items"

**ARAS:** "You have 3 high-priority items requiring review:
1. Bob Smith - AWS Prod Admin (Score: 23) - unusual for peer group, dormant
2. Alice Chen - Snowflake DBA (Score: 31) - 180 days unused
3. ..."

**Compliance:** "Why was Carol's Salesforce access auto-approved?"

**ARAS:** "Carol's access scored 87/100:
- 94% of her team has this access
- Sensitivity: Internal
- Active usage: 45 logins in 30 days
This exceeded the 80-point auto-certification threshold for this graduated category."

---

# Demo Architecture

## What we'll demonstrate

| Component | Technology | Status |
|-----------|------------|--------|
| Synthetic Data | 10K employees, 500K access grants | Ready |
| Analytics Engine | Python + scikit-learn | In development |
| Backend API | FastAPI | In development |
| Frontend UI | React | In development |
| Conversational AI | Claude API | In development |
| Local Access | ngrok | Ready |

**Demo shows full workflow:** Campaign → Scoring → Review → Decision → Audit

---

# Key Differentiators Summary

## Why ARAS stands apart

1. **Sensitivity ceiling, not weight**
   - Critical access NEVER auto-certifies regardless of typicality

2. **Earned automation, not configured**
   - Categories must demonstrate performance to graduate

3. **Multi-algorithm robustness**
   - Disagreement triggers human review, not forced consensus

4. **Automatic rollback**
   - Quality degradation returns category to human review

5. **Full explainability**
   - Every decision traceable and justifiable

---

# Addressing Concerns

## Common objections and responses

**"Typical doesn't mean safe"**
→ Correct. That's why sensitivity is a ceiling, not a weight.

**"Auto-certification removes human judgment"**
→ It focuses human judgment. Current 98% approval isn't "judgment."

**"Auditors won't accept this"**
→ Risk-based approaches are accepted when governed. Full audit trail provided.

**"The model will drift"**
→ Continuous monitoring + automatic rollback = fail-safe design.

**"This just shifts work to IAM team"**
→ Partially true, but scales sublinearly vs. reviewer burden.

---

# Next Steps

## Path forward

**Immediate:**
1. Review position paper and provide feedback
2. Run synthetic data generation, validate patterns
3. Finalize technical stack decisions

**Short-term:**
4. Build analytics engine (clustering + scoring)
5. Build backend API
6. Build reviewer dashboard

**Medium-term:**
7. Implement conversational interface
8. Integration testing with demo data
9. Prepare for stakeholder demo

---

# Discussion

## Questions for consideration

1. **Sensitivity classification**: Who owns this in your organization?

2. **Graduation governance**: Who should approve auto-certification enablement?

3. **Regulatory engagement**: Should we engage internal audit early?

4. **Pilot scope**: Which systems/populations for initial deployment?

5. **Success criteria**: What metrics matter most to you?

---

<!-- _class: lead -->
# Thank You

## Access Recertification Assurance System

**Transforming compliance theater into meaningful security**

Questions and discussion welcome

---

# Appendix: Detailed Scoring Model

## Component calculations

**Peer Typicality (0-1):**
```
typicality = peers_with_same_access / total_peers_in_cluster
```

**Sensitivity Multiplier:**
| Level | Multiplier |
|-------|------------|
| Public | 1.0 |
| Internal | 0.85 |
| Confidential | 0.5 |
| Critical | 0.0 |

**Usage Factor (0-1):**
| Pattern | Factor |
|---------|--------|
| Active (used in 30d) | 1.0 |
| Recent (used in 90d) | 0.8 |
| Stale (used in 1yr) | 0.5 |
| Dormant (never/1yr+) | 0.1 |

---

# Appendix: Graduation Criteria

## Metrics required for auto-certification

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Recommendation acceptance | >90% over 3 campaigns | Reviewers trust the model |
| Override rate | <10% | Few disagreements |
| False positive rate | <15% | Flagged items are genuinely unusual |
| Minimum observations | 100+ decisions | Statistical significance |
| Algorithm consensus | >80% | Multiple methods agree |
| Cluster stability | <10% churn | Peer groups are stable |

**All criteria must be met + human governance approval**

---

# Appendix: Data Sources Modeled

## Enterprise systems in demo

| System | Access Types | Activity Signals |
|--------|--------------|------------------|
| Azure AD | Groups, Apps, Roles | Sign-in logs |
| AWS IAM | Roles, Policies, Permission Sets | CloudTrail, Last Accessed |
| GCP IAM | Roles, Service Accounts | Audit Logs |
| GitHub | Orgs, Teams, Repos | Commits, PRs |
| Confluence | Spaces, Pages | Views, Edits |
| Jira | Projects, Security | Ticket activity |
| ServiceNow | Roles, Catalog | Requests |
| Salesforce | Profiles, Permission Sets | Record access |
| SAP | Roles, Auth Objects | Transaction logs |
| Snowflake | Database grants | Query history |

---

# Appendix: Risk Signals

## Security context from Sentinel-like systems

| Signal Type | Severity | Impact on Score |
|-------------|----------|-----------------|
| Impossible travel | High | Flag for immediate review |
| Unusual access pattern | Medium | Reduce assurance score |
| Off-hours access | Low | Contextual consideration |
| Bulk download | High | Flag for review |
| Privilege escalation attempt | Critical | Mandatory review |
| MFA fatigue | Medium | Security concern flag |

**Risk signals supplement peer analysis—they don't replace it**

---

# Appendix: Anomaly Types Seeded

## Patterns in synthetic data for testing

| Anomaly | Prevalence | Purpose |
|---------|------------|---------|
| Stale access after job transfer | 40% of transfers | Test temporal detection |
| Dormant privileged accounts | 25% of privileged | Test usage detection |
| SoD violations | 1.5% of users | Test toxic combination detection |
| Outlier access for role | 8% of users | Test peer analysis |

**Demo data includes realistic anomaly distribution for validation**
