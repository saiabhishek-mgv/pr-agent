"""Main entry point for PR Agent."""

import os
import sys

from src.analysis.analyzer import PRAnalyzer
from src.config.settings import load_settings
from src.formatters.comment_formatter import CommentFormatter
from src.github_client.client import GitHubClient
from src.utils.exceptions import ConfigurationError, FatalError, GitHubAPIError
from src.utils.logger import logger, setup_logger


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logger(level=log_level)

    logger.info("Starting PR Agent")

    try:
        # Load configuration
        config_path = os.getenv("PR_AGENT_CONFIG_PATH", ".pr-agent.yml")
        settings = load_settings(config_path)

        # Initialize GitHub client
        github_client = GitHubClient(
            token=settings.github_token,
            repository=settings.repository
        )

        # Initialize analyzer
        analyzer = PRAnalyzer(settings=settings, github_client=github_client)

        # Run analysis (pattern-based + AI)
        result = analyzer.analyze_pr(pr_number=settings.pr_number)

        # Format comment
        formatter = CommentFormatter(settings)
        comment_body = formatter.format_comment(
            result=result,
            total_files=len(result.key_files)
        )

        # Post or update comment
        logger.info("Posting analysis comment to PR")
        github_client.post_or_update_comment(
            pr_number=settings.pr_number,
            body=comment_body
        )

        logger.info("PR Agent completed successfully")
        return 0

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    except GitHubAPIError as e:
        logger.error(f"GitHub API error: {e}")

        # Try to post error comment
        try:
            settings = load_settings()
            github_client = GitHubClient(
                token=settings.github_token,
                repository=settings.repository
            )
            formatter = CommentFormatter(settings)
            error_comment = formatter.format_error_comment(str(e))
            github_client.post_or_update_comment(
                pr_number=settings.pr_number,
                body=error_comment
            )
        except Exception:
            logger.error("Failed to post error comment", exc_info=True)

        return 1

    except FatalError as e:
        logger.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
