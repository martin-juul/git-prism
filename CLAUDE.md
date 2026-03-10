# Git Prism - Project Conventions

This document defines the coding conventions and patterns for the git-prism project.

## Project Structure

```
git-prism/
├── src/git_prism/          # Main package
│   ├── __init__.py         # Public API exports
│   ├── cli.py              # Typer CLI commands
│   ├── crawler.py          # Git repository discovery
│   ├── analyzer/           # Analysis engine
│   │   ├── __init__.py     # Analyzer class
│   │   ├── commits.py      # Commit streaming (pygit2)
│   │   ├── contributors.py # Identity resolution
│   │   ├── scoring.py      # Expertise algorithms
│   │   ├── classification.py # Language/framework detection
│   │   └── filters.py      # File filtering
│   ├── visualizations/     # Chart generation
│   │   ├── charts.py       # Plotly charts
│   │   └── networks.py     # NetworkX/Pyvis graphs
│   └── report/             # HTML generation
│       └── generator.py    # Jinja2 reports
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── templates/              # Jinja2 HTML templates
└── config/                 # Configuration files
```

## Coding Standards

### Python Version
- Target: Python 3.11+
- Use modern type hints (`list[str]` not `List[str]`)
- Use `from __future__ import annotations` for forward references

### Imports
```python
# Standard library first
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

# Third-party second
import pygit2
import typer

# Local imports last
from git_prism.analyzer import Analyzer
```

### Type Hints
- All public functions must have type hints
- Use `TYPE_CHECKING` for import-time type checking
- Use dataclasses for data structures

```python
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

@dataclass
class MyData:
    name: str
    count: int = 0
```

### Docstrings
- Use Google-style docstrings
- Include Args, Returns, and Examples sections

```python
def calculate_score(contributor: Contributor) -> float:
    """Calculate expertise score for a contributor.

    Args:
        contributor: The contributor to score.

    Returns:
        Expertise score between 0 and 100.

    Example:
        >>> score = calculate_score(contributor)
        >>> assert 0 <= score <= 100
    """
```

### Error Handling
- Use specific exceptions
- Provide helpful error messages
- Log errors appropriately

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = analyze_repo(path)
except pygit2.GitError as e:
    logger.error("Failed to analyze %s: %s", path, e)
    raise typer.Exit(1)
```

## Testing

### Test Organization
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Shared fixtures in `tests/conftest.py`

### Test Naming
```python
class TestClassName:
    """Tests for ClassName."""

    def test_method_name_scenario(self) -> None:
        """Test method behavior in specific scenario."""
```

### Fixtures
- Use pytest fixtures for setup
- Create sample data in fixtures, not in tests

```python
@pytest.fixture
def sample_repo(temp_dir: Path) -> Path:
    """Create a sample git repository."""
    repo = temp_dir / "sample-repo"
    # ... setup code ...
    return repo
```

### Test Markers
```python
@pytest.mark.slow
def test_large_repo_analysis() -> None:
    """Test analysis of large repository."""
    pass

@pytest.mark.integration
def test_full_workflow() -> None:
    """Test complete analysis workflow."""
    pass
```

## CLI Conventions

### Command Structure
- Use Typer for CLI framework
- Use Rich for output formatting
- Follow noun-verb command structure

```python
@app.command()
def analyze(
    path: Annotated[Path, typer.Argument(help="Directory to scan")],
    output: Annotated[Path, typer.Option("-o", "--output")] = Path("report.html"),
) -> None:
    """Analyze git repositories and generate expertise report."""
```

### Output Formatting
- Use Rich tables for tabular data
- Use Rich progress bars for long operations
- Use colors consistently (green=success, red=error, yellow=warning)

```python
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(title="Contributors")
table.add_column("Name", style="green")
table.add_column("Score", justify="right", style="yellow")
console.print(table)
```

## Visualization Conventions

### Plotly Charts
- Use dark theme colors
- Include titles and labels
- Make charts responsive

### Network Graphs
- Use Pyvis for interactive networks
- Size nodes by importance
- Color-code by category

## Performance Guidelines

- Stream commits in batches (5000-10000)
- Use generators for large datasets
- Cache computed values
- Progress reporting for long operations

```python
def stream_commits(repo_path: str, batch_size: int = 5000) -> Iterator[list[CommitInfo]]:
    """Stream commits in batches to avoid memory issues."""
    batch = []
    for commit in walker:
        batch.append(commit)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
```

## Commit Messages

Follow Conventional Commits:
```
feat(analyzer): add support for monorepo detection
fix(cli): handle empty repository gracefully
docs: update README with new CLI options
test(scoring): add tests for recency decay
```
