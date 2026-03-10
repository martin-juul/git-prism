---
title: Git Repository Contributor Expertise Analyzer CLI
type: feat
date: 2026-03-10
---

# Git Repository Contributor Expertise Analyzer CLI

## Overview

A Python CLI tool (`git-prism`) that crawls directories to discover git repositories, analyzes commit history to rank and score contributors by expertise, and generates comprehensive HTML reports with interactive visualizations. The tool identifies which contributors are experts in which repositories, their specializations (frontend/backend, languages, frameworks), and visualizes team knowledge distribution.

## Problem Statement / Motivation

Understanding contributor expertise across multiple repositories is challenging, especially for:
- **Organizations with many microservices/repos**: Who knows what?
- **Teams with SVN-to-Git migrations**: Multiple identities per contributor
- **Onboarding**: Identifying subject matter experts for knowledge transfer
- **Knowledge continuity**: Detecting knowledge gaps and code rot risk

Current solutions require manual git log analysis or expensive enterprise tools. This CLI provides an open-source, offline-capable solution.

## Proposed Solution

Build a Python CLI using:
- **pygit2** for high-performance git operations (handles 100k+ commit repos)
- **tree-sitter** for multi-language AST parsing
- **Radon** for complexity metrics
- **NetworkX + Pyvis** for contributor relationship graphs
- **Plotly** for interactive HTML charts
- **Jinja2** for report templating
- **Typer** for modern CLI interface

## Technical Considerations

### Architecture

```
git-prism/
├── cli.py                    # Typer CLI entry point
├── git_prism/
│   ├── __init__.py
│   ├── crawler.py            # Directory/repo discovery
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── commits.py        # Commit stream processing
│   │   ├── contributors.py   # Identity resolution (mailmap)
│   │   ├── scoring.py        # Expertise scoring algorithms
│   │   ├── complexity.py     # AST + cyclomatic complexity
│   │   └── classification.py # Frontend/backend detection
│   ├── visualizations/
│   │   ├── __init__.py
│   │   ├── charts.py         # Plotly chart generation
│   │   └── networks.py       # NetworkX/Pyvis graphs
│   └── report/
│       ├── __init__.py
│       └── generator.py      # Jinja2 HTML report
├── templates/
│   ├── base.html
│   ├── report.html
│   └── components/
├── config/
│   └── file_patterns.yaml    # BLOB/generated file patterns
└── tests/
```

### Git Library Decision

**Recommended: pygit2**

| Library | Performance | Dependencies | Large Repos | Decision |
|---------|------------|--------------|-------------|----------|
| pygit2 | Excellent (C bindings) | libgit2 native | Excellent | **Primary** |
| Dulwich | Good (pure Python) | None | Good | Fallback |
| GitPython | Poor (subprocess) | git binary | Poor | Avoid |

### Scoring Algorithm

```python
expertise_score = (
    lines_changed_weight * recency_decay(lines_changed) +
    commit_frequency_weight * recency_decay(commit_count) +
    file_importance_weight * core_module_bonus +
    complexity_weight * average_complexity_touched
) / normalization_factor
```

**Recency Weighting**: Exponential decay with half-life of 180 days

### BLOB File Exclusion Strategy

1. **Extension-based**: `*.png, *.jpg, *.pdf, *.zip, *.pyc, etc.`
2. **Filename patterns**: `package-lock.json, yarn.lock, *.min.js`
3. **Content heuristics**: NUL bytes in first 8000 bytes
4. **Git attributes**: Parse `.gitattributes` for `linguist-generated`

### Contributor Identity Resolution

Support for SVN migration scenarios:
1. Parse `.mailmap` file for canonical identity mapping
2. Allow manual identity mapping via config file
3. Fuzzy matching suggestions for unmapped identities

```gitconfig
# .mailmap example
John Doe <john@company.com> <jdoe@svn.local>
John Doe <john@company.com> <john.doe@old-domain.com>
```

### Large Repository Handling

- Stream commits in batches of 5,000-10,000
- Use generators to avoid memory bloat
- Progress reporting for repos > 50k commits
- Optional commit limit for initial analysis

## Acceptance Criteria

### Functional Requirements

- [ ] **Directory Crawling**
  - [ ] Recursively find git repositories in nested directories
  - [ ] Detect and handle git submodules
  - [ ] Support filtering by glob patterns
  - [ ] Skip directories matching ignore patterns

- [ ] **Commit Analysis**
  - [ ] Stream commits efficiently for repos with 100k+ commits
  - [ ] Exclude merge commits (2+ parents)
  - [ ] Parse file diffs for lines added/removed
  - [ ] Track file modification history per contributor

- [ ] **File Filtering**
  - [ ] Exclude binary files (images, compiled code, archives)
  - [ ] Exclude generated files (lock files, minified code)
  - [ ] Exclude data files (CSV, JSON when not source)
  - [ ] Parse `.gitattributes` for additional rules

- [ ] **Contributor Scoring**
  - [ ] Calculate lines changed (weighted by recency)
  - [ ] Calculate commit frequency (weighted by recency)
  - [ ] Assess file importance (core vs peripheral modules)
  - [ ] Measure code complexity contributions
  - [ ] Aggregate scores per contributor per repo

- [ ] **Classification**
  - [ ] Detect programming language by file extension
  - [ ] Detect frameworks from dependencies (package.json, requirements.txt)
  - [ ] Classify files as frontend/backend/data/config
  - [ ] Identify contributor specializations

- [ ] **Identity Resolution**
  - [ ] Parse `.mailmap` for canonical identities
  - [ ] Support manual identity mapping config
  - [ ] Handle SVN migration edge cases

- [ ] **Visualizations**
  - [ ] Service map: contributor → repo expertise heatmap
  - [ ] Contributor relation map: collaboration network graph
  - [ ] Knowledge gap map: understaffed areas visualization
  - [ ] Code rot map: stale code ownership analysis

- [ ] **HTML Report Generation**
  - [ ] Generate standalone HTML files
  - [ ] Include interactive Plotly charts
  - [ ] Include Pyvis network visualizations
  - [ ] Support custom templates

### Non-Functional Requirements

- [ ] **Performance**
  - [ ] Process 100k commit repo in < 5 minutes
  - [ ] Memory usage < 500MB for large repos
  - [ ] Streaming/pagination for all operations

- [ ] **CLI UX**
  - [ ] Progress indicators for long operations
  - [ ] Verbose mode with detailed logging
  - [ ] Graceful error handling
  - [ ] Clear help documentation

- [ ] **Output**
  - [ ] Valid HTML5 reports
  - [ ] Responsive design for reports
  - [ ] Charts render without internet (bundled JS)

## Success Metrics

1. **Accuracy**: Manual verification of top 3 experts per repo matches team knowledge
2. **Performance**: 100k commit repo analyzed in < 5 minutes
3. **Coverage**: Handles at least 10 common programming languages
4. **Usability**: Non-technical users can generate reports with single command

## Dependencies & Risks

### Dependencies
- **pygit2** requires libgit2 installation (document for users)
- **tree-sitter** requires language grammars (bundle common ones)
- **puremagic** for file detection (pure Python, low risk)

### Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| pygit2 installation complexity | High | Provide Docker image, detailed docs |
| Large repo memory issues | Medium | Streaming, batch processing |
| Incorrect identity mapping | Medium | Validation warnings, manual override |
| Performance on network drives | Low | Document local clone recommendation |

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Project setup (pyproject.toml, dependencies)
- [ ] CLI framework with Typer
- [ ] Directory crawler with git detection
- [ ] pygit2 commit streaming

### Phase 2: Analysis Engine
- [ ] Contributor identity resolution
- [ ] BLOB file filtering
- [ ] Scoring algorithms
- [ ] Code classification

### Phase 3: Visualizations
- [ ] Plotly chart generation
- [ ] NetworkX contributor graphs
- [ ] Pyvis network visualization
- [ ] Jinja2 report templates

### Phase 4: Polish & Testing
- [ ] Performance optimization
- [ ] Test suite (unit + integration)
- [ ] Documentation
- [ ] Error handling

## MVP

### cli.py

```python
"""git-prism CLI entry point."""
import typer
from typing_extensions import Annotated
from pathlib import Path

app = typer.Typer(
    name="git-prism",
    help="Analyze git repositories to rank contributor expertise"
)

@app.command()
def analyze(
    path: Annotated[str, typer.Argument(help="Directory to scan for git repos")],
    output: Annotated[str, typer.Option("--output", "-o")] = "report.html",
    max_commits: Annotated[int, typer.Option("--max-commits")] = 0,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Analyze git repositories and generate expertise report."""
    from git_prism.crawler import discover_repos
    from git_prism.analyzer import Analyzer
    from git_prism.report import ReportGenerator

    if verbose:
        typer.echo(f"Scanning {path} for git repositories...")

    repos = discover_repos(path)
    typer.echo(f"Found {len(repos)} repositories")

    analyzer = Analyzer(max_commits=max_commits, verbose=verbose)

    results = []
    for repo in repos:
        typer.echo(f"Analyzing {repo.name}...")
        results.append(analyzer.analyze(repo))

    typer.echo("Generating report...")
    generator = ReportGenerator()
    generator.generate(results, output)

    typer.echo(f"Report saved to: {output}")

@app.command()
def contributors(
    repo_path: str,
    format: str = typer.Option("table", "--format", "-f")
) -> None:
    """List contributors for a single repository."""
    pass

if __name__ == "__main__":
    app()
```

### git_prism/crawler.py

```python
"""Directory crawler for discovering git repositories."""
from pathlib import Path
from typing import List, Iterator
from dataclasses import dataclass

@dataclass
class GitRepo:
    path: Path
    name: str
    is_submodule: bool = False

def discover_repos(root_path: str, ignore_patterns: List[str] = None) -> List[GitRepo]:
    """Recursively discover git repositories in directory tree."""
    root = Path(root_path).resolve()
    repos = []
    ignore_patterns = ignore_patterns or ["node_modules", ".venv", "venv", "__pycache__"]

    for path in root.rglob(".git"):
        # Skip ignored directories
        if any(ignored in path.parts for ignored in ignore_patterns):
            continue

        repo_path = path.parent
        is_submodule = path.is_file()  # Submodules have .git as file

        repos.append(GitRepo(
            path=repo_path,
            name=repo_path.name,
            is_submodule=is_submodule
        ))

    return repos
```

### git_prism/analyzer/commits.py

```python
"""Commit streaming and analysis using pygit2."""
import pygit2
from typing import Iterator, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CommitInfo:
    sha: str
    author_name: str
    author_email: str
    timestamp: datetime
    message: str
    is_merge: bool
    files_changed: int
    insertions: int
    deletions: int

def stream_commits(
    repo_path: str,
    batch_size: int = 5000,
    max_commits: int = 0
) -> Iterator[List[CommitInfo]]:
    """Stream commits from repository in batches."""
    repo = pygit2.Repository(repo_path)
    head = repo[repo.head.target]
    walker = repo.walk(head.id, pygit2.enums.SortMode.TIME)

    batch = []
    count = 0

    for commit in walker:
        if max_commits > 0 and count >= max_commits:
            break

        is_merge = len(commit.parents) > 1

        # Get diff stats
        insertions, deletions, files = 0, 0, 0
        if commit.parents:
            diff = repo.diff(commit.parents[0], commit)
            insertions = diff.stats.insertions
            deletions = diff.stats.deletions
            files = len(list(diff))

        info = CommitInfo(
            sha=str(commit.id),
            author_name=commit.author.name,
            author_email=commit.author.email,
            timestamp=datetime.fromtimestamp(commit.commit_time),
            message=commit.message,
            is_merge=is_merge,
            files_changed=files,
            insertions=insertions,
            deletions=deletions
        )

        batch.append(info)
        count += 1

        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch
```

### git_prism/analyzer/contributors.py

```python
"""Contributor identity resolution with mailmap support."""
from typing import Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Contributor:
    canonical_name: str
    canonical_email: str
    aliases: list

def parse_mailmap(repo_path: str) -> Dict[Tuple[str, str], Tuple[str, str]]:
    """Parse .mailmap for identity mapping."""
    mailmap_path = Path(repo_path) / ".mailmap"
    mapping = {}

    if not mailmap_path.exists():
        return mapping

    with open(mailmap_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse: Canonical Name <canonical@email> [Other Name] <other@email>
            parts = line.split("<")
            canonical_name = parts[0].strip()
            canonical_email = parts[1].split(">")[0].strip()

            if len(parts) > 2:
                other_name = parts[1].split(">")[1].strip() if ">" in parts[1] else canonical_name
                other_email = parts[2].split(">")[0].strip()
                mapping[(other_name, other_email)] = (canonical_name, canonical_email)

    return mapping

def resolve_contributor(
    name: str,
    email: str,
    mailmap: Dict[Tuple[str, str], Tuple[str, str]]
) -> Tuple[str, str]:
    """Resolve contributor to canonical identity."""
    return mailmap.get((name, email), (name, email))
```

## References & Research

### Internal References
- Project structure follows Python packaging best practices
- CLAUDE.md will be created with project conventions

### External References

**Git Libraries:**
- pygit2 documentation: https://www.pygit2.org/
- Dulwich documentation: https://www.dulwich.io/

**CLI Framework:**
- Typer documentation: https://typer.tiangolo.com/

**Visualization:**
- Plotly Python: https://plotly.com/python/
- NetworkX: https://networkx.org/
- Pyvis: https://pyvis.readthedocs.io/

**Code Analysis:**
- tree-sitter: https://tree-sitter.github.io/tree-sitter/
- Radon complexity: https://radon.readthedocs.io/

**File Detection:**
- puremagic: https://github.com/cdgriffith/puremagic

### Key Design Decisions

1. **pygit2 over GitPython**: Performance critical for 100k+ commit repos
2. **Streaming architecture**: Never load full history into memory
3. **Mailmap-first identity**: Standard Git solution for SVN migrations
4. **Plotly over Matplotlib**: Interactive charts for better UX
5. **Standalone HTML**: No server required, portable reports
