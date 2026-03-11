"""Unit tests for the classification module."""

from __future__ import annotations

from pathlib import Path

import pytest

from git_prism.analyzer.classification import (
    FileType,
    classify_file,
    detect_frameworks,
)


class TestClassifyFile:
    """Tests for classify_file function."""

    def test_classify_python_file(self) -> None:
        """Test classifying a Python file."""
        result = classify_file("src/main.py")

        assert result.language == "Python"
        assert result.file_type in {FileType.BACKEND, FileType.UNKNOWN}
        assert not result.is_binary

    def test_classify_javascript_file(self) -> None:
        """Test classifying a JavaScript file."""
        result = classify_file("components/Button.jsx")

        assert result.language == "JavaScript"
        assert result.file_type == FileType.FRONTEND

    def test_classify_typescript_file(self) -> None:
        """Test classifying a TypeScript file."""
        result = classify_file("src/utils.ts")

        assert result.language == "TypeScript"

    def test_classify_test_file(self) -> None:
        """Test classifying a test file."""
        result = classify_file("tests/test_main.py")

        assert result.file_type == FileType.TEST

    def test_classify_test_file_with_spec(self) -> None:
        """Test classifying a spec test file."""
        result = classify_file("src/utils.spec.ts")

        assert result.file_type == FileType.TEST

    def test_classify_markdown_file(self) -> None:
        """Test classifying a markdown file."""
        result = classify_file("README.md")

        assert result.language == "Markdown"
        assert result.file_type == FileType.DOCUMENTATION

    def test_classify_json_config(self) -> None:
        """Test classifying a JSON config file."""
        result = classify_file("config/settings.json")

        assert result.language == "JSON"
        assert result.file_type == FileType.CONFIG

    def test_classify_sql_file(self) -> None:
        """Test classifying a SQL file."""
        result = classify_file("migrations/001_create_users.sql")

        assert result.language == "SQL"
        assert result.file_type in {FileType.BACKEND, FileType.DATA}

    def test_classify_generated_lock_file(self) -> None:
        """Test that lock files are marked as generated."""
        result = classify_file("package-lock.json")

        assert result.is_generated

    def test_classify_minified_file(self) -> None:
        """Test that minified files are marked as generated."""
        result = classify_file("dist/bundle.min.js")

        assert result.is_generated

    def test_classify_binary_image(self) -> None:
        """Test classifying a binary image file."""
        result = classify_file("images/logo.png")

        assert result.is_binary

    def test_classify_unknown_extension(self) -> None:
        """Test classifying a file with unknown extension."""
        result = classify_file("data/custom.xyz")

        assert result.language == "unknown"


class TestDetectFrameworks:
    """Tests for detect_frameworks function."""

    def test_detect_nodejs_package_json(self, temp_dir: Path) -> None:
        """Test detecting Node.js package.json (no language name as framework)."""
        (temp_dir / "package.json").write_text('{"name": "test"}')

        frameworks = detect_frameworks(temp_dir)

        # Note: Node.js is a runtime, not a framework
        # Empty package.json should not return any frameworks
        assert frameworks == []

    def test_detect_python_requirements(self, temp_dir: Path) -> None:
        """Test detecting Python framework from requirements.txt."""
        (temp_dir / "requirements.txt").write_text("flask==2.0.0")

        frameworks = detect_frameworks(temp_dir)

        # Flask is an actual framework, Python is a language
        assert "Flask" in frameworks
        assert "Python" not in frameworks  # Language, not framework

    def test_detect_rust_cargo(self, temp_dir: Path) -> None:
        """Test detecting Rust Cargo.toml (no language name as framework)."""
        (temp_dir / "Cargo.toml").write_text('[package]\nname = "test"')

        frameworks = detect_frameworks(temp_dir)

        # Note: Rust is a language, not a framework
        # Cargo.toml alone doesn't indicate a framework
        assert frameworks == []

    def test_detect_react_framework(self, temp_dir: Path) -> None:
        """Test detecting React framework from package.json."""
        import json

        package_json = {"dependencies": {"react": "^18.0.0"}}
        (temp_dir / "package.json").write_text(json.dumps(package_json))

        frameworks = detect_frameworks(temp_dir)

        assert "React" in frameworks

    def test_detect_django_framework(self, temp_dir: Path) -> None:
        """Test detecting Django framework from requirements.txt."""
        (temp_dir / "requirements.txt").write_text("django>=4.0")

        frameworks = detect_frameworks(temp_dir)

        assert "Django" in frameworks

    def test_detect_no_frameworks(self, temp_dir: Path) -> None:
        """Test with no framework indicator files."""
        frameworks = detect_frameworks(temp_dir)

        assert frameworks == []


class TestFileType:
    """Tests for FileType enum."""

    def test_file_type_values(self) -> None:
        """Test FileType enum values."""
        assert FileType.FRONTEND.value == "frontend"
        assert FileType.BACKEND.value == "backend"
        assert FileType.TEST.value == "test"
        assert FileType.CONFIG.value == "config"
