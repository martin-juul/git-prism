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
        area: Detected area name (for monorepos).
    """

    path: str
    language: str = "unknown"
    file_type: FileType = FileType.UNKNOWN
    framework: str | None = None
    is_generated: bool = False
    is_binary: bool = False
    area: str | None = None


@dataclass
class AreaDefinition:
    """Definition of a logical area within a monorepo.

    Attributes:
        name: Area name (e.g., "frontend", "backend", "api").
        path_pattern: Glob pattern for matching files in this area.
        area_type: Type classification ("frontend", "backend", "shared").
        detected_from: Source of detection (e.g., "indicator:package.json").
    """

    name: str
    path_pattern: str
    area_type: str
    detected_from: str


@dataclass
class MonorepoInfo:
    """Detected monorepo structure information.

    Attributes:
        detection_source: How monorepo was detected ("pnpm-workspace", "nx.json", etc.).
        areas: List of detected areas.
    """

    detection_source: str
    areas: list[AreaDefinition] = field(default_factory=list)


@dataclass
class AreaClassification:
    """Classification statistics for a single area.

    Attributes:
        area_name: Name of the area.
        area_path: Path pattern for the area.
        languages: Mapping of language name to file count.
        file_types: Mapping of FileType to file count.
        frameworks: List of detected frameworks.
        total_files: Total number of files in this area.
    """

    area_name: str
    area_path: str
    languages: dict[str, int] = field(default_factory=dict)
    file_types: dict[FileType, int] = field(default_factory=dict)
    frameworks: list[str] = field(default_factory=list)
    total_files: int = 0


@dataclass
class RepoClassification:
    """Aggregated classification summary for a repository.

    Attributes:
        languages: Mapping of language name to file count.
        file_types: Mapping of FileType to file count.
        frameworks: List of detected frameworks.
        primary_language: Most common language by file count.
        total_files: Total number of files classified.
        is_monorepo: Whether the repository is a monorepo.
        monorepo_info: Monorepo detection info (if monorepo).
        areas: Per-area classification stats.
    """

    languages: dict[str, int] = field(default_factory=dict)
    file_types: dict[FileType, int] = field(default_factory=dict)
    frameworks: list[str] = field(default_factory=list)
    primary_language: str = "None"
    total_files: int = 0
    is_monorepo: bool = False
    monorepo_info: MonorepoInfo | None = None
    areas: dict[str, AreaClassification] = field(default_factory=dict)


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


# =============================================================================
# Monorepo Detection
# =============================================================================

# Minimum number of areas to consider a repo a monorepo
MIN_MONOREPO_AREAS = 2

# Project file indicators and their inferred area type
PROJECT_INDICATORS: dict[str, str] = {
    "package.json": "frontend",
    "pom.xml": "backend",
    "build.gradle": "backend",
    "build.gradle.kts": "backend",
    "requirements.txt": "backend",
    "pyproject.toml": "backend",
    "go.mod": "backend",
    "Cargo.toml": "backend",
    "Gemfile": "backend",
}

# Common monorepo directory patterns
MONOREPO_DIR_PATTERNS: list[str] = [
    "apps",
    "packages",
    "libs",
    "services",
    "modules",
]

# Common area names that indicate type
AREA_TYPE_NAMES: dict[str, str] = {
    "frontend": "frontend",
    "web": "frontend",
    "client": "frontend",
    "ui": "frontend",
    "backend": "backend",
    "api": "backend",
    "server": "backend",
    "service": "backend",
    "shared": "shared",
    "common": "shared",
    "lib": "shared",
    "core": "shared",
}


def detect_monorepo_structure(repo_path: str | Path) -> MonorepoInfo | None:
    """Detect monorepo structure from workspace configs or directory patterns.

    Detection precedence (highest to lowest):
    1. nx.json - Nx workspace
    2. turbo.json - Turborepo
    3. lerna.json - Lerna
    4. pnpm-workspace.yaml - pnpm workspaces
    5. package.json workspaces - Yarn/npm workspaces
    6. Project indicators in subdirs
    7. Directory patterns (apps/*, packages/*, etc.)

    Args:
        repo_path: Path to the git repository.

    Returns:
        MonorepoInfo if monorepo detected with 2+ areas, None otherwise.
    """
    path = Path(repo_path) if isinstance(repo_path, str) else repo_path

    # 1. Check for workspace config files
    areas: list[AreaDefinition] = []

    # Check nx.json
    if (path / "nx.json").exists():
        areas = _parse_nx_config(path)
        if len(areas) >= MIN_MONOREPO_AREAS:
            return MonorepoInfo(detection_source="nx.json", areas=areas)

    # Check turbo.json
    if (path / "turbo.json").exists():
        areas = _parse_turbo_config(path)
        if len(areas) >= MIN_MONOREPO_AREAS:
            return MonorepoInfo(detection_source="turbo.json", areas=areas)

    # Check lerna.json
    if (path / "lerna.json").exists():
        areas = _parse_lerna_config(path)
        if len(areas) >= MIN_MONOREPO_AREAS:
            return MonorepoInfo(detection_source="lerna.json", areas=areas)

    # Check pnpm-workspace.yaml
    if (path / "pnpm-workspace.yaml").exists():
        areas = _parse_pnpm_workspaces(path)
        if len(areas) >= MIN_MONOREPO_AREAS:
            return MonorepoInfo(detection_source="pnpm-workspace.yaml", areas=areas)

    # Check package.json workspaces
    package_json = path / "package.json"
    if package_json.exists():
        areas = _parse_package_json_workspaces(path)
        if len(areas) >= MIN_MONOREPO_AREAS:
            return MonorepoInfo(detection_source="package.json", areas=areas)

    # 2. Detect areas by scanning subdirectories for project indicators
    areas = _detect_areas_by_project_indicators(path)
    if len(areas) >= MIN_MONOREPO_AREAS:
        return MonorepoInfo(detection_source="project-indicators", areas=areas)

    # 3. Fall back to directory pattern detection
    areas = _detect_area_directories(path)
    if len(areas) >= MIN_MONOREPO_AREAS:
        return MonorepoInfo(detection_source="directory-pattern", areas=areas)

    return None


def _parse_nx_config(repo_path: Path) -> list[AreaDefinition]:
    """Parse nx.json for workspace projects."""
    import json

    areas: list[AreaDefinition] = []

    try:
        with open(repo_path / "nx.json") as f:
            config = json.load(f)

        # Nx uses "projects" key
        projects = config.get("projects", {})
        for name, project_config in projects.items():
            if isinstance(project_config, dict):
                project_path = project_config.get("root", name)
            else:
                project_path = project_config if isinstance(project_config, str) else name

            area_type = _infer_area_type(name, repo_path / project_path)
            areas.append(AreaDefinition(
                name=_normalize_area_name(name),
                path_pattern=f"{project_path}/**",
                area_type=area_type,
                detected_from="nx.json",
            ))
    except (json.JSONDecodeError, OSError, KeyError):
        pass

    return areas


def _parse_turbo_config(repo_path: Path) -> list[AreaDefinition]:
    """Parse turbo.json for workspace packages."""
    import json

    areas: list[AreaDefinition] = []

    try:
        with open(repo_path / "turbo.json") as f:
            config = json.load(f)

        # Turborepo doesn't define packages directly, check package.json workspaces
        # But we can infer from pipeline dependencies
        pipeline = config.get("pipeline", {})
        for name in pipeline.keys():
            if name == "//":  # Root task marker
                continue
            # Extract package name from task (e.g., "build" -> check package.json)
            pass
    except (json.JSONDecodeError, OSError):
        pass

    # Turbo typically uses package.json workspaces, fall back to that
    return _parse_package_json_workspaces(repo_path)


def _parse_lerna_config(repo_path: Path) -> list[AreaDefinition]:
    """Parse lerna.json for workspace packages."""
    import json

    areas: list[AreaDefinition] = []

    try:
        with open(repo_path / "lerna.json") as f:
            config = json.load(f)

        packages = config.get("packages", [])
        for pattern in packages:
            # Lerna uses glob patterns like "packages/*"
            for matched in repo_path.glob(pattern):
                if matched.is_dir():
                    area_type = _infer_area_type(matched.name, matched)
                    areas.append(AreaDefinition(
                        name=_normalize_area_name(matched.name),
                        path_pattern=f"{matched.relative_to(repo_path)}/**",
                        area_type=area_type,
                        detected_from="lerna.json",
                    ))
    except (json.JSONDecodeError, OSError):
        pass

    return areas


def _parse_pnpm_workspaces(repo_path: Path) -> list[AreaDefinition]:
    """Parse pnpm-workspace.yaml for workspace packages."""
    areas: list[AreaDefinition] = []

    try:
        import yaml

        with open(repo_path / "pnpm-workspace.yaml") as f:
            config = yaml.safe_load(f)

        packages = config.get("packages", [])
        for pattern in packages:
            for matched in repo_path.glob(pattern):
                if matched.is_dir():
                    area_type = _infer_area_type(matched.name, matched)
                    areas.append(AreaDefinition(
                        name=_normalize_area_name(matched.name),
                        path_pattern=f"{matched.relative_to(repo_path)}/**",
                        area_type=area_type,
                        detected_from="pnpm-workspace.yaml",
                    ))
    except (ImportError, yaml.YAMLError, OSError):
        pass

    return areas


def _parse_package_json_workspaces(repo_path: Path) -> list[AreaDefinition]:
    """Parse package.json workspaces field."""
    import json

    areas: list[AreaDefinition] = []

    try:
        with open(repo_path / "package.json") as f:
            config = json.load(f)

        workspaces = config.get("workspaces", [])
        # Workspaces can be a list of strings or an object with "packages" key
        if isinstance(workspaces, dict):
            workspaces = workspaces.get("packages", [])

        for pattern in workspaces:
            if not isinstance(pattern, str):
                continue
            for matched in repo_path.glob(pattern):
                if matched.is_dir():
                    area_type = _infer_area_type(matched.name, matched)
                    areas.append(AreaDefinition(
                        name=_normalize_area_name(matched.name),
                        path_pattern=f"{matched.relative_to(repo_path)}/**",
                        area_type=area_type,
                        detected_from="package.json",
                    ))
    except (json.JSONDecodeError, OSError):
        pass

    return areas


def _detect_areas_by_project_indicators(repo_path: Path) -> list[AreaDefinition]:
    """Detect areas by checking subdirectories for project indicator files.

    Note: We check SUBDIRECTORIES only, not the repo root. A root-level
    pom.xml or package.json is often a parent config in monorepos, not
    an indicator of project type.
    """
    areas: list[AreaDefinition] = []

    for item in repo_path.iterdir():
        if not item.is_dir() or item.name.startswith("."):
            continue

        # Check for project indicator files in this SUBDIRECTORY
        for indicator, area_type in PROJECT_INDICATORS.items():
            if (item / indicator).exists():
                areas.append(AreaDefinition(
                    name=_normalize_area_name(item.name),
                    path_pattern=f"{item.name}/**",
                    area_type=area_type,
                    detected_from=f"indicator:{indicator}",
                ))
                break  # Only use first match per directory

    return areas


def _detect_area_directories(repo_path: Path) -> list[AreaDefinition]:
    """Detect areas by common monorepo directory patterns."""
    areas: list[AreaDefinition] = []

    for pattern_dir in MONOREPO_DIR_PATTERNS:
        pattern_path = repo_path / pattern_dir
        if not pattern_path.is_dir():
            continue

        for item in pattern_path.iterdir():
            if not item.is_dir() or item.name.startswith("."):
                continue

            area_type = _infer_area_type(item.name, item)
            areas.append(AreaDefinition(
                name=_normalize_area_name(item.name),
                path_pattern=f"{pattern_dir}/{item.name}/**",
                area_type=area_type,
                detected_from=f"directory-pattern:{pattern_dir}",
            ))

    # Also check for top-level frontend/backend/shared directories
    for dir_name, area_type in AREA_TYPE_NAMES.items():
        dir_path = repo_path / dir_name
        if dir_path.is_dir():
            areas.append(AreaDefinition(
                name=dir_name,
                path_pattern=f"{dir_name}/**",
                area_type=area_type,
                detected_from="directory-pattern:top-level",
            ))

    return areas


def _infer_area_type(name: str, path: Path) -> str:
    """Infer area type from name or directory contents.

    Args:
        name: Directory name.
        path: Full path to the directory.

    Returns:
        Inferred area type: "frontend", "backend", or "shared".
    """
    name_lower = name.lower()

    # Check name patterns
    for pattern, area_type in AREA_TYPE_NAMES.items():
        if pattern in name_lower:
            return area_type

    # Check for project indicators
    for indicator, area_type in PROJECT_INDICATORS.items():
        if (path / indicator).exists():
            return area_type

    # Default to shared for unknown
    return "shared"


def _normalize_area_name(name: str) -> str:
    """Normalize area name by stripping common prefixes and suffixes.

    Args:
        name: Original directory name.

    Returns:
        Normalized area name.
    """
    import re

    # Strip common prefixes: packages-frontend -> frontend
    for prefix in ["packages-", "libs-", "apps-", "services-", "modules-"]:
        if name.lower().startswith(prefix):
            return name[len(prefix) :]

    # Strip @scope/ prefix for scoped packages
    if name.startswith("@"):
        name = re.sub(r"^@[^/]+/", "", name)

    return name


def classify_repository(
    repo_path: str | Path,
    file_filter: FileFilter | None = None,
    monorepo_info: MonorepoInfo | None = None,
) -> RepoClassification:
    """Classify all files in a repository and aggregate results.

    Args:
        repo_path: Path to the git repository.
        file_filter: Optional filter for excluding files.
        monorepo_info: Optional pre-detected monorepo structure.

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

    # Detect monorepo structure if not provided
    if monorepo_info is None:
        monorepo_info = detect_monorepo_structure(path)

    # Initialize area classifications if monorepo
    areas: dict[str, AreaClassification] = {}
    if monorepo_info:
        for area_def in monorepo_info.areas:
            areas[area_def.name] = AreaClassification(
                area_name=area_def.name,
                area_path=area_def.path_pattern,
            )

    # Walk the working tree
    for file_path in path.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip excluded files
        relative_path = file_path.relative_to(path)
        rel_path_str = str(relative_path)
        if not filter_.should_include(rel_path_str):
            continue

        try:
            # Classify with area if monorepo
            area_name = None
            if monorepo_info:
                area_name = _determine_file_area(rel_path_str, monorepo_info.areas)

            classification = classify_file(file_path)
            classification.area = area_name

            if classification.is_binary:
                continue

            # Aggregate repository-wide
            languages[classification.language] = languages.get(classification.language, 0) + 1
            file_types[classification.file_type] = file_types.get(classification.file_type, 0) + 1

            # Aggregate by area if monorepo
            if area_name and area_name in areas:
                area_cls = areas[area_name]
                area_cls.languages[classification.language] = area_cls.languages.get(classification.language, 0) + 1
                area_cls.file_types[classification.file_type] = area_cls.file_types.get(classification.file_type, 0) + 1
                area_cls.total_files += 1

        except (PermissionError, OSError):
            continue  # Skip unreadable files

    # Detect frameworks
    frameworks = detect_frameworks(path)

    # Find primary language
    primary_language = max(languages, key=languages.get) if languages else "None"
    total_files = sum(languages.values())

    # Detect frameworks per area
    if monorepo_info and areas:
        for area_def in monorepo_info.areas:
            if area_def.name in areas:
                area_cls = areas[area_def.name]
                # Extract base path from pattern (e.g., "packages/frontend/**" -> "packages/frontend")
                base_path = area_def.path_pattern.rstrip("/*")
                area_path = path / base_path
                if area_path.exists():
                    area_cls.frameworks = detect_frameworks(area_path)

    return RepoClassification(
        languages=languages,
        file_types=file_types,
        frameworks=frameworks,
        primary_language=primary_language,
        total_files=total_files,
        is_monorepo=monorepo_info is not None,
        monorepo_info=monorepo_info,
        areas=areas,
    )


def _determine_file_area(file_path: str, areas: list[AreaDefinition]) -> str | None:
    """Determine which area a file belongs to.

    Args:
        file_path: Relative path to the file.
        areas: List of area definitions.

    Returns:
        Area name if matched, None for shared/root files.
    """
    import fnmatch

    # Check each area's pattern
    for area in areas:
        if fnmatch.fnmatch(file_path, area.path_pattern) or file_path.startswith(area.path_pattern.rstrip("*")):
            return area.name

    # Root-level files and configs go to shared
    if file_path.startswith((".", "_")) or "/" not in file_path:
        return "shared"

    return None  # Will default to shared in aggregation
