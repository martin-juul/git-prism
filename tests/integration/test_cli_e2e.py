"""Integration tests for the CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from git_prism.cli import app

runner = CliRunner()


class TestCLIAnalyze:
    """Integration tests for the analyze command."""

    def test_analyze_help(self) -> None:
        """Test analyze command help output."""
        result = runner.invoke(app, ["analyze", "--help"])

        assert result.exit_code == 0
        assert "Analyze git repositories" in result.output

    def test_analyze_nonexistent_directory(self) -> None:
        """Test analyze with non-existent directory."""
        result = runner.invoke(app, ["analyze", "/nonexistent/path"])

        assert result.exit_code != 0

    def test_analyze_empty_directory(self, temp_dir: Path) -> None:
        """Test analyze with directory containing no git repos."""
        result = runner.invoke(app, ["analyze", str(temp_dir)])

        assert result.exit_code == 1
        assert "No git repositories found" in result.output

    def test_analyze_single_repo(self, sample_git_repo: Path) -> None:
        """Test analyze with a single git repository."""
        output_file = sample_git_repo.parent / "report.html"

        result = runner.invoke(
            app,
            ["analyze", str(sample_git_repo), "-o", str(output_file)],
        )

        assert result.exit_code == 0
        assert "Report saved to" in result.output
        assert output_file.exists()

    def test_analyze_with_max_commits(self, sample_git_repo: Path) -> None:
        """Test analyze with max commits limit."""
        output_file = sample_git_repo.parent / "report.html"

        result = runner.invoke(
            app,
            [
                "analyze",
                str(sample_git_repo),
                "-o",
                str(output_file),
                "--max-commits",
                "100",
            ],
        )

        assert result.exit_code == 0

    def test_analyze_verbose_mode(self, sample_git_repo: Path) -> None:
        """Test analyze with verbose output."""
        output_file = sample_git_repo.parent / "report.html"

        result = runner.invoke(
            app,
            ["analyze", str(sample_git_repo), "-o", str(output_file), "-v"],
        )

        assert result.exit_code == 0


class TestCLIContributors:
    """Integration tests for the contributors command."""

    def test_contributors_help(self) -> None:
        """Test contributors command help output."""
        result = runner.invoke(app, ["contributors", "--help"])

        assert result.exit_code == 0
        assert "List contributors" in result.output

    def test_contributors_table_format(self, sample_git_repo: Path) -> None:
        """Test contributors with table format."""
        result = runner.invoke(
            app,
            ["contributors", str(sample_git_repo), "--format", "table"],
        )

        assert result.exit_code == 0
        # Table should have headers

    def test_contributors_json_format(self, sample_git_repo: Path) -> None:
        """Test contributors with JSON format."""
        result = runner.invoke(
            app,
            ["contributors", str(sample_git_repo), "--format", "json"],
        )

        assert result.exit_code == 0
        assert "{" in result.output  # JSON output

    def test_contributors_csv_format(self, sample_git_repo: Path) -> None:
        """Test contributors with CSV format."""
        result = runner.invoke(
            app,
            ["contributors", str(sample_git_repo), "--format", "csv"],
        )

        assert result.exit_code == 0
        assert "name,email" in result.output

    def test_contributors_top_limit(self, sample_git_repo: Path) -> None:
        """Test contributors with top limit."""
        result = runner.invoke(
            app,
            ["contributors", str(sample_git_repo), "--top", "5"],
        )

        assert result.exit_code == 0


class TestCLIRepos:
    """Integration tests for the repos command."""

    def test_repos_help(self) -> None:
        """Test repos command help output."""
        result = runner.invoke(app, ["repos", "--help"])

        assert result.exit_code == 0
        assert "List all git repositories" in result.output

    def test_repos_empty_directory(self, temp_dir: Path) -> None:
        """Test repos with empty directory."""
        result = runner.invoke(app, ["repos", str(temp_dir)])

        assert result.exit_code == 0
        assert "No git repositories found" in result.output

    def test_repos_with_repositories(self, sample_git_repo: Path) -> None:
        """Test repos with actual repositories."""
        result = runner.invoke(app, ["repos", str(sample_git_repo.parent)])

        assert result.exit_code == 0
        assert "sample-repo" in result.output

    def test_repos_with_ignore_patterns(self, sample_git_repo: Path) -> None:
        """Test repos with custom ignore patterns."""
        result = runner.invoke(
            app,
            ["repos", str(sample_git_repo.parent), "-i", "node_modules"],
        )

        assert result.exit_code == 0


class TestCLIVersion:
    """Integration tests for version output."""

    def test_version_flag(self) -> None:
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "git-prism version" in result.output
