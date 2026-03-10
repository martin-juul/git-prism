"""Contributor identity resolution with mailmap support."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from git_prism.analyzer.commits import CommitInfo


@dataclass
class Contributor:
    """Represents a contributor with aggregated statistics.

    Attributes:
        canonical_name: Resolved canonical name.
        canonical_email: Resolved canonical email.
        aliases: List of (name, email) tuples that map to this contributor.
        commits: List of commit SHAs.
        total_insertions: Total lines added.
        total_deletions: Total lines removed.
        first_commit: Date of first commit.
        last_commit: Date of most recent commit.
        files_modified: Set of file paths this contributor has modified.
    """

    canonical_name: str
    canonical_email: str
    aliases: list[tuple[str, str]] = field(default_factory=list)
    commits: list[str] = field(default_factory=list)
    total_insertions: int = 0
    total_deletions: int = 0
    first_commit: datetime | None = None
    last_commit: datetime | None = None
    files_modified: set[str] = field(default_factory=set)

    def add_commit(self, commit: CommitInfo) -> None:
        """Add a commit to this contributor's statistics.

        Args:
            commit: CommitInfo object to add.
        """
        self.commits.append(commit.sha)
        self.total_insertions += commit.insertions
        self.total_deletions += commit.deletions

        commit_time = commit.timestamp
        if self.first_commit is None or commit_time < self.first_commit:
            self.first_commit = commit_time
        if self.last_commit is None or commit_time > self.last_commit:
            self.last_commit = commit_time

        self.files_modified.update(commit.files)

    @property
    def lines_changed(self) -> int:
        """Total lines changed (additions + deletions)."""
        return self.total_insertions + self.total_deletions

    @property
    def commit_count(self) -> int:
        """Number of commits."""
        return len(self.commits)


def parse_mailmap(repo_path: str | Path) -> dict[tuple[str, str], tuple[str, str]]:
    """Parse .mailmap for identity mapping.

    The .mailmap file maps multiple identities to a single canonical identity.
    This is useful for SVN migrations or when contributors use different
    email addresses.

    Format:
        Canonical Name <canonical@email> [Other Name] <other@email>

    Args:
        repo_path: Path to the git repository.

    Returns:
        Dictionary mapping (other_name, other_email) -> (canonical_name, canonical_email).

    Example:
        >>> mailmap = parse_mailmap("/path/to/repo")
        >>> canonical = mailmap.get(("John", "john@old.com"), ("John", "john@old.com"))
    """
    mailmap_path = Path(repo_path) / ".mailmap"
    mapping: dict[tuple[str, str], tuple[str, str]] = {}

    if not mailmap_path.exists():
        return mapping

    # Regex to parse mailmap lines
    # Format: Canonical Name <canonical@email> [Other Name] <other@email>
    pattern = re.compile(
        r"^(?P<canonical>[^<]+)<(?P<canonical_email>[^>]+)>"
        r"(?:\s+(?P<other>[^<]+)<(?P<other_email>[^>]+)>)?"
    )

    with open(mailmap_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            match = pattern.match(line)
            if match:
                canonical_name = match.group("canonical").strip()
                canonical_email = match.group("canonical_email").strip()

                other_name = match.group("other")
                other_email = match.group("other_email")

                if other_name and other_email:
                    # Map other identity to canonical
                    other_name = other_name.strip()
                    other_email = other_email.strip()
                    mapping[(other_name, other_email)] = (canonical_name, canonical_email)

    return mapping


def resolve_contributor(
    name: str,
    email: str,
    mailmap: dict[tuple[str, str], tuple[str, str]],
) -> tuple[str, str]:
    """Resolve contributor to canonical identity.

    Args:
        name: Contributor name from commit.
        email: Contributor email from commit.
        mailmap: Mailmap dictionary from parse_mailmap().

    Returns:
        Tuple of (canonical_name, canonical_email).
    """
    return mailmap.get((name, email), (name, email))


def suggest_identity_mappings(
    contributors: list[tuple[str, str]],
    threshold: float = 0.8,
) -> list[tuple[tuple[str, str], tuple[str, str], float]]:
    """Suggest potential identity mappings based on name similarity.

    Useful for repositories that don't have a .mailmap file but have
    contributors using multiple identities.

    Args:
        contributors: List of (name, email) tuples.
        threshold: Minimum similarity score (0-1) to suggest mapping.

    Returns:
        List of ((name1, email1), (name2, email2), similarity_score) tuples.
    """
    from difflib import SequenceMatcher

    suggestions: list[tuple[tuple[str, str], tuple[str, str], float]] = []
    seen: set[frozenset] = set()

    for i, (name1, email1) in enumerate(contributors):
        for name2, email2 in contributors[i + 1 :]:
            # Skip if emails are identical
            if email1 == email2:
                continue

            pair = frozenset([(name1, email1), (name2, email2)])
            if pair in seen:
                continue
            seen.add(pair)

            # Compare names
            similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

            if similarity >= threshold:
                suggestions.append(((name1, email1), (name2, email2), similarity))

    # Sort by similarity descending
    suggestions.sort(key=lambda x: x[2], reverse=True)

    return suggestions
