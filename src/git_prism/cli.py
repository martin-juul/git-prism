"""Command-line interface for git-prism."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from git_prism import __version__
from git_prism.analyzer import AnalysisResult, Analyzer
from git_prism.analyzer.parallel import ParallelResult, analyze_repos_parallel, resolve_worker_count
from git_prism.report import ReportGenerator

app = typer.Typer(
    name="git-prism",
    help="Analyze git repositories to rank contributor expertise and visualize team knowledge",
    add_completion=False,
)

console = Console()
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Args:
        verbose: Enable DEBUG level logging if True, otherwise WARNING.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )


def version_callback(value: bool) -> None:
    """Print version and exit if --version flag is provided."""
    if value:
        console.print(f"git-prism version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Git Prism: Analyze contributor expertise across git repositories."""
    pass


@app.command()
def analyze(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to scan for git repositories",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output HTML report file path",
            resolve_path=True,
        ),
    ] = Path("report.html"),
    max_commits: Annotated[
        int,
        typer.Option(
            "--max-commits",
            "-m",
            help="Maximum commits to analyze per repo (0 = all)",
        ),
    ] = 0,
    ignore: Annotated[
        list[str] | None,
        typer.Option(
            "--ignore",
            "-i",
            help="Directories to ignore (can be specified multiple times)",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose output"),
    ] = False,
    workers: Annotated[
        str | None,
        typer.Option(
            "--workers",
            "-w",
            help="Number of parallel workers (integer or 'auto' for CPU count - 1)",
        ),
    ] = None,
) -> None:
    """Analyze git repositories and generate expertise report.

    Scans the specified directory for git repositories, analyzes commit
    history to score contributor expertise, and generates an interactive
    HTML report.

    Examples:
        git-prism analyze ~/projects -o report.html
        git-prism analyze . --max-commits 10000
        git-prism analyze ~/work -i node_modules -i .venv
        git-prism analyze ~/projects -w auto
        git-prism analyze ~/projects -w 4
    """
    setup_logging(verbose)

    # If output is a directory, use default filename within it
    if output.is_dir():
        output = output / "report.html"

    from git_prism.crawler import discover_repos

    ignore_patterns = ignore or ["node_modules", ".venv", "venv", "__pycache__", ".git"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        # Discover repositories
        discover_task = progress.add_task(
            "[cyan]Scanning for repositories...",
            total=None,
        )

        repos = discover_repos(str(path), ignore_patterns=ignore_patterns)
        progress.update(discover_task, total=1, completed=1)

        if not repos:
            console.print("[yellow]No git repositories found in[/yellow]", path)
            raise typer.Exit(1)

        console.print(f"[green]Found {len(repos)} repositories[/green]")

        # Resolve worker count
        try:
            resolved_workers = resolve_worker_count(workers)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

        # Track failures for exit code
        failure_count = 0
        results: list[AnalysisResult] = []

        if resolved_workers == 1:
            # Sequential path (existing behavior)
            analyzer = Analyzer(max_commits=max_commits, verbose=verbose)

            for repo in repos:
                analyze_task = progress.add_task(
                    f"[cyan]Analyzing {repo.name}...",
                    total=None,
                )

                try:
                    result = analyzer.analyze(repo)
                    results.append(result)
                    progress.update(analyze_task, total=1, completed=1)
                except Exception as e:
                    console.print(f"[red]Error analyzing {repo.name}: {e}[/red]")
                    progress.update(analyze_task, total=1, completed=1)
                    failure_count += 1
        else:
            # Parallel path
            parallel_task = progress.add_task(
                f"[cyan]Analyzing {len(repos)} repositories with {resolved_workers} workers...",
                total=len(repos),
            )

            try:
                parallel_result = analyze_repos_parallel(
                    repos, max_commits, resolved_workers
                )
                results = parallel_result.successes
                failure_count = len(parallel_result.failures)
                progress.update(parallel_task, completed=len(results))

                # Report failures
                for repo_name, repo_path, error in parallel_result.failures:
                    console.print(f"[red]Error analyzing {repo_name}: {error}[/red]")

            except KeyboardInterrupt:
                console.print("\n[yellow]Analysis interrupted. Partial results discarded.[/yellow]")
                raise typer.Exit(130)

        # Generate report
        report_task = progress.add_task(
            "[cyan]Generating HTML report...",
            total=None,
        )

        generator = ReportGenerator()
        generator.generate(results, output)

        progress.update(report_task, total=1, completed=1)

    console.print(f"\n[green]Report saved to:[/green] {output}")
    console.print(f"[dim]Open in browser:[/dim] file://{output}")

    # Exit with failure count if any repos failed
    if failure_count > 0:
        console.print(
            f"\n[yellow]Completed with {failure_count} error(s)[/yellow]"
        )
        raise typer.Exit(min(125, failure_count))


@app.command()
def contributors(
    repo_path: Annotated[
        Path,
        typer.Argument(
            help="Path to git repository",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: table, json, csv",
        ),
    ] = "table",
    top: Annotated[
        int,
        typer.Option(
            "--top",
            "-t",
            help="Number of top contributors to show (0 = all)",
        ),
    ] = 10,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose output"),
    ] = False,
) -> None:
    """List contributors for a single repository with expertise scores.

    Shows contributor rankings based on weighted analysis of commits,
    lines changed, and recency of contributions.

    Examples:
        git-prism contributors ~/projects/my-repo
        git-prism contributors . --format json
        git-prism contributors . --top 5
    """
    import json

    setup_logging(verbose)

    from git_prism.crawler import GitRepo

    repo = GitRepo(path=repo_path, name=repo_path.name)

    analyzer = Analyzer(verbose=verbose)
    result = analyzer.analyze(repo)

    # Sort by expertise score
    sorted_scores = sorted(result.scores, key=lambda s: s.total_score, reverse=True)

    if top > 0:
        sorted_scores = sorted_scores[:top]

    if format == "json":
        data = [
            {
                "name": score.contributor_name,
                "email": score.contributor_email,
                "total_score": round(score.total_score, 2),
                "commits": score.commit_count,
                "lines_changed": score.lines_changed,
            }
            for score in sorted_scores
        ]
        console.print_json(json.dumps(data, indent=2))

    elif format == "csv":
        console.print("name,email,score,commits,lines_changed")
        for score in sorted_scores:
            console.print(
                f"{score.contributor_name},{score.contributor_email},"
                f"{score.total_score:.2f},{score.commit_count},{score.lines_changed}"
            )

    else:  # table
        table = Table(title=f"Contributors for {repo.name}")
        table.add_column("Rank", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Score", justify="right", style="yellow")
        table.add_column("Commits", justify="right")
        table.add_column("Lines Changed", justify="right")

        for i, score in enumerate(sorted_scores, 1):
            table.add_row(
                str(i),
                score.contributor_name,
                f"{score.total_score:.1f}",
                str(score.commit_count),
                f"{score.lines_changed:,}",
            )

        console.print(table)


@app.command()
def repos(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to scan for git repositories",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    ignore: Annotated[
        list[str] | None,
        typer.Option(
            "--ignore",
            "-i",
            help="Directories to ignore (can be specified multiple times)",
        ),
    ] = None,
) -> None:
    """List all git repositories found in a directory.

    Scans the specified directory recursively and lists all discovered
    git repositories, including submodules.

    Examples:
        git-prism repos ~/projects
        git-prism repos . -i node_modules
    """
    from git_prism.crawler import discover_repos

    ignore_patterns = ignore or ["node_modules", ".venv", "venv", "__pycache__"]

    discovered = discover_repos(str(path), ignore_patterns=ignore_patterns)

    if not discovered:
        console.print("[yellow]No git repositories found[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Repositories in {path}")
    table.add_column("Name", style="green")
    table.add_column("Path", style="dim")
    table.add_column("Type", style="cyan")

    for repo in discovered:
        repo_type = "submodule" if repo.is_submodule else "repository"
        table.add_row(repo.name, str(repo.path), repo_type)

    console.print(table)
    console.print(f"\n[green]Total:[/green] {len(discovered)} repositories")


if __name__ == "__main__":
    app()
