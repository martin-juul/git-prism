# Git Prism

Refract your team's git history into a spectrum of expertise insights. Git Prism analyzes repositories to reveal contributor knowledge, identify subject matter experts, and surface hidden team capabilities through interactive visualizations.

## Features

- **Repository Discovery**: Recursively scan directories to find all git repositories, including submodules and nested projects
- **Identity Resolution**: Unify contributor identities using `.mailmap` support—handle email changes, SVN migrations, and multiple aliases gracefully
- **Expertise Scoring**: Weighted algorithms that factor in contribution recency, code complexity, and file importance—not just commit counts
- **Code Classification**: Automatic detection of languages, frameworks, and frontend/backend component categorization
- **Interactive Visualizations**: Heatmaps, contributor networks, and knowledge gap analysis powered by Plotly
- **Standalone HTML Reports**: Self-contained reports with embedded charts—no server required

## Installation

### Quick Start (Recommended)

**Using uv** (fast, 10-100x faster than pip):

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/martin-juul/git-prism.git
cd git-prism
make init
```

**Using venv** (standard, built-in):

```bash
git clone https://github.com/martin-juul/git-prism.git
cd git-prism
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Prerequisites

- Python 3.11 or higher
- libgit2 (for pygit2)

On macOS:
```bash
brew install libgit2
```

On Ubuntu/Debian:
```bash
sudo apt-get install libgit2-dev
```

### From PyPI (when published)

```bash
# Using uv
uv pip install git-prism

# Using pip
pip install git-prism
```

## Usage

### Basic Usage

```bash
# Analyze all git repos in a directory and generate HTML report
git-prism analyze ~/projects -o report.html

# List contributors for a single repository
git-prism contributors ~/projects/my-repo

# Discover all git repositories in a directory
git-prism repos ~/projects

# Show version
git-prism --version
```

### The `analyze` Command

Analyze git repositories and generate an expertise report with interactive visualizations.

```bash
git-prism analyze [PATH] [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-o, --output PATH` | Output HTML report file path [default: report.html] |
| `-m, --max-commits INT` | Maximum commits to analyze per repo (0 = all) |
| `-i, --ignore TEXT` | Directories to ignore (can be specified multiple times) |
| `-v, --verbose` | Enable verbose output |

**Examples:**
```bash
# Basic analysis
git-prism analyze ~/projects -o expertise-report.html

# Limit commits for faster analysis on large repos
git-prism analyze . --max-commits 10000

# Ignore common directories
git-prism analyze ~/work -i node_modules -i .venv -i build

# Verbose mode for debugging
git-prism analyze . -v
```

### The `contributors` Command

List contributors for a single repository with expertise scores.

```bash
git-prism contributors [REPO_PATH] [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-f, --format TEXT` | Output format: table, json, csv [default: table] |
| `-t, --top INT` | Number of top contributors to show (0 = all) [default: 10] |
| `-v, --verbose` | Enable verbose output |

**Examples:**
```bash
# Show top 10 contributors in a rich table
git-prism contributors ~/projects/my-repo

# Export all contributors as JSON for scripting
git-prism contributors . --format json --top 0 > contributors.json

# CSV output for spreadsheets
git-prism contributors . --format csv --top 20

# Show top 5 experts
git-prism contributors . --top 5
```

### The `repos` Command

List all git repositories found in a directory.

```bash
git-prism repos [PATH] [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-i, --ignore TEXT` | Directories to ignore (can be specified multiple times) |

**Examples:**
```bash
# Discover all repos in your projects folder
git-prism repos ~/projects

# Ignore specific directories
git-prism repos . -i node_modules -i .venv
```

## How Scoring Works

Git Prism calculates expertise scores using a multi-factor weighted algorithm that goes beyond simple commit counting.

### Scoring Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Lines Changed | 40% | Total lines added and removed, weighted by recency |
| Commit Frequency | 30% | Number of commits over time, weighted by recency |
| File Importance | 15% | Core modules rank higher than peripheral files |
| Complexity | 15% | Average cyclomatic complexity of code touched |

### Recency Weighting

Contributions decay exponentially with a 180-day half-life:

| Age | Weight |
|-----|--------|
| Today | 100% |
| 3 months | ~70% |
| 6 months | 50% |
| 1 year | 25% |
| 2 years | ~6% |

This ensures recent contributions are valued appropriately while still acknowledging historical work.

### File Importance

Files are categorized and weighted:

- **Core modules** (main entry points, central logic): 1.0x
- **Feature modules**: 0.8x
- **Tests**: 0.6x
- **Configuration/infrastructure**: 0.5x
- **Generated/vendor files**: Excluded

## Identity Resolution

Git Prism supports `.mailmap` files for resolving multiple identities to canonical contributors. This handles common scenarios:

- Contributors using different email addresses over time
- SVN-to-Git migrations with inconsistent usernames
- Work vs. personal email addresses

**Example `.mailmap`:**
```
Jane Smith <jane@company.com> <jane.smith@old-company.com>
Jane Smith <jane@company.com> <jsmith@svn.local>
John Doe <john@company.com> <johndoe@personal.com>
```

## Development

### Environment Setup

This project supports **uv** (fast, recommended) or **venv** (standard).

**Why uv?**
- 10-100x faster than pip
- Better dependency resolution
- Built-in lockfile support
- From the creators of Ruff

**Using uv (recommended):**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup and sync dependencies
make init

# Run commands
make test
make fmt
```

**Using venv (fallback):**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run commands (make auto-detects venv)
make test
make fmt
```

### Project Structure

```
git-prism/
├── src/git_prism/
│   ├── __init__.py           # Public API exports
│   ├── cli.py                # Typer CLI commands
│   ├── crawler.py            # Git repository discovery
│   ├── analyzer/
│   │   ├── __init__.py       # Analyzer class
│   │   ├── commits.py        # Commit streaming (pygit2)
│   │   ├── contributors.py   # Identity resolution
│   │   ├── scoring.py        # Expertise algorithms
│   │   ├── classification.py # Language/framework detection
│   │   └── filters.py        # File filtering patterns
│   ├── visualizations/
│   │   ├── charts.py         # Plotly chart generation
│   │   └── networks.py       # NetworkX/Pyvis graphs
│   └── report/
│       └── generator.py      # Jinja2 HTML report generation
├── tests/
│   ├── conftest.py           # Shared pytest fixtures
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── templates/                # Jinja2 HTML templates
├── config/                   # Configuration files
├── pyproject.toml            # Project configuration
├── Makefile                  # Common development tasks
└── CLAUDE.md                 # AI assistant conventions
```

**Module Overview:**
- `crawler.py` - `discover_repos()` for recursive repository discovery
- `analyzer/` - Core analysis engine with commit streaming and scoring
- `visualizations/` - Chart and network graph generation
- `report/` - HTML report generation with Jinja2 templates

### Running Tests

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
uv run pytest tests/unit/test_scoring.py

# Run with verbose output
uv run pytest -v

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Skip slow tests
uv run pytest -m "not slow"
```

### Code Quality

```bash
# Format code with ruff
make fmt

# Check linting
make lint

# Run type checking
make typecheck

# Run all quality checks
make check
```

### Make Targets

| Target | Description |
|--------|-------------|
| `make help` | Show all available commands |
| `make init` | Initialize dev environment (auto-detects uv) |
| `make install-uv` | Install uv package manager |
| `make ci` | CI pipeline: install, lint, test, build |
| `make build` | Build Python package (wheel/source) |
| `make test` | Run all tests |
| `make test-cov` | Run tests with coverage report |
| `make test-unit` | Run only unit tests |
| `make test-integration` | Run only integration tests |
| `make fmt` | Format code with ruff |
| `make lint` | Check code with ruff |
| `make typecheck` | Run mypy type checking |
| `make check` | Run all quality checks |
| `make run` | Run git-prism CLI |
| `make run-analyze` | Run analyze on current directory |
| `make clean` | Remove build artifacts |
| `make lock` | Generate/update uv.lock file |
| `make publish` | Upload to PyPI |
| `make publish-test` | Upload to TestPyPI |

### CI Pipeline

For continuous integration or automated builds:

```bash
make ci
```

The CI target:
1. Auto-detects and uses `uv` if available, falls back to `venv`
2. Creates a virtual environment if needed
3. Installs all dependencies
4. Runs ruff linting
5. Runs mypy type checking
6. Runs the test suite
7. Builds the package

### Building and Publishing

```bash
# Build the package
make build

# Generate lockfile (uv only)
make lock

# Upload to TestPyPI for testing
make publish-test

# Upload to PyPI (production)
make publish
```

## Requirements

- Python 3.11+
- libgit2 (for pygit2)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run `make check` to ensure code quality
6. Commit using conventional commits (`feat:`, `fix:`, `docs:`, etc.)
7. Submit a pull request

## Troubleshooting

### "libgit2 not found" Error

Install the libgit2 library:

**macOS:**
```bash
brew install libgit2
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libgit2-dev
```

**Fedora:**
```bash
sudo dnf install libgit2-devel
```

### Slow Analysis on Large Repositories

Use the `--max-commits` flag to limit the analysis:

```bash
git-prism analyze . --max-commits 50000
```

### Missing Contributors

If contributors appear under multiple names, create a `.mailmap` file in the repository root to unify identities.

### Empty Report Generated

Ensure the directory contains valid git repositories:

```bash
git-prism repos ~/projects
```
