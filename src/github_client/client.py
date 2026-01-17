"""GitHub API client for PR Agent."""

from typing import List, Optional

from github import Github, GithubException
from tenacity import retry, stop_after_attempt, wait_exponential

from src.github_client.models import FileChange, PRData, PRMetadata
from src.utils.exceptions import GitHubAPIError
from src.utils.logger import logger


class GitHubClient:
    """Wrapper for GitHub API operations."""

    def __init__(self, token: str, repository: str):
        """
        Initialize GitHub client.

        Args:
            token: GitHub API token
            repository: Repository in format 'owner/repo'
        """
        self.client = Github(token)
        self.repository = repository
        self.repo = None
        self._bot_comment_marker = "<!-- pr-agent-comment -->"

        try:
            self.repo = self.client.get_repo(repository)
            logger.info(f"Connected to repository: {repository}")
        except GithubException as e:
            raise GitHubAPIError(f"Failed to connect to repository {repository}: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_pr_metadata(self, pr_number: int) -> PRMetadata:
        """
        Fetch PR metadata.

        Args:
            pr_number: Pull request number

        Returns:
            PRMetadata instance

        Raises:
            GitHubAPIError: If API request fails
        """
        try:
            pr = self.repo.get_pull(pr_number)

            labels = [label.name for label in pr.labels]

            metadata = PRMetadata(
                number=pr.number,
                title=pr.title,
                description=pr.body or "",
                author=pr.user.login,
                labels=labels,
                base_branch=pr.base.ref,
                head_branch=pr.head.ref,
                created_at=pr.created_at,
                updated_at=pr.updated_at,
                additions=pr.additions,
                deletions=pr.deletions,
                changed_files=pr.changed_files
            )

            logger.info(f"Fetched metadata for PR #{pr_number}: {pr.title}")
            return metadata

        except GithubException as e:
            raise GitHubAPIError(f"Failed to fetch PR #{pr_number}: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_changed_files(self, pr_number: int) -> List[FileChange]:
        """
        Fetch changed files in the PR.

        Args:
            pr_number: Pull request number

        Returns:
            List of FileChange instances

        Raises:
            GitHubAPIError: If API request fails
        """
        try:
            pr = self.repo.get_pull(pr_number)
            files = []

            for file in pr.get_files():
                file_change = FileChange(
                    filename=file.filename,
                    status=file.status,
                    additions=file.additions,
                    deletions=file.deletions,
                    changes=file.changes,
                    patch=file.patch if hasattr(file, 'patch') else None,
                    previous_filename=file.previous_filename if hasattr(file, 'previous_filename') else None
                )
                files.append(file_change)

            logger.info(f"Fetched {len(files)} changed files for PR #{pr_number}")
            return files

        except GithubException as e:
            raise GitHubAPIError(f"Failed to fetch files for PR #{pr_number}: {e}") from e

    def get_pr_data(self, pr_number: int) -> PRData:
        """
        Fetch complete PR data (metadata + files).

        Args:
            pr_number: Pull request number

        Returns:
            PRData instance

        Raises:
            GitHubAPIError: If API request fails
        """
        metadata = self.get_pr_metadata(pr_number)
        files = self.get_changed_files(pr_number)

        return PRData(metadata=metadata, files=files)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def find_existing_bot_comment(self, pr_number: int) -> Optional[int]:
        """
        Find existing bot comment on the PR.

        Args:
            pr_number: Pull request number

        Returns:
            Comment ID if found, None otherwise
        """
        try:
            pr = self.repo.get_pull(pr_number)
            comments = pr.get_issue_comments()

            for comment in comments:
                if self._bot_comment_marker in comment.body:
                    logger.info(f"Found existing bot comment #{comment.id}")
                    return comment.id

            return None

        except GithubException as e:
            logger.warning(f"Failed to search for existing comments: {e}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def post_comment(self, pr_number: int, body: str) -> None:
        """
        Post a comment on the PR.

        Args:
            pr_number: Pull request number
            body: Comment body (markdown)

        Raises:
            GitHubAPIError: If posting fails
        """
        try:
            # Add bot marker to comment
            body_with_marker = f"{self._bot_comment_marker}\n{body}"

            pr = self.repo.get_pull(pr_number)
            pr.create_issue_comment(body_with_marker)
            logger.info(f"Posted comment on PR #{pr_number}")

        except GithubException as e:
            raise GitHubAPIError(f"Failed to post comment on PR #{pr_number}: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def update_comment(self, comment_id: int, body: str) -> None:
        """
        Update an existing comment.

        Args:
            comment_id: Comment ID
            body: New comment body (markdown)

        Raises:
            GitHubAPIError: If update fails
        """
        try:
            # Add bot marker to comment
            body_with_marker = f"{self._bot_comment_marker}\n{body}"

            comment = self.repo.get_issue_comment(comment_id)
            comment.edit(body_with_marker)
            logger.info(f"Updated comment #{comment_id}")

        except GithubException as e:
            raise GitHubAPIError(f"Failed to update comment #{comment_id}: {e}") from e

    def post_or_update_comment(self, pr_number: int, body: str) -> None:
        """
        Post a new comment or update existing bot comment.

        Args:
            pr_number: Pull request number
            body: Comment body (markdown)

        Raises:
            GitHubAPIError: If operation fails
        """
        existing_comment_id = self.find_existing_bot_comment(pr_number)

        if existing_comment_id:
            logger.info(f"Updating existing comment on PR #{pr_number}")
            self.update_comment(existing_comment_id, body)
        else:
            logger.info(f"Creating new comment on PR #{pr_number}")
            self.post_comment(pr_number, body)
