"""
Analytics Engine
================

Main orchestration engine that ties together:
- Peer proximity calculation
- Multi-strategy clustering
- Assurance scoring

Provides a unified interface for analyzing access recertification data.

Author: Chiradeep Chhaya
"""

import logging
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from .peer_proximity import PeerProximityCalculator, ProximityWeights, EmployeeFeatures
from .clustering import MultiStrategyClusterer, ClusteringConfig, ClusteringStrategy, ConsensusResult
from .assurance import AssuranceScorer, AssuranceConfig, AssuranceScore

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsResult:
    """Complete analytics result for a certification campaign."""

    # Employee features
    employee_features: Dict[str, EmployeeFeatures]

    # Clustering results
    cluster_assignments: Dict[ClusteringStrategy, Dict[str, Any]]
    consensus_results: Dict[str, ConsensusResult]

    # Assurance scores
    assurance_scores: Dict[str, AssuranceScore]

    # Summary statistics
    total_employees: int = 0
    total_grants: int = 0
    high_assurance_count: int = 0
    medium_assurance_count: int = 0
    low_assurance_count: int = 0
    auto_certify_eligible_count: int = 0
    needs_human_review_count: int = 0
    clustering_disagreement_count: int = 0


class AnalyticsEngine:
    """
    Main analytics engine for access recertification.

    This engine orchestrates:
    1. Loading data from SQLite database
    2. Extracting employee features
    3. Calculating peer proximity
    4. Running multi-strategy clustering
    5. Calculating assurance scores
    6. Generating review recommendations
    """

    def __init__(
        self,
        db_path: str,
        proximity_weights: Optional[ProximityWeights] = None,
        clustering_config: Optional[ClusteringConfig] = None,
        assurance_config: Optional[AssuranceConfig] = None
    ):
        self.db_path = db_path
        self.proximity_calculator = PeerProximityCalculator(weights=proximity_weights)
        self.clusterer = MultiStrategyClusterer(config=clustering_config)
        self.scorer = AssuranceScorer(config=assurance_config)

        # Data caches
        self._employees: List[Dict] = []
        self._teams: List[Dict] = []
        self._sub_lobs: List[Dict] = []
        self._lobs: List[Dict] = []
        self._resources: Dict[str, Dict] = {}
        self._access_grants: List[Dict] = []
        self._activity_summaries: Dict[str, Dict] = {}

    def load_data(self) -> None:
        """Load all required data from SQLite database."""
        logger.info(f"Loading data from {self.db_path}")

        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        try:
            # Load employees
            cursor = conn.execute("SELECT * FROM employees WHERE status = 'Active'")
            self._employees = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Loaded {len(self._employees)} employees")

            # Load teams
            cursor = conn.execute("SELECT * FROM teams")
            self._teams = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Loaded {len(self._teams)} teams")

            # Load sub-LOBs
            cursor = conn.execute("SELECT * FROM sub_lobs")
            self._sub_lobs = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Loaded {len(self._sub_lobs)} sub-LOBs")

            # Load LOBs
            cursor = conn.execute("SELECT * FROM lobs")
            self._lobs = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Loaded {len(self._lobs)} LOBs")

            # Load resources
            cursor = conn.execute("SELECT * FROM resources")
            resources = [dict(row) for row in cursor.fetchall()]
            self._resources = {r["id"]: r for r in resources}
            logger.info(f"Loaded {len(self._resources)} resources")

            # Load access grants
            cursor = conn.execute("""
                SELECT ag.* FROM access_grants ag
                JOIN employees e ON ag.employee_id = e.id
                WHERE e.status = 'Active'
            """)
            self._access_grants = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Loaded {len(self._access_grants)} access grants")

            # Load activity summaries
            cursor = conn.execute("SELECT * FROM activity_summaries")
            for row in cursor.fetchall():
                row_dict = dict(row)
                key = f"{row_dict['employee_id']}:{row_dict['resource_id']}"
                self._activity_summaries[key] = row_dict
            logger.info(f"Loaded {len(self._activity_summaries)} activity summaries")

        finally:
            conn.close()

    def run_analysis(
        self,
        lob_filter: Optional[str] = None,
        strategies: Optional[List[ClusteringStrategy]] = None,
        block_by_lob: bool = True
    ) -> AnalyticsResult:
        """
        Run complete analytics pipeline.

        Args:
            lob_filter: Optional LOB ID to filter employees
            strategies: List of clustering strategies to use
            block_by_lob: Whether to block proximity calculations by LOB

        Returns:
            Complete AnalyticsResult
        """
        logger.info("Starting analytics pipeline...")

        # Filter employees if LOB specified
        if lob_filter:
            # Support both LOB ID and LOB name
            lob_id = lob_filter
            if not lob_filter.startswith("lob_"):
                # Look up by name
                matching_lobs = [l for l in self._lobs if l.get("name") == lob_filter]
                if matching_lobs:
                    lob_id = matching_lobs[0]["id"]
                else:
                    logger.warning(f"LOB not found: {lob_filter}")
                    lob_id = None

            if lob_id:
                team_ids_in_lob = {
                    t["id"] for t in self._teams if t.get("lob_id") == lob_id
                }
                employees = [e for e in self._employees if e.get("team_id") in team_ids_in_lob]
                logger.info(f"Filtered to {len(employees)} employees in LOB {lob_filter} (id: {lob_id})")
            else:
                employees = []
                logger.warning(f"No employees found for LOB filter: {lob_filter}")
        else:
            employees = self._employees

        employee_ids = [e["id"] for e in employees]

        # Handle empty employee set
        if not employees:
            logger.warning("No employees to analyze")
            return AnalyticsResult(
                employee_features={},
                cluster_assignments={},
                consensus_results={},
                assurance_scores={},
                total_employees=0,
                total_grants=0,
                high_assurance_count=0,
                medium_assurance_count=0,
                low_assurance_count=0,
                auto_certify_eligible_count=0,
                needs_human_review_count=0,
                clustering_disagreement_count=0
            )

        # Filter access grants to these employees
        employee_id_set = set(employee_ids)
        access_grants = [
            g for g in self._access_grants
            if g["employee_id"] in employee_id_set
        ]
        logger.info(f"Filtered to {len(access_grants)} access grants")

        # Filter activity summaries
        activity_summaries = {
            k: v for k, v in self._activity_summaries.items()
            if v["employee_id"] in employee_id_set
        }

        # Step 1: Extract features
        logger.info("Step 1: Extracting employee features...")
        features = self.proximity_calculator.extract_features(
            employees=employees,
            access_grants=access_grants,
            activity_summaries=list(activity_summaries.values()),
            teams=self._teams,
            sub_lobs=self._sub_lobs
        )

        # Step 2: Calculate proximity matrix
        logger.info("Step 2: Calculating proximity matrix...")
        proximity_matrix = self.proximity_calculator.calculate_pairwise_proximity_matrix(
            employee_ids=employee_ids,
            features=features,
            block_by_lob=block_by_lob
        )

        # Step 3: Run clustering
        logger.info("Step 3: Running multi-strategy clustering...")
        cluster_assignments = self.clusterer.run_all_strategies(
            proximity_matrix=proximity_matrix,
            employee_ids=employee_ids,
            strategies=strategies
        )

        # Step 4: Analyze consensus
        logger.info("Step 4: Analyzing clustering consensus...")
        consensus_results = self.clusterer.analyze_consensus(
            all_assignments=cluster_assignments,
            employee_ids=employee_ids
        )

        # Step 5: Calculate assurance scores
        logger.info("Step 5: Calculating assurance scores...")
        assurance_scores = self.scorer.score_all_grants(
            access_grants=access_grants,
            resources=self._resources,
            consensus_results=consensus_results,
            activity_summaries=activity_summaries
        )

        # Calculate summary statistics
        high_assurance = sum(1 for s in assurance_scores.values() if s.classification == "high_assurance")
        medium_assurance = sum(1 for s in assurance_scores.values() if s.classification == "medium_assurance")
        low_assurance = sum(1 for s in assurance_scores.values() if s.classification == "low_assurance")
        auto_eligible = sum(1 for s in assurance_scores.values() if s.auto_certify_eligible)
        needs_review = sum(1 for c in consensus_results.values() if c.needs_human_review)
        disagreements = sum(1 for c in consensus_results.values() if c.consensus_score < 0.7)

        result = AnalyticsResult(
            employee_features=features,
            cluster_assignments=cluster_assignments,
            consensus_results=consensus_results,
            assurance_scores=assurance_scores,
            total_employees=len(employees),
            total_grants=len(access_grants),
            high_assurance_count=high_assurance,
            medium_assurance_count=medium_assurance,
            low_assurance_count=low_assurance,
            auto_certify_eligible_count=auto_eligible,
            needs_human_review_count=needs_review,
            clustering_disagreement_count=disagreements
        )

        logger.info("Analytics pipeline complete!")
        self._log_summary(result)

        return result

    def _log_summary(self, result: AnalyticsResult) -> None:
        """Log summary of analytics result."""
        total = result.total_grants
        if total == 0:
            return

        logger.info("=" * 60)
        logger.info("ANALYTICS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Employees: {result.total_employees:,}")
        logger.info(f"Total Access Grants: {result.total_grants:,}")
        logger.info("-" * 60)
        logger.info(f"High Assurance: {result.high_assurance_count:,} ({result.high_assurance_count/total*100:.1f}%)")
        logger.info(f"Medium Assurance: {result.medium_assurance_count:,} ({result.medium_assurance_count/total*100:.1f}%)")
        logger.info(f"Low Assurance: {result.low_assurance_count:,} ({result.low_assurance_count/total*100:.1f}%)")
        logger.info("-" * 60)
        logger.info(f"Auto-Certify Eligible: {result.auto_certify_eligible_count:,} ({result.auto_certify_eligible_count/total*100:.1f}%)")
        logger.info(f"Clustering Disagreements: {result.clustering_disagreement_count:,}")
        logger.info("=" * 60)

    def get_review_items(
        self,
        result: AnalyticsResult,
        reviewer_employee_id: str,
        include_auto_certified: bool = False
    ) -> List[Dict]:
        """
        Get review items for a specific reviewer (manager).

        Args:
            result: AnalyticsResult from run_analysis()
            reviewer_employee_id: Employee ID of the reviewer
            include_auto_certified: Whether to include auto-certified items

        Returns:
            List of review items with scores and explanations
        """
        # Find direct reports
        direct_reports = {
            e["id"] for e in self._employees
            if e.get("manager_id") == reviewer_employee_id
        }

        if not direct_reports:
            return []

        # Get grants for direct reports
        review_items = []
        for grant_id, score in result.assurance_scores.items():
            if score.employee_id not in direct_reports:
                continue

            if not include_auto_certified and score.auto_certify_eligible:
                continue

            # Get employee name
            employee = next(
                (e for e in self._employees if e["id"] == score.employee_id),
                {}
            )

            # Get consensus info
            consensus = result.consensus_results.get(score.employee_id)

            review_item = {
                "grant_id": grant_id,
                "employee_id": score.employee_id,
                "employee_name": employee.get("full_name", "Unknown"),
                "employee_title": employee.get("job_title", "Unknown"),
                "resource_id": score.resource_id,
                "resource_name": score.resource_name,
                "resource_sensitivity": score.resource_sensitivity,
                "assurance_score": score.overall_score,
                "classification": score.classification,
                "auto_certify_eligible": score.auto_certify_eligible,
                "peer_percentage": score.peer_percentage,
                "peers_with_access": score.peers_with_access,
                "total_peers": score.total_peers,
                "usage_pattern": score.usage_pattern,
                "days_since_last_use": score.days_since_last_use,
                "explanations": score.explanations,
                "clustering_consensus": consensus.consensus_score if consensus else 0,
                "needs_clustering_review": consensus.needs_human_review if consensus else False,
                "clustering_disagreement": consensus.disagreement_reason if consensus else None
            }

            review_items.append(review_item)

        # Sort by assurance score ascending (lowest first = most attention needed)
        review_items.sort(key=lambda x: x["assurance_score"])

        return review_items

    def get_employee_access_summary(
        self,
        result: AnalyticsResult,
        employee_id: str
    ) -> Dict:
        """
        Get complete access summary for a single employee.
        """
        # Get employee info
        employee = next(
            (e for e in self._employees if e["id"] == employee_id),
            {}
        )

        if not employee:
            return {}

        # Get their grants
        employee_grants = [
            score for score in result.assurance_scores.values()
            if score.employee_id == employee_id
        ]

        # Get consensus info
        consensus = result.consensus_results.get(employee_id)

        # Categorize grants
        high = [g for g in employee_grants if g.classification == "high_assurance"]
        medium = [g for g in employee_grants if g.classification == "medium_assurance"]
        low = [g for g in employee_grants if g.classification == "low_assurance"]
        dormant = [g for g in employee_grants if g.usage_pattern == "dormant"]

        return {
            "employee_id": employee_id,
            "employee_name": employee.get("full_name"),
            "employee_title": employee.get("job_title"),
            "team_id": employee.get("team_id"),
            "manager_id": employee.get("manager_id"),
            "total_grants": len(employee_grants),
            "high_assurance_count": len(high),
            "medium_assurance_count": len(medium),
            "low_assurance_count": len(low),
            "dormant_access_count": len(dormant),
            "auto_certify_eligible": sum(1 for g in employee_grants if g.auto_certify_eligible),
            "peer_count": consensus.peer_count if consensus else 0,
            "clustering_consensus": consensus.consensus_score if consensus else 0,
            "needs_clustering_review": consensus.needs_human_review if consensus else False,
            "grants": [
                {
                    "grant_id": g.grant_id,
                    "resource_name": g.resource_name,
                    "resource_sensitivity": g.resource_sensitivity,
                    "score": g.overall_score,
                    "classification": g.classification,
                    "usage_pattern": g.usage_pattern,
                    "peer_percentage": g.peer_percentage,
                    "explanations": g.explanations
                }
                for g in sorted(employee_grants, key=lambda x: x.overall_score)
            ]
        }

    def export_results(
        self,
        result: AnalyticsResult,
        output_path: str
    ) -> None:
        """
        Export analytics results to JSON file.
        """
        logger.info(f"Exporting results to {output_path}")

        # Convert to serializable format
        export_data = {
            "summary": {
                "total_employees": result.total_employees,
                "total_grants": result.total_grants,
                "high_assurance_count": result.high_assurance_count,
                "medium_assurance_count": result.medium_assurance_count,
                "low_assurance_count": result.low_assurance_count,
                "auto_certify_eligible_count": result.auto_certify_eligible_count,
                "needs_human_review_count": result.needs_human_review_count,
                "clustering_disagreement_count": result.clustering_disagreement_count
            },
            "assurance_scores": {
                grant_id: {
                    "grant_id": score.grant_id,
                    "employee_id": score.employee_id,
                    "resource_id": score.resource_id,
                    "resource_name": score.resource_name,
                    "resource_sensitivity": score.resource_sensitivity,
                    "overall_score": score.overall_score,
                    "classification": score.classification,
                    "auto_certify_eligible": score.auto_certify_eligible,
                    "peer_typicality": score.peer_typicality,
                    "peer_percentage": score.peer_percentage,
                    "usage_pattern": score.usage_pattern,
                    "usage_factor": score.usage_factor,
                    "explanations": score.explanations
                }
                for grant_id, score in result.assurance_scores.items()
            },
            "consensus_results": {
                emp_id: {
                    "employee_id": consensus.employee_id,
                    "consensus_score": consensus.consensus_score,
                    "strategies_agreeing": consensus.strategies_agreeing,
                    "total_strategies": consensus.total_strategies,
                    "peer_count": consensus.peer_count,
                    "needs_human_review": consensus.needs_human_review,
                    "disagreement_reason": consensus.disagreement_reason
                }
                for emp_id, consensus in result.consensus_results.items()
            }
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Results exported to {output_path}")


# CLI for testing
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="Run ARAS Analytics Engine")
    parser.add_argument("--db", required=True, help="Path to SQLite database")
    parser.add_argument("--output", default="analytics_results.json", help="Output JSON file")
    parser.add_argument("--lob", default=None, help="Filter by LOB ID")

    args = parser.parse_args()

    engine = AnalyticsEngine(db_path=args.db)
    engine.load_data()
    result = engine.run_analysis(lob_filter=args.lob)
    engine.export_results(result, args.output)
