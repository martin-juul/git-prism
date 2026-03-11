"""Jinja2 HTML report generation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from git_prism.analyzer import AnalysisResult


TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates"


def format_number(value: int | float) -> str:
    """Format number with thousands separator.

    Args:
        value: Number to format.

    Returns:
        Formatted string with commas as thousands separator.
    """
    return f"{value:,}"


class ReportGenerator:
    """Generates HTML reports from analysis results."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        """Initialize the report generator.

        Args:
            templates_dir: Directory containing Jinja2 templates.
        """
        from jinja2 import Environment, FileSystemLoader

        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True,
        )
        # Register custom filters
        self.env.filters["number_format"] = format_number

    def generate(
        self,
        results: list[AnalysisResult],
        output_path: Path | str,
        title: str = "Git Prism Report",
    ) -> None:
        """Generate an HTML report from analysis results.

        Args:
            results: List of AnalysisResult objects.
            output_path: Path to write the HTML report.
            title: Title for the report.
        """
        from git_prism.analyzer.scoring import calculate_knowledge_distribution
        from git_prism.visualizations.charts import (
            create_code_rot_chart,
            create_expertise_heatmap,
            create_filetype_chart,
            create_knowledge_gap_chart,
            create_language_distribution_chart,
            create_timeline_chart,
        )
        from git_prism.visualizations.networks import (
            create_collaboration_network,
            create_expertise_network,
        )

        output = Path(output_path) if isinstance(output_path, str) else output_path

        # Generate visualizations
        heatmap_chart = create_expertise_heatmap(results)
        language_chart = create_language_distribution_chart(results)
        filetype_chart = create_filetype_chart(results)
        knowledge_gap_chart = create_knowledge_gap_chart(results)
        code_rot_chart = create_code_rot_chart(results)
        timeline_chart = create_timeline_chart(results)
        collaboration_graph = create_collaboration_network(results)
        expertise_graph = create_expertise_network(results)

        # Calculate summary statistics
        total_contributors = len({s.contributor_email for r in results for s in r.scores})
        total_commits = sum(sum(s.commit_count for s in r.scores) for r in results)
        total_lines = sum(sum(s.lines_changed for s in r.scores) for r in results)

        # Knowledge distribution per repo
        knowledge_stats = {}
        for result in results:
            knowledge_stats[result.repo_name] = calculate_knowledge_distribution(result.scores)

        # Sort repos by total activity
        sorted_results = sorted(
            results,
            key=lambda r: sum(s.total_score for s in r.scores),
            reverse=True,
        )

        # Render template
        template = self.env.get_template("report.html")
        html = template.render(
            title=title,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            results=sorted_results,
            total_repos=len(results),
            total_contributors=total_contributors,
            total_commits=total_commits,
            total_lines=total_lines,
            knowledge_stats=knowledge_stats,
            heatmap_chart=heatmap_chart,
            language_chart=language_chart,
            filetype_chart=filetype_chart,
            knowledge_gap_chart=knowledge_gap_chart,
            code_rot_chart=code_rot_chart,
            timeline_chart=timeline_chart,
            collaboration_graph=collaboration_graph,
            expertise_graph=expertise_graph,
        )

        # Write output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html)

    def generate_single_repo(
        self,
        result: AnalysisResult,
        output_path: Path | str,
    ) -> None:
        """Generate a detailed report for a single repository.

        Args:
            result: AnalysisResult for one repository.
            output_path: Path to write the HTML report.
        """
        from git_prism.visualizations.charts import (
            create_filetype_chart,
            create_score_distribution_chart,
        )
        from git_prism.visualizations.networks import create_contributor_graph

        output = Path(output_path) if isinstance(output_path, str) else output_path

        # Generate visualizations
        score_chart = create_score_distribution_chart(result.scores)
        contributor_graph = create_contributor_graph(result)

        # Generate classification chart for single repo
        filetype_chart = create_filetype_chart([result]) if result.classification else ""

        # Render template
        template = self.env.get_template("repo_detail.html")
        html = template.render(
            repo_name=result.repo_name,
            repo_path=result.repo_path,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            scores=result.scores,
            contributors=result.contributors,
            classification=result.classification,
            score_chart=score_chart,
            contributor_graph=contributor_graph,
            filetype_chart=filetype_chart,
        )

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html)
