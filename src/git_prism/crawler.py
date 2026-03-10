"""Directory crawler for discovering git repositories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitRepo:
    """Represents a discovered git repository.

    Attributes:
        path: Absolute path to the repository root.
        name: Name of the repository (directory name).
        is_submodule: True if this is a git submodule (.git is a file).
    """

    path: Path
    name: str
    is_submodule: bool = False

    def __post_init__(self) -> None:
        """Ensure path is a Path object."""
        if isinstance(self.path, str):
            self.path = Path(self.path)


def discover_repos(
    root_path: str | Path,
    ignore_patterns: list[str] | None = None,
    max_depth: int = 10,
) -> list[GitRepo]:
    """Recursively discover git repositories in directory tree.

    Scans the specified directory and all subdirectories for git repositories.
    Handles both regular repositories and submodules.

    Args:
        root_path: Root directory to start scanning from.
        ignore_patterns: Directory names to skip during scanning.
        max_depth: Maximum directory depth to traverse.

    Returns:
        List of GitRepo objects for each discovered repository.

    Example:
        >>> repos = discover_repos("~/projects", ignore_patterns=["node_modules"])
        >>> for repo in repos:
        ...     print(f"{repo.name} at {repo.path}")
    """
    root = Path(root_path).expanduser().resolve()
    repos: list[GitRepo] = []
    ignore_patterns = ignore_patterns or ["node_modules", ".venv", "venv", "__pycache__"]

    def should_ignore(path: Path) -> bool:
        """Check if path should be ignored based on patterns."""
        return any(ignored in path.parts for ignored in ignore_patterns)

    def scan_directory(directory: Path, depth: int = 0) -> None:
        """Recursively scan directory for git repositories."""
        if depth > max_depth:
            return

        if should_ignore(directory):
            return

        try:
            git_path = directory / ".git"

            if git_path.exists():
                # Found a git repository
                is_submodule = git_path.is_file()
                repos.append(
                    GitRepo(
                        path=directory,
                        name=directory.name,
                        is_submodule=is_submodule,
                    )
                )
                # Don't recurse into found repositories (they manage their own .git)
                return

            # Recurse into subdirectories
            for item in directory.iterdir():
                if item.is_dir() and not should_ignore(item):
                    scan_directory(item, depth + 1)

        except PermissionError:
            # Skip directories we can't read
            pass

    scan_directory(root)

    # Sort by path for consistent output
    repos.sort(key=lambda r: str(r.path))

    return repos
