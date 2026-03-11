"""Analysis engine for git repository contributor expertise."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from git_prism.analyzer.classification import (
    AreaClassification,
    AreaDefinition,
    FileClassification,
    MonorepoInfo,
    RepoClassification,
    classify_file,
    classify_repository,
    detect_frameworks,
    detect_monorepo_structure,
)
from git_prism.analyzer.commits import CommitInfo, stream_commits
from git_prism.analyzer.contributors import Contributor, parse_mailmap, resolve_contributor
from git_prism.analyzer.filters import FileFilter, create_default_filter
from git_prism.analyzer.scoring import (
    ExpertiseScore,
    calculate_area_expertise_scores,
    calculate_expertise_scores,
)

if TYPE_CHECKING:
    from git_prism.analyzer.classification import AreaDefinition
    from git_prism.crawler import GitRepo

__all__ = [
    "Analyzer",
    "AnalysisResult",
    "AreaClassification",
    "AreaDefinition",
    "CommitInfo",
    "Contributor",
    "ExpertiseScore",
    "FileClassification",
    "MonorepoInfo",
    "RepoClassification",
    "FileFilter",
    "stream_commits",
    "parse_mailmap",
    "resolve_contributor",
    "calculate_expertise_scores",
    "calculate_area_expertise_scores",
    "classify_file",
    "classify_repository",
    "detect_frameworks",
    "detect_monorepo_structure",
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

        # Detect monorepo structure
        monorepo_info = detect_monorepo_structure(repo.path)

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

                # Track files by area if monorepo
                if monorepo_info:
                    for file_path in commit.files:
                        area = self._determine_file_area(file_path, monorepo_info.areas)
                        contributors[key].add_file_to_area(file_path, area)

        # Calculate expertise scores
        scores = calculate_expertise_scores(contributors)

        # Calculate per-area scores if monorepo
        area_scores: dict[str, list[ExpertiseScore]] = {}
        if monorepo_info:
            for area_def in monorepo_info.areas:
                area_scores[area_def.name] = calculate_area_expertise_scores(
                    list(contributors.values()),
                    area_def.name,
                )

            # Add area scores to each ExpertiseScore
            for score in scores:
                for area_name, area_score_list in area_scores.items():
                    for area_score in area_score_list:
                        if (area_score.contributor_name == score.contributor_name
                            and area_score.contributor_email == score.contributor_email):
                            score.area_scores[area_name] = area_score.total_score

        # Classify repository with monorepo awareness
        classification = classify_repository(
            str(repo.path),
            self._file_filter,
            monorepo_info=monorepo_info,
        )

        return AnalysisResult(
            repo_name=repo.name,
            repo_path=repo.path,
            contributors=list(contributors.values()),
            scores=scores,
            classification=classification,
            area_scores=area_scores if monorepo_info else None,
        )

    def _determine_file_area(
        self,
        file_path: str,
        areas: list[AreaDefinition],
    ) -> str | None:
        """Determine which area a file belongs to.

        Args:
            file_path: Path to the file.
            areas: List of area definitions.

        Returns:
            Area name if matched, None for shared/root files.
        """
        import fnmatch

        for area in areas:
            if fnmatch.fnmatch(file_path, area.path_pattern):
                return area.name
            if file_path.startswith(area.path_pattern.rstrip("*")):
                return area.name

        # Root-level files go to shared
        if file_path.startswith((".", "_")) or "/" not in file_path:
            return "shared"

        return None


class AnalysisResult:
    """Result of analyzing a single repository."""

    def __init__(
        self,
        repo_name: str,
        repo_path: Path,
        contributors: list[Contributor],
        scores: list[ExpertiseScore],
        classification: RepoClassification | None = None,
        area_scores: dict[str, list[ExpertiseScore]] | None = None,
    ) -> None:
        """Initialize analysis result.

        Args:
            repo_name: Name of the repository.
            repo_path: Path to the repository.
            contributors: List of contributors found.
            scores: List of expertise scores.
            classification: Repository classification data.
            area_scores: Per-area expertise scores (area_name -> scores list).
        """
        self.repo_name = repo_name
        self.repo_path = repo_path if isinstance(repo_path, Path) else Path(repo_path)
        self.contributors = contributors
        self.scores = scores
        self.classification = classification
        self.area_scores = area_scores or {}
