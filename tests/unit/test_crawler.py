"""Unit tests for the crawler module."""

from __future__ import annotations

from pathlib import Path

import pytest

from git_prism.crawler import GitRepo, discover_repos


class TestGitRepo:
    """Tests for GitRepo dataclass."""

    def test_git_repo_creation(self) -> None:
        """Test creating a GitRepo instance."""
        repo = GitRepo(
            path=Path("/path/to/repo"),
            name="repo",
            is_submodule=False,
        )

        assert repo.path == Path("/path/to/repo")
        assert repo.name == "repo"
        assert repo.is_submodule is False

    def test_git_repo_string_path_conversion(self) -> None:
        """Test that string paths are converted to Path objects."""
        repo = GitRepo(
            path="/path/to/repo",
            name="repo",
        )

        assert isinstance(repo.path, Path)
        assert repo.path == Path("/path/to/repo")

    def test_git_repo_default_values(self) -> None:
        """Test default values for optional fields."""
        repo = GitRepo(
            path=Path("/path/to/repo"),
            name="repo",
        )

        assert repo.is_submodule is False


class TestDiscoverRepos:
    """Tests for discover_repos function."""

    def test_discover_empty_directory(self, temp_dir: Path) -> None:
        """Test discovering repos in an empty directory."""
        repos = discover_repos(temp_dir)

        assert repos == []

    def test_discover_single_repo(self, sample_git_repo: Path) -> None:
        """Test discovering a single git repository."""
        repos = discover_repos(sample_git_repo.parent)

        assert len(repos) == 1
        assert repos[0].name == "sample-repo"
        assert repos[0].is_submodule is False

    def test_discover_with_ignore_patterns(self, temp_dir: Path) -> None:
        """Test that ignored directories are skipped."""
        import subprocess

        # Create a repo in node_modules (should be ignored)
        node_modules = temp_dir / "node_modules" / "some-package"
        node_modules.mkdir(parents=True)
        subprocess.run(["git", "init"], cwd=node_modules, check=True, capture_output=True)

        # Create a regular repo
        regular_repo = temp_dir / "my-project"
        regular_repo.mkdir()
        subprocess.run(["git", "init"], cwd=regular_repo, check=True, capture_output=True)

        repos = discover_repos(temp_dir, ignore_patterns=["node_modules"])

        # Should only find the regular repo
        assert len(repos) == 1
        assert repos[0].name == "my-project"

    def test_discover_nested_repos(self, temp_dir: Path) -> None:
        """Test discovering nested git repositories."""
        import subprocess

        # Create parent repo
        parent = temp_dir / "parent"
        parent.mkdir()
        subprocess.run(["git", "init"], cwd=parent, check=True, capture_output=True)

        # Create nested repo (but not inside parent's .git)
        nested = temp_dir / "separate" / "nested"
        nested.mkdir(parents=True)
        subprocess.run(["git", "init"], cwd=nested, check=True, capture_output=True)

        repos = discover_repos(temp_dir)

        assert len(repos) == 2
        names = {r.name for r in repos}
        assert "parent" in names
        assert "nested" in names

    def test_discover_sorted_by_path(self, temp_dir: Path) -> None:
        """Test that discovered repos are sorted by path."""
        import subprocess

        # Create repos in non-alphabetical order
        for name in ["zebra", "alpha", "middle"]:
            repo = temp_dir / name
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

        repos = discover_repos(temp_dir)

        # Should be sorted alphabetically by path
        assert repos[0].name == "alpha"
        assert repos[1].name == "middle"
        assert repos[2].name == "zebra"

    def test_discover_max_depth(self, temp_dir: Path) -> None:
        """Test that max_depth limits traversal depth."""
        import subprocess

        # Create deeply nested repo
        deep = temp_dir / "a" / "b" / "c" / "d" / "e" / "deep-repo"
        deep.mkdir(parents=True)
        subprocess.run(["git", "init"], cwd=deep, check=True, capture_output=True)

        # With low max_depth, shouldn't find the deep repo
        repos = discover_repos(temp_dir, max_depth=3)
        assert len(repos) == 0

        # With higher max_depth, should find it
        repos = discover_repos(temp_dir, max_depth=10)
        assert len(repos) == 1
