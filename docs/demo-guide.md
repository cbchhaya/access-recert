# ARAS Demo Guide

This guide walks through key features of the Access Recertification Assurance System for demonstration purposes.

## Setup

1. Start the system: `start.bat`
2. Open browser to http://localhost:3000
3. Ensure API key is configured in `.env` for Chat Assistant

## Demo Flow

### 1. Dashboard Overview (30 seconds)
**URL:** http://localhost:3000

- Show the main dashboard with system statistics
- Point out: employees, resources, access grants counts
- Highlight that this is a risk-focused approach vs traditional rubber-stamping

### 2. Create a Campaign (1 minute)
**URL:** http://localhost:3000/campaigns

1. Click "New Campaign"
2. Hover over the `?` icons to show tooltips explaining each field:
   - **Scope Type**: How reviews are organized
   - **Auto-Approve Threshold**: Items scoring above this auto-approve (default 80)
   - **Review Threshold**: Items below this get flagged for attention (default 50)
3. Create campaign for "Technology" LOB
4. Click "Activate" - explain this runs the analytics engine

### 3. Campaign Review Items (2 minutes)
**URL:** http://localhost:3000/campaigns/{id}

Show the three types of items:

#### A. High Assurance (Auto-Approved)
- Filter by "Auto-Approved" status
- Click on an item
- **Key points to highlight:**
  - Score > 80 (or your threshold)
  - High peer typicality (many peers have same access)
  - Active usage pattern
  - No clustering disagreement
  - No small peer group warning
- These items saved reviewer time - no action needed

#### B. Needs Review (Low Score)
- Filter by "Needs-Review" status
- Click on an item with low score
- **Key points to highlight:**
  - Score < 50 (or your threshold)
  - May have low peer typicality (unusual access for role)
  - May have stale/dormant usage
  - Sensitivity ceiling (Critical = 0, Confidential = 0.5)
- Show "Human Review Required" warning if present
- Show "System suggestion" hint

#### C. Needs Review (Uncertainty Flags)
- Look for items with amber warnings
- **Key points to highlight:**
  - Clustering disagreement: algorithms disagree on peer grouping
  - Small peer group: not enough similar employees to compare
  - Even with high score, system requires human verification
  - Shows what system WOULD have recommended

### 4. AI-Assisted Explanation (1 minute)
**From a review item page:**

1. Click "Ask AI to Explain" button next to the item ID
2. The Chat Assistant automatically asks about this specific item
3. AI provides detailed explanation of:
   - Why the score was calculated this way
   - What factors contributed
   - Whether human review is needed and why
4. Show you can ask follow-up questions

**Alternative Chat queries to demo:**
- "Show me system stats"
- "Find employees named John"
- "What low assurance items need review?"
- "Explain the peer proximity model"

### 5. Bulk Actions (30 seconds)
**Back in campaign review items:**

1. Select multiple pending items using checkboxes
2. Show bulk "Certify" and "Revoke" buttons
3. Explain this helps with efficiency for clear-cut cases

### 6. Campaign Management (30 seconds)
**URL:** http://localhost:3000/campaigns

1. Show the 3-dot menu on a campaign
2. Demonstrate "Rename" functionality
3. Demonstrate "Archive" to hide completed campaigns
4. Toggle "Show archived" checkbox

## Key Talking Points

### The Problem with Traditional Access Reviews
- Thousands of items, no differentiation
- Time pressure leads to rubber-stamping
- No context about what's typical vs unusual
- Binary approve/reject with no nuance

### How ARAS Solves This
1. **Assurance Scoring**: Each item gets a risk score (0-100)
2. **Peer Analysis**: Compare against similar employees
3. **Sensitivity Ceiling**: Critical access NEVER auto-approves
4. **Multi-Algorithm Clustering**: Detect uncertainty in peer grouping
5. **Three Lines of Defense**: Manager, Compliance, Audit

### The Formula
```
raw_score = (peer_typicality × 0.7) + (usage_factor × 0.3)
final_score = raw_score × sensitivity_ceiling × 100
```

### Sensitivity Ceilings
| Level | Ceiling | Effect |
|-------|---------|--------|
| Critical | 0.0 | Always requires review |
| Confidential | 0.5 | Max 50 points |
| Internal | 0.85 | Max 85 points |
| Public | 1.0 | No cap |

## Recording Tips

For creating video demos:
- Use a screen recording tool (OBS, Loom, or built-in OS tools)
- Set browser to 1920x1080 for crisp recordings
- Zoom to 100-125% for readability
- Close unnecessary tabs/notifications
- Use a consistent, methodical pace
- Pause briefly on key screens for emphasis

## Screenshots Checklist

Capture these key screens:
- [ ] Dashboard overview
- [ ] Campaign list (showing different statuses)
- [ ] Campaign creation modal (with tooltips visible)
- [ ] Review items list (filtered views)
- [ ] Auto-approved item detail (showing high score)
- [ ] Needs-review item detail (showing warnings)
- [ ] Human review reason with system suggestion
- [ ] Chat assistant explaining an item
- [ ] Bulk selection UI
