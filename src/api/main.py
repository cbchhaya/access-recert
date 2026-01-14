"""
ARAS REST API
=============

FastAPI application providing REST endpoints for the Access Recertification
Assurance System.

Author: Chiradeep Chhaya
"""

import os

# Load .env file FIRST before any other imports
from dotenv import load_dotenv
_env_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".env"
)
if os.path.exists(_env_path):
    load_dotenv(_env_path)
    print(f"[ARAS] Loaded environment from: {_env_path}")

import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
import json
import uuid

from fastapi import FastAPI, HTTPException, Query, Depends, Path
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignSummaryResponse,
    CampaignProgressResponse, CampaignStatus, CampaignScopeType,
    ReviewItemResponse, ReviewItemSummary, ReviewItemStatus,
    DecisionCreate, BulkDecisionCreate, DecisionAction,
    EmployeeResponse, ResourceResponse, AssuranceScoreResponse,
    AssuranceClassification, SensitivityLevel,
    WeightsResponse, WeightsUpdate, WeightsPreviewResponse,
    GraduationStatusResponse, EmployeeAccessSummaryResponse,
    AuditRecordResponse, ComplianceSampleResponse, SampleReviewCreate,
    AnalyticsResponse, PaginatedResponse, ErrorResponse
)

# Import analytics engine
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analytics.engine import AnalyticsEngine


# Database path
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "aras.db"
)


# FastAPI app
app = FastAPI(
    title="ARAS API",
    description="Access Recertification Assurance System - REST API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include chat router
try:
    from .chat import router as chat_router
    app.include_router(chat_router, prefix="/api", tags=["chat"])
except Exception as e:
    print(f"Chat router not available: {e}")


# Database connection
@contextmanager
def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def dict_from_row(row) -> dict:
    """Convert sqlite3.Row to dict."""
    return dict(zip(row.keys(), row))


# Analytics engine singleton
_engine: Optional[AnalyticsEngine] = None

def get_engine() -> AnalyticsEngine:
    """Get or create analytics engine."""
    global _engine
    if _engine is None:
        _engine = AnalyticsEngine(DB_PATH)
        _engine.load_data()
    return _engine


# ============================================================================
# Health & Status
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/status")
async def system_status():
    """Get system status and statistics."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get counts
        cursor.execute("SELECT COUNT(*) FROM employees")
        employee_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM resources")
        resource_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM access_grants")
        grant_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM campaigns")
        campaign_count = cursor.fetchone()[0]

        return {
            "status": "operational",
            "database": DB_PATH,
            "statistics": {
                "employees": employee_count,
                "resources": resource_count,
                "access_grants": grant_count,
                "campaigns": campaign_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# ============================================================================
# Campaigns
# ============================================================================

@app.post("/api/campaigns", response_model=CampaignResponse, status_code=201)
async def create_campaign(campaign: CampaignCreate):
    """Create a new certification campaign."""
    campaign_id = str(uuid.uuid4())
    now = datetime.utcnow()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO campaigns (
                id, name, scope_type, scope_filter, auto_approve_threshold,
                review_threshold, start_date, due_date, status, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign_id, campaign.name, campaign.scope_type.value,
            json.dumps(campaign.scope_filter), campaign.auto_approve_threshold,
            campaign.review_threshold, now.isoformat(), campaign.due_date.isoformat(),
            CampaignStatus.DRAFT.value, "system", now.isoformat()
        ))
        conn.commit()

        return CampaignResponse(
            id=campaign_id,
            name=campaign.name,
            scope_type=campaign.scope_type,
            scope_filter=campaign.scope_filter,
            auto_approve_threshold=campaign.auto_approve_threshold,
            review_threshold=campaign.review_threshold,
            start_date=now,
            due_date=campaign.due_date,
            status=CampaignStatus.DRAFT,
            created_by="system",
            created_at=now
        )


@app.get("/api/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[CampaignStatus] = None,
    include_archived: bool = Query(default=False, description="Include archived campaigns"),
    limit: int = Query(default=50, ge=1, le=100)
):
    """List all campaigns."""
    with get_db() as conn:
        cursor = conn.cursor()

        if status:
            cursor.execute(
                "SELECT * FROM campaigns WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status.value, limit)
            )
        elif include_archived:
            cursor.execute(
                "SELECT * FROM campaigns ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        else:
            cursor.execute(
                "SELECT * FROM campaigns WHERE status != ? ORDER BY created_at DESC LIMIT ?",
                (CampaignStatus.ARCHIVED.value, limit)
            )

        campaigns = []
        for row in cursor.fetchall():
            row_dict = dict_from_row(row)
            campaigns.append(CampaignResponse(
                id=row_dict["id"],
                name=row_dict["name"],
                scope_type=CampaignScopeType(row_dict["scope_type"]),
                scope_filter=json.loads(row_dict["scope_filter"] or "{}"),
                auto_approve_threshold=row_dict["auto_approve_threshold"],
                review_threshold=row_dict["review_threshold"],
                start_date=datetime.fromisoformat(row_dict["start_date"]),
                due_date=datetime.fromisoformat(row_dict["due_date"]),
                status=CampaignStatus(row_dict["status"]),
                created_by=row_dict["created_by"],
                created_at=datetime.fromisoformat(row_dict["created_at"])
            ))

        return campaigns


@app.get("/api/campaigns/{campaign_id}", response_model=CampaignSummaryResponse)
async def get_campaign(campaign_id: str = Path(...)):
    """Get campaign details with statistics."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get campaign
        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")

        row_dict = dict_from_row(row)
        campaign = CampaignResponse(
            id=row_dict["id"],
            name=row_dict["name"],
            scope_type=CampaignScopeType(row_dict["scope_type"]),
            scope_filter=json.loads(row_dict["scope_filter"] or "{}"),
            auto_approve_threshold=row_dict["auto_approve_threshold"],
            review_threshold=row_dict["review_threshold"],
            start_date=datetime.fromisoformat(row_dict["start_date"]),
            due_date=datetime.fromisoformat(row_dict["due_date"]),
            status=CampaignStatus(row_dict["status"]),
            created_by=row_dict["created_by"],
            created_at=datetime.fromisoformat(row_dict["created_at"])
        )

        # Get review item statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Auto-Approved' THEN 1 ELSE 0 END) as auto_approved,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'Decided' THEN 1 ELSE 0 END) as decided
            FROM review_items WHERE campaign_id = ?
        """, (campaign_id,))
        stats = cursor.fetchone()

        # Get decision breakdown
        cursor.execute("""
            SELECT
                SUM(CASE WHEN json_extract(decision, '$.action') = 'Certify' THEN 1 ELSE 0 END) as certified,
                SUM(CASE WHEN json_extract(decision, '$.action') = 'Revoke' THEN 1 ELSE 0 END) as revoked
            FROM review_items WHERE campaign_id = ? AND decision IS NOT NULL
        """, (campaign_id,))
        decisions = cursor.fetchone()

        # Get score distribution
        cursor.execute("""
            SELECT classification, COUNT(*) as count
            FROM review_items WHERE campaign_id = ?
            GROUP BY classification
        """, (campaign_id,))
        dist_rows = cursor.fetchall()
        score_distribution = {row["classification"]: row["count"] for row in dist_rows}

        total = stats["total"] or 0
        auto_approved = stats["auto_approved"] or 0
        pending = stats["pending"] or 0
        decided = stats["decided"] or 0
        certified = decisions["certified"] or 0
        revoked = decisions["revoked"] or 0

        completed = auto_approved + decided
        completion_pct = (completed / total * 100) if total > 0 else 0
        revocation_rate = (revoked / (certified + revoked) * 100) if (certified + revoked) > 0 else 0

        return CampaignSummaryResponse(
            campaign=campaign,
            total_items=total,
            pending_items=pending,
            auto_approved_items=auto_approved,
            manually_reviewed_items=decided,
            certified_items=certified,
            revoked_items=revoked,
            completion_percentage=round(completion_pct, 1),
            revocation_rate=round(revocation_rate, 1),
            score_distribution=score_distribution
        )


@app.patch("/api/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str = Path(...),
    update: CampaignUpdate = None
):
    """Update campaign settings."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check campaign exists
        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")

        row_dict = dict_from_row(row)

        # Build update
        updates = []
        params = []

        if update.name is not None:
            updates.append("name = ?")
            params.append(update.name)
        if update.status is not None:
            updates.append("status = ?")
            params.append(update.status.value)
        if update.auto_approve_threshold is not None:
            updates.append("auto_approve_threshold = ?")
            params.append(update.auto_approve_threshold)
        if update.review_threshold is not None:
            updates.append("review_threshold = ?")
            params.append(update.review_threshold)
        if update.due_date is not None:
            updates.append("due_date = ?")
            params.append(update.due_date.isoformat())

        if updates:
            params.append(campaign_id)
            cursor.execute(
                f"UPDATE campaigns SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()

        # Return updated campaign
        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        row = cursor.fetchone()
        row_dict = dict_from_row(row)

        return CampaignResponse(
            id=row_dict["id"],
            name=row_dict["name"],
            scope_type=CampaignScopeType(row_dict["scope_type"]),
            scope_filter=json.loads(row_dict["scope_filter"] or "{}"),
            auto_approve_threshold=row_dict["auto_approve_threshold"],
            review_threshold=row_dict["review_threshold"],
            start_date=datetime.fromisoformat(row_dict["start_date"]),
            due_date=datetime.fromisoformat(row_dict["due_date"]),
            status=CampaignStatus(row_dict["status"]),
            created_by=row_dict["created_by"],
            created_at=datetime.fromisoformat(row_dict["created_at"])
        )


@app.post("/api/campaigns/{campaign_id}/archive", response_model=CampaignResponse)
async def archive_campaign(campaign_id: str = Path(...)):
    """Archive a campaign."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check campaign exists
        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")

        row_dict = dict_from_row(row)

        # Can archive any campaign except already archived ones
        if row_dict["status"] == CampaignStatus.ARCHIVED.value:
            raise HTTPException(
                status_code=400,
                detail="Campaign is already archived"
            )

        # Archive the campaign
        cursor.execute(
            "UPDATE campaigns SET status = ? WHERE id = ?",
            (CampaignStatus.ARCHIVED.value, campaign_id)
        )
        conn.commit()

        # Return updated campaign
        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        row = cursor.fetchone()
        row_dict = dict_from_row(row)

        return CampaignResponse(
            id=row_dict["id"],
            name=row_dict["name"],
            scope_type=CampaignScopeType(row_dict["scope_type"]),
            scope_filter=json.loads(row_dict["scope_filter"] or "{}"),
            auto_approve_threshold=row_dict["auto_approve_threshold"],
            review_threshold=row_dict["review_threshold"],
            start_date=datetime.fromisoformat(row_dict["start_date"]),
            due_date=datetime.fromisoformat(row_dict["due_date"]),
            status=CampaignStatus(row_dict["status"]),
            created_by=row_dict["created_by"],
            created_at=datetime.fromisoformat(row_dict["created_at"])
        )


@app.post("/api/campaigns/{campaign_id}/activate", response_model=CampaignSummaryResponse)
async def activate_campaign(campaign_id: str = Path(...)):
    """Activate a campaign - run analytics and generate review items."""
    import statistics

    with get_db() as conn:
        cursor = conn.cursor()

        # Check campaign exists and is in draft status
        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")

        row_dict = dict_from_row(row)
        if row_dict["status"] != CampaignStatus.DRAFT.value:
            raise HTTPException(
                status_code=400,
                detail=f"Campaign is {row_dict['status']}, must be Draft to activate"
            )

        # Parse scope
        scope_filter = json.loads(row_dict["scope_filter"] or "{}")
        lob_filter = scope_filter.get("lob")

        # Run analytics
        engine = get_engine()
        result = engine.run_analysis(lob_filter=lob_filter)

        # Check if we have any results
        if result.total_grants == 0:
            raise HTTPException(
                status_code=400,
                detail=f"No access grants found for LOB filter: {lob_filter}"
            )

        # Calculate peer group size statistics to identify small peer groups
        peer_group_sizes = [score.total_peers for score in result.assurance_scores.values()]
        if len(peer_group_sizes) > 1:
            mean_peer_size = statistics.mean(peer_group_sizes)
            stdev_peer_size = statistics.stdev(peer_group_sizes) if len(peer_group_sizes) > 2 else 0
            small_peer_threshold = max(3, mean_peer_size - stdev_peer_size)  # At least 3
        else:
            mean_peer_size = peer_group_sizes[0] if peer_group_sizes else 0
            stdev_peer_size = 0
            small_peer_threshold = 3

        auto_approve_threshold = row_dict["auto_approve_threshold"]
        review_threshold = row_dict["review_threshold"]

        # Create review items
        now = datetime.utcnow()
        for grant_id, score in result.assurance_scores.items():
            emp_id = score.employee_id

            # Get consensus info
            consensus = result.consensus_results.get(emp_id)
            consensus_score_val = consensus.consensus_score if consensus else 1.0
            needs_cluster_review = consensus.needs_human_review if consensus else False
            disagreement = consensus.disagreement_reason if consensus else None

            # Check for small peer group
            peer_group_size = score.total_peers
            is_small_peer_group = peer_group_size < small_peer_threshold

            # Determine what the system WOULD recommend (for transparency)
            if score.overall_score >= auto_approve_threshold:
                system_recommendation = "Certify"
            elif score.overall_score < review_threshold:
                system_recommendation = "Review Carefully"
            else:
                system_recommendation = "Likely Certify"

            # Collect reasons requiring human review
            human_review_reasons = []
            if needs_cluster_review:
                human_review_reasons.append(f"Clustering disagreement: {disagreement or 'algorithms disagree on peer grouping'}")
            if is_small_peer_group:
                human_review_reasons.append(f"Small peer group ({peer_group_size} peers vs avg {mean_peer_size:.0f})")

            human_review_reason = "; ".join(human_review_reasons) if human_review_reasons else None

            # Determine initial status - DON'T auto-approve if human review needed
            if score.auto_certify_eligible and not human_review_reasons:
                # Safe to auto-approve: high score AND no red flags
                status = ReviewItemStatus.AUTO_APPROVED.value
            elif human_review_reasons:
                # Has red flags - always needs review regardless of score
                status = ReviewItemStatus.NEEDS_REVIEW.value
            elif score.overall_score < review_threshold:
                # Low score, needs attention
                status = ReviewItemStatus.NEEDS_REVIEW.value
            else:
                # Medium score, pending manual review
                status = ReviewItemStatus.PENDING.value

            item_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO review_items (
                    id, campaign_id, access_grant_id, employee_id,
                    assurance_score, classification, auto_certify_eligible,
                    clustering_consensus, needs_clustering_review, clustering_disagreement,
                    status, created_at, system_recommendation, peer_group_size, human_review_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id, campaign_id, grant_id, emp_id,
                score.overall_score, score.classification, score.auto_certify_eligible,
                consensus_score_val, needs_cluster_review, disagreement,
                status, now.isoformat(), system_recommendation, peer_group_size, human_review_reason
            ))

        # Update campaign status
        cursor.execute(
            "UPDATE campaigns SET status = ? WHERE id = ?",
            (CampaignStatus.ACTIVE.value, campaign_id)
        )
        conn.commit()

    # Return updated summary
    return await get_campaign(campaign_id)


@app.get("/api/campaigns/{campaign_id}/progress", response_model=List[CampaignProgressResponse])
async def get_campaign_progress(campaign_id: str = Path(...)):
    """Get campaign progress by reviewer."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check campaign exists
        cursor.execute("SELECT id FROM campaigns WHERE id = ?", (campaign_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Get progress by reviewer (manager)
        cursor.execute("""
            SELECT
                e.manager_id as reviewer_id,
                m.full_name as reviewer_name,
                COUNT(*) as total_items,
                SUM(CASE WHEN ri.status IN ('Auto-Approved', 'Decided') THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN ri.status IN ('Pending', 'Needs-Review') THEN 1 ELSE 0 END) as pending
            FROM review_items ri
            JOIN employees e ON ri.employee_id = e.id
            LEFT JOIN employees m ON e.manager_id = m.id
            WHERE ri.campaign_id = ?
            GROUP BY e.manager_id, m.full_name
        """, (campaign_id,))

        progress = []
        for row in cursor.fetchall():
            total = row["total_items"]
            completed = row["completed"]
            progress.append(CampaignProgressResponse(
                reviewer_id=row["reviewer_id"] or "unknown",
                reviewer_name=row["reviewer_name"] or "Unknown",
                total_items=total,
                completed_items=completed,
                pending_items=row["pending"],
                completion_percentage=round(completed / total * 100, 1) if total > 0 else 0
            ))

        return sorted(progress, key=lambda x: x.completion_percentage)


# ============================================================================
# Review Items
# ============================================================================

@app.get("/api/campaigns/{campaign_id}/review-items", response_model=PaginatedResponse)
async def list_review_items(
    campaign_id: str = Path(...),
    status: Optional[ReviewItemStatus] = None,
    classification: Optional[AssuranceClassification] = None,
    needs_review: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = Query(default="assurance_score", pattern="^(assurance_score|employee_name|resource_name|status)$"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """List review items for a campaign with filtering and pagination."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Build query
        base_query = """
            SELECT ri.*,
                   e.full_name as employee_name, e.job_title as employee_title,
                   r.name as resource_name, r.sensitivity as resource_sensitivity
            FROM review_items ri
            JOIN employees e ON ri.employee_id = e.id
            JOIN access_grants ag ON ri.access_grant_id = ag.id
            JOIN resources r ON ag.resource_id = r.id
            WHERE ri.campaign_id = ?
        """
        params = [campaign_id]

        if status:
            base_query += " AND ri.status = ?"
            params.append(status.value)

        if classification:
            base_query += " AND ri.classification = ?"
            params.append(classification.value)

        if needs_review is not None:
            base_query += " AND ri.needs_clustering_review = ?"
            params.append(1 if needs_review else 0)

        if search:
            base_query += " AND (e.full_name LIKE ? OR r.name LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({base_query})"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Add sorting and pagination
        sort_column = {
            "assurance_score": "ri.assurance_score",
            "employee_name": "e.full_name",
            "resource_name": "r.name",
            "status": "ri.status"
        }.get(sort_by, "ri.assurance_score")

        base_query += f" ORDER BY {sort_column} {sort_order.upper()}"
        base_query += " LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])

        cursor.execute(base_query, params)

        items = []
        for row in cursor.fetchall():
            row_dict = dict_from_row(row)
            items.append(ReviewItemSummary(
                id=row_dict["id"],
                employee_id=row_dict["employee_id"],
                employee_name=row_dict["employee_name"],
                employee_title=row_dict["employee_title"],
                resource_id=row_dict["access_grant_id"],
                resource_name=row_dict["resource_name"],
                resource_sensitivity=SensitivityLevel(row_dict["resource_sensitivity"]),
                assurance_score=row_dict["assurance_score"],
                classification=AssuranceClassification(row_dict["classification"]),
                auto_certify_eligible=bool(row_dict["auto_certify_eligible"]),
                usage_pattern="Unknown",  # Would need activity join
                peer_percentage=0.0,  # Would need calculation
                status=ReviewItemStatus(row_dict["status"]),
                explanations=[]
            ))

        total_pages = (total + page_size - 1) // page_size

        return PaginatedResponse(
            items=[item.model_dump() for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


@app.get("/api/review-items/{item_id}", response_model=ReviewItemResponse)
async def get_review_item(item_id: str = Path(...)):
    """Get detailed review item information."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get review item with joins - use explicit column names to avoid conflicts
        cursor.execute("""
            SELECT ri.id as ri_id, ri.campaign_id, ri.access_grant_id, ri.employee_id,
                   ri.assurance_score, ri.classification, ri.auto_certify_eligible,
                   ri.clustering_consensus, ri.needs_clustering_review, ri.clustering_disagreement,
                   ri.status as ri_status, ri.decision, ri.created_at as ri_created_at, ri.updated_at as ri_updated_at,
                   ri.system_recommendation, ri.peer_group_size, ri.human_review_reason,
                   e.employee_number, e.email, e.full_name, e.job_title, e.job_code,
                   e.job_family, e.job_level, e.team_id, e.manager_id, e.location_id,
                   e.employment_type, e.status as emp_status,
                   ag.resource_id,
                   r.system_id, r.resource_type, r.name as resource_name,
                   r.description as resource_description, r.sensitivity
            FROM review_items ri
            JOIN employees e ON ri.employee_id = e.id
            JOIN access_grants ag ON ri.access_grant_id = ag.id
            JOIN resources r ON ag.resource_id = r.id
            WHERE ri.id = ?
        """, (item_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Review item not found")

        row_dict = dict_from_row(row)

        # Build response
        employee = EmployeeResponse(
            id=row_dict["employee_id"],
            employee_number=row_dict["employee_number"],
            email=row_dict["email"],
            full_name=row_dict["full_name"],
            job_title=row_dict["job_title"],
            job_code=row_dict["job_code"],
            job_family=row_dict["job_family"],
            job_level=row_dict["job_level"],
            team_id=row_dict["team_id"],
            manager_id=row_dict["manager_id"],
            location_id=row_dict["location_id"],
            employment_type=row_dict["employment_type"],
            status=row_dict["emp_status"]
        )

        resource = ResourceResponse(
            id=row_dict["resource_id"],
            system_id=row_dict["system_id"],
            resource_type=row_dict["resource_type"],
            name=row_dict["resource_name"],
            description=row_dict["resource_description"],
            sensitivity=SensitivityLevel(row_dict["sensitivity"])
        )

        # Build assurance score response
        assurance = AssuranceScoreResponse(
            overall_score=row_dict["assurance_score"],
            peer_typicality=0.0,  # Would need to recalculate
            sensitivity_ceiling=get_sensitivity_ceiling(row_dict["sensitivity"]),
            usage_factor=0.0,
            classification=AssuranceClassification(row_dict["classification"]),
            auto_certify_eligible=bool(row_dict["auto_certify_eligible"]),
            peers_with_access=0,
            total_peers=0,
            peer_percentage=0.0,
            usage_pattern="Unknown",
            days_since_last_use=None,
            explanations=[]
        )

        decision = json.loads(row_dict["decision"]) if row_dict["decision"] else None

        return ReviewItemResponse(
            id=row_dict["ri_id"],
            campaign_id=row_dict["campaign_id"],
            access_grant_id=row_dict["access_grant_id"],
            employee=employee,
            resource=resource,
            assurance_score=assurance,
            status=ReviewItemStatus(row_dict["ri_status"]),
            clustering_consensus=row_dict["clustering_consensus"],
            needs_clustering_review=bool(row_dict["needs_clustering_review"]),
            clustering_disagreement=row_dict["clustering_disagreement"],
            system_recommendation=row_dict.get("system_recommendation"),
            peer_group_size=row_dict.get("peer_group_size"),
            human_review_reason=row_dict.get("human_review_reason"),
            decision=decision,
            created_at=datetime.fromisoformat(row_dict["ri_created_at"]),
            updated_at=datetime.fromisoformat(row_dict["ri_updated_at"]) if row_dict["ri_updated_at"] else None
        )


def get_sensitivity_ceiling(sensitivity: str) -> float:
    """Get sensitivity ceiling value."""
    ceilings = {
        "Critical": 0.0,
        "Confidential": 0.5,
        "Internal": 0.85,
        "Public": 1.0
    }
    return ceilings.get(sensitivity, 0.5)


# ============================================================================
# Decisions
# ============================================================================

@app.post("/api/review-items/{item_id}/decision", response_model=ReviewItemResponse)
async def submit_decision(
    item_id: str = Path(...),
    decision: DecisionCreate = None
):
    """Submit a decision for a review item."""
    now = datetime.utcnow()

    with get_db() as conn:
        cursor = conn.cursor()

        # Check item exists
        cursor.execute("SELECT * FROM review_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Review item not found")

        row_dict = dict_from_row(row)

        # Validate state
        if row_dict["status"] == ReviewItemStatus.AUTO_APPROVED.value:
            raise HTTPException(
                status_code=400,
                detail="Cannot modify auto-approved item"
            )

        # Build decision record
        decision_record = {
            "action": decision.action.value,
            "rationale": decision.rationale,
            "decided_by": "reviewer",  # Would come from auth
            "decided_at": now.isoformat()
        }

        if decision.action == DecisionAction.MODIFY:
            decision_record["modification_details"] = decision.modification_details
        elif decision.action == DecisionAction.DELEGATE:
            decision_record["delegated_to"] = decision.delegated_to

        # Update review item
        cursor.execute("""
            UPDATE review_items
            SET status = ?, decision = ?, updated_at = ?
            WHERE id = ?
        """, (
            ReviewItemStatus.DECIDED.value,
            json.dumps(decision_record),
            now.isoformat(),
            item_id
        ))

        # Create audit record
        audit_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO audit_records (
                id, review_item_id, action, decision_by, decision_at,
                rationale, assurance_score, auto_certified, campaign_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            audit_id, item_id, decision.action.value, "reviewer",
            now.isoformat(), decision.rationale, row_dict["assurance_score"],
            False, row_dict["campaign_id"]
        ))

        conn.commit()

    return await get_review_item(item_id)


@app.post("/api/campaigns/{campaign_id}/bulk-decisions", response_model=Dict[str, Any])
async def submit_bulk_decisions(
    campaign_id: str = Path(...),
    bulk: BulkDecisionCreate = None
):
    """Submit decisions for multiple review items."""
    now = datetime.utcnow()
    success_count = 0
    error_count = 0
    errors = []

    with get_db() as conn:
        cursor = conn.cursor()

        for item_id in bulk.review_item_ids:
            try:
                # Check item exists and belongs to campaign
                cursor.execute(
                    "SELECT * FROM review_items WHERE id = ? AND campaign_id = ?",
                    (item_id, campaign_id)
                )
                row = cursor.fetchone()

                if not row:
                    errors.append({"item_id": item_id, "error": "Not found"})
                    error_count += 1
                    continue

                row_dict = dict_from_row(row)

                if row_dict["status"] == ReviewItemStatus.AUTO_APPROVED.value:
                    errors.append({"item_id": item_id, "error": "Auto-approved item"})
                    error_count += 1
                    continue

                # Build decision
                decision_record = {
                    "action": bulk.action.value,
                    "rationale": bulk.rationale,
                    "decided_by": "reviewer",
                    "decided_at": now.isoformat(),
                    "bulk_decision": True
                }

                # Update
                cursor.execute("""
                    UPDATE review_items
                    SET status = ?, decision = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    ReviewItemStatus.DECIDED.value,
                    json.dumps(decision_record),
                    now.isoformat(),
                    item_id
                ))

                # Audit
                audit_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO audit_records (
                        id, review_item_id, action, decision_by, decision_at,
                        rationale, assurance_score, auto_certified, campaign_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    audit_id, item_id, bulk.action.value, "reviewer",
                    now.isoformat(), bulk.rationale, row_dict["assurance_score"],
                    False, campaign_id
                ))

                success_count += 1

            except Exception as e:
                errors.append({"item_id": item_id, "error": str(e)})
                error_count += 1

        conn.commit()

    return {
        "success_count": success_count,
        "error_count": error_count,
        "errors": errors
    }


# ============================================================================
# Analytics & Weights
# ============================================================================

@app.get("/api/weights", response_model=WeightsResponse)
async def get_weights():
    """Get current proximity weights."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM proximity_weights ORDER BY updated_at DESC LIMIT 1")
        row = cursor.fetchone()

        if row:
            row_dict = dict_from_row(row)
            return WeightsResponse(
                structural=row_dict["structural"],
                functional=row_dict["functional"],
                behavioral=row_dict["behavioral"],
                temporal=row_dict["temporal"],
                last_updated=datetime.fromisoformat(row_dict["updated_at"]) if row_dict["updated_at"] else None,
                updated_by=row_dict["updated_by"]
            )
        else:
            # Return defaults
            return WeightsResponse(
                structural=0.25,
                functional=0.35,
                behavioral=0.30,
                temporal=0.10,
                last_updated=None,
                updated_by=None
            )


@app.post("/api/weights/preview", response_model=WeightsPreviewResponse)
async def preview_weight_changes(weights: WeightsUpdate):
    """Preview impact of weight changes."""
    if not weights.validate_sum():
        raise HTTPException(
            status_code=400,
            detail="Weights must sum to 1.0"
        )

    current = await get_weights()

    # Calculate impact (simplified)
    impact = {
        "affected_employees": 0,
        "score_changes": {
            "increased": 0,
            "decreased": 0,
            "unchanged": 0
        },
        "classification_changes": {
            "to_high": 0,
            "to_medium": 0,
            "to_low": 0
        }
    }

    return WeightsPreviewResponse(
        current_weights=current,
        proposed_weights=weights,
        impact=impact
    )


@app.put("/api/weights", response_model=WeightsResponse)
async def update_weights(weights: WeightsUpdate):
    """Update proximity weights."""
    if not weights.validate_sum():
        raise HTTPException(
            status_code=400,
            detail="Weights must sum to 1.0"
        )

    now = datetime.utcnow()

    with get_db() as conn:
        cursor = conn.cursor()

        weight_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO proximity_weights (
                id, structural, functional, behavioral, temporal,
                updated_at, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            weight_id, weights.structural, weights.functional,
            weights.behavioral, weights.temporal,
            now.isoformat(), "admin"
        ))
        conn.commit()

    return WeightsResponse(
        structural=weights.structural,
        functional=weights.functional,
        behavioral=weights.behavioral,
        temporal=weights.temporal,
        last_updated=now,
        updated_by="admin"
    )


@app.post("/api/analytics/run", response_model=AnalyticsResponse)
async def run_analytics(
    lob: Optional[str] = Query(default=None, description="Filter by LOB")
):
    """Run analytics engine and return results."""
    engine = get_engine()
    result = engine.run_analysis(lob_filter=lob)

    return AnalyticsResponse(
        generated_at=datetime.utcnow(),
        data={
            "employees_analyzed": result.total_employees,
            "grants_scored": result.total_grants,
            "high_assurance": result.high_assurance_count,
            "medium_assurance": result.medium_assurance_count,
            "low_assurance": result.low_assurance_count,
            "auto_certify_eligible": result.auto_certify_eligible_count,
            "lob_filter": lob
        }
    )


# ============================================================================
# Employees
# ============================================================================

@app.get("/api/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: str = Path(...)):
    """Get employee details."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Employee not found")

        row_dict = dict_from_row(row)
        return EmployeeResponse(
            id=row_dict["id"],
            employee_number=row_dict["employee_number"],
            email=row_dict["email"],
            full_name=row_dict["full_name"],
            job_title=row_dict["job_title"],
            job_code=row_dict["job_code"],
            job_family=row_dict["job_family"],
            job_level=row_dict["job_level"],
            team_id=row_dict["team_id"],
            manager_id=row_dict["manager_id"],
            location_id=row_dict["location_id"],
            employment_type=row_dict["employment_type"],
            status=row_dict["status"]
        )


@app.get("/api/employees/{employee_id}/access-summary", response_model=EmployeeAccessSummaryResponse)
async def get_employee_access_summary(employee_id: str = Path(...)):
    """Get employee's access summary with assurance breakdown."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get employee
        cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
        emp_row = cursor.fetchone()
        if not emp_row:
            raise HTTPException(status_code=404, detail="Employee not found")

        emp_dict = dict_from_row(emp_row)
        employee = EmployeeResponse(
            id=emp_dict["id"],
            employee_number=emp_dict["employee_number"],
            email=emp_dict["email"],
            full_name=emp_dict["full_name"],
            job_title=emp_dict["job_title"],
            job_code=emp_dict["job_code"],
            job_family=emp_dict["job_family"],
            job_level=emp_dict["job_level"],
            team_id=emp_dict["team_id"],
            manager_id=emp_dict["manager_id"],
            location_id=emp_dict["location_id"],
            employment_type=emp_dict["employment_type"],
            status=emp_dict["status"]
        )

        # Get access grants with resources
        cursor.execute("""
            SELECT ag.*, r.name as resource_name, r.sensitivity, r.system_id
            FROM access_grants ag
            JOIN resources r ON ag.resource_id = r.id
            WHERE ag.employee_id = ?
        """, (employee_id,))

        grants = []
        high_count = 0
        medium_count = 0
        low_count = 0
        dormant_count = 0
        auto_certify_count = 0

        for row in cursor.fetchall():
            row_dict = dict_from_row(row)
            grants.append({
                "id": row_dict["id"],
                "resource_name": row_dict["resource_name"],
                "system_id": row_dict["system_id"],
                "sensitivity": row_dict["sensitivity"],
                "granted_at": row_dict["granted_at"]
            })

        # Get peer count
        cursor.execute("""
            SELECT COUNT(DISTINCT id) FROM employees
            WHERE job_code = ? AND id != ?
        """, (emp_dict["job_code"], employee_id))
        peer_count = cursor.fetchone()[0]

        return EmployeeAccessSummaryResponse(
            employee=employee,
            total_grants=len(grants),
            high_assurance_count=high_count,
            medium_assurance_count=medium_count,
            low_assurance_count=low_count,
            dormant_access_count=dormant_count,
            auto_certify_eligible=auto_certify_count,
            peer_count=peer_count,
            clustering_consensus=1.0,
            grants=grants
        )


# ============================================================================
# Audit & Compliance
# ============================================================================

@app.get("/api/audit", response_model=PaginatedResponse)
async def list_audit_records(
    campaign_id: Optional[str] = None,
    action: Optional[DecisionAction] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100)
):
    """List audit records with filtering."""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM audit_records WHERE 1=1"
        params = []

        if campaign_id:
            query += " AND campaign_id = ?"
            params.append(campaign_id)

        if action:
            query += " AND action = ?"
            params.append(action.value)

        if start_date:
            query += " AND decision_at >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND decision_at <= ?"
            params.append(end_date.isoformat())

        # Get total
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Add pagination
        query += " ORDER BY decision_at DESC LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])

        cursor.execute(query, params)

        items = []
        for row in cursor.fetchall():
            row_dict = dict_from_row(row)
            items.append(AuditRecordResponse(
                id=row_dict["id"],
                review_item_id=row_dict["review_item_id"],
                action=row_dict["action"],
                decision_by=row_dict["decision_by"],
                decision_at=datetime.fromisoformat(row_dict["decision_at"]),
                rationale=row_dict["rationale"],
                assurance_score=row_dict["assurance_score"],
                auto_certified=bool(row_dict["auto_certified"]),
                campaign_id=row_dict["campaign_id"]
            ))

        total_pages = (total + page_size - 1) // page_size

        return PaginatedResponse(
            items=[item.model_dump() for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


@app.post("/api/campaigns/{campaign_id}/compliance-sample", response_model=ComplianceSampleResponse)
async def create_compliance_sample(
    campaign_id: str = Path(...),
    sample_size: int = Query(default=50, ge=10, le=500)
):
    """Create a compliance sample for 2nd line review."""
    now = datetime.utcnow()

    with get_db() as conn:
        cursor = conn.cursor()

        # Check campaign exists
        cursor.execute("SELECT id FROM campaigns WHERE id = ?", (campaign_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Get random sample of decided items
        cursor.execute("""
            SELECT ri.id, ri.assurance_score, ri.classification, ri.decision,
                   e.full_name as employee_name, r.name as resource_name
            FROM review_items ri
            JOIN employees e ON ri.employee_id = e.id
            JOIN access_grants ag ON ri.access_grant_id = ag.id
            JOIN resources r ON ag.resource_id = r.id
            WHERE ri.campaign_id = ? AND ri.status IN ('Decided', 'Auto-Approved')
            ORDER BY RANDOM()
            LIMIT ?
        """, (campaign_id, sample_size))

        sample_items = []
        for row in cursor.fetchall():
            row_dict = dict_from_row(row)
            sample_items.append({
                "review_item_id": row_dict["id"],
                "employee_name": row_dict["employee_name"],
                "resource_name": row_dict["resource_name"],
                "assurance_score": row_dict["assurance_score"],
                "classification": row_dict["classification"],
                "decision": json.loads(row_dict["decision"]) if row_dict["decision"] else None,
                "review_status": "pending",
                "review_notes": None
            })

        # Create sample record
        sample_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO compliance_samples (
                id, campaign_id, sample_size, created_at, created_by,
                status, items
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_id, campaign_id, len(sample_items), now.isoformat(),
            "compliance_officer", "pending", json.dumps(sample_items)
        ))
        conn.commit()

        return ComplianceSampleResponse(
            id=sample_id,
            campaign_id=campaign_id,
            sample_size=len(sample_items),
            created_at=now,
            created_by="compliance_officer",
            status="pending",
            items=sample_items,
            reviewed_count=0,
            flagged_count=0
        )


# ============================================================================
# Graduation Status
# ============================================================================

@app.get("/api/graduation-status", response_model=List[GraduationStatusResponse])
async def list_graduation_status():
    """List graduation status for all categories."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM graduation_status ORDER BY category")

        statuses = []
        for row in cursor.fetchall():
            row_dict = dict_from_row(row)
            statuses.append(GraduationStatusResponse(
                category=row_dict["category"],
                status=row_dict["status"],
                metrics=json.loads(row_dict["metrics"] or "{}"),
                meets_criteria=bool(row_dict["meets_criteria"]),
                last_evaluated=datetime.fromisoformat(row_dict["last_evaluated"]),
                graduated_at=datetime.fromisoformat(row_dict["graduated_at"]) if row_dict["graduated_at"] else None,
                approved_by=row_dict["approved_by"]
            ))

        return statuses


@app.get("/api/graduation-status/{category}", response_model=GraduationStatusResponse)
async def get_graduation_status(category: str = Path(...)):
    """Get graduation status for a specific category."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM graduation_status WHERE category = ?", (category,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Category not found")

        row_dict = dict_from_row(row)
        return GraduationStatusResponse(
            category=row_dict["category"],
            status=row_dict["status"],
            metrics=json.loads(row_dict["metrics"] or "{}"),
            meets_criteria=bool(row_dict["meets_criteria"]),
            last_evaluated=datetime.fromisoformat(row_dict["last_evaluated"]),
            graduated_at=datetime.fromisoformat(row_dict["graduated_at"]) if row_dict["graduated_at"] else None,
            approved_by=row_dict["approved_by"]
        )


# Run with: uvicorn src.api.main:app --reload
