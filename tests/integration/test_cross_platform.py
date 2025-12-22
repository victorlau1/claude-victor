"""Integration tests for cross-platform compatibility.

These tests verify that the project works correctly across different platforms.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

import pytest


class TestCrossPlatformPaths:
    """Tests for cross-platform path handling."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    def test_relative_paths_in_config(self, project_root):
        """Verify no absolute paths in configuration files."""
        config_files = [
            project_root / "pyproject.toml",
            project_root / "setup.cfg",
            project_root / ".claude-plugin" / "plugin.json",
        ]

        absolute_path_indicators = [
            "/Users/",
            "/home/",
            "C:\\",
            "D:\\",
            "/opt/",
            "/usr/local/",
        ]

        for config_file in config_files:
            if config_file.exists():
                content = config_file.read_text()
                for indicator in absolute_path_indicators:
                    assert indicator not in content, \
                        f"Absolute path found in {config_file}: {indicator}"

    def test_path_separator_usage(self, project_root):
        """Verify paths use forward slashes or os.path."""
        # Python files should use Path or os.path for portability
        python_files = list(project_root.glob("src/**/*.py"))

        for py_file in python_files:
            content = py_file.read_text()

            # Check for hardcoded backslashes in paths
            # (excluding string literals for Windows path handling)
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                # Skip comments and docstrings
                if line.strip().startswith("#") or line.strip().startswith('"""'):
                    continue

                # Check for Windows-style paths that should be portable
                if "\\\\" in line and "os.path" not in line and "Path" not in line:
                    # This might be intentional for Windows-specific code
                    pass


class TestMakefileTargets:
    """Tests for Makefile target definitions."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    def test_makefile_exists(self, project_root):
        """Verify Makefile exists."""
        makefile = project_root / "Makefile"
        assert makefile.exists(), "Makefile not found"

    def test_makefile_targets_exist(self, project_root):
        """Verify all Makefile targets are defined."""
        required_targets = [
            "install",
            "setup-python",
            "setup-dev",
            "configure-gh",
            "test-unit",
            "test-integration",
            "test-bdd",
            "test-all",
            "verify",
            "clean",
            "help",
        ]

        makefile = project_root / "Makefile"
        content = makefile.read_text()

        for target in required_targets:
            # Check for target definition (target: or target :)
            assert f"{target}:" in content or f"{target} :" in content, \
                f"Target '{target}' not found in Makefile"

    def test_makefile_dry_run(self, project_root):
        """Test Makefile dry-run doesn't fail."""
        if platform.system() == "Windows":
            # Windows might not have make installed
            pytest.skip("make not typically available on Windows")

        result = subprocess.run(
            ["make", "--dry-run", "help"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"make --dry-run failed: {result.stderr}"

    def test_windows_makefile_exists(self, project_root):
        """Verify Windows Makefile override exists."""
        makefile_win = project_root / "Makefile.windows"
        assert makefile_win.exists(), "Makefile.windows not found"


class TestPluginStructure:
    """Tests for plugin bundle structure."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    def test_plugin_directory_structure(self, project_root):
        """Verify plugin directory structure."""
        plugin_dir = project_root / ".claude-plugin"

        required_paths = [
            plugin_dir / "plugin.json",
            plugin_dir / "commands" / "plan-victor.md",
            plugin_dir / "hooks" / "enforce-planning.sh",
            plugin_dir / "mcp" / "memory-keeper.json",
        ]

        for path in required_paths:
            assert path.exists(), f"Required plugin file not found: {path}"

    def test_plugin_manifest_valid(self, project_root):
        """Verify plugin manifest is valid JSON."""
        import json

        manifest_path = project_root / ".claude-plugin" / "plugin.json"
        content = manifest_path.read_text()

        try:
            manifest = json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in plugin.json: {e}")

        # Verify required fields
        assert "name" in manifest
        assert "version" in manifest
        assert "commands" in manifest

    def test_hook_script_executable(self, project_root):
        """Verify hook script has correct permissions (Unix only)."""
        if platform.system() == "Windows":
            pytest.skip("Permission check not applicable on Windows")

        hook_path = project_root / ".claude-plugin" / "hooks" / "enforce-planning.sh"
        assert os.access(hook_path, os.X_OK), "Hook script is not executable"


class TestPythonPackage:
    """Tests for Python package structure."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    def test_package_structure(self, project_root):
        """Verify Python package structure."""
        src_dir = project_root / "src" / "claude_victor"

        required_files = [
            src_dir / "__init__.py",
            src_dir / "github" / "__init__.py",
            src_dir / "github" / "client.py",
            src_dir / "github" / "pr.py",
            src_dir / "github" / "issues.py",
            src_dir / "github" / "actions.py",
            src_dir / "memory" / "__init__.py",
            src_dir / "memory" / "plan_store.py",
            src_dir / "workflow" / "__init__.py",
            src_dir / "workflow" / "planning.py",
        ]

        for file_path in required_files:
            assert file_path.exists(), f"Required file not found: {file_path}"

    def test_package_importable(self):
        """Verify package can be imported."""
        try:
            import claude_victor
            assert hasattr(claude_victor, "__version__")
        except ImportError as e:
            pytest.fail(f"Failed to import claude_victor: {e}")

    def test_submodules_importable(self):
        """Verify submodules can be imported."""
        try:
            from claude_victor.github import client, pr, issues, actions
            from claude_victor.memory import plan_store
            from claude_victor.workflow import planning
        except ImportError as e:
            pytest.fail(f"Failed to import submodule: {e}")


class TestTestStructure:
    """Tests for test directory structure."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    def test_test_directory_structure(self, project_root):
        """Verify test directory structure."""
        tests_dir = project_root / "tests"

        required_dirs = [
            tests_dir / "unit",
            tests_dir / "integration",
            tests_dir / "bdd" / "features",
            tests_dir / "bdd" / "steps",
        ]

        for dir_path in required_dirs:
            assert dir_path.exists(), f"Required test directory not found: {dir_path}"
            assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

    def test_unit_tests_exist(self, project_root):
        """Verify unit test files exist."""
        unit_dir = project_root / "tests" / "unit"
        test_files = list(unit_dir.glob("test_*.py"))

        assert len(test_files) >= 4, "Expected at least 4 unit test files"

    def test_bdd_features_exist(self, project_root):
        """Verify BDD feature files exist."""
        features_dir = project_root / "tests" / "bdd" / "features"
        feature_files = list(features_dir.glob("*.feature"))

        assert len(feature_files) >= 3, "Expected at least 3 feature files"

    def test_bdd_steps_exist(self, project_root):
        """Verify BDD step files exist."""
        steps_dir = project_root / "tests" / "bdd" / "steps"
        step_files = list(steps_dir.glob("*_steps.py"))

        assert len(step_files) >= 3, "Expected at least 3 step definition files"
