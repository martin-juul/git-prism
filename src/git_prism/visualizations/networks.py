"""NetworkX and Pyvis contributor relationship graphs."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from git_prism.analyzer import AnalysisResult


def _wrap_in_iframe(html: str | None, height: str = "100%") -> str:
    """Wrap Pyvis HTML in an iframe to isolate it from the main document.

    Pyvis generate_html() returns a full HTML document. Embedding it directly
    causes nested HTML structure issues. Using an iframe with srcdoc properly
    isolates the Pyvis content.

    Also removes Bootstrap CSS/JS to prevent theme conflicts.

    Args:
        html: Full HTML document from Pyvis generate_html().
        height: Iframe height (default 100%).

    Returns:
        Iframe element with Pyvis content, or empty string on failure.
    """
    if not html or not html.strip():
        return ""

    # Remove Bootstrap CSS link
    html = re.sub(
        r'<link[^>]*bootstrap[^>]*\.css[^>]*>',
        "",
        html,
        flags=re.IGNORECASE,
    )
    # Remove Bootstrap JS script
    html = re.sub(
        r'<script[^>]*bootstrap[^>]*>\s*</script>',
        "",
        html,
        flags=re.IGNORECASE,
    )

    # Escape quotes for srcdoc attribute
    escaped = html.replace('"', "&quot;")

    return f'<iframe srcdoc="{escaped}" style="width: 100%; height: {height}; border: none;"></iframe>'


def create_collaboration_network(
    results: list[AnalysisResult],
    min_shared_repos: int = 1,
) -> str:
    """Create a network graph showing contributor collaborations.

    Contributors are connected if they've worked on the same repositories.

    Args:
        results: List of AnalysisResult objects.
        min_shared_repos: Minimum shared repos to create a connection.

    Returns:
        HTML string with embedded Pyvis network.
    """
    import networkx as nx
    from pyvis.network import Network

    # Build contributor → repos mapping
    contributor_repos: dict[str, set[str]] = {}

    for result in results:
        for score in result.scores:
            name = score.contributor_name
            if name not in contributor_repos:
                contributor_repos[name] = set()
            contributor_repos[name].add(result.repo_name)

    # Build collaboration edges
    G = nx.Graph()

    contributors = list(contributor_repos.keys())

    for i, c1 in enumerate(contributors):
        for c2 in contributors[i + 1 :]:
            shared = contributor_repos[c1] & contributor_repos[c2]
            if len(shared) >= min_shared_repos:
                G.add_edge(c1, c2, weight=len(shared), repos=", ".join(sorted(shared)))

    # Add isolated nodes (contributors with no shared repos)
    for contributor in contributors:
        if contributor not in G.nodes():
            G.add_node(contributor)

    # Calculate node sizes based on number of repos
    node_sizes = {c: len(repos) * 5 + 10 for c, repos in contributor_repos.items()}

    # Create Pyvis network
    net = Network(height="600px", width="100%", bgcolor="#1f2937", font_color="white", cdn_resources="in_line")
    net.from_nx(G)

    # Style nodes
    for node in net.nodes:
        node["size"] = node_sizes.get(node["id"], 15)
        node["title"] = f"{node['id']}: {len(contributor_repos.get(node['id'], set()))} repos"
        node["color"] = "#6366f1"

    # Style edges
    for edge in net.edges:
        edge["title"] = f"Shared: {edge.get('repos', '')}"
        edge["color"] = "#4f46e5"

    net.set_options(
        """
    {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -3000,
          "centralGravity": 0.3,
          "springLength": 100
        }
      }
    }
    """
    )

    return _wrap_in_iframe(net.generate_html())


def create_contributor_graph(
    result: AnalysisResult,
    output_path: Path | None = None,
) -> str:
    """Create a single-repo contributor graph.

    Shows contributors sized by their expertise score.

    Args:
        result: Single AnalysisResult for one repository.
        output_path: Optional path to save standalone HTML.

    Returns:
        HTML string with embedded Pyvis network.
    """
    import networkx as nx
    from pyvis.network import Network

    G = nx.Graph()

    # Add repo as central node
    G.add_node(result.repo_name, group="repo", size=30)

    # Add contributors
    for score in result.scores:
        G.add_node(
            score.contributor_name,
            group="contributor",
            size=min(score.total_score / 2 + 5, 40),
            title=f"{score.contributor_name}<br>Score: {score.total_score:.1f}<br>Commits: {score.commit_count}",
        )
        G.add_edge(result.repo_name, score.contributor_name, weight=score.total_score)

    net = Network(height="500px", width="100%", bgcolor="#1f2937", font_color="white", cdn_resources="in_line")
    net.from_nx(G)

    # Style nodes
    for node in net.nodes:
        if node["group"] == "repo":
            node["color"] = "#10b981"
            node["shape"] = "diamond"
        else:
            node["color"] = "#6366f1"

    net.set_options(
        """
    {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -2000,
          "centralGravity": 0.5,
          "springLength": 150
        }
      }
    }
    """
    )

    html = _wrap_in_iframe(net.generate_html())

    if output_path:
        output_path.write_text(html)

    return html


def create_expertise_network(
    results: list[AnalysisResult],
    top_n: int = 15,
) -> str:
    """Create a bipartite graph of contributors and repositories.

    Shows the expertise relationship between contributors and repos.

    Args:
        results: List of AnalysisResult objects.
        top_n: Top contributors per repo to include.

    Returns:
        HTML string with embedded Pyvis network.
    """
    import networkx as nx
    from pyvis.network import Network

    G = nx.Graph()

    # Track all contributors for node sizing
    contributor_scores: dict[str, float] = {}

    # Add repo and contributor nodes
    for result in results:
        # Add repo node
        G.add_node(result.repo_name, group="repo", size=25, color="#10b981", shape="diamond")

        # Add top contributors for this repo
        for score in result.scores[:top_n]:
            name = score.contributor_name

            # Track max score for sizing
            if name not in contributor_scores or score.total_score > contributor_scores[name]:
                contributor_scores[name] = score.total_score

            G.add_node(
                name,
                group="contributor",
                color="#6366f1",
            )

            # Edge weight is expertise score
            G.add_edge(
                result.repo_name,
                name,
                weight=score.total_score,
                title=f"Score: {score.total_score:.1f}",
            )

    # Update contributor sizes based on max score
    for node in G.nodes:
        if G.nodes[node].get("group") == "contributor":
            G.nodes[node]["size"] = min(contributor_scores.get(node, 10) / 2 + 10, 35)

    net = Network(height="700px", width="100%", bgcolor="#1f2937", font_color="white", cdn_resources="in_line")
    net.from_nx(G)

    net.set_options(
        """
    {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -5000,
          "centralGravity": 0.3,
          "springLength": 120
        }
      }
    }
    """
    )

    return _wrap_in_iframe(net.generate_html())
