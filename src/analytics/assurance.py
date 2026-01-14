"""
Assurance Scoring Engine
========================

Calculates assurance scores for access grants based on:
- Peer Typicality: How common is this access among peers?
- Resource Sensitivity: How critical is the resource? (acts as CEILING)
- Usage Activity: Is the access being used?

Key Design Decision: Sensitivity acts as a CEILING, not a weight.
Critical-sensitivity access CANNOT be auto-certified regardless of typicality.

Author: Chiradeep Chhaya
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class SensitivityLevel(Enum):
    """Resource sensitivity levels."""
    PUBLIC = "Public"
    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    CRITICAL = "Critical"


@dataclass
class SensitivityConfig:
    """
    Sensitivity ceiling configuration.

    These are CEILINGS, not weights. The score cannot exceed this value
    for a given sensitivity level.
    """
    PUBLIC: float = 1.0       # Max score 100
    INTERNAL: float = 0.85    # Max score 85
    CONFIDENTIAL: float = 0.50  # Max score 50
    CRITICAL: float = 0.0     # Max score 0 - ALWAYS requires review

    def get_ceiling(self, level: str) -> float:
        """Get ceiling for a sensitivity level string."""
        level_upper = level.upper() if level else "INTERNAL"
        return getattr(self, level_upper, self.INTERNAL)


@dataclass
class UsagePattern:
    """Usage pattern for an access grant."""
    total_access_count: int = 0
    last_accessed_days_ago: Optional[int] = None
    access_count_30d: int = 0
    access_count_90d: int = 0
    days_since_grant: int = 0


@dataclass
class AssuranceScore:
    """Complete assurance score for an access grant."""
    grant_id: str
    employee_id: str
    resource_id: str

    # Overall score (0-100)
    overall_score: float = 0.0

    # Component scores (0-1)
    peer_typicality: float = 0.0
    sensitivity_ceiling: float = 0.0
    usage_factor: float = 0.0

    # Raw values before ceiling applied
    raw_score: float = 0.0

    # Peer context
    peers_with_access: int = 0
    total_peers: int = 0
    peer_percentage: float = 0.0

    # Usage context
    usage_pattern: str = ""  # "active", "occasional", "stale", "dormant"
    days_since_last_use: Optional[int] = None

    # Resource context
    resource_sensitivity: str = ""
    resource_name: str = ""

    # Classification
    classification: str = ""  # "high_assurance", "medium_assurance", "low_assurance"
    auto_certify_eligible: bool = False

    # Explanations for reviewer
    explanations: List[str] = field(default_factory=list)


@dataclass
class AssuranceConfig:
    """Configuration for assurance scoring."""
    # Score thresholds
    high_assurance_threshold: float = 80.0  # Above this = auto-certify eligible
    medium_assurance_threshold: float = 50.0  # Above this = review recommended
    # Below medium = review required

    # Sensitivity config
    sensitivity: SensitivityConfig = field(default_factory=SensitivityConfig)

    # Usage scoring
    active_days_threshold: int = 30  # Used within N days = "active"
    occasional_days_threshold: int = 90  # Used within N days = "occasional"
    stale_days_threshold: int = 365  # Used within N days = "stale"
    # Beyond stale = "dormant"

    # Component weights (for raw score before ceiling)
    weight_typicality: float = 0.6
    weight_usage: float = 0.4


class AssuranceScorer:
    """
    Calculates assurance scores for access grants.

    The assurance score represents confidence that an access grant is appropriate.
    Higher scores indicate higher confidence; lower scores require more scrutiny.

    Formula:
        raw_score = (weight_typicality * typicality) + (weight_usage * usage)
        final_score = raw_score * sensitivity_ceiling * 100

    Key: Sensitivity ceiling CAPS the score. Critical access = ceiling of 0.
    """

    def __init__(self, config: Optional[AssuranceConfig] = None):
        self.config = config or AssuranceConfig()

    def calculate_typicality(
        self,
        employee_id: str,
        resource_id: str,
        peer_ids: List[str],
        access_by_employee: Dict[str, set]
    ) -> Tuple[float, int, int]:
        """
        Calculate peer typicality for an access grant.

        Returns:
            Tuple of (typicality_score, peers_with_access, total_peers)
        """
        if not peer_ids:
            # No peers = can't determine typicality, assume low
            return 0.5, 0, 0

        total_peers = len(peer_ids)
        peers_with_access = sum(
            1 for peer_id in peer_ids
            if resource_id in access_by_employee.get(peer_id, set())
        )

        if total_peers > 0:
            typicality = peers_with_access / total_peers
        else:
            typicality = 0.5

        return typicality, peers_with_access, total_peers

    def calculate_usage_factor(self, usage: UsagePattern) -> Tuple[float, str]:
        """
        Calculate usage factor and classify usage pattern.

        Returns:
            Tuple of (usage_factor, usage_pattern_label)
        """
        # Never used
        if usage.total_access_count == 0:
            return 0.1, "dormant"

        # Check recency
        if usage.last_accessed_days_ago is None:
            return 0.1, "dormant"

        if usage.last_accessed_days_ago <= self.config.active_days_threshold:
            # Active: used in last 30 days
            # Score based on frequency
            if usage.access_count_30d >= 10:
                return 1.0, "active"
            elif usage.access_count_30d >= 3:
                return 0.9, "active"
            else:
                return 0.8, "active"

        elif usage.last_accessed_days_ago <= self.config.occasional_days_threshold:
            # Occasional: used in last 90 days
            return 0.6, "occasional"

        elif usage.last_accessed_days_ago <= self.config.stale_days_threshold:
            # Stale: used in last year
            return 0.3, "stale"

        else:
            # Dormant: not used in over a year
            return 0.1, "dormant"

    def calculate_score(
        self,
        grant_id: str,
        employee_id: str,
        resource_id: str,
        resource_sensitivity: str,
        resource_name: str,
        peer_ids: List[str],
        access_by_employee: Dict[str, set],
        usage: UsagePattern
    ) -> AssuranceScore:
        """
        Calculate complete assurance score for an access grant.

        Args:
            grant_id: Access grant ID
            employee_id: Employee ID
            resource_id: Resource ID
            resource_sensitivity: Sensitivity level string
            resource_name: Human-readable resource name
            peer_ids: List of peer employee IDs
            access_by_employee: Mapping of employee_id to set of resource_ids
            usage: Usage pattern data

        Returns:
            Complete AssuranceScore object
        """
        # Calculate components
        typicality, peers_with, total_peers = self.calculate_typicality(
            employee_id, resource_id, peer_ids, access_by_employee
        )

        usage_factor, usage_pattern = self.calculate_usage_factor(usage)

        # Get sensitivity ceiling
        sensitivity_ceiling = self.config.sensitivity.get_ceiling(resource_sensitivity)

        # Calculate raw score (before ceiling)
        raw_score = (
            self.config.weight_typicality * typicality +
            self.config.weight_usage * usage_factor
        )

        # Apply ceiling
        final_score = raw_score * sensitivity_ceiling * 100

        # Peer percentage
        peer_percentage = (peers_with / total_peers * 100) if total_peers > 0 else 0

        # Classify
        if final_score >= self.config.high_assurance_threshold:
            classification = "high_assurance"
            auto_eligible = True
        elif final_score >= self.config.medium_assurance_threshold:
            classification = "medium_assurance"
            auto_eligible = False
        else:
            classification = "low_assurance"
            auto_eligible = False

        # Critical sensitivity = NEVER auto-certify
        if sensitivity_ceiling == 0:
            auto_eligible = False

        # Generate explanations
        explanations = self._generate_explanations(
            typicality=typicality,
            peer_percentage=peer_percentage,
            peers_with=peers_with,
            total_peers=total_peers,
            usage_pattern=usage_pattern,
            usage_factor=usage_factor,
            sensitivity=resource_sensitivity,
            sensitivity_ceiling=sensitivity_ceiling,
            final_score=final_score,
            days_since_last_use=usage.last_accessed_days_ago
        )

        return AssuranceScore(
            grant_id=grant_id,
            employee_id=employee_id,
            resource_id=resource_id,
            overall_score=round(final_score, 1),
            peer_typicality=round(typicality, 3),
            sensitivity_ceiling=sensitivity_ceiling,
            usage_factor=round(usage_factor, 3),
            raw_score=round(raw_score, 3),
            peers_with_access=peers_with,
            total_peers=total_peers,
            peer_percentage=round(peer_percentage, 1),
            usage_pattern=usage_pattern,
            days_since_last_use=usage.last_accessed_days_ago,
            resource_sensitivity=resource_sensitivity,
            resource_name=resource_name,
            classification=classification,
            auto_certify_eligible=auto_eligible,
            explanations=explanations
        )

    def _generate_explanations(
        self,
        typicality: float,
        peer_percentage: float,
        peers_with: int,
        total_peers: int,
        usage_pattern: str,
        usage_factor: float,
        sensitivity: str,
        sensitivity_ceiling: float,
        final_score: float,
        days_since_last_use: Optional[int]
    ) -> List[str]:
        """Generate human-readable explanations for the score."""
        explanations = []

        # Peer comparison
        if total_peers > 0:
            if peer_percentage >= 80:
                explanations.append(
                    f"Common access: {peer_percentage:.0f}% of peers ({peers_with}/{total_peers}) have this access"
                )
            elif peer_percentage >= 50:
                explanations.append(
                    f"Moderate access: {peer_percentage:.0f}% of peers ({peers_with}/{total_peers}) have this access"
                )
            elif peer_percentage >= 20:
                explanations.append(
                    f"Uncommon access: Only {peer_percentage:.0f}% of peers ({peers_with}/{total_peers}) have this access"
                )
            else:
                explanations.append(
                    f"Unusual access: Only {peer_percentage:.0f}% of peers ({peers_with}/{total_peers}) have this access"
                )
        else:
            explanations.append("No peer group available for comparison")

        # Usage
        if usage_pattern == "active":
            explanations.append(f"Active usage: Access used recently")
        elif usage_pattern == "occasional":
            explanations.append(f"Occasional usage: Last used {days_since_last_use} days ago")
        elif usage_pattern == "stale":
            explanations.append(f"Stale access: Last used {days_since_last_use} days ago")
        elif usage_pattern == "dormant":
            if days_since_last_use:
                explanations.append(f"Dormant access: Not used in {days_since_last_use} days")
            else:
                explanations.append("Dormant access: Never used")

        # Sensitivity
        if sensitivity_ceiling == 0:
            explanations.append(f"Critical sensitivity: Requires mandatory review (cannot auto-certify)")
        elif sensitivity_ceiling < 0.6:
            explanations.append(f"Confidential sensitivity: Score capped at {sensitivity_ceiling*100:.0f}")
        elif sensitivity_ceiling < 0.9:
            explanations.append(f"Internal sensitivity: Standard business access")

        # Final assessment
        if final_score >= 80:
            explanations.append("High assurance: Eligible for auto-certification")
        elif final_score >= 50:
            explanations.append("Medium assurance: Review recommended")
        else:
            explanations.append("Low assurance: Review required")

        return explanations

    def score_all_grants(
        self,
        access_grants: List[Dict],
        resources: Dict[str, Dict],
        consensus_results: Dict[str, "ConsensusResult"],
        activity_summaries: Dict[str, Dict]
    ) -> Dict[str, AssuranceScore]:
        """
        Score all access grants.

        Args:
            access_grants: List of access grant records
            resources: Dictionary mapping resource_id to resource record
            consensus_results: Dictionary mapping employee_id to ConsensusResult (from clustering)
            activity_summaries: Dictionary mapping (employee_id, resource_id) to activity summary

        Returns:
            Dictionary mapping grant_id to AssuranceScore
        """
        logger.info(f"Scoring {len(access_grants)} access grants")

        # Build access_by_employee lookup
        access_by_employee: Dict[str, set] = {}
        for grant in access_grants:
            emp_id = grant["employee_id"]
            res_id = grant["resource_id"]
            if emp_id not in access_by_employee:
                access_by_employee[emp_id] = set()
            access_by_employee[emp_id].add(res_id)

        scores = {}
        for grant in access_grants:
            grant_id = grant["id"]
            emp_id = grant["employee_id"]
            res_id = grant["resource_id"]

            # Get resource info
            resource = resources.get(res_id, {})
            sensitivity = resource.get("sensitivity", "Internal")
            resource_name = resource.get("name", res_id)

            # Get peer info from consensus
            consensus = consensus_results.get(emp_id)
            if consensus:
                peer_ids = consensus.peer_ids
            else:
                peer_ids = []

            # Get usage info
            activity_key = f"{emp_id}:{res_id}"
            activity = activity_summaries.get(activity_key, {})

            # Calculate days since last use
            last_accessed = activity.get("last_accessed")
            days_since_last = activity.get("days_since_last_use")

            usage = UsagePattern(
                total_access_count=activity.get("total_access_count", 0),
                last_accessed_days_ago=days_since_last,
                access_count_30d=activity.get("access_count_30d", 0),
                access_count_90d=activity.get("access_count_90d", 0),
                days_since_grant=activity.get("days_since_grant", 0)
            )

            # Calculate score
            score = self.calculate_score(
                grant_id=grant_id,
                employee_id=emp_id,
                resource_id=res_id,
                resource_sensitivity=sensitivity,
                resource_name=resource_name,
                peer_ids=peer_ids,
                access_by_employee=access_by_employee,
                usage=usage
            )

            scores[grant_id] = score

        # Log summary
        high = sum(1 for s in scores.values() if s.classification == "high_assurance")
        medium = sum(1 for s in scores.values() if s.classification == "medium_assurance")
        low = sum(1 for s in scores.values() if s.classification == "low_assurance")
        auto_eligible = sum(1 for s in scores.values() if s.auto_certify_eligible)

        logger.info(f"Scoring complete: {high} high, {medium} medium, {low} low assurance")
        if len(scores) > 0:
            logger.info(f"Auto-certification eligible: {auto_eligible}/{len(scores)} ({auto_eligible/len(scores)*100:.1f}%)")
        else:
            logger.info("No scores to calculate - empty grant set")

        return scores
