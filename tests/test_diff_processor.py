"""Tests for diff processor."""

import pytest

from src.analysis.diff_processor import DiffProcessor
from src.github_client.models import FileChange


class TestDiffProcessor:
    """Test DiffProcessor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DiffProcessor(max_diff_size=100)

    def test_should_skip_binary_files(self):
        """Test that binary files are skipped."""
        assert self.processor.should_skip_file("image.png") is True
        assert self.processor.should_skip_file("document.pdf") is True
        assert self.processor.should_skip_file("src/main.py") is False

    def test_should_skip_generated_files(self):
        """Test that generated files are skipped."""
        assert self.processor.should_skip_file("dist/bundle.js") is True
        assert self.processor.should_skip_file("build/output.js") is True
        assert self.processor.should_skip_file("node_modules/package/index.js") is True

    def test_should_skip_minified_files(self):
        """Test that minified files are skipped."""
        assert self.processor.should_skip_file("script.min.js") is True
        assert self.processor.should_skip_file("style.min.css") is True

    def test_clean_diff_truncates_large_diffs(self):
        """Test that large diffs are truncated."""
        large_patch = "\n".join([f"+line {i}" for i in range(200)])
        cleaned = self.processor.clean_diff(large_patch)
        assert "truncated" in cleaned.lower()
        assert len(cleaned.split('\n')) <= self.processor.max_diff_size + 2

    def test_clean_diff_preserves_small_diffs(self):
        """Test that small diffs are preserved."""
        small_patch = "+line 1\n+line 2\n-line 3"
        cleaned = self.processor.clean_diff(small_patch)
        assert cleaned == small_patch

    def test_calculate_diff_stats(self):
        """Test diff statistics calculation."""
        patch = "+def new_function():\n+    pass\n-def old_function():\n-    pass"
        stats = self.processor.calculate_diff_stats(patch)

        assert stats.added_lines == 2
        assert stats.deleted_lines == 2
        assert stats.total_lines > 0

    def test_process_files_filters_binary(self):
        """Test that process_files filters binary files."""
        files = [
            FileChange(filename="src/main.py", status="modified", additions=10, deletions=5, changes=15),
            FileChange(filename="image.png", status="added", additions=0, deletions=0, changes=0),
            FileChange(filename="lib/util.js", status="modified", additions=8, deletions=3, changes=11),
        ]

        processed = self.processor.process_files(files)
        assert len(processed) == 2
        assert all(f.filename != "image.png" for f in processed)

    def test_prioritize_files_security_first(self):
        """Test that security-related files are prioritized."""
        files = [
            FileChange(filename="README.md", status="modified", additions=5, deletions=2, changes=7),
            FileChange(filename="src/auth/login.py", status="modified", additions=20, deletions=10, changes=30),
            FileChange(filename="tests/test_main.py", status="modified", additions=15, deletions=5, changes=20),
        ]

        prioritized = self.processor.prioritize_files(files)
        # Auth file should be first (high priority)
        assert "auth" in prioritized[0].filename
