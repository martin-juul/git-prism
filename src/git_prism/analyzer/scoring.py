"""Expertise scoring algorithms."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from git_prism.analyzer.contributors import Contributor


# Default scoring weights
DEFAULT_WEIGHTS = {
    "lines_changed": 0.4,
    "commit_frequency": 0.3,
    "file_importance": 0.15,
    "complexity": 0.15,
}

# Recency decay half-life in days
RECENCY_HALF_LIFE_DAYS = 180


def recency_decay(timestamp: datetime, half_life_days: int = RECENCY_HALF_LIFE_DAYS) -> float:
    """Calculate recency weight using exponential decay.

    More recent contributions get higher weights. Uses exponential decay
    with specified half-life.

    Args:
        timestamp: The timestamp to weight.
        half_life_days: Days until weight is halved.

    Returns:
        Weight between 0 and 1 (higher = more recent).
    """
    now = datetime.now()
    age_days = (now - timestamp).total_seconds() / 86400  # seconds per day

    # Exponential decay: weight = 0.5^(age / half_life)
    decay_factor = math.log(0.5) / half_life_days
    weight = math.exp(decay_factor * age_days)

    return max(0.0, min(1.0, weight))


@dataclass
class ExpertiseScore:
    """Expertise score for a contributor in a repository.

    Attributes:
        contributor_name: Canonical name of the contributor.
        contributor_email: Canonical email of the contributor.
        total_score: Combined expertise score.
        commit_count: Number of commits.
        lines_changed: Total lines changed.
        recency_score: Weighted recency of contributions.
        complexity_score: Average complexity of code touched.
        file_importance_score: Importance of files modified.
    """

    contributor_name: str
    contributor_email: str
    total_score: float
    commit_count: int
    lines_changed: int
    recency_score: float = 0.0
    complexity_score: float = 0.0
    file_importance_score: float = 0.0


def calculate_expertise_scores(
    contributors: dict[tuple[str, str], Contributor] | list[Contributor],
    weights: dict[str, float] | None = None,
) -> list[ExpertiseScore]:
    """Calculate expertise scores for all contributors.

    Uses a weighted combination of:
    - Lines changed (weighted by recency)
    - Commit frequency (weighted by recency)
    - File importance (core vs peripheral modules)
    - Code complexity contributions

    Args:
        contributors: Dictionary or list of Contributor objects.
        weights: Custom scoring weights (uses defaults if None).

    Returns:
        List of ExpertiseScore objects sorted by total_score descending.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    # Convert dict to list if needed
    if isinstance(contributors, dict):
        contributor_list = list(contributors.values())
    else:
        contributor_list = contributors

    if not contributor_list:
        return []

    # Find max values for normalization
    max_lines = max(c.lines_changed for c in contributor_list) or 1
    max_commits = max(c.commit_count for c in contributor_list) or 1

    scores: list[ExpertiseScore] = []

    for contributor in contributor_list:
        # Calculate weighted lines changed
        lines_score = 0.0
        if contributor.last_commit:
            recency = recency_decay(contributor.last_commit)
            lines_score = (contributor.lines_changed / max_lines) * recency

        # Calculate weighted commit frequency
        commit_score = 0.0
        if contributor.last_commit:
            recency = recency_decay(contributor.last_commit)
            commit_score = (contributor.commit_count / max_commits) * recency

        # File importance (simple heuristic: more unique files = higher importance)
        file_count = len(contributor.files_modified)
        file_score = min(1.0, file_count / 100)  # Cap at 100 files

        # Complexity (placeholder - would integrate with AST analysis)
        complexity_score = 0.5  # Default medium complexity

        # Combine scores
        total_score = (
            weights["lines_changed"] * lines_score
            + weights["commit_frequency"] * commit_score
            + weights["file_importance"] * file_score
            + weights["complexity"] * complexity_score
        )

        scores.append(
            ExpertiseScore(
                contributor_name=contributor.canonical_name,
                contributor_email=contributor.canonical_email,
                total_score=total_score * 100,  # Scale to 0-100
                commit_count=contributor.commit_count,
                lines_changed=contributor.lines_changed,
                recency_score=lines_score,
                complexity_score=complexity_score,
                file_importance_score=file_score,
            )
        )

    # Sort by total score descending
    scores.sort(key=lambda s: s.total_score, reverse=True)

    return scores


def calculate_knowledge_distribution(
    scores: list[ExpertiseScore],
) -> dict[str, float]:
    """Calculate knowledge distribution metrics.

    Identifies potential knowledge gaps and concentration of expertise.

    Args:
        scores: List of ExpertiseScore objects.

    Returns:
        Dictionary with distribution metrics:
        - gini_coefficient: 0 = equal distribution, 1 = concentrated
        - top_contributor_share: Percentage owned by top contributor
        - bus_factor: Estimated bus factor (unique contributors with >5% share)
    """
    if not scores:
        return {
            "gini_coefficient": 0.0,
            "top_contributor_share": 0.0,
            "bus_factor": 0,
        }

    total = sum(s.total_score for s in scores)
    if total == 0:
        return {
            "gini_coefficient": 0.0,
            "top_contributor_share": 0.0,
            "bus_factor": len(scores),
        }

    # Sort scores ascending for Gini calculation
    sorted_scores = sorted(scores, key=lambda s: s.total_score)
    n = len(sorted_scores)

    # Gini coefficient
    cumulative = 0.0
    for i, score in enumerate(sorted_scores, 1):
        cumulative += i * score.total_score
    gini = (2 * cumulative / (n * total)) - (n + 1) / n

    # Top contributor share
    top_share = (sorted_scores[-1].total_score / total) * 100

    # Bus factor (contributors with >5% share)
    bus_factor = sum(1 for s in scores if (s.total_score / total) > 0.05)

    return {
        "gini_coefficient": round(gini, 3),
        "top_contributor_share": round(top_share, 1),
        "bus_factor": max(1, bus_factor),
    }
