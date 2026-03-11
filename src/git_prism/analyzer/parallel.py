"""Parallel processing utilities for repository analysis."""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from git_prism.analyzer import AnalysisResult, Analyzer
from git_prism.crawler import GitRepo

if TYPE_CHECKING:
    pass


@dataclass
class ParallelResult:
    """Result of parallel analysis including failures.

    Attributes:
        successes: List of successful analysis results.
        failures: List of (repo_name, repo_path, error_message) tuples for failures.
    """

    successes: list[AnalysisResult]
    failures: list[tuple[str, str, str]]


def resolve_worker_count(workers: str | None) -> int:
    """Resolve worker count from CLI input.

    Args:
        workers: None, numeric string, or "auto".

    Returns:
        Resolved worker count (minimum 1).

    Raises:
        ValueError: If workers string is not "auto" or a valid integer >= 1.

    Example:
        >>> resolve_worker_count(None)
        1
        >>> resolve_worker_count("4")
        4
        >>> resolve_worker_count("auto")  # Returns cpu_count - 1
    """
    if workers is None:
        return 1  # Default: sequential

    if workers.lower() == "auto":
        cpu_count = os.cpu_count() or 1
        return max(1, cpu_count - 1)

    # Try to parse as integer
    try:
        worker_int = int(workers)
    except ValueError:
        raise ValueError(f"Invalid workers value: {workers!r}. Use integer or 'auto'.") from None

    if worker_int < 1:
        raise ValueError(f"Workers must be >= 1, got {worker_int}")
    return min(worker_int, 64)  # Cap at 64 for sanity


def analyze_repo_worker(
    repo_path: str,
    repo_name: str,
    is_submodule: bool,
    max_commits: int,
) -> AnalysisResult:
    """Worker function for parallel repository analysis.

    Creates its own Analyzer instance to avoid pickling issues.
    Must be module-level for ProcessPoolExecutor.

    Args:
        repo_path: Path to repository.
        repo_name: Repository name.
        is_submodule: Whether this is a submodule.
        max_commits: Maximum commits to analyze.

    Returns:
        AnalysisResult for the repository.

    Raises:
        Exception: Any error during analysis (caught by executor).
    """
    repo = GitRepo(
        path=Path(repo_path),
        name=repo_name,
        is_submodule=is_submodule,
    )
    analyzer = Analyzer(max_commits=max_commits)
    return analyzer.analyze(repo)


def analyze_repos_parallel(
    repos: list[GitRepo],
    max_commits: int,
    workers: int,
) -> ParallelResult:
    """Analyze multiple repositories in parallel.

    Args:
        repos: List of repositories to analyze.
        max_commits: Maximum commits per repo.
        workers: Number of parallel workers.

    Returns:
        ParallelResult with successes and failures.

    Example:
        >>> result = analyze_repos_parallel(repos, max_commits=0, workers=4)
        >>> print(f"Success: {len(result.successes)}, Failed: {len(result.failures)}")
    """
    successes: list[AnalysisResult] = []
    failures: list[tuple[str, str, str]] = []

    # Cap workers at repo count to avoid idle processes
    actual_workers = min(workers, len(repos))

    with ProcessPoolExecutor(max_workers=actual_workers) as executor:
        # Submit all repos
        future_to_repo = {
            executor.submit(
                analyze_repo_worker,
                str(repo.path),
                repo.name,
                repo.is_submodule,
                max_commits,
            ): repo
            for repo in repos
        }

        # Collect results as they complete
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                result = future.result()
                successes.append(result)
            except Exception as e:
                failures.append((repo.name, str(repo.path), str(e)))

    return ParallelResult(successes=successes, failures=failures)
