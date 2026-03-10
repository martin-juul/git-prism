"""File filtering for excluding binary, generated, and data files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class FileFilter:
    """Filter for excluding unwanted files from analysis.

    Attributes:
        binary_extensions: Extensions to exclude as binary files.
        generated_patterns: Filename patterns to exclude as generated.
        data_extensions: Extensions to exclude as data files.
        ignore_paths: Path components to ignore entirely.
        custom_rules: Custom filter functions.
    """

    binary_extensions: set[str] = field(default_factory=set)
    generated_patterns: set[str] = field(default_factory=set)
    data_extensions: set[str] = field(default_factory=set)
    ignore_paths: set[str] = field(default_factory=set)
    custom_rules: list[Callable[[Path], bool]] = field(default_factory=list)

    def should_include(self, file_path: str | Path) -> bool:
        """Check if a file should be included in analysis.

        Args:
            file_path: Path to check.

        Returns:
            True if the file should be included, False to exclude.
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        extension = path.suffix.lower()
        name = path.name.lower()

        # Check ignore paths
        for ignore in self.ignore_paths:
            if ignore in path.parts:
                return False

        # Check binary extensions
        if extension in self.binary_extensions:
            return False

        # Check generated patterns
        for pattern in self.generated_patterns:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:].lower()):
                    return False
            elif name == pattern.lower():
                return False

        # Check data extensions (optional - may want to include some)
        # For now, we include data files in analysis

        # Check custom rules
        for rule in self.custom_rules:
            if not rule(path):
                return False

        # Check for binary content
        return not self._appears_binary(path)

    def _appears_binary(self, path: Path, sample_size: int = 8000) -> bool:
        """Check if file appears to be binary by checking for NUL bytes.

        Args:
            path: Path to check.
            sample_size: Number of bytes to sample.

        Returns:
            True if file appears to be binary.
        """
        try:
            with open(path, "rb") as f:
                chunk = f.read(sample_size)
                return b"\x00" in chunk
        except OSError:
            return True


# Default binary extensions
DEFAULT_BINARY_EXTENSIONS = {
    # Images
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".webp",
    ".tiff",
    ".psd",
    ".ai",
    ".eps",
    # Audio/Video
    ".mp3",
    ".mp4",
    ".wav",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".mkv",
    ".webm",
    ".ogg",
    ".flac",
    # Archives
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".rar",
    ".7z",
    ".tgz",
    # Executables
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".app",
    ".dmg",
    ".deb",
    ".rpm",
    ".msi",
    # Compiled
    ".pyc",
    ".pyo",
    ".class",
    ".jar",
    ".war",
    ".ear",
    ".o",
    ".a",
    ".lib",
    ".obj",
    # Fonts
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".eot",
    # Documents
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".odt",
    ".ods",
    ".odp",
    # Database
    ".db",
    ".sqlite",
    ".sqlite3",
    ".mdb",
    # Other
    ".iso",
    ".img",
    ".bin",
    ".dat",
}

# Default generated file patterns
DEFAULT_GENERATED_PATTERNS = {
    # Lock files
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "composer.lock",
    "cargo.lock",
    "poetry.lock",
    "gemfile.lock",
    "pipfile.lock",
    "pdm.lock",
    # Minified
    "*.min.js",
    "*.min.css",
    # Generated
    "*.pb.go",
    "*.pb.rs",
    "*.grpc.pb.go",
    "*_pb2.py",
    "*_pb2_grpc.py",
    # IDE
    ".ds_store",
    "thumbs.db",
    # Build outputs
    "*.d.ts",
    "*.map",
}


def create_default_filter(
    additional_binary: set[str] | None = None,
    additional_generated: set[str] | None = None,
    ignore_paths: set[str] | None = None,
) -> FileFilter:
    """Create a FileFilter with sensible defaults.

    Args:
        additional_binary: Extra binary extensions to exclude.
        additional_generated: Extra generated patterns to exclude.
        ignore_paths: Path components to ignore.

    Returns:
        Configured FileFilter instance.
    """
    binary = DEFAULT_BINARY_EXTENSIONS.copy()
    if additional_binary:
        binary.update(additional_binary)

    generated = DEFAULT_GENERATED_PATTERNS.copy()
    if additional_generated:
        generated.update(additional_generated)

    ignore = ignore_paths or {"node_modules", ".venv", "venv", "__pycache__", ".git", "dist", "build"}

    return FileFilter(
        binary_extensions=binary,
        generated_patterns=generated,
        ignore_paths=ignore,
    )


def parse_gitattributes(repo_path: str | Path) -> dict[str, dict[str, str]]:
    """Parse .gitattributes for linguist-generated rules.

    Args:
        repo_path: Path to the git repository.

    Returns:
        Dictionary mapping file patterns to their attributes.
    """
    path = Path(repo_path) if isinstance(repo_path, str) else repo_path
    gitattributes = path / ".gitattributes"
    rules: dict[str, dict[str, str]] = {}

    if not gitattributes.exists():
        return rules

    with open(gitattributes) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            pattern = parts[0]
            attrs: dict[str, str] = {}

            for attr in parts[1:]:
                if "=" in attr:
                    key, value = attr.split("=", 1)
                    attrs[key] = value
                else:
                    attrs[attr] = "true"

            rules[pattern] = attrs

    return rules


def is_linguist_generated(file_path: Path, gitattributes_rules: dict[str, dict[str, str]]) -> bool:
    """Check if a file is marked as linguist-generated in .gitattributes.

    Args:
        file_path: Path to the file.
        gitattributes_rules: Rules from parse_gitattributes().

    Returns:
        True if the file is marked as generated.
    """
    import fnmatch

    file_str = str(file_path)
    name = file_path.name

    for pattern, attrs in gitattributes_rules.items():
        if attrs.get("linguist-generated") == "true" and (
            fnmatch.fnmatch(file_str, pattern) or fnmatch.fnmatch(name, pattern)
        ):
            return True

    return False
