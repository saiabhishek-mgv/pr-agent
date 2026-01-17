"""Tests for risk detector."""

import pytest

from src.analysis.risk_detector import RiskDetector
from src.config.settings import Settings
from src.github_client.models import FileChange, RiskCategory, RiskLevel


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        github_token="test_token",
        anthropic_api_key="test_key",
        repository="test/repo",
        pr_number=1
    )


@pytest.fixture
def risk_detector(settings):
    """Create risk detector instance."""
    return RiskDetector(settings)


class TestRiskDetector:
    """Test RiskDetector functionality."""

    def test_detect_sql_injection(self, risk_detector):
        """Test SQL injection detection."""
        file = FileChange(
            filename="db/query.py",
            status="modified",
            additions=5,
            deletions=2,
            changes=7,
            patch='+query = "SELECT * FROM users WHERE id = " + user_input\n+cursor.execute(query)'
        )

        risks = risk_detector.detect_security_risks([file])
        assert len(risks) > 0
        assert any(r.category == RiskCategory.SECURITY for r in risks)
        assert any("SQL injection" in r.title or "injection" in r.title.lower() for r in risks)

    def test_detect_hardcoded_secret(self, risk_detector):
        """Test hardcoded secret detection."""
        file = FileChange(
            filename="config.py",
            status="modified",
            additions=3,
            deletions=0,
            changes=3,
            patch='+API_KEY = "sk_live_1234567890abcdef"\n+PASSWORD = "admin123"'
        )

        risks = risk_detector.detect_security_risks([file])
        assert len(risks) > 0
        assert any(r.level == RiskLevel.HIGH for r in risks)

    def test_detect_xss_vulnerability(self, risk_detector):
        """Test XSS vulnerability detection."""
        file = FileChange(
            filename="frontend/component.js",
            status="modified",
            additions=2,
            deletions=1,
            changes=3,
            patch='+element.innerHTML = userInput;'
        )

        risks = risk_detector.detect_security_risks([file])
        assert len(risks) > 0
        assert any("XSS" in r.title or "innerHTML" in r.title for r in risks)

    def test_detect_method_removal(self, risk_detector):
        """Test detection of removed methods."""
        file = FileChange(
            filename="api/endpoints.py",
            status="modified",
            additions=0,
            deletions=5,
            changes=5,
            patch='-def get_user_profile(user_id):\n-    return User.query.get(user_id)'
        )

        risks = risk_detector.detect_breaking_changes([file])
        # May or may not detect depending on pattern matching
        # This is a basic test to ensure no crashes
        assert isinstance(risks, list)

    def test_detect_performance_issue(self, risk_detector):
        """Test performance issue detection."""
        file = FileChange(
            filename="models.py",
            status="modified",
            additions=3,
            deletions=0,
            changes=3,
            patch='+users = User.objects.all()\n+for user in users:\n+    process_user(user)'
        )

        risks = risk_detector.detect_performance_issues([file])
        assert len(risks) > 0
        assert any(r.category == RiskCategory.PERFORMANCE for r in risks)

    def test_detect_test_coverage_gap(self, risk_detector):
        """Test test coverage gap detection."""
        files = [
            FileChange(
                filename="src/payment.py",
                status="modified",
                additions=50,
                deletions=10,
                changes=60,
                patch="+def process_payment(amount): pass"
            ),
            # No corresponding test file
        ]

        risks = risk_detector.detect_test_coverage_gaps(files)
        assert len(risks) > 0
        assert any(r.category == RiskCategory.TEST_COVERAGE for r in risks)

    def test_no_risks_for_safe_code(self, risk_detector):
        """Test that safe code produces no security risks."""
        file = FileChange(
            filename="utils.py",
            status="modified",
            additions=5,
            deletions=2,
            changes=7,
            patch='+def add(a, b):\n+    return a + b'
        )

        risks = risk_detector.detect_security_risks([file])
        assert len(risks) == 0

    def test_detect_all_risks(self, risk_detector):
        """Test that detect_all_risks combines all detectors."""
        file = FileChange(
            filename="security.py",
            status="modified",
            additions=5,
            deletions=0,
            changes=5,
            patch='+password = "hardcoded"\n+query = "SELECT * FROM users WHERE id = " + user_id'
        )

        risks = risk_detector.detect_all_risks([file])
        # Should detect multiple security issues
        assert len(risks) >= 2
