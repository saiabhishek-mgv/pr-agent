"""Prompt templates for Claude AI integration."""

SUMMARY_PROMPT = """You are analyzing a GitHub Pull Request. Based on the PR metadata and file changes below, provide a concise 2-3 sentence summary of what this PR does and its main purpose.

PR Title: {title}
PR Description: {description}
Base Branch: {base_branch}
Head Branch: {head_branch}

Files Changed ({file_count} files):
{file_list}

Key Changes:
{key_changes}

Provide a clear, technical summary focusing on:
1. What functionality is being added, modified, or removed
2. The main technical approach or pattern used
3. Any notable architectural decisions

Keep it concise and professional."""

RISK_ANALYSIS_PROMPT = """You are a senior software engineer reviewing a Pull Request. Analyze the code changes below and identify potential risks beyond basic pattern matching.

PR Context:
Title: {title}
Description: {description}

File Changes:
{file_changes}

Pattern-Based Risks Already Detected:
{existing_risks}

Your task is to identify additional risks that require deeper code understanding:

1. **Logic Errors**: Race conditions, edge cases, incorrect business logic
2. **Security**: Context-specific vulnerabilities not caught by patterns
3. **Performance**: Algorithmic complexity, memory leaks, inefficient queries
4. **Maintainability**: Code smells, tight coupling, violation of design principles
5. **Data Integrity**: Migration issues, schema changes, data loss risks

For each risk you identify, provide:
- Category (Security/Performance/Logic/Maintainability/Data)
- Severity (HIGH/MEDIUM/LOW)
- Description
- File and approximate location
- Specific recommendation

Focus on substantive issues that could impact production. Skip minor style issues.

Format your response as a JSON array of risk objects:
[
  {{
    "category": "Security",
    "severity": "HIGH",
    "title": "Brief title",
    "description": "Detailed description",
    "file_path": "path/to/file.py",
    "suggestion": "Specific recommendation"
  }}
]

If no significant additional risks are found, return an empty array []."""

REVIEW_FOCUS_PROMPT = """You are helping a code reviewer prioritize their review of a Pull Request. Based on the changes and risks below, generate a checklist of 3-7 specific items the reviewer should focus on.

PR Context:
Title: {title}
Description: {description}

Files Changed: {file_count}
Lines Added: {additions}
Lines Deleted: {deletions}

Key Files:
{key_files}

Detected Risks:
{risks}

Generate a prioritized checklist of review focus areas. Each item should be:
- Specific and actionable
- Related to actual changes in this PR
- Important for code quality, security, or functionality
- Written as a clear task (e.g., "Verify error handling in X", "Check backward compatibility of Y")

Format your response as a JSON array of strings:
[
  "Verify JWT token validation includes expiration checks",
  "Check that database migrations are backward compatible",
  "Confirm all error cases are handled in payment processing"
]

Provide 3-7 items maximum, ordered by priority."""

CODE_ANALYSIS_PROMPT = """Analyze the following code changes from a Pull Request and provide insights about potential issues, improvements, or concerns.

File: {filename}
Changes:
{diff}

Provide analysis in the following areas:
1. Correctness: Any logical errors or bugs?
2. Security: Any security vulnerabilities?
3. Performance: Any performance concerns?
4. Best Practices: Any deviations from best practices?
5. Testing: What should be tested?

Be concise and focus on the most important issues."""
