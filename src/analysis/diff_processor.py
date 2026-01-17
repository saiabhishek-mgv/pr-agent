"""Diff processing and statistics calculation."""

import re
from typing import List, Optional

from src.github_client.models import DiffStats, FileChange
from src.utils.logger import logger


class DiffProcessor:
    """Process and analyze file diffs."""

    # File extensions to skip (binary, generated, etc.)
    SKIP_EXTENSIONS = {
        # Binary/media
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
        '.pdf', '.zip', '.tar', '.gz', '.bz2', '.7z',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv',
        # Compiled/generated
        '.pyc', '.pyo', '.so', '.dll', '.exe', '.class', '.jar',
        '.min.js', '.min.css', '.map',
        # Lock files
        '.lock', 'package-lock.json', 'yarn.lock', 'poetry.lock', 'Pipfile.lock',
    }

    SKIP_PATTERNS = [
        r'.*\.min\..*',  # Minified files
        r'.*-lock\..*',  # Lock files
        r'.*/dist/.*',   # Distribution files
        r'.*/build/.*',  # Build files
        r'.*/node_modules/.*',  # Dependencies
        r'.*/__pycache__/.*',   # Python cache
    ]

    def __init__(self, max_diff_size: int = 1000):
        """
        Initialize diff processor.

        Args:
            max_diff_size: Maximum lines of diff per file
        """
        self.max_diff_size = max_diff_size

    def should_skip_file(self, filename: str) -> bool:
        """
        Check if file should be skipped from analysis.

        Args:
            filename: File path

        Returns:
            True if file should be skipped
        """
        # Check extension
        for ext in self.SKIP_EXTENSIONS:
            if filename.lower().endswith(ext):
                return True

        # Check patterns
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, filename):
                return True

        return False

    def clean_diff(self, patch: Optional[str]) -> str:
        """
        Clean and format diff patch.

        Args:
            patch: Raw diff patch

        Returns:
            Cleaned diff string
        """
        if not patch:
            return ""

        lines = patch.split('\n')

        # Truncate if too large
        if len(lines) > self.max_diff_size:
            truncated_lines = lines[:self.max_diff_size]
            truncated_lines.append(f"\n... (truncated {len(lines) - self.max_diff_size} lines)")
            return '\n'.join(truncated_lines)

        return patch

    def calculate_diff_stats(self, patch: Optional[str]) -> DiffStats:
        """
        Calculate statistics from a diff patch.

        Args:
            patch: Diff patch content

        Returns:
            DiffStats instance
        """
        if not patch:
            return DiffStats(
                total_lines=0,
                added_lines=0,
                deleted_lines=0,
                complexity_score=0.0
            )

        lines = patch.split('\n')
        added = 0
        deleted = 0
        complexity = 0.0

        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                added += 1
                # Increase complexity for control structures
                if any(keyword in line for keyword in ['if ', 'for ', 'while ', 'try:', 'except', 'class ', 'def ']):
                    complexity += 1.5
                elif any(keyword in line for keyword in ['import ', 'from ', 'return ', 'yield ']):
                    complexity += 0.5
            elif line.startswith('-') and not line.startswith('---'):
                deleted += 1

        # Normalize complexity score (0-10 scale)
        total_changed = added + deleted
        if total_changed > 0:
            complexity_score = min(10.0, (complexity / total_changed) * 10)
        else:
            complexity_score = 0.0

        return DiffStats(
            total_lines=len(lines),
            added_lines=added,
            deleted_lines=deleted,
            complexity_score=complexity_score
        )

    def process_files(self, files: List[FileChange]) -> List[FileChange]:
        """
        Process and filter file changes.

        Args:
            files: List of file changes

        Returns:
            Filtered and processed file changes
        """
        processed_files = []

        for file in files:
            # Skip binary/generated files
            if self.should_skip_file(file.filename):
                logger.debug(f"Skipping file: {file.filename}")
                continue

            # Clean the patch
            if file.patch:
                file.patch = self.clean_diff(file.patch)

            processed_files.append(file)

        logger.info(f"Processed {len(processed_files)} files (skipped {len(files) - len(processed_files)})")
        return processed_files

    def prioritize_files(self, files: List[FileChange]) -> List[FileChange]:
        """
        Prioritize files for analysis based on importance.

        High priority: Security-sensitive files, API endpoints, core business logic
        Medium priority: Services, utilities, middleware
        Low priority: Tests, docs, configs

        Args:
            files: List of file changes

        Returns:
            Sorted list with high-priority files first
        """
        def get_priority(file: FileChange) -> int:
            filename = file.filename.lower()

            # High priority patterns
            high_priority_patterns = [
                'auth', 'security', 'crypto', 'password', 'token',
                'api', 'endpoint', 'route', 'controller',
                'sql', 'database', 'query', 'model',
                'payment', 'billing', 'transaction'
            ]

            # Low priority patterns
            low_priority_patterns = [
                'test', 'spec', 'mock',
                'readme', 'doc', '.md',
                'config', 'setting', '.yml', '.yaml', '.json',
                'migration', 'fixture'
            ]

            # Check high priority
            for pattern in high_priority_patterns:
                if pattern in filename:
                    return 3

            # Check low priority
            for pattern in low_priority_patterns:
                if pattern in filename:
                    return 1

            # Medium priority (default)
            return 2

        # Sort by priority (descending) and then by filename
        sorted_files = sorted(files, key=lambda f: (-get_priority(f), f.filename))

        logger.info(f"Prioritized {len(sorted_files)} files for analysis")
        return sorted_files
