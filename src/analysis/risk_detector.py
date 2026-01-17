"""Pattern-based risk detection for PR analysis."""

import re
from typing import List

from src.config.settings import Settings
from src.github_client.models import FileChange, RiskCategory, RiskItem, RiskLevel
from src.utils.logger import logger


class RiskDetector:
    """Detect potential risks using pattern matching."""

    # Security patterns
    SECURITY_PATTERNS = [
        # SQL injection
        (r'execute\s*\(.*\+.*\)', RiskLevel.HIGH, "Potential SQL injection",
         "Use parameterized queries instead of string concatenation"),
        (r'\.raw\s*\(.*\+.*\)', RiskLevel.HIGH, "Potential SQL injection in raw query",
         "Use parameterized queries with placeholders"),
        (r'format\s*\(.*SELECT.*\)', RiskLevel.HIGH, "SQL query with string formatting",
         "Use ORM or parameterized queries"),

        # Hardcoded secrets
        (r'password\s*=\s*["\'][^"\']+["\']', RiskLevel.HIGH, "Hardcoded password detected",
         "Use environment variables for sensitive data"),
        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', RiskLevel.HIGH, "Hardcoded API key detected",
         "Store API keys in environment variables"),
        (r'secret\s*=\s*["\'][^"\']+["\']', RiskLevel.HIGH, "Hardcoded secret detected",
         "Use secure secret management"),
        (r'token\s*=\s*["\'][a-zA-Z0-9]{20,}["\']', RiskLevel.HIGH, "Hardcoded token detected",
         "Store tokens securely in environment variables"),

        # XSS vulnerabilities
        (r'innerHTML\s*=', RiskLevel.MEDIUM, "Potential XSS via innerHTML",
         "Use textContent or sanitize input before setting innerHTML"),
        (r'dangerouslySetInnerHTML', RiskLevel.MEDIUM, "Using dangerouslySetInnerHTML",
         "Ensure content is properly sanitized"),
        (r'eval\s*\(', RiskLevel.HIGH, "Using eval() - security risk",
         "Avoid eval(), use safer alternatives like JSON.parse()"),

        # Unsafe deserialization
        (r'pickle\.loads?\s*\(', RiskLevel.HIGH, "Unsafe deserialization with pickle",
         "Use safer serialization formats like JSON"),
        (r'yaml\.load\s*\((?!.*Loader)', RiskLevel.MEDIUM, "Unsafe YAML loading",
         "Use yaml.safe_load() instead of yaml.load()"),

        # Command injection
        (r'os\.system\s*\(.*\+', RiskLevel.HIGH, "Potential command injection",
         "Use subprocess with argument list instead of shell=True"),
        (r'subprocess\..*shell\s*=\s*True', RiskLevel.MEDIUM, "Shell=True in subprocess",
         "Avoid shell=True, use argument list for safety"),

        # Weak crypto
        (r'MD5|md5', RiskLevel.MEDIUM, "MD5 is cryptographically weak",
         "Use SHA-256 or stronger hash algorithms"),
        (r'SHA1|sha1', RiskLevel.MEDIUM, "SHA-1 is deprecated",
         "Use SHA-256 or stronger hash algorithms"),
    ]

    # Breaking change patterns
    BREAKING_CHANGE_PATTERNS = [
        (r'^-\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', RiskLevel.MEDIUM,
         "Public method removed", "This may break existing code"),
        (r'^-\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)', RiskLevel.HIGH,
         "Class removed", "This will break code depending on this class"),
        (r'^-\s*export\s+(function|class|const|let|var)', RiskLevel.MEDIUM,
         "Export removed", "This may break imports in other files"),
        (r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):.*\n.*def\s+\1\s*\([^)]*\):', RiskLevel.MEDIUM,
         "Function signature changed", "Verify all callers are updated"),
    ]

    # Performance patterns
    PERFORMANCE_PATTERNS = [
        (r'\.all\(\).*for.*in', RiskLevel.MEDIUM, "N+1 query pattern detected",
         "Consider using select_related() or prefetch_related()"),
        (r'for\s+\w+\s+in\s+range\s*\(\s*\d{4,}', RiskLevel.MEDIUM,
         "Large loop iteration", "Consider pagination or batch processing"),
        (r'while\s+True:', RiskLevel.LOW, "Infinite loop detected",
         "Ensure there's a proper exit condition"),
        (r'sleep\s*\(\s*[0-9]+\s*\)', RiskLevel.LOW, "Sleep call in code",
         "Consider async/await or event-driven approach"),
    ]

    def __init__(self, settings: Settings):
        """
        Initialize risk detector.

        Args:
            settings: Configuration settings
        """
        self.settings = settings

    def _extract_line_number(self, patch: str, match_position: int) -> int:
        """
        Extract line number from patch where match occurred.

        Args:
            patch: Diff patch content
            match_position: Position of match in patch

        Returns:
            Approximate line number
        """
        lines_before = patch[:match_position].count('\n')

        # Parse patch to find actual line number
        current_line = 0
        for i, line in enumerate(patch.split('\n')[:lines_before + 1]):
            if line.startswith('@@'):
                # Extract starting line number
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line = int(match.group(1))
            elif line.startswith('+'):
                current_line += 1

        return current_line if current_line > 0 else lines_before + 1

    def detect_security_risks(self, files: List[FileChange]) -> List[RiskItem]:
        """
        Detect security vulnerabilities using pattern matching.

        Args:
            files: List of file changes

        Returns:
            List of security risk items
        """
        if not self.settings.analysis.enable_security_check:
            return []

        risks = []

        for file in files:
            if not file.patch:
                continue

            # Only check added lines
            added_lines = [line for line in file.patch.split('\n') if line.startswith('+')]
            content = '\n'.join(added_lines)

            for pattern, level, title, suggestion in self.SECURITY_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = self._extract_line_number(file.patch, match.start())

                    # Extract code snippet
                    snippet = match.group(0)[:100]

                    risk = RiskItem(
                        category=RiskCategory.SECURITY,
                        level=level,
                        title=title,
                        description=f"Found pattern: {snippet}",
                        file_path=file.filename,
                        line_number=line_num,
                        suggestion=suggestion,
                        code_snippet=snippet
                    )
                    risks.append(risk)

        logger.info(f"Detected {len(risks)} security risks")
        return risks

    def detect_breaking_changes(self, files: List[FileChange]) -> List[RiskItem]:
        """
        Detect potential breaking changes.

        Args:
            files: List of file changes

        Returns:
            List of breaking change risk items
        """
        if not self.settings.analysis.enable_breaking_change_check:
            return []

        risks = []

        for file in files:
            if not file.patch:
                continue

            # Check for removed public APIs
            for pattern, level, title, suggestion in self.BREAKING_CHANGE_PATTERNS:
                matches = re.finditer(pattern, file.patch, re.MULTILINE)
                for match in matches:
                    line_num = self._extract_line_number(file.patch, match.start())

                    risk = RiskItem(
                        category=RiskCategory.BREAKING_CHANGE,
                        level=level,
                        title=title,
                        description=f"Breaking change in {file.filename}",
                        file_path=file.filename,
                        line_number=line_num,
                        suggestion=suggestion
                    )
                    risks.append(risk)

        logger.info(f"Detected {len(risks)} potential breaking changes")
        return risks

    def detect_performance_issues(self, files: List[FileChange]) -> List[RiskItem]:
        """
        Detect potential performance issues.

        Args:
            files: List of file changes

        Returns:
            List of performance risk items
        """
        if not self.settings.analysis.enable_performance_check:
            return []

        risks = []

        for file in files:
            if not file.patch:
                continue

            added_lines = [line for line in file.patch.split('\n') if line.startswith('+')]
            content = '\n'.join(added_lines)

            for pattern, level, title, suggestion in self.PERFORMANCE_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = self._extract_line_number(file.patch, match.start())

                    risk = RiskItem(
                        category=RiskCategory.PERFORMANCE,
                        level=level,
                        title=title,
                        description=f"Performance concern in {file.filename}",
                        file_path=file.filename,
                        line_number=line_num,
                        suggestion=suggestion
                    )
                    risks.append(risk)

        logger.info(f"Detected {len(risks)} performance issues")
        return risks

    def detect_test_coverage_gaps(self, files: List[FileChange]) -> List[RiskItem]:
        """
        Detect missing test coverage for code changes.

        Args:
            files: List of file changes

        Returns:
            List of test coverage risk items
        """
        if not self.settings.analysis.enable_test_coverage_check:
            return []

        risks = []

        # Separate source and test files
        source_files = []
        test_files = set()

        for file in files:
            if any(pattern in file.filename.lower() for pattern in ['test', 'spec', '__test__']):
                test_files.add(file.filename)
            elif not any(ext in file.filename.lower() for ext in ['.md', '.yml', '.yaml', '.json', '.txt']):
                source_files.append(file)

        # Check if source files have corresponding test changes
        for file in source_files:
            # Skip if it's a small change
            if file.changes < 10:
                continue

            # Extract base filename for matching
            base_name = file.filename.split('/')[-1].replace('.py', '').replace('.js', '').replace('.ts', '')

            # Check if there's a related test file in changes
            has_test = any(base_name in test_file for test_file in test_files)

            if not has_test:
                risk = RiskItem(
                    category=RiskCategory.TEST_COVERAGE,
                    level=RiskLevel.MEDIUM,
                    title="No test updates for changed file",
                    description=f"{file.filename} was modified significantly without test updates",
                    file_path=file.filename,
                    suggestion="Add or update tests to cover the changes"
                )
                risks.append(risk)

        logger.info(f"Detected {len(risks)} test coverage gaps")
        return risks

    def detect_all_risks(self, files: List[FileChange]) -> List[RiskItem]:
        """
        Run all risk detection checks.

        Args:
            files: List of file changes

        Returns:
            Combined list of all risk items
        """
        all_risks = []

        all_risks.extend(self.detect_security_risks(files))
        all_risks.extend(self.detect_breaking_changes(files))
        all_risks.extend(self.detect_performance_issues(files))
        all_risks.extend(self.detect_test_coverage_gaps(files))

        logger.info(f"Total risks detected: {len(all_risks)}")
        return all_risks
