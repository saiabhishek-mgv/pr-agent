"""Format analysis results as GitHub comment markdown."""

from datetime import datetime
from typing import Dict, List

from src.config.settings import Settings
from src.github_client.models import AnalysisResult, FileChange, RiskCategory, RiskItem, RiskLevel


class CommentFormatter:
    """Format analysis results as markdown comments."""

    # Emoji mapping for risk categories
    CATEGORY_EMOJI = {
        RiskCategory.SECURITY: "🔒",
        RiskCategory.BREAKING_CHANGE: "⚠️",
        RiskCategory.PERFORMANCE: "⚡",
        RiskCategory.TEST_COVERAGE: "🧪",
        RiskCategory.OTHER: "📌",
    }

    def __init__(self, settings: Settings):
        """
        Initialize comment formatter.

        Args:
            settings: Configuration settings
        """
        self.settings = settings

    def _format_risk_level(self, level: RiskLevel) -> str:
        """Format risk level with appropriate styling."""
        if level == RiskLevel.HIGH:
            return "**HIGH**"
        elif level == RiskLevel.MEDIUM:
            return "**MEDIUM**"
        elif level == RiskLevel.LOW:
            return "**LOW**"
        else:
            return "**INFO**"

    def _format_file_table(self, files: List[FileChange]) -> str:
        """
        Format file changes as a markdown table.

        Args:
            files: List of file changes

        Returns:
            Markdown table string
        """
        if not files:
            return "*No files to display*"

        lines = [
            "| File | Changes | Impact |",
            "|------|---------|--------|"
        ]

        for file in files[:self.settings.comment.max_key_files]:
            # Determine impact based on changes
            if file.changes > 100:
                impact = "High"
            elif file.changes > 50:
                impact = "Medium"
            else:
                impact = "Low"

            # Format status
            status_emoji = {
                "added": "✨",
                "removed": "🗑️",
                "modified": "📝",
                "renamed": "🔄"
            }.get(file.status, "📝")

            lines.append(
                f"| {status_emoji} `{file.filename}` | +{file.additions}, -{file.deletions} | {impact} |"
            )

        return "\n".join(lines)

    def _group_risks_by_category(self, risks: List[RiskItem]) -> Dict[RiskCategory, List[RiskItem]]:
        """Group risks by category."""
        grouped = {}
        for risk in risks:
            if risk.category not in grouped:
                grouped[risk.category] = []
            grouped[risk.category].append(risk)
        return grouped

    def _format_risk_section(self, category: RiskCategory, risks: List[RiskItem]) -> str:
        """
        Format a risk category section.

        Args:
            category: Risk category
            risks: List of risks in this category

        Returns:
            Markdown formatted section
        """
        emoji = self.CATEGORY_EMOJI.get(category, "📌")
        category_name = category.value.replace("_", " ").title()

        lines = [f"#### {emoji} {category_name}\n"]

        # Sort by risk level (HIGH -> MEDIUM -> LOW -> INFO)
        level_order = {RiskLevel.HIGH: 0, RiskLevel.MEDIUM: 1, RiskLevel.LOW: 2, RiskLevel.INFO: 3}
        sorted_risks = sorted(risks, key=lambda r: level_order.get(r.level, 4))

        for risk in sorted_risks:
            lines.append(f"- {self._format_risk_level(risk.level)}: {risk.title}")

            if risk.file_path:
                location = f"  - File: `{risk.file_path}`"
                if risk.line_number:
                    location += f":{risk.line_number}"
                lines.append(location)

            if risk.description and risk.description != risk.title:
                lines.append(f"  - {risk.description}")

            if risk.suggestion:
                lines.append(f"  - Suggestion: {risk.suggestion}")

            lines.append("")  # Empty line between risks

        return "\n".join(lines)

    def format_comment(self, result: AnalysisResult, total_files: int) -> str:
        """
        Format complete analysis result as a GitHub comment.

        Args:
            result: Analysis result
            total_files: Total number of files changed

        Returns:
            Markdown formatted comment
        """
        sections = []

        # Header
        sections.append("## 🤖 PR Analysis\n")

        # Warnings/errors section
        if result.partial:
            sections.append("⚠️ **Partial Analysis**: Some components failed during analysis.\n")

        if result.errors:
            sections.append("### Errors\n")
            for error in result.errors:
                sections.append(f"- {error}")
            sections.append("")

        # Summary section
        if self.settings.comment.include_summary and result.summary:
            sections.append("### Summary\n")
            sections.append(f"{result.summary}\n")

        # Key files section
        if self.settings.comment.include_key_files and result.key_files:
            sections.append("### Key Files Changed\n")

            if self.settings.comment.collapse_file_list and len(result.key_files) > 10:
                sections.append(f"<details>\n<summary>📁 {total_files} files modified</summary>\n")
                sections.append(self._format_file_table(result.key_files))
                sections.append("\n</details>\n")
            else:
                sections.append(self._format_file_table(result.key_files))
                sections.append("")

        # Risk analysis section
        if self.settings.comment.include_risks and result.risks:
            sections.append("### Risk Analysis\n")

            grouped_risks = self._group_risks_by_category(result.risks)

            # Order categories by importance
            category_order = [
                RiskCategory.SECURITY,
                RiskCategory.BREAKING_CHANGE,
                RiskCategory.PERFORMANCE,
                RiskCategory.TEST_COVERAGE,
                RiskCategory.OTHER
            ]

            for category in category_order:
                if category in grouped_risks:
                    sections.append(self._format_risk_section(category, grouped_risks[category]))

        elif self.settings.comment.include_risks and not result.risks:
            sections.append("### Risk Analysis\n")
            sections.append("✅ No significant risks detected.\n")

        # Review focus areas
        if result.review_focus_areas:
            sections.append("### Review Focus Areas\n")
            for area in result.review_focus_areas:
                sections.append(f"- [ ] {area}")
            sections.append("")

        # Footer
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        ai_status = "Powered by Claude AI" if result.ai_enabled else "Pattern-based analysis"
        sections.append("---")
        sections.append(f"*Analysis generated on {timestamp} | {ai_status}*")

        return "\n".join(sections)

    def format_error_comment(self, error_message: str) -> str:
        """
        Format an error message as a GitHub comment.

        Args:
            error_message: Error message

        Returns:
            Markdown formatted error comment
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        return f"""## 🤖 PR Analysis

### Error

❌ Analysis failed: {error_message}

Please check the GitHub Actions logs for more details.

---
*Analysis attempted on {timestamp}*
"""
