"""Analysis engine for git repository contributor expertise."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from git_prism.analyzer.classification import (
    FileClassification,
    RepoClassification,
    classify_file,
    classify_repository,
    detect_frameworks,
)
from git_prism.analyzer.commits import CommitInfo, stream_commits
from git_prism.analyzer.contributors import Contributor, parse_mailmap, resolve_contributor
from git_prism.analyzer.filters import FileFilter, create_default_filter
from git_prism.analyzer.scoring import ExpertiseScore, calculate_expertise_scores

if TYPE_CHECKING:
    from git_prism.crawler import GitRepo

__all__ = [
    "Analyzer",
    "AnalysisResult",
    "CommitInfo",
    "Contributor",
    "ExpertiseScore",
    "FileClassification",
    "RepoClassification",
    "FileFilter",
    "stream_commits",
    "parse_mailmap",
    "resolve_contributor",
    "calculate_expertise_scores",
    "classify_file",
    "classify_repository",
    "detect_frameworks",
    "create_default_filter",
]


class Analyzer:
    """Main analyzer for processing git repositories."""

    def __init__(
        self,
        max_commits: int = 0,
        verbose: bool = False,
        batch_size: int = 5000,
    ) -> None:
        """Initialize the analyzer.

        Args:
            max_commits: Maximum commits to analyze (0 = all).
            verbose: Enable verbose output.
            batch_size: Number of commits to process per batch.
        """
        self.max_commits = max_commits
        self.verbose = verbose
        self.batch_size = batch_size
        self._file_filter = create_default_filter()

    def analyze(self, repo: GitRepo) -> AnalysisResult:
        """Analyze a git repository and return contributor expertise data.

        Args:
            repo: GitRepo instance to analyze.

        Returns:
            AnalysisResult with contributor scores and metadata.
        """
        # Parse mailmap for identity resolution
        mailmap = parse_mailmap(str(repo.path))

        # Stream and process commits
        contributors: dict[tuple[str, str], Contributor] = {}

        for batch in stream_commits(
            str(repo.path),
            batch_size=self.batch_size,
            max_commits=self.max_commits,
        ):
            for commit in batch:
                # Resolve to canonical identity
                canonical_name, canonical_email = resolve_contributor(
                    commit.author_name,
                    commit.author_email,
                    mailmap,
                )

                # Get or create contributor
                key = (canonical_name, canonical_email)
                if key not in contributors:
                    contributors[key] = Contributor(
                        canonical_name=canonical_name,
                        canonical_email=canonical_email,
                    )

                # Update contributor stats
                contributors[key].add_commit(commit)

        # Calculate expertise scores
        scores = calculate_expertise_scores(contributors)

        # Classify repository
        classification = classify_repository(str(repo.path), self._file_filter)

        return AnalysisResult(
            repo_name=repo.name,
            repo_path=repo.path,
            contributors=list(contributors.values()),
            scores=scores,
            classification=classification,
        )


class AnalysisResult:
    """Result of analyzing a single repository."""

    def __init__(
        self,
        repo_name: str,
        repo_path: Path,
        contributors: list[Contributor],
        scores: list[ExpertiseScore],
        classification: RepoClassification | None = None,
    ) -> None:
        """Initialize analysis result.

        Args:
            repo_name: Name of the repository.
            repo_path: Path to the repository.
            contributors: List of contributors found.
            scores: List of expertise scores.
            classification: Repository classification data.
        """
        self.repo_name = repo_name
        self.repo_path = repo_path if isinstance(repo_path, Path) else Path(repo_path)
        self.contributors = contributors
        self.scores = scores
        self.classification = classification
