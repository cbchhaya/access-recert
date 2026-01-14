"""
Pydantic Models for ARAS API
============================

Request/Response models for the REST API.

Author: Chiradeep Chhaya
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


# Enums
class CampaignStatus(str, Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    ARCHIVED = "Archived"


class CampaignScopeType(str, Enum):
    MANAGER = "manager"
    RESOURCE_OWNER = "resource_owner"
    LOB = "lob"
    SYSTEM = "system"


class ReviewItemStatus(str, Enum):
    PENDING = "Pending"
    AUTO_APPROVED = "Auto-Approved"
    NEEDS_REVIEW = "Needs-Review"
    DECIDED = "Decided"


class DecisionAction(str, Enum):
    CERTIFY = "Certify"
    REVOKE = "Revoke"
    MODIFY = "Modify"
    DELEGATE = "Delegate"


class AssuranceClassification(str, Enum):
    HIGH = "high_assurance"
    MEDIUM = "medium_assurance"
    LOW = "low_assurance"


class SensitivityLevel(str, Enum):
    PUBLIC = "Public"
    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    CRITICAL = "Critical"


# Request Models
class CampaignCreate(BaseModel):
    """Request model for creating a campaign."""
    name: str = Field(..., min_length=1, max_length=200)
    scope_type: CampaignScopeType
    scope_filter: Dict[str, Any] = Field(default_factory=dict)
    auto_approve_threshold: float = Field(default=80.0, ge=0, le=100)
    review_threshold: float = Field(default=50.0, ge=0, le=100)
    due_date: datetime


class CampaignUpdate(BaseModel):
    """Request model for updating a campaign."""
    name: Optional[str] = None
    status: Optional[CampaignStatus] = None
    auto_approve_threshold: Optional[float] = None
    review_threshold: Optional[float] = None
    due_date: Optional[datetime] = None


class DecisionCreate(BaseModel):
    """Request model for submitting a decision."""
    action: DecisionAction
    rationale: Optional[str] = None
    modification_details: Optional[str] = None
    delegated_to: Optional[str] = None


class BulkDecisionCreate(BaseModel):
    """Request model for bulk decisions."""
    review_item_ids: List[str]
    action: DecisionAction
    rationale: Optional[str] = None


class WeightsUpdate(BaseModel):
    """Request model for updating proximity weights."""
    structural: float = Field(..., ge=0, le=1)
    functional: float = Field(..., ge=0, le=1)
    behavioral: float = Field(..., ge=0, le=1)
    temporal: float = Field(..., ge=0, le=1)

    def validate_sum(self) -> bool:
        total = self.structural + self.functional + self.behavioral + self.temporal
        return abs(total - 1.0) < 0.01


class SampleReviewCreate(BaseModel):
    """Request model for compliance sample review."""
    decision: str = Field(..., pattern="^(confirmed|flagged)$")
    notes: Optional[str] = None


# Response Models
class EmployeeResponse(BaseModel):
    """Employee information response."""
    id: str
    employee_number: str
    email: str
    full_name: str
    job_title: str
    job_code: str
    job_family: str
    job_level: int
    team_id: Optional[str]
    manager_id: Optional[str]
    location_id: Optional[str]
    employment_type: str
    status: str


class ResourceResponse(BaseModel):
    """Resource information response."""
    id: str
    system_id: str
    resource_type: str
    name: str
    description: str
    sensitivity: SensitivityLevel


class AssuranceScoreResponse(BaseModel):
    """Assurance score details response."""
    overall_score: float
    peer_typicality: float
    sensitivity_ceiling: float
    usage_factor: float
    classification: AssuranceClassification
    auto_certify_eligible: bool
    peers_with_access: int
    total_peers: int
    peer_percentage: float
    usage_pattern: str
    days_since_last_use: Optional[int]
    explanations: List[str]


class ReviewItemResponse(BaseModel):
    """Review item response."""
    id: str
    campaign_id: str
    access_grant_id: str
    employee: EmployeeResponse
    resource: ResourceResponse
    assurance_score: AssuranceScoreResponse
    status: ReviewItemStatus
    clustering_consensus: float
    needs_clustering_review: bool
    clustering_disagreement: Optional[str]
    system_recommendation: Optional[str] = None  # What the system would recommend
    peer_group_size: Optional[int] = None  # Size of the peer group
    human_review_reason: Optional[str] = None  # Why human review is required
    decision: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime]


class ReviewItemSummary(BaseModel):
    """Lightweight review item for list views."""
    id: str
    employee_id: str
    employee_name: str
    employee_title: str
    resource_id: str
    resource_name: str
    resource_sensitivity: SensitivityLevel
    assurance_score: float
    classification: AssuranceClassification
    auto_certify_eligible: bool
    usage_pattern: str
    peer_percentage: float
    status: ReviewItemStatus
    explanations: List[str]


class CampaignResponse(BaseModel):
    """Campaign response."""
    id: str
    name: str
    scope_type: CampaignScopeType
    scope_filter: Dict[str, Any]
    auto_approve_threshold: float
    review_threshold: float
    start_date: datetime
    due_date: datetime
    status: CampaignStatus
    created_by: str
    created_at: datetime


class CampaignSummaryResponse(BaseModel):
    """Campaign summary with statistics."""
    campaign: CampaignResponse
    total_items: int
    pending_items: int
    auto_approved_items: int
    manually_reviewed_items: int
    certified_items: int
    revoked_items: int
    completion_percentage: float
    revocation_rate: float
    score_distribution: Dict[str, int]  # classification -> count


class CampaignProgressResponse(BaseModel):
    """Campaign progress by reviewer."""
    reviewer_id: str
    reviewer_name: str
    total_items: int
    completed_items: int
    pending_items: int
    completion_percentage: float


class WeightsResponse(BaseModel):
    """Proximity weights response."""
    structural: float
    functional: float
    behavioral: float
    temporal: float
    last_updated: Optional[datetime]
    updated_by: Optional[str]


class WeightsPreviewResponse(BaseModel):
    """Preview of weight change impact."""
    current_weights: WeightsResponse
    proposed_weights: WeightsUpdate
    impact: Dict[str, Any]  # Stats about score changes


class GraduationStatusResponse(BaseModel):
    """Category graduation status response."""
    category: str
    status: str  # "observation", "eligible", "graduated", "suspended"
    metrics: Dict[str, float]
    meets_criteria: bool
    last_evaluated: datetime
    graduated_at: Optional[datetime]
    approved_by: Optional[str]


class EmployeeAccessSummaryResponse(BaseModel):
    """Employee access summary response."""
    employee: EmployeeResponse
    total_grants: int
    high_assurance_count: int
    medium_assurance_count: int
    low_assurance_count: int
    dormant_access_count: int
    auto_certify_eligible: int
    peer_count: int
    clustering_consensus: float
    grants: List[Dict[str, Any]]


class AuditRecordResponse(BaseModel):
    """Audit record response."""
    id: str
    review_item_id: str
    action: str
    decision_by: str
    decision_at: datetime
    rationale: Optional[str]
    assurance_score: float
    auto_certified: bool
    campaign_id: str


class ComplianceSampleResponse(BaseModel):
    """Compliance sample response."""
    id: str
    campaign_id: str
    sample_size: int
    created_at: datetime
    created_by: str
    status: str  # "pending", "in_progress", "completed"
    items: List[Dict[str, Any]]
    reviewed_count: int
    flagged_count: int


class AnalyticsResponse(BaseModel):
    """General analytics response."""
    generated_at: datetime
    data: Dict[str, Any]


# Pagination
class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
