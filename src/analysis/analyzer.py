"""Main analyzer orchestrating pattern-based and AI analysis."""

from typing import List, Optional

from src.ai.claude_client import ClaudeClient
from src.analysis.diff_processor import DiffProcessor
from src.analysis.risk_detector import RiskDetector
from src.config.settings import Settings
from src.github_client.client import GitHubClient
from src.github_client.models import AnalysisResult, PRData
from src.utils.logger import logger


class PRAnalyzer:
    """Main orchestrator for PR analysis."""

    def __init__(self, settings: Settings, github_client: GitHubClient):
        """
        Initialize PR analyzer.

        Args:
            settings: Configuration settings
            github_client: GitHub API client
        """
        self.settings = settings
        self.github_client = github_client
        self.diff_processor = DiffProcessor(
            max_diff_size=settings.analysis.max_diff_size_per_file
        )
        self.risk_detector = RiskDetector(settings)

        # Initialize AI client if API key is available
        self.claude_client: Optional[ClaudeClient] = None
        if settings.anthropic_api_key:
            try:
                self.claude_client = ClaudeClient(settings)
                logger.info("AI analysis enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize AI client: {e}")
                self.claude_client = None
        else:
            logger.info("AI analysis disabled (no API key)")

    def analyze_pr(self, pr_number: int) -> AnalysisResult:
        """
        Perform complete PR analysis.

        Args:
            pr_number: Pull request number

        Returns:
            AnalysisResult with all analysis data
        """
        result = AnalysisResult(ai_enabled=self.claude_client is not None)
        errors = []

        try:
            # Step 1: Fetch PR data
            logger.info(f"Fetching PR #{pr_number} data")
            pr_data = self.github_client.get_pr_data(pr_number)

            # Step 2: Process files
            logger.info("Processing file diffs")
            processed_files = self.diff_processor.process_files(pr_data.files)

            # Check if large PR
            is_large_pr = len(processed_files) > self.settings.analysis.max_files_full_analysis

            if is_large_pr:
                logger.warning(
                    f"Large PR detected: {len(processed_files)} files. "
                    f"Prioritizing top {self.settings.analysis.max_files_full_analysis} files."
                )
                processed_files = self.diff_processor.prioritize_files(processed_files)
                errors.append(
                    f"⚠️ Large PR: Analysis focused on top "
                    f"{self.settings.analysis.max_files_full_analysis} of "
                    f"{len(pr_data.files)} files (based on security/business logic priority)"
                )

            result.key_files = processed_files

            # Step 3: Pattern-based risk detection
            logger.info("Running pattern-based risk detection")
            try:
                pattern_risks = self.risk_detector.detect_all_risks(processed_files)
                result.risks.extend(pattern_risks)
                logger.info(f"Detected {len(pattern_risks)} risks via patterns")
            except Exception as e:
                logger.error(f"Pattern-based detection failed: {e}", exc_info=True)
                errors.append(f"Pattern-based analysis partially failed: {str(e)}")

            # Step 4: AI analysis (if enabled)
            if self.claude_client:
                logger.info("Running AI-powered analysis")

                # 4a: Generate summary
                try:
                    summary = self.claude_client.analyze_pr_summary(pr_data, processed_files)
                    if summary:
                        result.summary = summary
                    else:
                        errors.append("AI summary generation failed, using basic summary")
                        result.summary = self._generate_basic_summary(pr_data, processed_files)
                except Exception as e:
                    logger.warning(f"AI summary failed: {e}")
                    errors.append(f"AI summary failed: {str(e)}")
                    result.summary = self._generate_basic_summary(pr_data, processed_files)

                # 4b: AI risk analysis
                try:
                    ai_risks = self.claude_client.analyze_risks(
                        pr_data, processed_files, result.risks
                    )
                    if ai_risks:
                        result.risks.extend(ai_risks)
                        logger.info(f"AI identified {len(ai_risks)} additional risks")
                except Exception as e:
                    logger.warning(f"AI risk analysis failed: {e}")
                    errors.append(f"AI risk analysis failed: {str(e)}")

                # 4c: Generate review focus areas
                try:
                    focus_areas = self.claude_client.generate_review_focus_areas(
                        pr_data, processed_files, result.risks
                    )
                    if focus_areas:
                        result.review_focus_areas = focus_areas
                    else:
                        result.review_focus_areas = self._generate_basic_focus_areas(
                            processed_files, result.risks
                        )
                except Exception as e:
                    logger.warning(f"AI focus areas generation failed: {e}")
                    errors.append(f"AI review focus generation failed: {str(e)}")
                    result.review_focus_areas = self._generate_basic_focus_areas(
                        processed_files, result.risks
                    )

            else:
                # No AI - use basic analysis
                logger.info("Using pattern-based analysis only (AI disabled)")
                result.summary = self._generate_basic_summary(pr_data, processed_files)
                result.review_focus_areas = self._generate_basic_focus_areas(
                    processed_files, result.risks
                )

            # Set partial flag if any errors occurred
            if errors:
                result.partial = True
                result.errors = errors

            logger.info(
                f"Analysis complete: {len(result.key_files)} files, "
                f"{len(result.risks)} risks, {len(errors)} errors"
            )

            return result

        except Exception as e:
            logger.error(f"Analysis failed critically: {e}", exc_info=True)
            result.partial = True
            result.errors.append(f"Critical analysis error: {str(e)}")
            return result

    def _generate_basic_summary(self, pr_data: PRData, files: List) -> str:
        """
        Generate basic summary without AI.

        Args:
            pr_data: PR data
            files: Processed files

        Returns:
            Basic summary string
        """
        file_count = len(files)
        additions = pr_data.metadata.additions
        deletions = pr_data.metadata.deletions

        # Detect change type
        if additions > deletions * 3:
            change_type = "primarily adds new code"
        elif deletions > additions * 3:
            change_type = "primarily removes code"
        else:
            change_type = "modifies existing code"

        summary = (
            f"This PR {change_type}, affecting {file_count} files with "
            f"+{additions}/-{deletions} lines changed."
        )

        # Add context from PR title/description
        if pr_data.metadata.title:
            summary += f" {pr_data.metadata.title}"

        return summary

    def _generate_basic_focus_areas(self, files: List, risks: List) -> List[str]:
        """
        Generate basic review focus areas without AI.

        Args:
            files: Changed files
            risks: Detected risks

        Returns:
            List of focus area strings
        """
        focus_areas = []

        # Check for high-priority risks
        high_risks = [r for r in risks if r.level.value == "HIGH"]
        if high_risks:
            focus_areas.append(
                f"Address {len(high_risks)} high-priority "
                f"{'risk' if len(high_risks) == 1 else 'risks'}"
            )

        # Check for security risks
        security_risks = [r for r in risks if r.category.value == "SECURITY"]
        if security_risks:
            focus_areas.append("Review security-related changes carefully")

        # Check for breaking changes
        breaking_risks = [r for r in risks if r.category.value == "BREAKING_CHANGE"]
        if breaking_risks:
            focus_areas.append("Verify backward compatibility and update documentation")

        # Check for test coverage
        test_risks = [r for r in risks if r.category.value == "TEST_COVERAGE"]
        if test_risks:
            focus_areas.append("Add tests for modified code")

        # Large PR
        if len(files) > 20:
            focus_areas.append("Large changeset - consider breaking into smaller PRs")

        # Default if no specific areas
        if not focus_areas:
            focus_areas.append("Verify code correctness and test coverage")
            focus_areas.append("Check for edge cases and error handling")

        return focus_areas
