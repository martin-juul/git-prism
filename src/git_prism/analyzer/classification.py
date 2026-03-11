"""Code classification for languages, frameworks, and file types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from git_prism.analyzer.filters import FileFilter


class FileType(Enum):
    """Classification of file type."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    DATA = "data"
    CONFIG = "config"
    TEST = "test"
    DOCUMENTATION = "documentation"
    BUILD = "build"
    UNKNOWN = "unknown"


@dataclass
class FileClassification:
    """Classification result for a file.

    Attributes:
        path: File path.
        language: Detected programming language.
        file_type: Classification of file type.
        framework: Detected framework (if any).
        is_generated: Whether the file is generated.
        is_binary: Whether the file is binary.
    """

    path: str
    language: str = "unknown"
    file_type: FileType = FileType.UNKNOWN
    framework: str | None = None
    is_generated: bool = False
    is_binary: bool = False


@dataclass
class RepoClassification:
    """Aggregated classification summary for a repository.

    Attributes:
        languages: Mapping of language name to file count.
        file_types: Mapping of FileType to file count.
        frameworks: List of detected frameworks.
        primary_language: Most common language by file count.
        total_files: Total number of files classified.
    """

    languages: dict[str, int] = field(default_factory=dict)
    file_types: dict[FileType, int] = field(default_factory=dict)
    frameworks: list[str] = field(default_factory=list)
    primary_language: str = "None"
    total_files: int = 0


# Language detection by extension
LANGUAGE_MAP: dict[str, str] = {
    # Frontend
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    # Backend
    ".py": "Python",
    ".rb": "Ruby",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".php": "PHP",
    ".cs": "C#",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".clj": "Clojure",
    ".lisp": "Lisp",
    ".lua": "Lua",
    ".r": "R",
    ".jl": "Julia",
    # Data
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".sql": "SQL",
    ".graphql": "GraphQL",
    ".proto": "Protocol Buffers",
    # Config
    ".ini": "INI",
    ".cfg": "Config",
    ".conf": "Config",
    ".env": "Environment",
    ".sh": "Shell",
    ".bash": "Bash",
    ".zsh": "Zsh",
    ".ps1": "PowerShell",
    ".bat": "Batch",
    # Documentation
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".txt": "Text",
    ".adoc": "AsciiDoc",
    # Build
    ".mk": "Makefile",
    ".cmake": "CMake",
    ".gradle": "Gradle",
    ".maven": "Maven",
    ".dockerfile": "Dockerfile",
}

# Framework detection patterns
FRAMEWORK_FILES: dict[str, str] = {
    "package.json": "Node.js",
    "requirements.txt": "Python",
    "Pipfile": "Python (Pipenv)",
    "pyproject.toml": "Python",
    "Gemfile": "Ruby",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java (Gradle)",
    "composer.json": "PHP",
    "packages.config": ".NET",
    "*.csproj": ".NET",
    "Cartfile": "iOS (Carthage)",
    "Podfile": "iOS (CocoaPods)",
    "Package.swift": "Swift",
    "mix.exs": "Elixir",
    "rebar.config": "Erlang",
    "stack.yaml": "Haskell (Stack)",
    "project.clj": "Clojure (Leiningen)",
}

# Frontend file patterns
FRONTEND_PATTERNS = {
    "components",
    "views",
    "pages",
    "styles",
    "assets",
    "public",
    "static",
    "__tests__",
    "__mocks__",
    ".test.",
    ".spec.",
    ".stories.",
}

# Backend file patterns
BACKEND_PATTERNS = {
    "models",
    "controllers",
    "services",
    "repositories",
    "migrations",
    "schemas",
    "api",
    "routes",
    "middleware",
    "utils",
    "lib",
    "src",
    "app",
    "core",
    "domain",
}


def classify_file(
    file_path: str | Path,
    content: str | None = None,
) -> FileClassification:
    """Classify a file by language, type, and framework.

    Args:
        file_path: Path to the file.
        content: Optional file content for deeper analysis.

    Returns:
        FileClassification with detected metadata.
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path
    extension = path.suffix.lower()
    name = path.name.lower()
    parent = path.parent.name.lower()

    # Detect language
    language = LANGUAGE_MAP.get(extension, "unknown")

    # Detect file type
    file_type = FileType.UNKNOWN

    # Test files
    if ".test." in name or ".spec." in name or parent in {"tests", "test", "__tests__"}:
        file_type = FileType.TEST

    # Documentation
    elif extension in {".md", ".rst", ".txt", ".adoc"}:
        file_type = FileType.DOCUMENTATION

    # Config files
    elif extension in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env"}:
        if name in {"package.json", "tsconfig.json", "pyproject.toml"}:
            file_type = FileType.BUILD
        else:
            file_type = FileType.CONFIG

    # Build files
    elif name in {"makefile", "dockerfile", "rakefile", "gemfile"} or extension in {
        ".mk",
        ".cmake",
        ".gradle",
    }:
        file_type = FileType.BUILD

    # Frontend
    elif extension in {".jsx", ".tsx", ".vue", ".svelte", ".css", ".scss", ".sass", ".less"} or extension in {".js", ".ts"} and any(p in str(path).lower() for p in FRONTEND_PATTERNS):
        file_type = FileType.FRONTEND

    # Backend
    elif any(p in parent for p in BACKEND_PATTERNS):
        file_type = FileType.BACKEND

    # Data files
    elif extension in {".sql", ".graphql", ".proto"}:
        file_type = FileType.DATA

    # Check if generated
    is_generated = _is_generated_file(path, content)

    return FileClassification(
        path=str(path),
        language=language,
        file_type=file_type,
        is_generated=is_generated,
        is_binary=_is_binary_extension(extension),
    )


def _is_binary_extension(extension: str) -> bool:
    """Check if extension typically indicates a binary file."""
    binary_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".svg",
        ".webp",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".rar",
        ".7z",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".class",
        ".jar",
        ".war",
        ".pyc",
        ".pyo",
        ".o",
        ".a",
        ".lib",
        ".mp3",
        ".mp4",
        ".wav",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".ttf",
        ".otf",
        ".woff",
        ".woff2",
        ".eot",
    }
    return extension in binary_extensions


def _is_generated_file(path: Path, content: str | None = None) -> bool:
    """Check if file appears to be generated."""
    name = path.name.lower()

    # Known generated file patterns
    generated_patterns = {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "composer.lock",
        "cargo.lock",
        "poetry.lock",
        "gemfile.lock",
        "pipfile.lock",
        "*.min.js",
        "*.min.css",
        ".d.ts",
        "generated",
        "auto-generated",
    }

    for pattern in generated_patterns:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern:
            return True

    # Check content for generated markers
    if content:
        markers = [
            "auto-generated",
            "automatically generated",
            "do not edit",
            "generated by",
            "@generated",
        ]
        content_lower = content[:1000].lower()
        for marker in markers:
            if marker in content_lower:
                return True

    return False


def detect_frameworks(repo_path: str | Path) -> list[str]:
    """Detect frameworks used in a repository.

    Scans for common framework indicator files.

    Args:
        repo_path: Path to the git repository.

    Returns:
        List of detected framework names.
    """
    path = Path(repo_path) if isinstance(repo_path, str) else repo_path
    frameworks: list[str] = []

    # Check for framework indicator files
    for indicator, framework in FRAMEWORK_FILES.items():
        if indicator.startswith("*"):
            # Glob pattern
            if list(path.glob(indicator)):
                frameworks.append(framework)
        elif (path / indicator).exists():
            frameworks.append(framework)

    # Deep inspection of package.json for JS frameworks
    package_json = path / "package.json"
    if package_json.exists():
        try:
            import json

            with open(package_json) as f:
                data = json.load(f)

            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

            js_frameworks = {
                "react": "React",
                "vue": "Vue.js",
                "angular": "Angular",
                "@angular/core": "Angular",
                "svelte": "Svelte",
                "next": "Next.js",
                "nuxt": "Nuxt.js",
                "gatsby": "Gatsby",
                "express": "Express.js",
                "fastify": "Fastify",
                "nestjs": "NestJS",
                "django": "Django",  # In case it's a monorepo
            }

            for dep, name in js_frameworks.items():
                if dep in deps:
                    frameworks.append(name)

        except (json.JSONDecodeError, OSError):
            pass

    # Check requirements.txt for Python frameworks
    requirements = path / "requirements.txt"
    if requirements.exists():
        try:
            content = requirements.read_text().lower()
            py_frameworks = {
                "django": "Django",
                "flask": "Flask",
                "fastapi": "FastAPI",
                "tornado": "Tornado",
                "pyramid": "Pyramid",
                "bottle": "Bottle",
                "sanic": "Sanic",
                "starlette": "Starlette",
            }
            for dep, name in py_frameworks.items():
                if dep in content:
                    frameworks.append(name)
        except OSError:
            pass

    return list(set(frameworks))  # Remove duplicates


def classify_repository(
    repo_path: str | Path,
    file_filter: FileFilter | None = None,
) -> RepoClassification:
    """Classify all files in a repository and aggregate results.

    Args:
        repo_path: Path to the git repository.
        file_filter: Optional filter for excluding files.

    Returns:
        RepoClassification with aggregated statistics.

    Example:
        >>> classification = classify_repository("./my-repo")
        >>> print(classification.primary_language)
        'Python'
        >>> print(classification.frameworks)
        ['Django', 'React']
    """
    from git_prism.analyzer.filters import create_default_filter

    path = Path(repo_path) if isinstance(repo_path, str) else repo_path
    filter_ = file_filter or create_default_filter()

    languages: dict[str, int] = {}
    file_types: dict[FileType, int] = {}

    # Walk the working tree
    for file_path in path.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip excluded files
        relative_path = file_path.relative_to(path)
        if not filter_.should_include(str(relative_path)):
            continue

        try:
            classification = classify_file(file_path)
            if classification.is_binary:
                continue

            # Aggregate
            languages[classification.language] = languages.get(classification.language, 0) + 1
            file_types[classification.file_type] = file_types.get(classification.file_type, 0) + 1

        except (PermissionError, OSError):
            continue  # Skip unreadable files

    # Detect frameworks
    frameworks = detect_frameworks(path)

    # Find primary language
    primary_language = max(languages, key=languages.get) if languages else "None"
    total_files = sum(languages.values())

    return RepoClassification(
        languages=languages,
        file_types=file_types,
        frameworks=frameworks,
        primary_language=primary_language,
        total_files=total_files,
    )
