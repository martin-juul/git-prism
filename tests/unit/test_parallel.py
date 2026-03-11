"""Unit tests for parallel processing utilities."""

from __future__ import annotations

import os

import pytest

from git_prism.analyzer.parallel import (
    ParallelResult,
    analyze_repos_parallel,
    resolve_worker_count,
)


class TestResolveWorkerCount:
    """Tests for resolve_worker_count function."""

    def test_none_returns_one(self) -> None:
        """None should return 1 (sequential default)."""
        assert resolve_worker_count(None) == 1

    def test_integer_string_returns_same(self) -> None:
        """Integer string should be parsed and returned (within bounds)."""
        assert resolve_worker_count("4") == 4

    def test_auto_returns_cpu_minus_one(self) -> None:
        """'auto' should return cpu_count - 1 (minimum 1)."""
        result = resolve_worker_count("auto")
        expected = max(1, (os.cpu_count() or 1) - 1)
        assert result == expected

    def test_auto_caps_at_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If cpu_count is 1, auto should still return 1."""
        monkeypatch.setattr(os, "cpu_count", lambda: 1)
        assert resolve_worker_count("auto") == 1

    def test_auto_handles_none_cpu_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If cpu_count returns None, auto should return 1."""
        monkeypatch.setattr(os, "cpu_count", lambda: None)
        assert resolve_worker_count("auto") == 1

    def test_integer_capped_at_64(self) -> None:
        """Workers should be capped at 64."""
        assert resolve_worker_count("100") == 64

    def test_negative_raises(self) -> None:
        """Negative values should raise ValueError."""
        with pytest.raises(ValueError, match="must be >= 1"):
            resolve_worker_count("-1")

    def test_zero_raises(self) -> None:
        """Zero should raise ValueError."""
        with pytest.raises(ValueError, match="must be >= 1"):
            resolve_worker_count("0")

    def test_invalid_string_raises(self) -> None:
        """Invalid string should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid workers value"):
            resolve_worker_count("invalid")

    def test_case_insensitive_auto(self) -> None:
        """'AUTO' should work the same as 'auto'."""
        result = resolve_worker_count("AUTO")
        expected = max(1, (os.cpu_count() or 1) - 1)
        assert result == expected
