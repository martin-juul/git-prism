"""Code classification for languages, frameworks, and file types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from git_prism.config import (
    get_area_type_names,
    get_binary_extensions,
    get_framework_detection,
    get_language_map,
    get_monorepo_patterns,
    get_project_indicators,
)

if TYPE_CHECKING:
    from git_prism.analyzer.filters import FileFilter


# Cached config values (loaded once)
_cached_language_map: dict[str, str] | None = None
_cached_binary_extensions: set[str] | None = None


def _get_cached_language_map() -> dict[str, str]:
    """Get cached language map from config."""
    global _cached_language_map
    if _cached_language_map is None:
        _cached_language_map = get_language_map()
    return _cached_language_map


def _get_cached_binary_extensions() -> set[str]:
    """Get cached binary extensions from config."""
    global _cached_binary_extensions
    if _cached_binary_extensions is None:
        _cached_binary_extensions = get_binary_extensions()
    return _cached_binary_extensions


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
        is_fullstack: Whether the repository is a fullstack app (single app with frontend + backend).
        monorepo_info: Monorepo detection info (if monorepo).
        areas: Per-area classification stats.
    """

    languages: dict[str, int] = field(default_factory=dict)
    file_types: dict[FileType, int] = field(default_factory=dict)
    frameworks: list[str] = field(default_factory=list)
    primary_language: str = "None"
    total_files: int = 0
    is_monorepo: bool = False
    is_fullstack: bool = False
    monorepo_info: MonorepoInfo | None = None
    areas: dict[str, AreaClassification] = field(default_factory=dict)


# Frontend file patterns (for directory-based detection)
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
}

# Backend file patterns (for directory-based detection)
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

    # Detect language from config
    language_map = get_language_map()
    language = language_map.get(extension, "unknown")

    # Detect file type
    file_type = FileType.UNKNOWN

    # Test files
    if ".test." in name or ".spec." in name or parent in {"tests", "test", "__tests__"}:
        file_type = FileType.TEST

    # Documentation
    elif extension in {".md", ".rst", ".txt", ".adoc", ".asciidoc", ".org"}:
        file_type = FileType.DOCUMENTATION

    # Config files
    elif extension in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env", ".properties"}:
        if name in {"package.json", "tsconfig.json", "pyproject.toml"}:
            file_type = FileType.BUILD
        else:
            file_type = FileType.CONFIG

    # Build files
    elif name in {"makefile", "dockerfile", "rakefile", "gemfile", "containerfile"} or extension in {
        ".mk",
        ".cmake",
        ".gradle",
    }:
        file_type = FileType.BUILD

    # Frontend
    elif extension in {".jsx", ".tsx", ".vue", ".svelte", ".css", ".scss", ".sass", ".less", ".styl"} or extension in {".js", ".ts"} and any(p in str(path).lower() for p in FRONTEND_PATTERNS):
        file_type = FileType.FRONTEND

    # Backend
    elif any(p in parent for p in BACKEND_PATTERNS):
        file_type = FileType.BACKEND

    # Data files
    elif extension in {".sql", ".graphql", ".gql", ".proto", ".prisma"}:
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

    Scans for common framework indicator files and dependencies.

    Args:
        repo_path: Path to the git repository.

    Returns:
        List of detected framework names.
    """
    path = Path(repo_path) if isinstance(repo_path, str) else repo_path
    frameworks: list[str] = []

    # Get framework detection config
    framework_config = get_framework_detection()
    framework_files = framework_config.get("framework_files", {})

    # Check for framework indicator files
    for indicator, framework in framework_files.items():
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
            js_frameworks = framework_config.get("js_frameworks", {})

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
            py_frameworks = framework_config.get("python_frameworks", {})
            for dep, name in py_frameworks.items():
                if dep in content:
                    frameworks.append(name)
        except OSError:
            pass

    # Check composer.json for PHP frameworks (Laravel, etc.)
    composer_json = path / "composer.json"
    if composer_json.exists():
        try:
            import json

            with open(composer_json) as f:
                data = json.load(f)

            deps = {**data.get("require", {}), **data.get("require-dev", {})}
            php_frameworks = framework_config.get("php_frameworks", {})

            for dep, name in php_frameworks.items():
                if dep in deps:
                    frameworks.append(name)

        except (json.JSONDecodeError, OSError):
            pass

    # Check Gemfile for Ruby frameworks
    gemfile = path / "Gemfile"
    if gemfile.exists():
        try:
            content = gemfile.read_text().lower()
            ruby_frameworks = framework_config.get("ruby_frameworks", {})
            for dep, name in ruby_frameworks.items():
                if dep in content:
                    frameworks.append(name)
        except OSError:
            pass

    # Check go.mod for Go frameworks
    go_mod = path / "go.mod"
    if go_mod.exists():
        try:
            content = go_mod.read_text().lower()
            go_frameworks = framework_config.get("go_frameworks", {})
            for dep, name in go_frameworks.items():
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


def _get_project_indicators() -> dict[str, str]:
    """Get project indicators from config."""
    return get_project_indicators()


def _get_monorepo_patterns() -> list[str]:
    """Get monorepo patterns from config."""
    return get_monorepo_patterns()


def _get_area_type_names() -> dict[str, str]:
    """Get area type names from config."""
    return get_area_type_names()


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

    # Check composer.json autoload paths for packages
    composer_json = path / "composer.json"
    if composer_json.exists():
        areas = _parse_composer_autoload_packages(path)
        if len(areas) >= MIN_MONOREPO_AREAS:
            return MonorepoInfo(detection_source="composer.json:autoload", areas=areas)

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


def _parse_composer_autoload_packages(repo_path: Path) -> list[AreaDefinition]:
    """Parse composer.json autoload paths for local packages.

    Detects monorepo structure from PSR-4 autoload paths like:
    "Baander\\RedisStack\\": "packages/redis-stack/src/"

    Args:
        repo_path: Path to the repository root.

    Returns:
        List of detected area definitions.
    """
    import json

    areas: list[AreaDefinition] = []

    try:
        with open(repo_path / "composer.json") as f:
            config = json.load(f)

        # Check autoload and autoload-dev
        autoload_sections = [
            config.get("autoload", {}).get("psr-4", {}),
            config.get("autoload-dev", {}).get("psr-4", {}),
        ]

        for autoload in autoload_sections:
            for namespace, path in autoload.items():
                if not isinstance(path, str):
                    continue

                # Look for packages/* or similar monorepo patterns
                for pattern in _get_monorepo_patterns():
                    if path.startswith(f"{pattern}/"):
                        # Extract area name: packages/redis-stack/src/ -> redis-stack
                        parts = path.split("/")
                        if len(parts) >= 2:
                            area_dir = parts[1]
                            area_path = repo_path / pattern / area_dir

                            if area_path.is_dir():
                                area_type = _infer_area_type(area_dir, area_path)
                                areas.append(AreaDefinition(
                                    name=_normalize_area_name(area_dir),
                                    path_pattern=f"{pattern}/{area_dir}/**",
                                    area_type=area_type,
                                    detected_from="composer.json:autoload",
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
    project_indicators = _get_project_indicators()

    for item in repo_path.iterdir():
        if not item.is_dir() or item.name.startswith("."):
            continue

        # Check for project indicator files in this SUBDIRECTORY
        for indicator, area_type in project_indicators.items():
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
    monorepo_patterns = _get_monorepo_patterns()
    area_type_names = _get_area_type_names()

    for pattern_dir in monorepo_patterns:
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
    for dir_name, area_type in area_type_names.items():
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
    area_type_names = _get_area_type_names()
    project_indicators = _get_project_indicators()

    # Check name patterns
    for pattern, area_type in area_type_names.items():
        if pattern in name_lower:
            return area_type

    # Check for project indicators
    for indicator, area_type in project_indicators.items():
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


def detect_fullstack(repo_path: Path, classification: RepoClassification) -> bool:
    """Detect if a repo is fullstack (single app with frontend + backend).

    Specifically detects Laravel + Vue.js fullstack applications.

    Args:
        repo_path: Path to the repository root.
        classification: Current classification (to check if monorepo).

    Returns:
        True if fullstack app detected, False otherwise.
    """
    # Must not already be a monorepo
    if classification.is_monorepo:
        return False

    # Check for both PHP (backend) and JS (frontend) at root level
    has_php_backend = (repo_path / "composer.json").exists()
    has_js_frontend = (repo_path / "package.json").exists()

    if not (has_php_backend and has_js_frontend):
        return False

    # Check for Laravel-specific indicators
    has_laravel = (repo_path / "artisan").exists()
    if not has_laravel:
        return False

    # Check for frontend build tools
    has_vite = any([
        (repo_path / "vite.config.js").exists(),
        (repo_path / "vite.config.ts").exists(),
        (repo_path / "vite.config.mjs").exists(),
        (repo_path / "vite.config.mts").exists(),
    ])
    has_mix = (repo_path / "webpack.mix.js").exists()

    # Check for frontend source in resources/js
    resources_js = repo_path / "resources" / "js"
    has_frontend_src = False
    if resources_js.exists():
        try:
            has_frontend_src = any(
                f.suffix in {".js", ".vue", ".ts", ".tsx"}
                for f in resources_js.rglob("*")
                if f.is_file()
            )
        except OSError:
            pass

    return has_vite or has_mix or has_frontend_src


def detect_fullstack_areas(repo_path: Path) -> MonorepoInfo | None:
    """Detect frontend/backend areas for Laravel fullstack applications.

    Creates virtual areas based on Laravel's standard directory structure:
    - Backend: app/, routes/, config/, database/, tests/
    - Frontend: resources/js/, resources/css/

    Args:
        repo_path: Path to the repository root.

    Returns:
        MonorepoInfo with frontend/backend areas, or None if not a Laravel fullstack app.
    """
    # Must be Laravel
    if not (repo_path / "artisan").exists():
        return None

    # Must have frontend indicators
    has_package_json = (repo_path / "package.json").exists()
    resources_js = repo_path / "resources" / "js"
    has_frontend_src = resources_js.exists()

    if not (has_package_json or has_frontend_src):
        return None

    areas: list[AreaDefinition] = []

    # Backend area: PHP files in Laravel directories
    backend_patterns = ["app/**", "routes/**", "config/**", "database/**", "tests/**"]
    has_backend = any(
        (repo_path / pattern.split("/")[0]).exists()
        for pattern in backend_patterns
    )
    if has_backend:
        areas.append(AreaDefinition(
            name="backend",
            path_pattern="backend/**",  # Virtual pattern, matched by _determine_fullstack_file_area
            area_type="backend",
            detected_from="laravel-fullstack",
        ))

    # Frontend area: JS/Vue files in resources
    frontend_patterns = ["resources/js/**", "resources/css/**"]
    has_frontend = any(
        (repo_path / p.split("/")[0] / p.split("/")[1]).exists()
        for p in frontend_patterns
    )
    if has_frontend:
        areas.append(AreaDefinition(
            name="frontend",
            path_pattern="frontend/**",  # Virtual pattern
            area_type="frontend",
            detected_from="laravel-fullstack",
        ))

    if len(areas) >= 2:
        return MonorepoInfo(detection_source="laravel-fullstack", areas=areas)

    return None


def _determine_fullstack_file_area(file_path: str) -> str | None:
    """Determine which fullstack area a file belongs to.

    Maps Laravel directory structure to frontend/backend areas.

    Args:
        file_path: Relative path to the file.

    Returns:
        "frontend", "backend", or None.
    """
    # Backend: Laravel PHP directories
    backend_prefixes = ["app/", "routes/", "config/", "database/", "tests/", "bootstrap/"]
    for prefix in backend_prefixes:
        if file_path.startswith(prefix):
            return "backend"

    # Frontend: resources/js, resources/css, resources/views (Blade/Vue)
    frontend_prefixes = ["resources/js/", "resources/css/", "resources/views/"]
    for prefix in frontend_prefixes:
        if file_path.startswith(prefix):
            return "frontend"

    # Check by file extension in resources
    if file_path.startswith("resources/"):
        ext = file_path.split(".")[-1] if "." in file_path else ""
        if ext in {"js", "vue", "ts", "tsx", "css", "scss", "sass"}:
            return "frontend"
        if ext in {"php"}:
            return "backend"

    return None


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

    # Detect fullstack areas if not a monorepo
    fullstack_info: MonorepoInfo | None = None
    is_fullstack = False
    if monorepo_info is None:
        fullstack_info = detect_fullstack_areas(path)
        is_fullstack = fullstack_info is not None

    # Initialize area classifications if monorepo or fullstack
    areas: dict[str, AreaClassification] = {}
    area_source = monorepo_info or fullstack_info
    if area_source:
        for area_def in area_source.areas:
            areas[area_def.name] = AreaClassification(
                area_name=area_def.name,
                area_path=area_def.path_pattern,
            )

    # Walk the working tree
    for file_path in path.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip excluded files - pass full path for binary detection
        relative_path = file_path.relative_to(path)
        rel_path_str = str(relative_path)
        if not filter_.should_include(file_path):
            continue

        try:
            # Classify with area if monorepo or fullstack
            area_name = None
            if monorepo_info:
                area_name = _determine_file_area(rel_path_str, monorepo_info.areas)
            elif fullstack_info:
                area_name = _determine_fullstack_file_area(rel_path_str)

            classification = classify_file(file_path)
            classification.area = area_name

            if classification.is_binary:
                continue

            # Aggregate repository-wide
            languages[classification.language] = languages.get(classification.language, 0) + 1
            file_types[classification.file_type] = file_types.get(classification.file_type, 0) + 1

            # Aggregate by area if monorepo or fullstack
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

    # Detect frameworks per area (for monorepo)
    if monorepo_info and areas:
        for area_def in monorepo_info.areas:
            if area_def.name in areas:
                area_cls = areas[area_def.name]
                # Extract base path from pattern (e.g., "packages/frontend/**" -> "packages/frontend")
                base_path = area_def.path_pattern.rstrip("/*")
                area_path = path / base_path
                if area_path.exists():
                    area_cls.frameworks = detect_frameworks(area_path)

    # Detect frameworks per area (for fullstack)
    if fullstack_info and areas:
        if "backend" in areas:
            # Backend frameworks from root (Laravel, etc.)
            backend_frameworks = [f for f in frameworks if f in {"PHP", "Laravel"}]
            areas["backend"].frameworks = backend_frameworks or ["PHP"]
        if "frontend" in areas:
            # Frontend frameworks from resources/js
            resources_js = path / "resources" / "js"
            if resources_js.exists():
                areas["frontend"].frameworks = detect_frameworks(resources_js)
            else:
                areas["frontend"].frameworks = ["JavaScript"]

    result = RepoClassification(
        languages=languages,
        file_types=file_types,
        frameworks=frameworks,
        primary_language=primary_language,
        total_files=total_files,
        is_monorepo=monorepo_info is not None,
        is_fullstack=is_fullstack,
        monorepo_info=monorepo_info,
        areas=areas,
    )

    return result


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
