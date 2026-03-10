"""Commit streaming and analysis using pygit2."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class CommitInfo:
    """Information about a single commit.

    Attributes:
        sha: Commit hash.
        author_name: Name of the commit author.
        author_email: Email of the commit author.
        timestamp: When the commit was made.
        message: Commit message.
        is_merge: Whether this is a merge commit (2+ parents).
        files_changed: Number of files modified.
        insertions: Lines added.
        deletions: Lines removed.
        files: List of file paths changed in this commit.
    """

    sha: str
    author_name: str
    author_email: str
    timestamp: datetime
    message: str
    is_merge: bool
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    files: list[str] = field(default_factory=list)


def stream_commits(
    repo_path: str,
    batch_size: int = 5000,
    max_commits: int = 0,
    include_merges: bool = False,
) -> Iterator[list[CommitInfo]]:
    """Stream commits from repository in batches.

    Uses pygit2 for high-performance commit traversal. Yields batches
    of commits to allow processing large repositories without memory bloat.

    Args:
        repo_path: Path to the git repository.
        batch_size: Number of commits per batch.
        max_commits: Maximum total commits to yield (0 = all).
        include_merges: Whether to include merge commits.

    Yields:
        Lists of CommitInfo objects, each list containing up to batch_size commits.

    Example:
        >>> for batch in stream_commits("/path/to/repo", batch_size=1000):
        ...     for commit in batch:
        ...         print(f"{commit.sha[:8]} by {commit.author_name}")
    """
    import pygit2

    repo = pygit2.Repository(repo_path)

    # Get HEAD commit
    try:
        head = repo[repo.head.target]
    except pygit2.GitError:
        # Empty repository
        return

    # Create walker sorted by time
    walker = repo.walk(head.id, pygit2.enums.SortMode.TIME)

    batch: list[CommitInfo] = []
    count = 0

    for commit in walker:
        if max_commits > 0 and count >= max_commits:
            break

        is_merge = len(commit.parents) > 1
        if is_merge and not include_merges:
            continue

        # Get diff stats
        insertions, deletions, files_changed = 0, 0, 0
        changed_files: list[str] = []

        if commit.parents:
            try:
                diff = repo.diff(commit.parents[0], commit)
                insertions = diff.stats.insertions
                deletions = diff.stats.deletions
                files_changed = len(list(diff))

                # Collect file paths
                for delta in diff.deltas:
                    if delta.new_file.path:
                        changed_files.append(delta.new_file.path)
            except pygit2.GitError:
                # Skip commits with diff errors (e.g., initial commit)
                pass

        info = CommitInfo(
            sha=str(commit.id),
            author_name=commit.author.name or "Unknown",
            author_email=commit.author.email or "unknown@unknown",
            timestamp=datetime.fromtimestamp(commit.commit_time, tz=None),
            message=commit.message or "",
            is_merge=is_merge,
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
            files=changed_files,
        )

        batch.append(info)
        count += 1

        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch
