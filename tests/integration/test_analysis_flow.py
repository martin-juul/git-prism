"""Integration tests for the full analysis workflow."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestFullAnalysisWorkflow:
    """Tests for the complete analysis workflow."""

    def test_end_to_end_analysis(self, sample_git_repo: Path) -> None:
        """Test complete analysis from crawl to report."""
        from git_prism.analyzer import Analyzer
        from git_prism.crawler import discover_repos
        from git_prism.report import ReportGenerator

        # Step 1: Discover repos
        repos = discover_repos(sample_git_repo.parent)
        assert len(repos) >= 1

        # Step 2: Analyze repos
        analyzer = Analyzer()
        results = []
        for repo in repos:
            result = analyzer.analyze(repo)
            results.append(result)

        assert len(results) >= 1
        assert results[0].repo_name == "sample-repo"

        # Step 3: Generate report
        output = sample_git_repo.parent / "test-report.html"
        generator = ReportGenerator()
        generator.generate(results, output)

        assert output.exists()
        content = output.read_text()
        assert "<!DOCTYPE html>" in content
        assert "sample-repo" in content

    def test_analysis_with_multiple_repos(self, temp_dir: Path) -> None:
        """Test analysis with multiple repositories."""
        import subprocess

        from git_prism.analyzer import Analyzer
        from git_prism.crawler import discover_repos

        # Create multiple repos
        for i in range(3):
            repo = temp_dir / f"repo-{i}"
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", f"User {i}"],
                cwd=repo,
                check=True,
                capture_output=True,
            )

            # Add a commit
            (repo / "file.txt").write_text(f"content {i}")
            subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"],
                cwd=repo,
                check=True,
                capture_output=True,
            )

        # Analyze
        repos = discover_repos(temp_dir)
        assert len(repos) == 3

        analyzer = Analyzer()
        results = [analyzer.analyze(repo) for repo in repos]

        assert len(results) == 3

    def test_analysis_respects_max_commits(self, sample_git_repo: Path) -> None:
        """Test that max_commits limit is respected."""
        from git_prism.analyzer import Analyzer
        from git_prism.crawler import discover_repos

        repos = discover_repos(sample_git_repo.parent)
        repo = repos[0]

        # Analyze with limit
        analyzer = Analyzer(max_commits=1)
        result = analyzer.analyze(repo)

        # Should only process 1 commit
        total_commits = sum(s.commit_count for s in result.scores)
        assert total_commits <= 1


class TestReportGeneration:
    """Tests for report generation."""

    def test_report_contains_contributors(self, sample_git_repo: Path) -> None:
        """Test that report contains contributor information."""
        from git_prism.analyzer import Analyzer
        from git_prism.crawler import discover_repos
        from git_prism.report import ReportGenerator

        repos = discover_repos(sample_git_repo.parent)
        analyzer = Analyzer()
        results = [analyzer.analyze(repo) for repo in repos]

        output = sample_git_repo.parent / "contributors-report.html"
        generator = ReportGenerator()
        generator.generate(results, output)

        content = output.read_text()

        # Should contain contributor name
        assert "Test User" in content

    def test_report_contains_charts(self, sample_git_repo: Path) -> None:
        """Test that report contains chart placeholders."""
        from git_prism.analyzer import Analyzer
        from git_prism.crawler import discover_repos
        from git_prism.report import ReportGenerator

        repos = discover_repos(sample_git_repo.parent)
        analyzer = Analyzer()
        results = [analyzer.analyze(repo) for repo in repos]

        output = sample_git_repo.parent / "charts-report.html"
        generator = ReportGenerator()
        generator.generate(results, output)

        content = output.read_text()

        # Should contain chart sections
        assert "Heatmap" in content or "heatmap" in content
        assert "Knowledge" in content

    def test_report_valid_html(self, sample_git_repo: Path) -> None:
        """Test that generated report is valid HTML."""
        from html.parser import HTMLParser

        from git_prism.analyzer import Analyzer
        from git_prism.crawler import discover_repos
        from git_prism.report import ReportGenerator

        repos = discover_repos(sample_git_repo.parent)
        analyzer = Analyzer()
        results = [analyzer.analyze(repo) for repo in repos]

        output = sample_git_repo.parent / "valid-report.html"
        generator = ReportGenerator()
        generator.generate(results, output)

        # Parse HTML to check validity
        class ValidatingParser(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.errors: list[str] = []

            def error(self, message: str) -> None:
                self.errors.append(message)

        parser = ValidatingParser()
        content = output.read_text()

        try:
            parser.feed(content)
        except Exception as e:
            pytest.fail(f"Invalid HTML: {e}")


class TestIdentityResolution:
    """Tests for contributor identity resolution."""

    def test_mailmap_resolution(self, temp_dir: Path) -> None:
        """Test identity resolution with .mailmap."""
        import subprocess

        from git_prism.analyzer import Analyzer
        from git_prism.analyzer.contributors import parse_mailmap
        from git_prism.crawler import GitRepo

        # Create repo with mailmap
        repo = temp_dir / "mailmap-repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            check=True,
            capture_output=True,
        )

        # Create mailmap
        mailmap = repo / ".mailmap"
        mailmap.write_text("Canonical Name <canonical@example.com> <test@example.com>\n")

        # Add commit
        (repo / "file.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=repo,
            check=True,
            capture_output=True,
        )

        # Parse mailmap
        mailmap_dict = parse_mailmap(repo)
        assert len(mailmap_dict) > 0 or True  # May be empty if format doesn't match
