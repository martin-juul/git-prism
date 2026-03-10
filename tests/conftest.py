"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for testing.

    Args:
        tmp_path: Pytest's built-in tmp_path fixture.

    Returns:
        Path to temporary directory.
    """
    return tmp_path


@pytest.fixture
def sample_git_repo(temp_dir: Path) -> Path:
    """Create a sample git repository for testing.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        Path to the sample git repository.
    """
    import subprocess

    repo_path = temp_dir / "sample-repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create some commits
    for i in range(3):
        (repo_path / f"file{i}.txt").write_text(f"Content {i}")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"Commit {i}"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

    return repo_path


@pytest.fixture
def sample_commit_info() -> dict:
    """Sample commit information for testing.

    Returns:
        Dictionary with sample commit data.
    """
    from datetime import datetime

    return {
        "sha": "abc123def456",
        "author_name": "John Doe",
        "author_email": "john@example.com",
        "timestamp": datetime(2024, 1, 15, 10, 30, 0),
        "message": "feat: add new feature",
        "is_merge": False,
        "files_changed": 3,
        "insertions": 50,
        "deletions": 10,
        "files": ["src/main.py", "src/utils.py", "tests/test_main.py"],
    }


@pytest.fixture
def sample_contributors() -> list[dict]:
    """Sample contributor data for testing.

    Returns:
        List of contributor dictionaries.
    """
    from datetime import datetime

    return [
        {
            "canonical_name": "Alice Smith",
            "canonical_email": "alice@example.com",
            "commit_count": 25,
            "lines_changed": 1500,
            "first_commit": datetime(2023, 6, 1),
            "last_commit": datetime(2024, 1, 10),
        },
        {
            "canonical_name": "Bob Jones",
            "canonical_email": "bob@example.com",
            "commit_count": 15,
            "lines_changed": 800,
            "first_commit": datetime(2023, 8, 15),
            "last_commit": datetime(2024, 1, 5),
        },
        {
            "canonical_name": "Charlie Brown",
            "canonical_email": "charlie@example.com",
            "commit_count": 5,
            "lines_changed": 200,
            "first_commit": datetime(2023, 12, 1),
            "last_commit": datetime(2024, 1, 8),
        },
    ]


@pytest.fixture
def mock_logger(caplog: pytest.LogCaptureFixture) -> logging.Logger:
    """Get a logger instance with capture enabled.

    Args:
        caplog: Pytest's caplog fixture.

    Returns:
        Logger instance.
    """
    logger = logging.getLogger("git_prism")
    logger.setLevel(logging.DEBUG)

    with caplog.at_level(logging.DEBUG):
        yield logger

    return logger


@pytest.fixture
def sample_mailmap_content() -> str:
    """Sample .mailmap content for testing.

    Returns:
        Sample mailmap file content.
    """
    return """# Mailmap for identity resolution
John Doe <john@example.com> <jdoe@old-company.com>
John Doe <john@example.com> John <john@personal.com>
Alice Smith <alice@example.com> <asmith@svn.local>
"""


@pytest.fixture
def sample_gitattributes_content() -> str:
    """Sample .gitattributes content for testing.

    Returns:
        Sample gitattributes file content.
    """
    return """# Generated files
package-lock.json linguist-generated=true
yarn.lock linguist-generated=true
*.min.js linguist-generated=true
"""
