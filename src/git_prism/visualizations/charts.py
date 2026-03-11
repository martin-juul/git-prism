"""Plotly chart generation for git-prism reports."""

from __future__ import annotations

from typing import TYPE_CHECKING

from git_prism.visualizations.theme import (
    ACCENT_DANGER,
    ACCENT_PRIMARY,
    ACCENT_SECONDARY,
    ACCENT_WARNING,
    CHART_PALETTE,
    GRID_COLOR,
    PLOTLY_DARK_LAYOUT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

if TYPE_CHECKING:
    from git_prism.analyzer import AnalysisResult, ExpertiseScore


def _apply_dark_theme(fig, **extra_layout) -> None:
    """Apply dark theme to a Plotly figure."""
    layout = {
        **PLOTLY_DARK_LAYOUT,
        **extra_layout,
    }
    fig.update_layout(**layout)


def create_expertise_heatmap(
    results: list[AnalysisResult],
    top_n: int = 20,
) -> str:
    """Create a contributor→repo expertise heatmap."""
    import plotly.express as px

    contributor_scores: dict[str, dict[str, float]] = {}
    repo_names: list[str] = []

    for result in results:
        repo_names.append(result.repo_name)
        for score in result.scores[:top_n]:
            name = score.contributor_name
            if name not in contributor_scores:
                contributor_scores[name] = {}
            contributor_scores[name][result.repo_name] = score.total_score

    contributors = list(contributor_scores.keys())[:top_n]
    data = [
        [contributor_scores[c].get(repo, 0) for repo in repo_names]
        for c in contributors
    ]

    if not data:
        return "<p>No data available for heatmap</p>"

    fig = px.imshow(
        data,
        x=repo_names,
        y=contributors,
        labels={"x": "Repository", "y": "Contributor", "color": "Score"},
        title="Contributor Expertise by Repository",
        color_continuous_scale="Plasma",
        aspect="auto",
    )

    _apply_dark_theme(
        fig,
        height=max(400, len(contributors) * 25),
        xaxis_tickangle=-45,
    )

    return fig.to_html(include_plotlyjs=False, full_html=False)


def create_knowledge_gap_chart(
    results: list[AnalysisResult],
    threshold: float = 5.0,
) -> str:
    """Create a chart showing knowledge gaps."""
    import plotly.graph_objects as go

    repo_names = []
    knowledge_holders = []
    total_contributors = []

    for result in results:
        repo_names.append(result.repo_name)
        holders = sum(1 for s in result.scores if s.total_score >= threshold)
        knowledge_holders.append(holders)
        total_contributors.append(len(result.scores))

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Knowledge Holders", x=repo_names, y=knowledge_holders, marker_color=ACCENT_SECONDARY))
    fig.add_trace(go.Bar(name="Total Contributors", x=repo_names, y=total_contributors, marker_color=ACCENT_PRIMARY))

    _apply_dark_theme(
        fig,
        title="Knowledge Distribution by Repository",
        barmode="group",
        xaxis_tickangle=-45,
        height=500,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    return fig.to_html(include_plotlyjs=False, full_html=False)


def create_code_rot_chart(
    results: list[AnalysisResult],
    stale_days: int = 365,
) -> str:
    """Create a chart showing code rot risk."""
    from datetime import datetime, timedelta

    import plotly.graph_objects as go

    stale_threshold = datetime.now() - timedelta(days=stale_days)

    repo_names = []
    active_contributors = []
    stale_contributors = []
    stale_pct = []

    for result in results:
        repo_names.append(result.repo_name)
        active = sum(1 for c in result.contributors if c.last_commit and c.last_commit > stale_threshold)
        stale = len(result.contributors) - active
        active_contributors.append(active)
        stale_contributors.append(stale)
        total = active + stale
        stale_pct.append((stale / total * 100) if total > 0 else 0)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Active", x=repo_names, y=active_contributors, marker_color=ACCENT_SECONDARY))
    fig.add_trace(go.Bar(name="Stale", x=repo_names, y=stale_contributors, marker_color=ACCENT_DANGER))
    fig.add_trace(
        go.Scatter(
            name="Stale %",
            x=repo_names,
            y=stale_pct,
            mode="lines+markers",
            marker={"color": ACCENT_WARNING, "size": 8},
            line={"color": ACCENT_WARNING},
            yaxis="y2",
        )
    )

    _apply_dark_theme(
        fig,
        title="Code Rot: Active vs Stale Contributors",
        barmode="stack",
        xaxis_tickangle=-45,
        height=500,
        yaxis={"title": "Contributors"},
        yaxis2={"title": "Stale %", "overlaying": "y", "side": "right", "range": [0, 100]},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    return fig.to_html(include_plotlyjs=False, full_html=False)


def create_timeline_chart(
    results: list[AnalysisResult],
    months: int = 12,
) -> str:
    """Create a timeline chart showing contribution activity."""
    from collections import defaultdict
    from datetime import datetime, timedelta

    import plotly.graph_objects as go

    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)

    activity_by_repo: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for result in results:
        for contributor in result.contributors:
            if contributor.last_commit and start_date <= contributor.last_commit <= end_date:
                month_key = contributor.last_commit.strftime("%Y-%m")
                activity_by_repo[result.repo_name][month_key] += contributor.commit_count

    months_list = []
    current = start_date
    while current <= end_date:
        months_list.append(current.strftime("%Y-%m"))
        current = current + timedelta(days=30)

    fig = go.Figure()

    for i, (repo, activity) in enumerate(activity_by_repo.items()):
        values = [activity.get(m, 0) for m in months_list]
        color = CHART_PALETTE[i % len(CHART_PALETTE)]
        fig.add_trace(
            go.Scatter(
                name=repo,
                x=months_list,
                y=values,
                mode="lines+markers",
                marker={"color": color},
                line={"color": color},
                stackgroup="one",
            )
        )

    _apply_dark_theme(
        fig,
        title="Contribution Activity Timeline",
        xaxis_title="Month",
        yaxis_title="Commits",
        height=400,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    return fig.to_html(include_plotlyjs=False, full_html=False)


def create_score_distribution_chart(scores: list[ExpertiseScore]) -> str:
    """Create a histogram showing distribution of expertise scores."""
    import plotly.express as px

    if not scores:
        return "<p>No score data available</p>"

    values = [s.total_score for s in scores]
    names = [s.contributor_name for s in scores]

    fig = px.bar(
        x=names,
        y=values,
        labels={"x": "Contributor", "y": "Score"},
        title="Contributor Expertise Scores",
        color=values,
        color_continuous_scale="Plasma",
    )

    _apply_dark_theme(fig, xaxis_tickangle=-45, height=400, showlegend=False)

    return fig.to_html(include_plotlyjs=False, full_html=False)


def create_language_distribution_chart(
    results: list[AnalysisResult],
) -> str:
    """Create a horizontal bar chart showing language distribution.

    Args:
        results: List of AnalysisResult objects with classification data.

    Returns:
        HTML string containing Plotly chart.
    """
    from collections import Counter

    import plotly.graph_objects as go

    # Aggregate languages across all repos
    all_languages: Counter[str] = Counter()
    for result in results:
        if result.classification:
            all_languages.update(result.classification.languages)

    if not all_languages:
        return "<p>No languages detected</p>"

    # Get top 10 languages
    top_languages = dict(all_languages.most_common(10))

    fig = go.Figure(
        go.Bar(
            x=list(top_languages.values()),
            y=list(top_languages.keys()),
            orientation="h",
            marker_color=ACCENT_PRIMARY,
        )
    )

    _apply_dark_theme(
        fig,
        title="Language Distribution",
        xaxis_title="Files",
        yaxis_title="",
        height=400,
        margin=dict(l=120, r=20, t=40, b=40),
        autosize=True,
    )

    # Make responsive
    fig.update_layout(autosize=True)

    return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})


def create_filetype_chart(
    results: list[AnalysisResult],
) -> str:
    """Create a stacked horizontal bar showing file type distribution per repo.

    Args:
        results: List of AnalysisResult objects with classification data.

    Returns:
        HTML string containing Plotly chart.
    """
    from git_prism.analyzer.classification import FileType

    import plotly.graph_objects as go

    # Collect file type data per repo
    repo_names = []
    frontend_counts = []
    backend_counts = []
    data_counts = []
    config_counts = []
    test_counts = []
    doc_counts = []

    file_type_order = [
        (FileType.FRONTEND, frontend_counts),
        (FileType.BACKEND, backend_counts),
        (FileType.DATA, data_counts),
        (FileType.CONFIG, config_counts),
        (FileType.TEST, test_counts),
        (FileType.DOCUMENTATION, doc_counts),
    ]

    for result in results:
        if not result.classification:
            continue

        repo_names.append(result.repo_name)
        ft = result.classification.file_types

        for file_type, counts_list in file_type_order:
            counts_list.append(ft.get(file_type, 0))

    if not repo_names:
        return "<p>No file type data available</p>"

    fig = go.Figure()

    colors = [
        ACCENT_PRIMARY,  # Frontend - Indigo
        ACCENT_SECONDARY,  # Backend - Green
        ACCENT_WARNING,  # Data - Amber
        "#a78bfa",  # Config - Purple
        ACCENT_DANGER,  # Test - Red
        "#2dd4bf",  # Docs - Teal
    ]

    labels = ["Frontend", "Backend", "Data", "Config", "Test", "Docs"]
    counts_lists = [frontend_counts, backend_counts, data_counts, config_counts, test_counts, doc_counts]

    for i, (label, counts, color) in enumerate(zip(labels, counts_lists, colors)):
        fig.add_trace(
            go.Bar(
                name=label,
                y=repo_names,
                x=counts,
                orientation="h",
                marker_color=color,
            )
        )

    _apply_dark_theme(
        fig,
        title="File Type Distribution",
        xaxis_title="Files",
        yaxis_title="",
        barmode="stack",
        height=max(300, len(repo_names) * 40),
        margin=dict(l=150, r=20, t=40, b=40),
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        autosize=True,
    )

    # Make responsive
    fig.update_layout(autosize=True)

    return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})
