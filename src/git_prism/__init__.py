"""Git Prism: Analyze git repositories to rank contributor expertise.

This module crawls directories to discover git repositories, analyzes commit
history to rank and score contributors by expertise, and generates comprehensive
HTML reports with interactive visualizations.

Features:
    - Repository discovery: Recursively find git repos in nested directories
    - Identity resolution: Handle multiple identities per contributor (mailmap)
    - Expertise scoring: Weight contributions by recency, complexity, importance
    - Code classification: Detect languages, frameworks, frontend/backend
    - Visualizations: Heatmaps, network graphs, knowledge gap analysis
    - HTML reports: Standalone reports with interactive charts

Example:
    >>> git-prism analyze ~/projects -o report.html
    >>> git-prism contributors ~/projects/my-repo --format table
"""

from __future__ import annotations

__version__ = "0.1.0"

# Public API exports
__all__ = [
    "__version__",
    "discover_repos",
    "GitRepo",
    "Analyzer",
    "ReportGenerator",
    "Contributor",
    "CommitInfo",
    "AnalysisResult",
]

from git_prism.analyzer import AnalysisResult, Analyzer, CommitInfo, Contributor
from git_prism.crawler import GitRepo, discover_repos
from git_prism.report import ReportGenerator
