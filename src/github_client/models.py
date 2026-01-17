"""Data models for GitHub PR Agent."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk severity levels."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class RiskCategory(str, Enum):
    """Risk categories."""

    SECURITY = "SECURITY"
    BREAKING_CHANGE = "BREAKING_CHANGE"
    PERFORMANCE = "PERFORMANCE"
    TEST_COVERAGE = "TEST_COVERAGE"
    OTHER = "OTHER"


class PRMetadata(BaseModel):
    """Pull request metadata."""

    number: int
    title: str
    description: Optional[str] = None
    author: str
    labels: List[str] = Field(default_factory=list)
    base_branch: str
    head_branch: str
    created_at: datetime
    updated_at: datetime
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0


class FileChange(BaseModel):
    """Information about a changed file."""

    filename: str
    status: str  # added, removed, modified, renamed
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None
    previous_filename: Optional[str] = None


class PRData(BaseModel):
    """Complete PR data including metadata and file changes."""

    metadata: PRMetadata
    files: List[FileChange]


class RiskItem(BaseModel):
    """A detected risk or issue."""

    category: RiskCategory
    level: RiskLevel
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


class AnalysisResult(BaseModel):
    """Complete analysis result."""

    summary: Optional[str] = None
    key_files: List[FileChange] = Field(default_factory=list)
    risks: List[RiskItem] = Field(default_factory=list)
    review_focus_areas: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    partial: bool = False  # True if analysis was incomplete
    ai_enabled: bool = False  # True if AI analysis was used


class DiffStats(BaseModel):
    """Statistics about diff content."""

    total_lines: int
    added_lines: int
    deleted_lines: int
    complexity_score: float = 0.0  # Simple metric based on nesting, loops, etc.
