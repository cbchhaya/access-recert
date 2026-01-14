"""
Multi-Strategy Clustering Engine
================================

Implements multiple clustering algorithms for peer group detection:
- K-means: Centroid-based clustering
- Hierarchical: Agglomerative clustering
- DBSCAN: Density-based clustering with outlier detection
- Graph Community: Network-based community detection

When algorithms disagree, cases are flagged for human review.

Author: Chiradeep Chhaya
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class ClusteringStrategy(Enum):
    """Available clustering strategies."""
    KMEANS = "kmeans"
    HIERARCHICAL = "hierarchical"
    DBSCAN = "dbscan"
    GRAPH_COMMUNITY = "graph_community"


@dataclass
class ClusterAssignment:
    """Cluster assignment for a single employee from one strategy."""
    employee_id: str
    strategy: ClusteringStrategy
    cluster_id: int  # -1 for outliers (DBSCAN)
    confidence: float  # 0-1, distance to centroid or other measure
    is_outlier: bool = False


@dataclass
class ConsensusResult:
    """Result of multi-strategy clustering with consensus analysis."""
    employee_id: str

    # Per-strategy assignments
    assignments: Dict[ClusteringStrategy, ClusterAssignment] = field(default_factory=dict)

    # Consensus metrics
    consensus_cluster_id: Optional[int] = None
    consensus_score: float = 0.0  # 0-1, how much strategies agree
    strategies_agreeing: int = 0
    total_strategies: int = 0

    # Peer information
    peer_ids: List[str] = field(default_factory=list)
    peer_count: int = 0

    # Flags
    needs_human_review: bool = False
    disagreement_reason: Optional[str] = None


@dataclass
class ClusteringConfig:
    """Configuration for clustering algorithms."""
    # K-means config
    kmeans_n_clusters: int = 0  # 0 = auto-determine
    kmeans_max_clusters: int = 50
    kmeans_min_cluster_size: int = 5

    # Hierarchical config
    hierarchical_n_clusters: int = 0  # 0 = auto-determine
    hierarchical_linkage: str = "ward"  # ward, complete, average, single

    # DBSCAN config
    dbscan_eps: float = 0.3  # Maximum distance between samples
    dbscan_min_samples: int = 5

    # Graph community config
    graph_resolution: float = 1.0  # Louvain resolution parameter
    graph_min_edge_weight: float = 0.2  # Minimum proximity to create edge

    # Consensus config
    consensus_threshold: float = 0.7  # Min agreement to avoid human review
    min_strategies_for_consensus: int = 3


class MultiStrategyClusterer:
    """
    Multi-strategy clustering engine that runs multiple algorithms
    and analyzes consensus.
    """

    def __init__(self, config: Optional[ClusteringConfig] = None):
        self.config = config or ClusteringConfig()
        self._results_cache: Dict[str, ConsensusResult] = {}

    def cluster_kmeans(
        self,
        proximity_matrix: np.ndarray,
        employee_ids: List[str]
    ) -> Dict[str, ClusterAssignment]:
        """
        Perform K-means clustering.

        Args:
            proximity_matrix: Pairwise proximity matrix
            employee_ids: List of employee IDs (same order as matrix)

        Returns:
            Dictionary mapping employee_id to ClusterAssignment
        """
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        n_samples = len(employee_ids)

        # Convert proximity to distance (1 - proximity)
        distance_matrix = 1 - proximity_matrix

        # Auto-determine number of clusters using silhouette score
        if self.config.kmeans_n_clusters == 0:
            max_k = min(self.config.kmeans_max_clusters, n_samples // self.config.kmeans_min_cluster_size)
            max_k = max(2, max_k)
            min_k = 2

            best_k = min_k
            best_score = -1

            for k in range(min_k, max_k + 1):
                try:
                    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                    labels = kmeans.fit_predict(distance_matrix)
                    if len(set(labels)) > 1:
                        score = silhouette_score(distance_matrix, labels, metric='precomputed')
                        if score > best_score:
                            best_score = score
                            best_k = k
                except Exception as e:
                    logger.warning(f"K-means with k={k} failed: {e}")
                    continue

            n_clusters = best_k
            logger.info(f"K-means auto-selected k={n_clusters} (silhouette={best_score:.3f})")
        else:
            n_clusters = self.config.kmeans_n_clusters

        # Fit final model
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(distance_matrix)

        # Calculate confidence based on distance to centroid
        distances_to_centroid = kmeans.transform(distance_matrix)

        assignments = {}
        for i, emp_id in enumerate(employee_ids):
            cluster_id = int(labels[i])
            # Confidence = 1 - normalized distance to own centroid
            dist = distances_to_centroid[i, cluster_id]
            max_dist = distances_to_centroid[:, cluster_id].max()
            confidence = 1 - (dist / max_dist) if max_dist > 0 else 1.0

            assignments[emp_id] = ClusterAssignment(
                employee_id=emp_id,
                strategy=ClusteringStrategy.KMEANS,
                cluster_id=cluster_id,
                confidence=confidence,
                is_outlier=False
            )

        return assignments

    def cluster_hierarchical(
        self,
        proximity_matrix: np.ndarray,
        employee_ids: List[str]
    ) -> Dict[str, ClusterAssignment]:
        """
        Perform hierarchical (agglomerative) clustering.
        """
        from sklearn.cluster import AgglomerativeClustering
        from sklearn.metrics import silhouette_score

        n_samples = len(employee_ids)
        distance_matrix = 1 - proximity_matrix

        # Auto-determine number of clusters
        if self.config.hierarchical_n_clusters == 0:
            max_k = min(self.config.kmeans_max_clusters, n_samples // self.config.kmeans_min_cluster_size)
            max_k = max(2, max_k)
            min_k = 2

            best_k = min_k
            best_score = -1

            for k in range(min_k, max_k + 1):
                try:
                    clustering = AgglomerativeClustering(
                        n_clusters=k,
                        metric='precomputed',
                        linkage='average'  # Ward doesn't work with precomputed
                    )
                    labels = clustering.fit_predict(distance_matrix)
                    if len(set(labels)) > 1:
                        score = silhouette_score(distance_matrix, labels, metric='precomputed')
                        if score > best_score:
                            best_score = score
                            best_k = k
                except Exception as e:
                    logger.warning(f"Hierarchical with k={k} failed: {e}")
                    continue

            n_clusters = best_k
            logger.info(f"Hierarchical auto-selected k={n_clusters} (silhouette={best_score:.3f})")
        else:
            n_clusters = self.config.hierarchical_n_clusters

        # Fit final model
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric='precomputed',
            linkage='average'
        )
        labels = clustering.fit_predict(distance_matrix)

        # Calculate confidence based on average proximity to cluster members
        assignments = {}
        for i, emp_id in enumerate(employee_ids):
            cluster_id = int(labels[i])

            # Find cluster members
            cluster_members = [j for j, l in enumerate(labels) if l == cluster_id and j != i]

            if cluster_members:
                avg_proximity = np.mean([proximity_matrix[i, j] for j in cluster_members])
                confidence = avg_proximity
            else:
                confidence = 1.0

            assignments[emp_id] = ClusterAssignment(
                employee_id=emp_id,
                strategy=ClusteringStrategy.HIERARCHICAL,
                cluster_id=cluster_id,
                confidence=confidence,
                is_outlier=False
            )

        return assignments

    def cluster_dbscan(
        self,
        proximity_matrix: np.ndarray,
        employee_ids: List[str]
    ) -> Dict[str, ClusterAssignment]:
        """
        Perform DBSCAN clustering with outlier detection.

        DBSCAN is particularly useful because it:
        1. Doesn't require specifying number of clusters
        2. Naturally identifies outliers (noise points)
        3. Can find arbitrarily shaped clusters
        """
        from sklearn.cluster import DBSCAN

        distance_matrix = 1 - proximity_matrix

        # DBSCAN with distance matrix
        clustering = DBSCAN(
            eps=self.config.dbscan_eps,
            min_samples=self.config.dbscan_min_samples,
            metric='precomputed'
        )
        labels = clustering.fit_predict(distance_matrix)

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_outliers = list(labels).count(-1)
        logger.info(f"DBSCAN found {n_clusters} clusters, {n_outliers} outliers")

        assignments = {}
        for i, emp_id in enumerate(employee_ids):
            cluster_id = int(labels[i])
            is_outlier = cluster_id == -1

            if is_outlier:
                confidence = 0.0
            else:
                # Confidence = average proximity to cluster members
                cluster_members = [j for j, l in enumerate(labels) if l == cluster_id and j != i]
                if cluster_members:
                    confidence = np.mean([proximity_matrix[i, j] for j in cluster_members])
                else:
                    confidence = 1.0

            assignments[emp_id] = ClusterAssignment(
                employee_id=emp_id,
                strategy=ClusteringStrategy.DBSCAN,
                cluster_id=cluster_id,
                confidence=confidence,
                is_outlier=is_outlier
            )

        return assignments

    def cluster_graph_community(
        self,
        proximity_matrix: np.ndarray,
        employee_ids: List[str]
    ) -> Dict[str, ClusterAssignment]:
        """
        Perform graph-based community detection using Louvain algorithm.
        """
        try:
            import networkx as nx
            from networkx.algorithms import community as nx_community
        except ImportError:
            logger.warning("NetworkX not available, skipping graph community clustering")
            return {}

        # Build graph from proximity matrix
        G = nx.Graph()

        # Add nodes
        for i, emp_id in enumerate(employee_ids):
            G.add_node(emp_id)

        # Add edges where proximity exceeds threshold
        for i in range(len(employee_ids)):
            for j in range(i + 1, len(employee_ids)):
                proximity = proximity_matrix[i, j]
                if proximity >= self.config.graph_min_edge_weight:
                    G.add_edge(
                        employee_ids[i],
                        employee_ids[j],
                        weight=proximity
                    )

        # Detect communities using Louvain
        try:
            communities = nx_community.louvain_communities(
                G,
                weight='weight',
                resolution=self.config.graph_resolution,
                seed=42
            )
        except Exception as e:
            logger.warning(f"Louvain community detection failed: {e}")
            return {}

        logger.info(f"Graph community detection found {len(communities)} communities")

        # Create assignments
        emp_to_cluster = {}
        for cluster_id, community in enumerate(communities):
            for emp_id in community:
                emp_to_cluster[emp_id] = cluster_id

        assignments = {}
        for i, emp_id in enumerate(employee_ids):
            cluster_id = emp_to_cluster.get(emp_id, -1)

            if cluster_id >= 0:
                # Confidence = average edge weight to community members
                community = communities[cluster_id]
                neighbors_in_community = [
                    n for n in G.neighbors(emp_id) if n in community
                ]
                if neighbors_in_community:
                    confidence = np.mean([
                        G[emp_id][n]['weight'] for n in neighbors_in_community
                    ])
                else:
                    confidence = 0.5
            else:
                confidence = 0.0

            assignments[emp_id] = ClusterAssignment(
                employee_id=emp_id,
                strategy=ClusteringStrategy.GRAPH_COMMUNITY,
                cluster_id=cluster_id,
                confidence=confidence,
                is_outlier=cluster_id == -1
            )

        return assignments

    def run_all_strategies(
        self,
        proximity_matrix: np.ndarray,
        employee_ids: List[str],
        strategies: Optional[List[ClusteringStrategy]] = None
    ) -> Dict[ClusteringStrategy, Dict[str, ClusterAssignment]]:
        """
        Run all specified clustering strategies.

        Args:
            proximity_matrix: Pairwise proximity matrix
            employee_ids: List of employee IDs
            strategies: List of strategies to run (default: all)

        Returns:
            Dictionary mapping strategy to assignments
        """
        if strategies is None:
            strategies = list(ClusteringStrategy)

        results = {}

        for strategy in strategies:
            logger.info(f"Running {strategy.value} clustering...")
            try:
                if strategy == ClusteringStrategy.KMEANS:
                    results[strategy] = self.cluster_kmeans(proximity_matrix, employee_ids)
                elif strategy == ClusteringStrategy.HIERARCHICAL:
                    results[strategy] = self.cluster_hierarchical(proximity_matrix, employee_ids)
                elif strategy == ClusteringStrategy.DBSCAN:
                    results[strategy] = self.cluster_dbscan(proximity_matrix, employee_ids)
                elif strategy == ClusteringStrategy.GRAPH_COMMUNITY:
                    results[strategy] = self.cluster_graph_community(proximity_matrix, employee_ids)
            except Exception as e:
                logger.error(f"Strategy {strategy.value} failed: {e}")
                continue

        return results

    def analyze_consensus(
        self,
        all_assignments: Dict[ClusteringStrategy, Dict[str, ClusterAssignment]],
        employee_ids: List[str]
    ) -> Dict[str, ConsensusResult]:
        """
        Analyze consensus across multiple clustering strategies.

        For each employee, determine:
        1. Whether strategies agree on peer grouping
        2. Who their peers are (union of cluster members across strategies)
        3. Whether human review is needed due to disagreement

        Args:
            all_assignments: Results from run_all_strategies()
            employee_ids: List of employee IDs

        Returns:
            Dictionary mapping employee_id to ConsensusResult
        """
        logger.info("Analyzing clustering consensus...")

        results = {}

        for emp_id in employee_ids:
            # Collect all assignments for this employee
            emp_assignments = {}
            for strategy, assignments in all_assignments.items():
                if emp_id in assignments:
                    emp_assignments[strategy] = assignments[emp_id]

            total_strategies = len(emp_assignments)

            if total_strategies == 0:
                results[emp_id] = ConsensusResult(
                    employee_id=emp_id,
                    needs_human_review=True,
                    disagreement_reason="No clustering results available"
                )
                continue

            # Find peer sets from each strategy
            peer_sets = []
            for strategy, assignment in emp_assignments.items():
                if assignment.is_outlier:
                    peer_sets.append(set())  # Outliers have no peers
                else:
                    # Find all employees in same cluster
                    cluster_members = set()
                    strategy_assignments = all_assignments[strategy]
                    for other_id, other_assign in strategy_assignments.items():
                        if other_id != emp_id and other_assign.cluster_id == assignment.cluster_id:
                            cluster_members.add(other_id)
                    peer_sets.append(cluster_members)

            # Calculate consensus
            # Use Jaccard similarity between peer sets
            if len(peer_sets) >= 2:
                pairwise_similarities = []
                for i in range(len(peer_sets)):
                    for j in range(i + 1, len(peer_sets)):
                        set_a, set_b = peer_sets[i], peer_sets[j]
                        if set_a or set_b:
                            intersection = len(set_a & set_b)
                            union = len(set_a | set_b)
                            jaccard = intersection / union if union > 0 else 1.0
                            pairwise_similarities.append(jaccard)

                consensus_score = np.mean(pairwise_similarities) if pairwise_similarities else 0.0
            else:
                consensus_score = 1.0  # Single strategy = full consensus

            # Determine consensus peers (intersection of all non-empty peer sets)
            non_empty_sets = [s for s in peer_sets if s]
            if non_empty_sets:
                consensus_peers = set.intersection(*non_empty_sets) if len(non_empty_sets) > 1 else non_empty_sets[0]
                all_peers = set.union(*non_empty_sets)
            else:
                consensus_peers = set()
                all_peers = set()

            # Check for outlier disagreement
            outlier_votes = sum(1 for a in emp_assignments.values() if a.is_outlier)
            non_outlier_votes = total_strategies - outlier_votes

            # Determine if human review is needed
            needs_review = False
            reason = None

            if consensus_score < self.config.consensus_threshold:
                needs_review = True
                reason = f"Low consensus score ({consensus_score:.2f} < {self.config.consensus_threshold})"
            elif outlier_votes > 0 and non_outlier_votes > 0:
                needs_review = True
                reason = f"Outlier disagreement ({outlier_votes}/{total_strategies} strategies mark as outlier)"
            elif len(consensus_peers) == 0 and len(all_peers) > 0:
                needs_review = True
                reason = "No common peers across all strategies"

            # Determine consensus cluster (mode of cluster IDs, excluding outliers)
            non_outlier_clusters = [
                a.cluster_id for a in emp_assignments.values()
                if not a.is_outlier
            ]
            if non_outlier_clusters:
                from collections import Counter
                cluster_counts = Counter(non_outlier_clusters)
                consensus_cluster = cluster_counts.most_common(1)[0][0]
                strategies_agreeing = cluster_counts[consensus_cluster]
            else:
                consensus_cluster = -1
                strategies_agreeing = outlier_votes

            results[emp_id] = ConsensusResult(
                employee_id=emp_id,
                assignments=emp_assignments,
                consensus_cluster_id=consensus_cluster,
                consensus_score=consensus_score,
                strategies_agreeing=strategies_agreeing,
                total_strategies=total_strategies,
                peer_ids=list(all_peers),  # Use union for peer list
                peer_count=len(all_peers),
                needs_human_review=needs_review,
                disagreement_reason=reason
            )

        # Log summary
        needs_review_count = sum(1 for r in results.values() if r.needs_human_review)
        logger.info(f"Consensus analysis complete: {needs_review_count}/{len(results)} need human review")

        self._results_cache = results
        return results

    def get_cluster_members(
        self,
        employee_id: str,
        strategy: ClusteringStrategy,
        all_assignments: Dict[ClusteringStrategy, Dict[str, ClusterAssignment]]
    ) -> List[str]:
        """
        Get all members of the same cluster as a given employee.
        """
        if strategy not in all_assignments:
            return []

        assignments = all_assignments[strategy]
        if employee_id not in assignments:
            return []

        target_cluster = assignments[employee_id].cluster_id
        if target_cluster == -1:  # Outlier
            return []

        return [
            emp_id for emp_id, assign in assignments.items()
            if assign.cluster_id == target_cluster and emp_id != employee_id
        ]
