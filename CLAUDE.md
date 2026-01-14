# Access Recertification Assurance System (ARAS)

## Project Overview

ARAS is an AI-assisted access recertification system that calculates assurance scores for access grants based on peer proximity analysis, enabling risk-based certification that focuses human attention on outlier access while maintaining full audit compliance.

This is a **demonstration system** showcasing modern access recertification practices. It is designed to run locally and be accessed via ngrok for demo purposes, but the architecture supports enterprise deployment.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Literature Foundation](#literature-foundation)
3. [Competitive Analysis](#competitive-analysis)
4. [Our Differentiators](#our-differentiators)
5. [Core Design Principles](#core-design-principles)
6. [Assurance Scoring Model](#assurance-scoring-model)
7. [Peer Proximity Model](#peer-proximity-model)
8. [Convergence-Based Graduation](#convergence-based-graduation)
9. [Three Lines of Defense](#three-lines-of-defense)
10. [Conversational Interface](#conversational-interface)
11. [Micro-Certifications Architecture](#micro-certifications-architecture)
12. [Plugin Architecture](#plugin-architecture)
13. [Data Models](#data-models)
14. [Regulatory Considerations](#regulatory-considerations)
15. [Success Metrics / KPIs](#success-metrics--kpis)
16. [Acknowledged Limitations](#acknowledged-limitations)
17. [Position Paper](#position-paper)
18. [Technical Stack](#technical-stack)
19. [References](#references)

---

## Problem Statement

### The Scale of the Challenge

- Enterprise organizations manage **230+ billion permissions** across their environments
- The average worker holds **96,000 permissions** spanning applications, data stores, and infrastructure
- **36% of organizations** still use manual spreadsheets for access reviews; only 17% use IGA platforms
- Application onboarding queues of **600+ applications** with **8+ year projected timelines**

### The Rubber-Stamp Epidemic

Traditional access certification has deteriorated into a compliance checkbox exercise:

- Traditional certification revocation rates of only **2-3%** (indicating rubber-stamping)
- Access review fatigue is "one of the most common causes of audit failure"
- Managers certify hundreds of items "with little understanding of what those permissions actually enable"
- **1 in 2 employees** retain access they do not need after role changes

### The Cost of Failure

- T-Mobile was fined **$60 million** for inability to prevent unauthorized access
- NYDFS violations can result in **$75,000 daily fines** for knowing and willful violations
- **39% of organizations** experienced security or compliance issues tied to governance gaps during cloud migration
- Dormant accounts doubled year-over-year; **78,000 former employees** retained active credentials in one study

---

## Literature Foundation

### Academic Grounding

| Research | Contribution | Relevance |
|----------|--------------|-----------|
| Bolton & Hand (2001) - "Peer Group Analysis: Local Anomaly Detection in Longitudinal Data" | Foundational methodology for detecting objects that behave differently from similar peers | Core theoretical basis for our peer proximity model |
| ACM RoleMiner | Bottom-up approaches using existing permissions to derive roles | Validates using access patterns to understand normal behavior |
| Purdue/IBM Role Mining Evaluation | Multiple algorithms (ORCA, CompleteMiner, FastMiner) evaluated for role mining | Supports multi-algorithm approach |
| UEBA Research (ScienceDirect) | ML-based deviation detection for user behavior analytics | Validates statistical approach to anomaly detection |

### Regulatory Support

| Framework | Relevant Guidance |
|-----------|-------------------|
| **FFIEC IT Examination Handbook** | Explicitly endorses risk-based auditing: "The frequency and depth of each area's audit will vary according to the risk assessment of that area" |
| **IDPro Body of Knowledge** | Recommends organizations "focus on high-risk permissions" rather than reviewing all access indiscriminately |
| **SR 11-7 Model Risk Management** | For financial services, AI/ML systems require formal model risk management including validation, documentation, governance, and monitoring |
| **SOX Section 404** | Requires complete audit trails with timestamps, approvals, and justifications; does not prohibit risk-based sampling |
| **GDPR Article 5** | Accountability principle requires demonstrating compliance; automated decisions affecting individuals require transparency |

### Industry Validation

Major IGA vendors have implemented similar capabilities:

- **SailPoint**: AI-driven identity security with peer group analysis since 2017; explainable AI in 2025
- **Saviynt**: Third-generation peer analytics engine; claims 75% improvement in revocation of unnecessary critical access
- **Gartner 2025 Market Guide**: Identifies AI-driven enhancements as key IGA innovation trend

---

## Competitive Analysis

### Vendor Landscape

| Vendor | AI Capabilities | Peer Analysis | Auto-Certification | Key Limitation |
|--------|-----------------|---------------|-------------------|----------------|
| **SailPoint** | Access Modeling, Outlier Risk Scores, Harbor Pilot | Yes, collaborative filtering | Yes, low-risk auto-approval | Roles via automation cannot be revoked |
| **Saviynt** | 14+ risk signals, Trust Scoring | 3rd gen, 40+ HR attributes | Yes, threshold-based | Weighted scores can override sensitivity |
| **Oracle** | Role Intelligence, GenAI descriptions | Yes, outlier detection | Event-based micro-certs | Oracle ecosystem focus |
| **IBM Verify** | Business-activity based modeling | Limited emphasis | Workflow-based | Legacy architecture |
| **Veza** | Access Graph (150+ systems), Access AI | Yes, natural language | Access AuthZ automation | Acquired by ServiceNow |
| **ConductorOne** | AI Copilot, AI agents | Yes, peer comparisons | Bulk approvals | Newer, smaller ecosystem |
| **Lumos** | Agentic UARs, Albus AI | Yes, multiple signals | Autonomous agents | Very new (Dec 2025) |
| **Pathlock** | Risk + usage assessment | Yes | Risk-tiered | Focused on ERP |

### Identified Market Gaps

| Gap | Evidence | Addressed by ARAS |
|-----|----------|-------------------|
| **Sensitivity as absolute ceiling** | All vendors use weighted scores where typicality can override sensitivity | Yes - sensitivity is a hard constraint |
| **Convergence-based graduation** | No vendor tracks metrics per category to earn auto-certification | Yes - formal graduation framework |
| **Human sign-off for auto-cert enablement** | Auto-cert thresholds set administratively, not through governance | Yes - requires approval |
| **Automatic rollback** | No vendor documents rollback when quality degrades | Yes - threshold breach triggers rollback |
| **Multi-algorithm disagreement detection** | All use single clustering approach | Yes - ensemble with disagreement flagging |

---

## Our Differentiators

### 1. Sensitivity as a Ceiling, Not a Weight

**Problem with weighted scores**: In existing solutions, a highly typical access to a critical system can still auto-approve if typicality score is high enough.

**Our approach**: Sensitivity acts as an **absolute ceiling**. Critical/Restricted sensitivity access **NEVER** auto-certifies regardless of typicality or usage scores.

### 2. Convergence-Based Graduation

**Problem**: Auto-certification thresholds are set by administrators based on assumptions.

**Our approach**: Categories must **earn** auto-certification rights by demonstrating:
- >90% recommendation acceptance rate over 3+ campaigns
- <10% override rate
- <15% false positive rate
- Human governance sign-off required
- Automatic rollback if metrics degrade

### 3. Multi-Algorithm Disagreement Detection

**Problem**: Single clustering algorithms can produce unreliable peer groupings for edge cases.

**Our approach**: Run multiple algorithms (K-means, hierarchical, DBSCAN, graph community) in parallel. When they **disagree significantly**, flag for human review rather than confidently applying wrong recommendation.

### 4. Three Lines of Defense by Design

**Problem**: Most solutions focus on first-line (manager review); second/third lines are afterthoughts.

**Our approach**: Built-in support for:
- First line: Manager/resource owner decisions
- Second line: Risk/compliance sampling of auto-approved items (min 5%)
- Third line: Full audit trail, any decision explainable

### 5. Governed Automation

**Problem**: "AI-assisted" often means "configured and deployed" without ongoing governance.

**Our approach**: Automation is **measured, governed, and automatically constrained**:
- Metrics tracked continuously
- Human approval gates
- Automatic rollback mechanisms
- Full audit trail

---

## Core Design Principles

### 1. Risk Stratification, Not Binary Classification

Access is categorized into risk tiers:

| Tier | Criteria | Certification Approach |
|------|----------|----------------------|
| Critical | Privileged, SOX-relevant, sensitive data | Always manual review |
| High | Cross-functional, elevated permissions | Manual with AI context |
| Standard | Peer-aligned, standard business | AI-assisted, can graduate to auto |
| Low | Read-only, common tools | Can auto-certify with sampling |

### 2. Explainable Recommendations

Every recommendation includes:
- Peer group composition and how user was assigned
- Factor contributions (typicality, sensitivity, usage)
- Algorithm consensus level
- Historical context

### 3. Human-in-the-Loop Architecture

- Reviewers can always override AI recommendations
- Auto-certifications require second-line sampling
- Disagreement patterns feed back into model improvement
- Override escalation path defined

### 4. Conservative Automation

- Maximum auto-certification rate: **70%**
- NEVER auto-certify: privileged access, SOX entitlements, sensitive data, SoD conflicts
- Shadow/recommendation period before any auto-certification

### 5. Multi-Signal Risk Assessment

Peer proximity is ONE input, combined with:
- Resource sensitivity ratings
- Usage analytics (is access actually used?)
- SoD conflict detection
- Dormancy signals
- Risk signals (from security tools)

---

## Assurance Scoring Model

### The Formula

```
Assurance Score = f(Peer Typicality, Sensitivity⁻¹, Usage Activity)
```

Where:
- **Peer Typicality** (0-1): How common is this access among similar users?
- **Sensitivity** (0-1, inverted): How sensitive/critical is the resource?
- **Usage Activity** (0-1): Is this access being used appropriately?

### Component Details

#### Peer Typicality (0-1)

| Metric | Score |
|--------|-------|
| >80% of peers have this access | 0.9-1.0 |
| 50-80% of peers | 0.6-0.9 |
| 20-50% of peers | 0.3-0.6 |
| <20% of peers | 0.0-0.3 |

#### Resource Sensitivity (Inverted)

| Level | Examples | Multiplier |
|-------|----------|------------|
| Public | Read-only wikis, company announcements | 1.0 |
| Internal | Standard business apps, team repos | 0.8 |
| Confidential | Customer data, financial systems | 0.4 |
| Critical | Production admin, privileged access, SOX-relevant | **0.0** (blocks auto-cert) |

**Key**: Critical sensitivity = 0.0 multiplier means **automatic manual review** regardless of other factors.

#### Usage Activity (0-1)

| Usage Pattern | Score | Interpretation |
|---------------|-------|----------------|
| Regular use matching peers | 1.0 | Strong legitimacy signal |
| Occasional use | 0.7 | Probably needed |
| Used once then dormant | 0.3 | Questionable |
| Never used | 0.1 | Why do they have this? |

### Score Interpretation

| Score Range | Classification | Action |
|-------------|----------------|--------|
| 80-100 | High Assurance | Eligible for auto-certification (if category graduated) |
| 50-79 | Medium Assurance | Review recommended, context provided |
| 0-49 | Low Assurance | Review required, flagged as outlier |

### Why This Works

The insight: **We use measurable proxy signals that correlate with risk without requiring full threat modeling.**

| Scenario | Typicality | Sensitivity | Usage | Score | Action |
|----------|------------|-------------|-------|-------|--------|
| Everyone has Confluence read | High | Low | Active | ~85 | Auto-certify |
| Dev has GitHub repo access | High | Medium | Active | ~70 | Review recommended |
| Dev has AWS prod admin (unusual) | Low | Critical | Any | **0** | Review required |
| Everyone has excessive S3 access | High | High | Mixed | ~40 | Review required |

The last row is critical: **Sensitivity overrides typicality** for critical resources.

---

## Peer Proximity Model

### Multi-Dimensional Similarity

"Peer" is not binary but a **continuous similarity score** across multiple dimensions:

```
Proximity(A, B) = w₁·Structural + w₂·Functional + w₃·Behavioral + w₄·Temporal
```

### Dimension Details

#### 1. Structural Proximity (Default: 25%)

| Factor | Encoding | Similarity Calculation |
|--------|----------|------------------------|
| Same direct manager | Binary | 1.0 if same, 0.0 if not |
| Manager distance | Hierarchy hops | 1 / (1 + hops) |
| Same team | Binary | 1.0 / 0.0 |
| Same sub-LOB | Binary | 1.0 / 0.0 |
| Same LOB | Binary | 1.0 / 0.0 |
| Same location/region | Categorical | 1.0 same / 0.5 region / 0.0 different |

#### 2. Functional Proximity (Default: 35%)

| Factor | Encoding | Similarity Calculation |
|--------|----------|------------------------|
| Job title | Text | Embedding cosine similarity |
| Job family/code | Categorical hierarchy | Jaccard on hierarchy path |
| Cost center | Categorical | 1.0 if same, partial by hierarchy |
| Project assignments | Set | Jaccard index |

#### 3. Behavioral Proximity (Default: 30%)

| Factor | Encoding | Similarity Calculation |
|--------|----------|------------------------|
| Access overlap | Set of entitlements | Jaccard index |
| Activity pattern | Usage frequency vector | Cosine similarity |
| Usage intensity | Normalized counts | Euclidean distance → similarity |

#### 4. Temporal Proximity (Default: 10%)

| Factor | Encoding | Similarity Calculation |
|--------|----------|------------------------|
| Tenure | Days since hire | Gaussian similarity |
| Time in current role | Days | Gaussian similarity |
| Hire cohort | Quarter/year | 1.0 same, decay over time |

### Weight Tuning

Weights are configurable via UI with pairwise interaction modifiers:

```python
class PeerProximityConfig:
    base_weights = {
        'structural': 0.25,
        'functional': 0.35,
        'behavioral': 0.30,
        'temporal': 0.10
    }

    # Pairwise interactions (optional advanced tuning)
    interactions = {
        ('structural', 'functional'): -0.1,  # High structural → reduce functional weight
        ('behavioral', 'functional'): +0.15, # Low functional → behavioral matters more
    }
```

### Multi-Algorithm Clustering

We employ multiple algorithms for robustness:

| Algorithm | Strengths | Use Case |
|-----------|-----------|----------|
| **K-means** | Fast, interpretable | Primary clustering |
| **Hierarchical** | Captures org structure | Organizational views |
| **DBSCAN** | Finds natural outliers | Anomaly detection |
| **Graph Community** | Captures actual relationships | Collaboration patterns |

**Disagreement Handling**: When algorithms disagree on peer assignment by >20%, the user/access is flagged for human review with explanation.

---

## Convergence-Based Graduation

### The Problem with Static Thresholds

Current market solutions allow administrators to configure auto-certification thresholds. This approach:
- Is based on assumptions, not data
- Lacks governance oversight
- Has no automatic correction when things go wrong

### Our Graduation Framework

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CATEGORY GRADUATION LIFECYCLE                           │
│                                                                             │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                │
│   │ Observation │ ───▶ │  Eligible   │ ───▶ │  Graduated  │                │
│   │   Phase     │      │   Phase     │      │   (Auto)    │                │
│   └─────────────┘      └─────────────┘      └─────────────┘                │
│                                                    │                        │
│   All recommendations    Metrics met,             │                        │
│   human-decided          awaiting sign-off        │                        │
│                                                    │                        │
│        ┌──────────────────────────────────────────┘                        │
│        │  Automatic Rollback if thresholds breached                        │
│        ▼                                                                    │
│   ┌─────────────┐                                                          │
│   │  Suspended  │  Requires re-qualification                               │
│   └─────────────┘                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Graduation Criteria (Per Access Category)

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| **Recommendation Acceptance** | >90% over 3 campaigns | Reviewers trust recommendations |
| **Override Rate** | <10% | Few disagreements |
| **False Positive Rate** | <15% | Flagged items are genuinely unusual |
| **Minimum Observations** | 100+ decisions | Statistical significance |
| **Algorithm Consensus** | >80% | Multiple methods agree |
| **Cluster Stability** | <10% churn | Peer groups are stable |

### Graduation Gates

1. **Metrics Achievement**: Category meets all thresholds
2. **Human Review**: IAM admin reviews category performance
3. **Governance Sign-Off**: Compliance/risk approves graduation
4. **Probation Period**: 30 days with 10% sampling
5. **Full Graduation**: Auto-certification enabled

### Automatic Rollback Triggers

- Override rate exceeds 15% post-graduation
- False positive rate exceeds 20%
- Algorithm consensus drops below 70%
- Manual suspension by governance

---

## Three Lines of Defense

### Architecture

| Line | Actor | Capabilities | Sampling Rate |
|------|-------|--------------|---------------|
| **First** | Manager / Resource Owner | Review recommendations, make decisions, override AI | 100% of flagged items |
| **Second** | Risk / Compliance | Sample auto-approved items, challenge decisions, flag for re-review | Minimum 5% of auto-approved |
| **Third** | Audit | Full decision trail, explanation for any decision, trend analysis | As needed |

### Audit Trail for Auto-Approved Items

Every auto-certification is logged with:

```typescript
interface AutoCertificationAuditRecord {
  grant_id: string;
  campaign_id: string;

  // Decision details
  decision: "auto_certified";
  decision_timestamp: Date;

  // Score breakdown
  assurance_score: number;
  score_components: {
    peer_typicality: number;
    sensitivity_factor: number;
    usage_factor: number;
  };

  // Peer context
  peer_group_size: number;
  peers_with_same_access: number;
  algorithm_consensus: number;
  clustering_strategy_scores: Record<string, number>;

  // Graduation status
  category_graduation_status: "graduated" | "probation";
  graduation_approval_id: string;

  // For second-line review
  selected_for_sampling: boolean;
  sampling_review?: {
    reviewed_by: string;
    reviewed_at: Date;
    decision: "confirmed" | "flagged";
    notes?: string;
  };
}
```

### Second-Line Review Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SECOND-LINE SAMPLING WORKFLOW                          │
│                                                                             │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐      │
│   │  Auto-Certified │────▶│ Random Sampling │────▶│  Compliance     │      │
│   │     Items       │     │    (≥5%)        │     │   Review Queue  │      │
│   └─────────────────┘     └─────────────────┘     └────────┬────────┘      │
│                                                            │               │
│                           ┌────────────────────────────────┼───────┐       │
│                           ▼                                ▼       │       │
│                    ┌─────────────┐                  ┌─────────────┐│       │
│                    │  Confirmed  │                  │   Flagged   ││       │
│                    │  (correct)  │                  │ (should have││       │
│                    └─────────────┘                  │  reviewed)  ││       │
│                                                     └──────┬──────┘│       │
│                                                            │       │       │
│                                                            ▼       │       │
│                                                     ┌─────────────┐│       │
│                                                     │ Escalation  ││       │
│                                                     │ + Category  ││       │
│                                                     │   Review    │┘       │
│                                                     └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Conversational Interface

### Architecture

The system includes an AI-powered conversational interface for natural language interaction:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CONVERSATIONAL ARCHITECTURE                            │
│                                                                             │
│  User Query ───▶ LLM (Claude API) ───▶ Tool Calls ───▶ Database            │
│                         │                    │                              │
│                         │                    ▼                              │
│                         │              Tool Results                         │
│                         │                    │                              │
│                         ◀────────────────────┘                              │
│                         │                                                   │
│                         ▼                                                   │
│                  Natural Language Response                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### LLM Integration

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Primary LLM** | Claude API | Excellent reasoning, tool use, explainability |
| **Fallback** | Ollama + Llama 3.1 | Zero-cost local option |
| **Integration Pattern** | Function calling | Precise, auditable, no hallucination on facts |

### Available Tools

```python
tools = [
    "get_user_access",           # Get all access grants for a user
    "explain_assurance_score",   # Explain why a grant has a particular score
    "compare_to_peers",          # Show peer comparison for a user
    "get_review_queue",          # Get pending items for a reviewer
    "search_users_with_access",  # Find users with specific access
    "get_dormant_access",        # Find unused access
    "explain_cluster_placement", # Explain peer group assignment
    "get_campaign_summary",      # Campaign statistics
    "get_graduation_status",     # Category graduation metrics
]
```

### Example Interactions

**Reviewer**: "Show me my highest priority items"
```
→ get_review_queue(reviewer_id="mgr_123", limit=10)
→ "You have 3 high-priority items:
   1. Bob Smith - AWS Prod Admin (Score: 23) - unusual for peer group
   2. Alice Chen - Snowflake DBA (Score: 31) - dormant 180 days
   ..."
```

**Compliance**: "Why was Carol's Salesforce access auto-approved?"
```
→ explain_assurance_score(grant_id="xxx")
→ "Carol's access scored 87/100:
   - Peer typicality: 94% of team has this
   - Sensitivity: Internal (0.8)
   - Usage: Active, 45 logins in 30 days
   Exceeded 80-point threshold for auto-certification."
```

---

## Micro-Certifications Architecture

### Design for Extensibility

While the demo implements traditional campaign-based certification, the architecture supports event-driven micro-certifications:

### Trigger Model

```typescript
interface CertificationTrigger {
  id: string;
  trigger_type: "periodic" | "event_based" | "continuous";

  // For periodic
  schedule?: string;  // cron expression

  // For event-based
  event_types?: EventType[];

  scope_filter: Record<string, any>;
  enabled: boolean;
}

type EventType =
  | "job_change"
  | "manager_change"
  | "team_transfer"
  | "new_access_grant"
  | "access_unused_30d"
  | "risk_signal_detected"
  | "sensitivity_upgrade";
```

### Event-Driven Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│   HR System ──┐                                                             │
│               │                                                             │
│  IAM System ──┼──▶ Event Bus ──▶ Trigger Service ──▶ ReviewItem Creation   │
│               │                                                             │
│   Activity ───┘                                                             │
│   Monitor                                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

For demo: Simple event simulator demonstrates micro-certification triggers.

---

## Plugin Architecture

### Canonical Data Model

New data sources map to a canonical model:

```typescript
// Canonical access representation
interface CanonicalAccessGrant {
  // Identity
  identity_id: string;
  identity_type: "human" | "service_account";

  // Resource
  resource_id: string;
  resource_system: string;
  resource_type: string;
  resource_sensitivity: SensitivityLevel;

  // Grant metadata
  grant_type: "direct" | "inherited" | "role_based";
  granted_at: Date;
  granted_by: string;

  // Activity (if available)
  last_used?: Date;
  usage_count_30d?: number;
}
```

### Plugin Interface

```typescript
interface DataSourcePlugin {
  // Metadata
  id: string;
  name: string;
  system_type: string;

  // Connection
  connect(config: ConnectionConfig): Promise<void>;
  disconnect(): Promise<void>;

  // Data extraction
  extractAccessGrants(): AsyncIterator<CanonicalAccessGrant>;
  extractActivityLogs(since: Date): AsyncIterator<ActivityEvent>;

  // Schema mapping
  mapToCanonical(rawGrant: any): CanonicalAccessGrant;
}
```

### Revalidation (Not Automatic Retraining)

When a new plugin is added:

1. **Schema Mapping**: Map source data to canonical model
2. **Validation Run**: Test existing model on new data
3. **Performance Check**: If accuracy drops below threshold, flag for review
4. **Human Decision**: IAM admin decides whether to retrain
5. **Controlled Retraining**: If approved, retrain with validation

```
New Plugin ──▶ Schema Mapping ──▶ Validation ──▶ Performance Check
                                                       │
                                    ┌──────────────────┴───────────────┐
                                    ▼                                  ▼
                              Acceptable                         Below Threshold
                                    │                                  │
                                    ▼                                  ▼
                              Continue                          Flag for Review
                                                                      │
                                                                      ▼
                                                              Human Decision
                                                                      │
                                                    ┌─────────────────┴────────┐
                                                    ▼                          ▼
                                              Approve Retrain            Reject/Adjust
```

---

## Data Models

### Organizational Entities

```typescript
interface Company {
  id: string;
  name: string;
  industry: string;
}

interface LOB {
  id: string;
  company_id: string;
  name: string;
  code: string;
}

interface SubLOB {
  id: string;
  lob_id: string;
  name: string;
  code: string;
}

interface Team {
  id: string;
  sub_lob_id: string;
  name: string;
  cost_center_id: string;
}

interface Location {
  id: string;
  name: string;
  region: string;
  country: string;
}

interface CostCenter {
  id: string;
  code: string;
  name: string;
  lob_id: string;
}
```

### Identity

```typescript
interface Employee {
  id: string;
  employee_number: string;
  email: string;
  full_name: string;

  // Organizational
  team_id: string;
  manager_id: string | null;
  location_id: string;
  cost_center_id: string;

  // Job
  job_title: string;
  job_code: string;
  job_family: string;
  job_level: number;

  // Employment
  employment_type: "FTE" | "Contractor" | "Vendor";
  hire_date: Date;
  role_start_date: Date;
  status: "Active" | "On Leave" | "Terminated";
}
```

### Systems & Resources

```typescript
interface System {
  id: string;
  name: string;
  type: SystemType;
  criticality: "Critical" | "High" | "Medium" | "Low";
  owner_employee_id: string;
}

type SystemType =
  | "azure_ad" | "aws_iam" | "gcp_iam"
  | "github" | "confluence" | "jira"
  | "servicenow" | "salesforce" | "sap"
  | "snowflake" | "custom_app";

interface Resource {
  id: string;
  system_id: string;
  resource_type: string;
  name: string;
  external_id: string;
  description: string;
  sensitivity: "Public" | "Internal" | "Confidential" | "Critical";
  grants_access_to: string[];
}
```

### Access & Activity

```typescript
interface AccessGrant {
  id: string;
  employee_id: string;
  resource_id: string;
  granted_date: Date;
  granted_by: string;
  grant_type: "Direct" | "Inherited" | "Role-Based";
  justification?: string;
  last_certified_date?: Date;
}

interface ActivitySummary {
  id: string;
  employee_id: string;
  resource_id: string;
  total_access_count: number;
  first_accessed: Date | null;
  last_accessed: Date | null;
  access_count_30d: number;
  access_count_90d: number;
}

interface RiskSignal {
  id: string;
  employee_id: string;
  signal_type: RiskSignalType;
  severity: "Critical" | "High" | "Medium" | "Low";
  timestamp: Date;
  description: string;
}
```

### Recertification

```typescript
interface Campaign {
  id: string;
  name: string;
  scope_type: "manager" | "resource_owner" | "lob" | "system";
  scope_filter: Record<string, any>;
  auto_approve_threshold: number;
  review_threshold: number;
  start_date: Date;
  due_date: Date;
  status: "Draft" | "Active" | "Completed";
}

interface ReviewItem {
  id: string;
  campaign_id: string;
  access_grant_id: string;
  reviewer_id: string;

  assurance_scores: {
    overall: number;
    by_strategy: Record<string, number>;
  };

  cluster_info: {
    peer_group_size: number;
    peers_with_same_access: number;
    percentile_in_cluster: number;
  };

  explanations: Explanation[];
  status: "Pending" | "Auto-Approved" | "Needs-Review" | "Decided";
  decision?: Decision;

  // Micro-cert support
  triggered_by: "campaign" | "event" | "continuous";
  trigger_event_type?: string;
}
```

---

## Regulatory Considerations

### SOX 404 Compliance

- Full audit trail for all certifications (manual and auto)
- Risk-based approach documented and approved
- Second-line sampling of auto-certifications
- SOX-relevant entitlements excluded from auto-certification

### SR 11-7 Model Risk Management (Financial Services)

- System formally registered as a model
- Initial validation before production
- Ongoing monitoring with drift detection
- Annual independent audit
- Full documentation per SR 11-7

### GDPR Considerations

- Article 5 accountability: Full decision logic documentation
- Article 22: Human review available for any decision
- Transparency: Employees can request explanations

---

## Success Metrics / KPIs

### Efficiency Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| Time per certification decision | Current | 50% reduction |
| Campaign completion time | Weeks/months | Days/weeks |
| Items requiring human review | 100% | 30-40% |

### Quality Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| Revocation rate | ~5% (rubber-stamping) | 10-15% |
| Override rate | N/A | <15% of recommendations |
| False positive rate | N/A | <20% of flagged items |

### Compliance Metrics

| Metric | Target |
|--------|--------|
| Audit findings (identity-related) | 80% reduction |
| Certification completion rate | Maintain 95%+ |
| Auto-certification sampling coverage | Minimum 5% |

### Model Performance

| Metric | Target |
|--------|--------|
| Algorithm consensus rate | >70% |
| Cluster stability | <10% churn between runs |
| Category graduation rate | Progressive improvement |

---

## Acknowledged Limitations

### 1. Learning Period Required

Convergence-based graduation requires data collection before auto-certification. Organizations seeking immediate automation may find this slower.

### 2. Sensitivity Classification Dependency

Effectiveness depends on accurate resource sensitivity classification. Miscategorization affects the ceiling constraint.

### 3. Computational Overhead

Multi-algorithm clustering is more resource-intensive. Very large enterprises may require optimization.

### 4. Scope Limitations

- **AI Agent Identities**: Not addressed (different ownership model, separate project)
- **Disconnected Applications**: Assumes connectable systems
- **Natural Language**: Demo implementation, not production-hardened

### 5. Cold Start for New Users/Roles

New employees or newly created roles lack peer data. Handled via rule-based defaults until sufficient data exists.

---

## Position Paper

### Thesis

Traditional access recertification has failed. The evidence is clear: 2-3% revocation rates indicate rubber-stamping, not meaningful review. AI-assisted certification is the solution, but current market implementations have fundamental flaws.

### The Problem with Current AI Approaches

**Weighted risk scores can fail silently.** When a highly typical access to a critical system can auto-approve because the typicality score overwhelms the sensitivity weight, the system is optimizing for the wrong objective.

**Static thresholds lack governance.** Auto-certification enabled by administrative configuration, without:
- Evidence that the threshold is appropriate
- Formal governance approval
- Automatic correction when quality degrades

**Single-algorithm peer analysis is brittle.** Different clustering algorithms produce different results. When they disagree, current systems don't notice.

### Our Counter-Position

**Sensitivity must be a ceiling, not a weight.** Critical access should never auto-certify, regardless of how typical it is. This is non-negotiable from a risk perspective.

**Auto-certification must be earned, not configured.** Categories should demonstrate readiness through measurable metrics, receive governance approval, and face automatic rollback if quality degrades.

**Algorithm disagreement is a signal, not noise.** When K-means and DBSCAN disagree on peer grouping, that's information. Flag for human review rather than confidently applying the wrong recommendation.

### Defensible Rationale

**Q: Why not use weighted scores like everyone else?**

A: Weighted scores optimize for a mathematical function that may not align with risk. A 95% typicality score and 0.3 sensitivity multiplier still produces a 28.5% composite—but that could represent a highly unusual person with critical access. Our approach treats these as separate concerns: typicality informs recommendations; sensitivity constrains automation.

**Q: Isn't convergence-based graduation just slower?**

A: Yes, initially. But it's slower in exchange for measurable confidence. We can prove the system works before enabling automation, and we can prove it's still working after. Static thresholds offer neither guarantee.

**Q: Multi-algorithm clustering seems expensive. Is it worth it?**

A: The cost is computational cycles. The benefit is catching cases where peer grouping is unreliable. Given that the entire purpose is to automate decisions that were previously human-made, the cost of a wrong automation far exceeds the cost of extra computation.

---

## Technical Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: SQLite (demo), PostgreSQL-ready
- **Analytics**: pandas, numpy, scikit-learn
- **Clustering**: scikit-learn, networkx (graph community)

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS + @tailwindcss/typography
- **State**: TanStack Query (React Query)
- **Routing**: React Router v6
- **Icons**: Lucide React
- **Markdown**: react-markdown

### AI/ML
- **LLM**: Claude API (primary), Ollama (fallback)
- **Integration**: Tool/function calling pattern

### Infrastructure
- **Local**: SQLite, uvicorn
- **Demo Access**: ngrok
- **Production-Ready**: Docker, PostgreSQL, proper auth

---

## References

### Academic

- Bolton, R.J. & Hand, D.J. (2001). "Peer Group Analysis - Local Anomaly Detection in Longitudinal Data"
- Molloy, I., Li, N., et al. (2009). "Evaluating Role Mining Algorithms." Purdue/IBM.
- ACM RoleMiner: Mining roles using subset enumeration

### Regulatory

- FFIEC IT Examination Handbook: Risk Assessment and Risk-Based Auditing
- OCC SR 11-7: Supervisory Guidance on Model Risk Management
- SOX Section 404: Management Assessment of Internal Controls
- GDPR Articles 5, 22: Processing principles and automated decisions

### Industry

- IDPro Body of Knowledge: Optimizing Access Recertifications (Gupta)
- Gartner Market Guide for Identity Governance and Administration (2025)
- SailPoint IdentityAI Documentation
- Saviynt Intelligence Documentation
- Veza Access AI Documentation
- ConductorOne Documentation
- Pathlock Risk-Based Certifications

### Market Research

- Identity Management Institute: Top IAM Metrics
- Ponemon IAM Maturity Report 2025
- Veza Identity & Access Research Report 2025

---

## Implementation Status

### Completed Features (v0.1.0)

| Feature | Status | Notes |
|---------|--------|-------|
| Synthetic data generation | Done | 10K employees, 3.3K resources, ~1M grants |
| Peer proximity calculation | Done | 4-dimension weighted model |
| Multi-algorithm clustering | Done | K-means, DBSCAN, Agglomerative, Graph community |
| Assurance scoring engine | Done | With sensitivity ceiling |
| Campaign management | Done | Create, activate, archive, rename |
| Review item workflow | Done | Filter, sort, paginate, decide |
| Bulk actions | Done | Multi-select certify/revoke |
| Clustering disagreement detection | Done | Flags items with algorithm disagreement |
| Small peer group detection | Done | Flags statistically unreliable comparisons |
| System recommendations | Done | Shows what system would recommend |
| Human review reasons | Done | Explains why human review required |
| Chat assistant | Done | Claude-powered with tool calling |
| Chat markdown rendering | Done | Formatted AI responses |
| URL-based filter persistence | Done | Preserves state on navigation |
| AI explain integration | Done | Direct link from item to chat |
| Demo automation | Done | Playwright screenshot capture |

### Not Yet Implemented

| Feature | Priority | Notes |
|---------|----------|-------|
| Convergence-based graduation | Medium | Metrics exist, governance flow not built |
| Compliance sampling | Medium | Data model exists, UI not built |
| Email notifications | Low | Demo doesn't need it |
| Authentication | Low | Demo runs locally |
| Role mining integration | Future | Enhancement idea |
| Predictive scoring | Future | Enhancement idea |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-01-14 | Full demo implementation with UI, analytics, chat |
| 0.1 | 2026-01-13 | Initial design document |
