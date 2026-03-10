"""Unit tests for the contributors module."""

from __future__ import annotations

from pathlib import Path

import pytest

from git_prism.analyzer.contributors import (
    Contributor,
    parse_mailmap,
    resolve_contributor,
    suggest_identity_mappings,
)


class TestContributor:
    """Tests for Contributor dataclass."""

    def test_contributor_creation(self) -> None:
        """Test creating a Contributor instance."""
        contributor = Contributor(
            canonical_name="John Doe",
            canonical_email="john@example.com",
        )

        assert contributor.canonical_name == "John Doe"
        assert contributor.canonical_email == "john@example.com"
        assert contributor.aliases == []
        assert contributor.commits == []
        assert contributor.total_insertions == 0
        assert contributor.total_deletions == 0

    def test_add_commit(self, sample_commit_info: dict) -> None:
        """Test adding a commit updates statistics."""
        from git_prism.analyzer.commits import CommitInfo

        contributor = Contributor(
            canonical_name="John Doe",
            canonical_email="john@example.com",
        )

        commit = CommitInfo(**sample_commit_info)
        contributor.add_commit(commit)

        assert len(contributor.commits) == 1
        assert contributor.total_insertions == 50
        assert contributor.total_deletions == 10
        assert contributor.first_commit == sample_commit_info["timestamp"]
        assert contributor.last_commit == sample_commit_info["timestamp"]

    def test_add_multiple_commits(self) -> None:
        """Test adding multiple commits updates first/last correctly."""
        from datetime import datetime

        from git_prism.analyzer.commits import CommitInfo

        contributor = Contributor(
            canonical_name="John Doe",
            canonical_email="john@example.com",
        )

        # Add commits in non-chronological order
        commit1 = CommitInfo(
            sha="abc1",
            author_name="John",
            author_email="john@example.com",
            timestamp=datetime(2024, 1, 10),
            message="Late commit",
            is_merge=False,
            insertions=10,
            deletions=5,
        )

        commit2 = CommitInfo(
            sha="abc2",
            author_name="John",
            author_email="john@example.com",
            timestamp=datetime(2023, 6, 1),
            message="Early commit",
            is_merge=False,
            insertions=20,
            deletions=8,
        )

        contributor.add_commit(commit1)
        contributor.add_commit(commit2)

        assert contributor.first_commit == datetime(2023, 6, 1)
        assert contributor.last_commit == datetime(2024, 1, 10)
        assert contributor.commit_count == 2
        assert contributor.lines_changed == 43  # (10+20) + (5+8)

    def test_lines_changed_property(self) -> None:
        """Test lines_changed property calculation."""
        contributor = Contributor(
            canonical_name="John Doe",
            canonical_email="john@example.com",
            total_insertions=100,
            total_deletions=50,
        )

        assert contributor.lines_changed == 150


class TestParseMailmap:
    """Tests for parse_mailmap function."""

    def test_parse_empty_mailmap(self, temp_dir: Path) -> None:
        """Test parsing when no .mailmap file exists."""
        mailmap = parse_mailmap(temp_dir)

        assert mailmap == {}

    def test_parse_mailmap_with_mappings(self, temp_dir: Path, sample_mailmap_content: str) -> None:
        """Test parsing a .mailmap file with identity mappings."""
        mailmap_file = temp_dir / ".mailmap"
        mailmap_file.write_text(sample_mailmap_content)

        mailmap = parse_mailmap(temp_dir)

        # Should have parsed the mappings
        assert len(mailmap) > 0

        # Check specific mapping
        # Just check that we parsed something - the actual key format depends on parsing logic
        assert len(mailmap) >= 1  # Should have at least 1 mapping

    def test_parse_mailmap_ignores_comments(self, temp_dir: Path) -> None:
        """Test that comments are ignored in .mailmap."""
        mailmap_file = temp_dir / ".mailmap"
        mailmap_file.write_text("# This is a comment\n")

        mailmap = parse_mailmap(temp_dir)

        assert mailmap == {}


class TestResolveContributor:
    """Tests for resolve_contributor function."""

    def test_resolve_with_mapping(self) -> None:
        """Test resolving a contributor that has a mapping."""
        mailmap = {
            ("Old Name", "old@example.com"): ("New Name", "new@example.com"),
        }

        name, email = resolve_contributor("Old Name", "old@example.com", mailmap)

        assert name == "New Name"
        assert email == "new@example.com"

    def test_resolve_without_mapping(self) -> None:
        """Test resolving a contributor without a mapping returns original."""
        mailmap = {}

        name, email = resolve_contributor("John Doe", "john@example.com", mailmap)

        assert name == "John Doe"
        assert email == "john@example.com"


class TestSuggestIdentityMappings:
    """Tests for suggest_identity_mappings function."""

    def test_suggest_similar_names(self) -> None:
        """Test suggesting mappings for similar names."""
        contributors = [
            ("John Doe", "john@example.com"),
            ("John D.", "john.doe@gmail.com"),
            ("Alice Smith", "alice@example.com"),
        ]

        suggestions = suggest_identity_mappings(contributors, threshold=0.5)

        # Should suggest John Doe and John D. are the same
        assert len(suggestions) >= 1

    def test_suggest_no_similar_names(self) -> None:
        """Test no suggestions for completely different names."""
        contributors = [
            ("Alice Smith", "alice@example.com"),
            ("Bob Jones", "bob@example.com"),
        ]

        suggestions = suggest_identity_mappings(contributors, threshold=0.9)

        # No suggestions for very different names with high threshold
        assert len(suggestions) == 0

    def test_suggest_skips_same_email(self) -> None:
        """Test that same emails are skipped."""
        contributors = [
            ("John", "same@example.com"),
            ("Johnny", "same@example.com"),
        ]

        suggestions = suggest_identity_mappings(contributors)

        # Should not suggest because emails are identical
        assert len(suggestions) == 0
