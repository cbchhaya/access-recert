"""
Peer Proximity Calculator
=========================

Calculates multi-dimensional similarity between employees to determine
peer relationships for access comparison.

Dimensions:
- Structural: Organizational placement (manager, team, LOB)
- Functional: Job attributes (title, family, cost center)
- Behavioral: Access and activity patterns
- Temporal: Career stage (tenure, time in role)

Author: Chiradeep Chhaya
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ProximityWeights:
    """Configurable weights for proximity dimensions."""
    structural: float = 0.25
    functional: float = 0.35
    behavioral: float = 0.30
    temporal: float = 0.10

    def validate(self) -> bool:
        """Ensure weights sum to 1.0."""
        total = self.structural + self.functional + self.behavioral + self.temporal
        return abs(total - 1.0) < 0.001

    def normalize(self) -> "ProximityWeights":
        """Normalize weights to sum to 1.0."""
        total = self.structural + self.functional + self.behavioral + self.temporal
        if total == 0:
            return ProximityWeights()
        return ProximityWeights(
            structural=self.structural / total,
            functional=self.functional / total,
            behavioral=self.behavioral / total,
            temporal=self.temporal / total
        )


@dataclass
class EmployeeFeatures:
    """Extracted features for an employee."""
    employee_id: str

    # Structural features
    manager_id: Optional[str] = None
    team_id: Optional[str] = None
    sub_lob_id: Optional[str] = None
    lob_id: Optional[str] = None
    location_id: Optional[str] = None

    # Functional features
    job_title: str = ""
    job_code: str = ""
    job_family: str = ""
    job_level: int = 0
    cost_center_id: Optional[str] = None

    # Behavioral features (computed)
    access_set: Set[str] = field(default_factory=set)  # Set of resource_ids
    activity_vector: Dict[str, float] = field(default_factory=dict)  # resource_id -> usage intensity

    # Temporal features
    tenure_days: int = 0
    time_in_role_days: int = 0
    hire_quarter: str = ""  # e.g., "2023-Q1"


class PeerProximityCalculator:
    """
    Calculates peer proximity scores between employees.

    The proximity score is a weighted combination of four dimensions:
    - Structural proximity: Organizational placement
    - Functional proximity: Job attributes similarity
    - Behavioral proximity: Access and activity pattern similarity
    - Temporal proximity: Career stage similarity
    """

    def __init__(self, weights: Optional[ProximityWeights] = None):
        self.weights = weights or ProximityWeights()
        if not self.weights.validate():
            self.weights = self.weights.normalize()
            logger.warning("Weights did not sum to 1.0, normalized automatically")

        # Caches for computed values
        self._manager_chain_cache: Dict[str, List[str]] = {}
        self._features_cache: Dict[str, EmployeeFeatures] = {}

    def extract_features(
        self,
        employees: List[Dict],
        access_grants: List[Dict],
        activity_summaries: List[Dict],
        teams: List[Dict],
        sub_lobs: List[Dict]
    ) -> Dict[str, EmployeeFeatures]:
        """
        Extract features for all employees.

        Args:
            employees: List of employee records
            access_grants: List of access grant records
            activity_summaries: List of activity summary records
            teams: List of team records
            sub_lobs: List of sub-LOB records

        Returns:
            Dictionary mapping employee_id to EmployeeFeatures
        """
        logger.info(f"Extracting features for {len(employees)} employees")

        # Build lookup tables
        team_lookup = {t["id"]: t for t in teams}
        sub_lob_lookup = {s["id"]: s for s in sub_lobs}

        # Build access sets per employee
        access_by_employee: Dict[str, Set[str]] = defaultdict(set)
        for grant in access_grants:
            access_by_employee[grant["employee_id"]].add(grant["resource_id"])

        # Build activity vectors per employee
        activity_by_employee: Dict[str, Dict[str, float]] = defaultdict(dict)
        for summary in activity_summaries:
            emp_id = summary["employee_id"]
            res_id = summary["resource_id"]
            # Normalize activity to 0-1 based on 30-day count
            count_30d = summary.get("access_count_30d", 0) or 0
            # Cap at 100 accesses for normalization
            intensity = min(count_30d / 100.0, 1.0)
            activity_by_employee[emp_id][res_id] = intensity

        # Extract features for each employee
        features = {}
        for emp in employees:
            emp_id = emp["id"]

            # Get team and LOB info
            team = team_lookup.get(emp.get("team_id"))
            sub_lob_id = team.get("sub_lob_id") if team else None
            lob_id = team.get("lob_id") if team else None

            if sub_lob_id and not lob_id:
                sub_lob = sub_lob_lookup.get(sub_lob_id)
                lob_id = sub_lob.get("lob_id") if sub_lob else None

            # Calculate tenure
            from datetime import datetime
            hire_date = emp.get("hire_date")
            role_start_date = emp.get("role_start_date")

            tenure_days = 0
            time_in_role_days = 0
            hire_quarter = ""

            if hire_date:
                try:
                    hd = datetime.fromisoformat(hire_date.replace("Z", "+00:00"))
                    tenure_days = (datetime.now(hd.tzinfo) - hd).days if hd.tzinfo else (datetime.now() - hd).days
                    quarter = (hd.month - 1) // 3 + 1
                    hire_quarter = f"{hd.year}-Q{quarter}"
                except:
                    pass

            if role_start_date:
                try:
                    rd = datetime.fromisoformat(role_start_date.replace("Z", "+00:00"))
                    time_in_role_days = (datetime.now(rd.tzinfo) - rd).days if rd.tzinfo else (datetime.now() - rd).days
                except:
                    pass

            features[emp_id] = EmployeeFeatures(
                employee_id=emp_id,
                manager_id=emp.get("manager_id"),
                team_id=emp.get("team_id"),
                sub_lob_id=sub_lob_id,
                lob_id=lob_id,
                location_id=emp.get("location_id"),
                job_title=emp.get("job_title", ""),
                job_code=emp.get("job_code", ""),
                job_family=emp.get("job_family", ""),
                job_level=emp.get("job_level", 0),
                cost_center_id=emp.get("cost_center_id"),
                access_set=access_by_employee.get(emp_id, set()),
                activity_vector=activity_by_employee.get(emp_id, {}),
                tenure_days=tenure_days,
                time_in_role_days=time_in_role_days,
                hire_quarter=hire_quarter
            )

        self._features_cache = features
        logger.info(f"Extracted features for {len(features)} employees")
        return features

    def calculate_structural_proximity(
        self,
        emp_a: EmployeeFeatures,
        emp_b: EmployeeFeatures,
        manager_chains: Optional[Dict[str, List[str]]] = None
    ) -> float:
        """
        Calculate structural proximity based on organizational placement.

        Factors:
        - Same direct manager: 0.3
        - Manager distance (hops to common ancestor): 0.2 * (1 / (1 + hops))
        - Same team: 0.2
        - Same sub-LOB: 0.15
        - Same LOB: 0.1
        - Same location: 0.05
        """
        score = 0.0

        # Same direct manager
        if emp_a.manager_id and emp_a.manager_id == emp_b.manager_id:
            score += 0.3

        # Manager distance (simplified - just check if same manager chain)
        # In a full implementation, we'd calculate actual hierarchy distance
        if manager_chains:
            chain_a = manager_chains.get(emp_a.employee_id, [])
            chain_b = manager_chains.get(emp_b.employee_id, [])
            common = set(chain_a) & set(chain_b)
            if common:
                # Find minimum distance to common ancestor
                min_dist = float('inf')
                for ancestor in common:
                    dist_a = chain_a.index(ancestor) if ancestor in chain_a else 999
                    dist_b = chain_b.index(ancestor) if ancestor in chain_b else 999
                    min_dist = min(min_dist, dist_a + dist_b)
                if min_dist < float('inf'):
                    score += 0.2 * (1.0 / (1.0 + min_dist))

        # Same team
        if emp_a.team_id and emp_a.team_id == emp_b.team_id:
            score += 0.2

        # Same sub-LOB
        if emp_a.sub_lob_id and emp_a.sub_lob_id == emp_b.sub_lob_id:
            score += 0.15

        # Same LOB
        if emp_a.lob_id and emp_a.lob_id == emp_b.lob_id:
            score += 0.1

        # Same location
        if emp_a.location_id and emp_a.location_id == emp_b.location_id:
            score += 0.05

        return min(score, 1.0)

    def calculate_functional_proximity(
        self,
        emp_a: EmployeeFeatures,
        emp_b: EmployeeFeatures
    ) -> float:
        """
        Calculate functional proximity based on job attributes.

        Factors:
        - Same job code: 0.35
        - Same job family: 0.25
        - Job level distance: 0.2 * (1 - |level_diff| / 7)
        - Same cost center: 0.2
        """
        score = 0.0

        # Same job code
        if emp_a.job_code and emp_a.job_code == emp_b.job_code:
            score += 0.35

        # Same job family
        if emp_a.job_family and emp_a.job_family == emp_b.job_family:
            score += 0.25

        # Job level distance (closer levels = higher score)
        if emp_a.job_level > 0 and emp_b.job_level > 0:
            level_diff = abs(emp_a.job_level - emp_b.job_level)
            # Normalize by max level difference (assume 7 levels)
            level_score = max(0, 1.0 - level_diff / 7.0)
            score += 0.2 * level_score

        # Same cost center
        if emp_a.cost_center_id and emp_a.cost_center_id == emp_b.cost_center_id:
            score += 0.2

        return min(score, 1.0)

    def calculate_behavioral_proximity(
        self,
        emp_a: EmployeeFeatures,
        emp_b: EmployeeFeatures
    ) -> float:
        """
        Calculate behavioral proximity based on access and activity patterns.

        Factors:
        - Access overlap (Jaccard index): 0.5
        - Activity pattern similarity (cosine): 0.5
        """
        score = 0.0

        # Access overlap (Jaccard index)
        if emp_a.access_set or emp_b.access_set:
            intersection = len(emp_a.access_set & emp_b.access_set)
            union = len(emp_a.access_set | emp_b.access_set)
            if union > 0:
                jaccard = intersection / union
                score += 0.5 * jaccard

        # Activity pattern similarity (cosine similarity)
        if emp_a.activity_vector and emp_b.activity_vector:
            # Get all resources
            all_resources = set(emp_a.activity_vector.keys()) | set(emp_b.activity_vector.keys())
            if all_resources:
                vec_a = np.array([emp_a.activity_vector.get(r, 0) for r in all_resources])
                vec_b = np.array([emp_b.activity_vector.get(r, 0) for r in all_resources])

                norm_a = np.linalg.norm(vec_a)
                norm_b = np.linalg.norm(vec_b)

                if norm_a > 0 and norm_b > 0:
                    cosine_sim = np.dot(vec_a, vec_b) / (norm_a * norm_b)
                    score += 0.5 * cosine_sim

        return min(score, 1.0)

    def calculate_temporal_proximity(
        self,
        emp_a: EmployeeFeatures,
        emp_b: EmployeeFeatures
    ) -> float:
        """
        Calculate temporal proximity based on career stage.

        Factors:
        - Tenure similarity (Gaussian): 0.4
        - Time in role similarity (Gaussian): 0.3
        - Same hire cohort: 0.3
        """
        score = 0.0

        # Tenure similarity (Gaussian with sigma = 365 days)
        if emp_a.tenure_days > 0 and emp_b.tenure_days > 0:
            tenure_diff = abs(emp_a.tenure_days - emp_b.tenure_days)
            sigma = 365  # 1 year standard deviation
            tenure_sim = np.exp(-(tenure_diff ** 2) / (2 * sigma ** 2))
            score += 0.4 * tenure_sim

        # Time in role similarity
        if emp_a.time_in_role_days > 0 and emp_b.time_in_role_days > 0:
            role_diff = abs(emp_a.time_in_role_days - emp_b.time_in_role_days)
            sigma = 180  # 6 months standard deviation
            role_sim = np.exp(-(role_diff ** 2) / (2 * sigma ** 2))
            score += 0.3 * role_sim

        # Same hire cohort
        if emp_a.hire_quarter and emp_a.hire_quarter == emp_b.hire_quarter:
            score += 0.3

        return min(score, 1.0)

    def calculate_proximity(
        self,
        emp_a: EmployeeFeatures,
        emp_b: EmployeeFeatures,
        manager_chains: Optional[Dict[str, List[str]]] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate overall proximity score between two employees.

        Returns:
            Tuple of (overall_score, component_scores)
        """
        structural = self.calculate_structural_proximity(emp_a, emp_b, manager_chains)
        functional = self.calculate_functional_proximity(emp_a, emp_b)
        behavioral = self.calculate_behavioral_proximity(emp_a, emp_b)
        temporal = self.calculate_temporal_proximity(emp_a, emp_b)

        overall = (
            self.weights.structural * structural +
            self.weights.functional * functional +
            self.weights.behavioral * behavioral +
            self.weights.temporal * temporal
        )

        components = {
            "structural": structural,
            "functional": functional,
            "behavioral": behavioral,
            "temporal": temporal
        }

        return overall, components

    def calculate_pairwise_proximity_matrix(
        self,
        employee_ids: List[str],
        features: Dict[str, EmployeeFeatures],
        manager_chains: Optional[Dict[str, List[str]]] = None,
        block_by_lob: bool = True
    ) -> np.ndarray:
        """
        Calculate pairwise proximity matrix for a set of employees.

        Args:
            employee_ids: List of employee IDs to compare
            features: Feature dictionary from extract_features()
            manager_chains: Optional manager chain lookup
            block_by_lob: If True, only calculate proximity within same LOB (performance optimization)

        Returns:
            Symmetric proximity matrix (n x n)
        """
        n = len(employee_ids)
        logger.info(f"Calculating {n}x{n} proximity matrix (block_by_lob={block_by_lob})")

        matrix = np.zeros((n, n))
        id_to_idx = {emp_id: i for i, emp_id in enumerate(employee_ids)}

        # Group by LOB if blocking
        lob_groups: Dict[str, List[str]] = defaultdict(list)
        for emp_id in employee_ids:
            feat = features.get(emp_id)
            if feat:
                lob_id = feat.lob_id or "unknown"
                lob_groups[lob_id].append(emp_id)

        comparisons = 0
        if block_by_lob:
            # Only compare within LOB
            for lob_id, lob_employees in lob_groups.items():
                for i, emp_a_id in enumerate(lob_employees):
                    feat_a = features.get(emp_a_id)
                    if not feat_a:
                        continue
                    idx_a = id_to_idx[emp_a_id]

                    for emp_b_id in lob_employees[i+1:]:
                        feat_b = features.get(emp_b_id)
                        if not feat_b:
                            continue
                        idx_b = id_to_idx[emp_b_id]

                        proximity, _ = self.calculate_proximity(feat_a, feat_b, manager_chains)
                        matrix[idx_a, idx_b] = proximity
                        matrix[idx_b, idx_a] = proximity
                        comparisons += 1
        else:
            # Full pairwise comparison
            for i, emp_a_id in enumerate(employee_ids):
                feat_a = features.get(emp_a_id)
                if not feat_a:
                    continue

                for j, emp_b_id in enumerate(employee_ids[i+1:], i+1):
                    feat_b = features.get(emp_b_id)
                    if not feat_b:
                        continue

                    proximity, _ = self.calculate_proximity(feat_a, feat_b, manager_chains)
                    matrix[i, j] = proximity
                    matrix[j, i] = proximity
                    comparisons += 1

        # Diagonal is 1.0 (self-similarity)
        np.fill_diagonal(matrix, 1.0)

        logger.info(f"Completed {comparisons} pairwise comparisons")
        return matrix

    def find_peers(
        self,
        employee_id: str,
        features: Dict[str, EmployeeFeatures],
        top_k: int = 20,
        min_proximity: float = 0.3,
        manager_chains: Optional[Dict[str, List[str]]] = None
    ) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Find top-k peers for a given employee.

        Args:
            employee_id: Target employee
            features: Feature dictionary
            top_k: Maximum number of peers to return
            min_proximity: Minimum proximity threshold
            manager_chains: Optional manager chain lookup

        Returns:
            List of (peer_id, proximity_score, component_scores) tuples
        """
        target = features.get(employee_id)
        if not target:
            return []

        peers = []
        for other_id, other_features in features.items():
            if other_id == employee_id:
                continue

            proximity, components = self.calculate_proximity(
                target, other_features, manager_chains
            )

            if proximity >= min_proximity:
                peers.append((other_id, proximity, components))

        # Sort by proximity descending
        peers.sort(key=lambda x: x[1], reverse=True)

        return peers[:top_k]
