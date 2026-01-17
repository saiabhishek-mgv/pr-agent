"""Claude AI client for PR analysis."""

import json
from typing import List, Optional

from anthropic import Anthropic, APIError, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.ai.prompts import REVIEW_FOCUS_PROMPT, RISK_ANALYSIS_PROMPT, SUMMARY_PROMPT
from src.config.settings import Settings
from src.github_client.models import FileChange, PRData, RiskCategory, RiskItem, RiskLevel
from src.utils.exceptions import AIError
from src.utils.logger import logger


class ClaudeClient:
    """Client for Claude AI API integration."""

    def __init__(self, settings: Settings):
        """
        Initialize Claude client.

        Args:
            settings: Configuration settings
        """
        self.settings = settings
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.ai.model
        self.max_tokens = settings.ai.max_tokens
        self.temperature = settings.ai.temperature

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=30)
    )
    def _call_claude(self, prompt: str) -> str:
        """
        Call Claude API with retry logic.

        Args:
            prompt: The prompt to send

        Returns:
            Claude's response text

        Raises:
            AIError: If API call fails
        """
        try:
            logger.debug(f"Calling Claude API with model {self.model}")

            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = message.content[0].text
            logger.debug(f"Claude API response received ({len(response_text)} chars)")
            return response_text

        except RateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            raise  # Will be retried by tenacity

        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise AIError(f"Claude API failed: {e}")

        except Exception as e:
            logger.error(f"Unexpected error calling Claude: {e}", exc_info=True)
            raise AIError(f"Unexpected AI error: {e}")

    def analyze_pr_summary(self, pr_data: PRData, key_files: List[FileChange]) -> Optional[str]:
        """
        Generate a high-level summary of the PR using AI.

        Args:
            pr_data: PR metadata and files
            key_files: Key files to include in analysis

        Returns:
            Summary string or None if failed
        """
        try:
            # Build file list
            file_list = "\n".join([
                f"- {f.filename} (+{f.additions}/-{f.deletions})"
                for f in key_files[:20]  # Limit to top 20 files
            ])

            # Build key changes from diffs (limited)
            key_changes = []
            for file in key_files[:5]:  # Only first 5 files for context
                if file.patch:
                    # Get first 20 lines of patch
                    patch_lines = file.patch.split('\n')[:20]
                    key_changes.append(f"\n{file.filename}:\n" + "\n".join(patch_lines))

            key_changes_str = "\n".join(key_changes) if key_changes else "See file list above"

            # Format prompt
            prompt = SUMMARY_PROMPT.format(
                title=pr_data.metadata.title,
                description=pr_data.metadata.description or "No description provided",
                base_branch=pr_data.metadata.base_branch,
                head_branch=pr_data.metadata.head_branch,
                file_count=len(key_files),
                file_list=file_list,
                key_changes=key_changes_str
            )

            logger.info("Generating AI summary")
            summary = self._call_claude(prompt)

            return summary.strip()

        except AIError as e:
            logger.warning(f"AI summary failed: {e}")
            return None

        except Exception as e:
            logger.warning(f"Unexpected error generating summary: {e}")
            return None

    def analyze_risks(
        self,
        pr_data: PRData,
        files: List[FileChange],
        existing_risks: List[RiskItem]
    ) -> List[RiskItem]:
        """
        Analyze risks using AI to supplement pattern-based detection.

        Args:
            pr_data: PR metadata and files
            files: Files to analyze
            existing_risks: Risks already detected by patterns

        Returns:
            Additional risks identified by AI
        """
        try:
            # Build file changes summary
            file_changes_parts = []
            for file in files[:10]:  # Limit to 10 files
                if file.patch:
                    patch_preview = '\n'.join(file.patch.split('\n')[:30])  # First 30 lines
                    file_changes_parts.append(
                        f"\nFile: {file.filename}\n"
                        f"Changes: +{file.additions}/-{file.deletions}\n"
                        f"Preview:\n{patch_preview}\n"
                    )

            file_changes_str = "\n---\n".join(file_changes_parts)

            # Format existing risks
            existing_risks_str = "\n".join([
                f"- {r.category.value}: {r.title} ({r.level.value})"
                for r in existing_risks[:10]
            ]) if existing_risks else "None detected by patterns"

            # Format prompt
            prompt = RISK_ANALYSIS_PROMPT.format(
                title=pr_data.metadata.title,
                description=pr_data.metadata.description or "No description",
                file_changes=file_changes_str,
                existing_risks=existing_risks_str
            )

            logger.info("Analyzing risks with AI")
            response = self._call_claude(prompt)

            # Parse JSON response
            try:
                # Extract JSON from response (handle markdown code blocks)
                json_str = response.strip()
                if json_str.startswith('```'):
                    # Remove markdown code block
                    lines = json_str.split('\n')
                    json_str = '\n'.join(lines[1:-1]) if len(lines) > 2 else json_str

                risk_data = json.loads(json_str)

                # Convert to RiskItem objects
                ai_risks = []
                for risk_dict in risk_data:
                    try:
                        # Map category string to enum
                        category_map = {
                            "Security": RiskCategory.SECURITY,
                            "Performance": RiskCategory.PERFORMANCE,
                            "Logic": RiskCategory.OTHER,
                            "Maintainability": RiskCategory.OTHER,
                            "Data": RiskCategory.OTHER,
                        }
                        category = category_map.get(risk_dict.get("category"), RiskCategory.OTHER)

                        # Map severity to level
                        level_map = {
                            "HIGH": RiskLevel.HIGH,
                            "MEDIUM": RiskLevel.MEDIUM,
                            "LOW": RiskLevel.LOW,
                        }
                        level = level_map.get(risk_dict.get("severity", "MEDIUM"), RiskLevel.MEDIUM)

                        risk = RiskItem(
                            category=category,
                            level=level,
                            title=risk_dict.get("title", "AI-identified risk"),
                            description=risk_dict.get("description", ""),
                            file_path=risk_dict.get("file_path"),
                            suggestion=risk_dict.get("suggestion")
                        )
                        ai_risks.append(risk)

                    except Exception as e:
                        logger.warning(f"Failed to parse risk item: {e}")
                        continue

                logger.info(f"AI identified {len(ai_risks)} additional risks")
                return ai_risks

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse AI risk response as JSON: {e}")
                return []

        except AIError as e:
            logger.warning(f"AI risk analysis failed: {e}")
            return []

        except Exception as e:
            logger.warning(f"Unexpected error in AI risk analysis: {e}")
            return []

    def generate_review_focus_areas(
        self,
        pr_data: PRData,
        key_files: List[FileChange],
        risks: List[RiskItem]
    ) -> List[str]:
        """
        Generate a checklist of review focus areas using AI.

        Args:
            pr_data: PR metadata
            key_files: Key files changed
            risks: Detected risks

        Returns:
            List of review focus area strings
        """
        try:
            # Format key files
            key_files_str = "\n".join([
                f"- {f.filename} (+{f.additions}/-{f.deletions})"
                for f in key_files[:15]
            ])

            # Format risks
            risks_str = "\n".join([
                f"- {r.category.value} ({r.level.value}): {r.title}"
                for r in risks[:10]
            ]) if risks else "No significant risks detected"

            # Format prompt
            prompt = REVIEW_FOCUS_PROMPT.format(
                title=pr_data.metadata.title,
                description=pr_data.metadata.description or "No description",
                file_count=len(key_files),
                additions=pr_data.metadata.additions,
                deletions=pr_data.metadata.deletions,
                key_files=key_files_str,
                risks=risks_str
            )

            logger.info("Generating review focus areas with AI")
            response = self._call_claude(prompt)

            # Parse JSON response
            try:
                json_str = response.strip()
                if json_str.startswith('```'):
                    lines = json_str.split('\n')
                    json_str = '\n'.join(lines[1:-1]) if len(lines) > 2 else json_str

                focus_areas = json.loads(json_str)

                if isinstance(focus_areas, list):
                    logger.info(f"Generated {len(focus_areas)} review focus areas")
                    return focus_areas[:7]  # Max 7 items

                return []

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse focus areas as JSON: {e}")
                # Fall back to splitting by newlines
                lines = [line.strip('- ').strip() for line in response.split('\n') if line.strip()]
                return [line for line in lines if len(line) > 10][:7]

        except AIError as e:
            logger.warning(f"AI focus areas generation failed: {e}")
            return []

        except Exception as e:
            logger.warning(f"Unexpected error generating focus areas: {e}")
            return []
