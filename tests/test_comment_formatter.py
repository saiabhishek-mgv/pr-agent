"""Tests for comment formatter."""

import pytest

from src.config.settings import Settings
from src.formatters.comment_formatter import CommentFormatter
from src.github_client.models import (
    AnalysisResult,
    FileChange,
    RiskCategory,
    RiskItem,
    RiskLevel,
)


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        github_token="test_token", anthropic_api_key="test_key", repository="test/repo", pr_number=1
    )


@pytest.fixture
def formatter(settings):
    """Create comment formatter."""
    return CommentFormatter(settings)


class TestCommentFormatter:
    """Test CommentFormatter functionality."""

    def test_format_basic_comment(self, formatter):
        """Test basic comment formatting."""
        result = AnalysisResult(
            summary="This is a test PR",
            key_files=[
                FileChange(
                    filename="test.py", status="modified", additions=10, deletions=5, changes=15
                )
            ],
            risks=[],
            ai_enabled=False,
        )

        comment = formatter.format_comment(result, total_files=1)

        assert "🤖 PR Analysis" in comment
        assert "This is a test PR" in comment
        assert "test.py" in comment

    def test_format_with_risks(self, formatter):
        """Test comment with risks."""
        result = AnalysisResult(
            summary="Test PR with risks",
            key_files=[],
            risks=[
                RiskItem(
                    category=RiskCategory.SECURITY,
                    level=RiskLevel.HIGH,
                    title="SQL Injection detected",
                    description="Unsafe query construction",
                    file_path="db/query.py",
                    line_number=42,
                    suggestion="Use parameterized queries",
                )
            ],
            ai_enabled=False,
        )

        comment = formatter.format_comment(result, total_files=1)

        assert "Risk Analysis" in comment
        assert "Security" in comment or "SECURITY" in comment
        assert "SQL Injection" in comment
        assert "db/query.py" in comment

    def test_format_with_review_focus(self, formatter):
        """Test comment with review focus areas."""
        result = AnalysisResult(
            summary="Test PR",
            review_focus_areas=["Check authentication logic", "Verify error handling"],
            ai_enabled=True,
        )

        comment = formatter.format_comment(result, total_files=1)

        assert "Review Focus Areas" in comment
        assert "Check authentication logic" in comment
        assert "Verify error handling" in comment

    def test_format_partial_analysis(self, formatter):
        """Test comment with partial analysis warning."""
        result = AnalysisResult(
            summary="Test PR", partial=True, errors=["AI analysis failed"], ai_enabled=False
        )

        comment = formatter.format_comment(result, total_files=1)

        assert "Partial Analysis" in comment
        assert "AI analysis failed" in comment

    def test_format_error_comment(self, formatter):
        """Test error comment formatting."""
        error_comment = formatter.format_error_comment("Test error message")

        assert "🤖 PR Analysis" in error_comment
        assert "Error" in error_comment
        assert "Test error message" in error_comment

    def test_format_with_collapsible_files(self, formatter):
        """Test file list collapsing for large PRs."""
        # Create many files
        files = [
            FileChange(
                filename=f"file{i}.py", status="modified", additions=5, deletions=2, changes=7
            )
            for i in range(15)
        ]

        result = AnalysisResult(summary="Large PR", key_files=files, ai_enabled=False)

        comment = formatter.format_comment(result, total_files=15)

        # Should use collapsible section
        assert "<details>" in comment
        assert "</details>" in comment

    def test_risk_grouping_by_category(self, formatter):
        """Test that risks are grouped by category."""
        result = AnalysisResult(
            summary="Test",
            risks=[
                RiskItem(
                    category=RiskCategory.SECURITY,
                    level=RiskLevel.HIGH,
                    title="Security issue 1",
                    description="Test",
                ),
                RiskItem(
                    category=RiskCategory.SECURITY,
                    level=RiskLevel.MEDIUM,
                    title="Security issue 2",
                    description="Test",
                ),
                RiskItem(
                    category=RiskCategory.PERFORMANCE,
                    level=RiskLevel.LOW,
                    title="Performance issue",
                    description="Test",
                ),
            ],
            ai_enabled=False,
        )

        comment = formatter.format_comment(result, total_files=1)

        # Should have separate sections for each category
        assert comment.count("Security") >= 1 or comment.count("SECURITY") >= 1
        assert comment.count("Performance") >= 1 or comment.count("PERFORMANCE") >= 1
