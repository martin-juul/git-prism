"""Unit tests for the scoring module."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from git_prism.analyzer.contributors import Contributor
from git_prism.analyzer.scoring import (
    ExpertiseScore,
    calculate_expertise_scores,
    calculate_knowledge_distribution,
    recency_decay,
)


class TestRecencyDecay:
    """Tests for recency_decay function."""

    def test_recent_commit_high_weight(self) -> None:
        """Test that recent commits get high weights."""
        recent = datetime.now() - timedelta(days=1)
        weight = recency_decay(recent)

        assert weight > 0.9

    def test_old_commit_low_weight(self) -> None:
        """Test that old commits get low weights."""
        old = datetime.now() - timedelta(days=365)
        weight = recency_decay(old)

        assert weight < 0.3

    def test_half_life_weight(self) -> None:
        """Test that commits at half-life get weight around 0.5."""
        half_life_date = datetime.now() - timedelta(days=180)
        weight = recency_decay(half_life_date, half_life_days=180)

        # Should be close to 0.5 (exponential decay)
        assert 0.4 < weight < 0.6

    def test_weight_between_0_and_1(self) -> None:
        """Test that weights are always between 0 and 1."""
        for days_ago in [0, 30, 90, 180, 365, 730, 1000]:
            timestamp = datetime.now() - timedelta(days=days_ago)
            weight = recency_decay(timestamp)

            assert 0 <= weight <= 1


class TestCalculateExpertiseScores:
    """Tests for calculate_expertise_scores function."""

    def test_empty_contributors(self) -> None:
        """Test with empty contributor list."""
        scores = calculate_expertise_scores([])

        assert scores == []

    def test_single_contributor(self) -> None:
        """Test with a single contributor."""
        contributor = Contributor(
            canonical_name="John Doe",
            canonical_email="john@example.com",
        )
        contributor.commits = ["sha1", "sha2", "sha3"]
        contributor.total_insertions = 100
        contributor.total_deletions = 50
        contributor.last_commit = datetime.now() - timedelta(days=30)

        scores = calculate_expertise_scores([contributor])

        assert len(scores) == 1
        assert scores[0].contributor_name == "John Doe"
        assert scores[0].total_score > 0

    def test_multiple_contributors_sorted(self) -> None:
        """Test that multiple contributors are sorted by score."""
        contributors = []

        for i, (commits, lines) in enumerate([(5, 100), (20, 500), (10, 200)]):
            c = Contributor(
                canonical_name=f"User {i}",
                canonical_email=f"user{i}@example.com",
            )
            c.commits = [f"sha{j}" for j in range(commits)]
            c.total_insertions = lines
            c.total_deletions = lines // 2
            c.last_commit = datetime.now() - timedelta(days=30)
            contributors.append(c)

        scores = calculate_expertise_scores(contributors)

        # Should be sorted by total_score descending
        assert scores[0].total_score >= scores[1].total_score >= scores[2].total_score

    def test_custom_weights(self) -> None:
        """Test with custom scoring weights."""
        contributor = Contributor(
            canonical_name="John Doe",
            canonical_email="john@example.com",
        )
        contributor.commits = ["sha1"]
        contributor.total_insertions = 100
        contributor.total_deletions = 50
        contributor.last_commit = datetime.now()

        custom_weights = {
            "lines_changed": 0.5,
            "commit_frequency": 0.3,
            "file_importance": 0.1,
            "complexity": 0.1,
        }

        scores = calculate_expertise_scores([contributor], weights=custom_weights)

        assert len(scores) == 1


class TestCalculateKnowledgeDistribution:
    """Tests for calculate_knowledge_distribution function."""

    def test_empty_scores(self) -> None:
        """Test with empty scores list."""
        result = calculate_knowledge_distribution([])

        assert result["gini_coefficient"] == 0.0
        assert result["top_contributor_share"] == 0.0
        assert result["bus_factor"] == 0

    def test_equal_distribution(self) -> None:
        """Test with equal scores (low Gini)."""
        scores = [
            ExpertiseScore(
                contributor_name=f"User {i}",
                contributor_email=f"user{i}@example.com",
                total_score=100.0,
                commit_count=10,
                lines_changed=1000,
            )
            for i in range(5)
        ]

        result = calculate_knowledge_distribution(scores)

        # Equal distribution should have low Gini
        assert result["gini_coefficient"] < 0.1
        assert result["bus_factor"] == 5  # All have >5% share

    def test_concentrated_distribution(self) -> None:
        """Test with concentrated scores (high Gini)."""
        scores = [
            ExpertiseScore(
                contributor_name="Main Dev",
                contributor_email="main@example.com",
                total_score=90.0,
                commit_count=100,
                lines_changed=10000,
            ),
            ExpertiseScore(
                contributor_name="Contrib 1",
                contributor_email="c1@example.com",
                total_score=5.0,
                commit_count=5,
                lines_changed=500,
            ),
            ExpertiseScore(
                contributor_name="Contrib 2",
                contributor_email="c2@example.com",
                total_score=5.0,
                commit_count=5,
                lines_changed=500,
            ),
        ]

        result = calculate_knowledge_distribution(scores)

        # Concentrated should have high Gini and top share
        assert result["gini_coefficient"] > 0.3
        assert result["top_contributor_share"] > 80

    def test_bus_factor_calculation(self) -> None:
        """Test bus factor calculation."""
        # 3 contributors with >5% share each
        scores = [
            ExpertiseScore(
                contributor_name=f"User {i}",
                contributor_email=f"user{i}@example.com",
                total_score=30.0,
                commit_count=10,
                lines_changed=1000,
            )
            for i in range(3)
        ]

        result = calculate_knowledge_distribution(scores)

        assert result["bus_factor"] == 3


class TestExpertiseScore:
    """Tests for ExpertiseScore dataclass."""

    def test_expertise_score_creation(self) -> None:
        """Test creating an ExpertiseScore instance."""
        score = ExpertiseScore(
            contributor_name="John Doe",
            contributor_email="john@example.com",
            total_score=75.5,
            commit_count=25,
            lines_changed=1500,
        )

        assert score.contributor_name == "John Doe"
        assert score.total_score == 75.5
        assert score.commit_count == 25
        assert score.lines_changed == 1500
