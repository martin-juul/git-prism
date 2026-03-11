"""Tests for network visualization functions."""

from __future__ import annotations

import pytest


class TestExtractPyvisContent:
    """Tests for _extract_pyvis_content function."""

    @pytest.fixture
    def extract_fn(self):
        """Import the function under test."""
        from git_prism.visualizations.networks import _extract_pyvis_content

        return _extract_pyvis_content

    def test_extracts_body_from_full_document(self, extract_fn) -> None:
        """Test extraction from typical Pyvis full HTML output."""
        html = (
            "<!DOCTYPE html><html><head><style>.node { color: red; }</style></head>"
            "<body><div id='mynetwork'>network content</div></body></html>"
        )
        result = extract_fn(html)
        assert "<div id='mynetwork'>network content</div>" in result
        assert "<!DOCTYPE" not in result
        assert "<html>" not in result
        assert "<head>" not in result
        assert "</body>" not in result

    def test_removes_bootstrap_css(self, extract_fn) -> None:
        """Test that Bootstrap CSS links are removed."""
        html = (
            "<!DOCTYPE html><html><head>"
            "<link href='https://cdn.example.com/bootstrap.min.css' rel='stylesheet'>"
            "</head><body><div>network</div></body></html>"
        )
        result = extract_fn(html)
        assert "bootstrap" not in result.lower()
        assert "<div>network</div>" in result

    def test_removes_bootstrap_js(self, extract_fn) -> None:
        """Test that Bootstrap JS scripts are removed."""
        html = (
            "<!DOCTYPE html><html><head></head><body>"
            "<div>network</div>"
            "<script src='https://cdn.example.com/bootstrap.min.js'></script>"
            "</body></html>"
        )
        result = extract_fn(html)
        assert "bootstrap" not in result.lower()
        assert "<div>network</div>" in result

    def test_empty_string_returns_empty(self, extract_fn) -> None:
        """Test handling of empty string."""
        assert extract_fn("") == ""

    def test_none_returns_empty(self, extract_fn) -> None:
        """Test handling of None input."""
        assert extract_fn(None) == ""

    def test_whitespace_only_returns_empty(self, extract_fn) -> None:
        """Test handling of whitespace-only input."""
        assert extract_fn("   \n\t  ") == ""

    def test_no_body_tags_fallback(self, extract_fn) -> None:
        """Test fallback when no body tags are present."""
        html = "<div>orphan content without body tags</div>"
        result = extract_fn(html)
        assert result == html

    def test_body_with_attributes(self, extract_fn) -> None:
        """Test extraction when body tag has attributes."""
        html = (
            "<!DOCTYPE html><html><head></head>"
            "<body class='dark-theme' data-test='value'><div>content</div></body></html>"
        )
        result = extract_fn(html)
        assert "<div>content</div>" in result
        assert "<body" not in result

    def test_multiline_body_content(self, extract_fn) -> None:
        """Test extraction with multiline content."""
        html = """<!DOCTYPE html>
<html>
<head><style>body { margin: 0; }</style></head>
<body>
    <div id="mynetwork">
        <canvas></canvas>
    </div>
    <script>
        var data = { nodes: [], edges: [] };
    </script>
</body>
</html>"""
        result = extract_fn(html)
        assert '<div id="mynetwork">' in result
        assert "<canvas></canvas>" in result
        assert "<html>" not in result

    def test_case_insensitive_body_extraction(self, extract_fn) -> None:
        """Test that body extraction is case insensitive."""
        html = "<HTML><BODY><div>content</div></BODY></HTML>"
        result = extract_fn(html)
        assert "<div>content</div>" in result
