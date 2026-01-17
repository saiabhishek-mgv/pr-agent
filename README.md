# PR Agent

AI-powered GitHub Pull Request analyzer using Claude. Automatically analyze PRs for security vulnerabilities, breaking changes, performance issues, and test coverage gaps.

## Features

- **AI-Powered Analysis**: Uses Claude Sonnet 4.5 for intelligent code review
- **Pattern-Based Detection**: Regex-based security and risk detection
- **Comprehensive Risk Analysis**:
  - Security vulnerabilities (SQL injection, XSS, hardcoded secrets)
  - Breaking changes (API signature changes, removed methods)
  - Performance issues (N+1 queries, inefficient loops)
  - Test coverage gaps
- **Smart Formatting**: Posts analysis as formatted GitHub comments with tables, bullets, and collapsible sections
- **Graceful Degradation**: Falls back to pattern-based analysis if AI fails
- **Configurable**: Via YAML file or workflow inputs
- **Large PR Handling**: Intelligently prioritizes files for analysis

## Quick Start

### 1. Add to Your Repository

Create `.github/workflows/pr-agent.yml`:

```yaml
name: PR Agent Analysis

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run PR Agent
        uses: yourusername/pr-agent@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### 2. Add Anthropic API Key

1. Get your API key from [Anthropic Console](https://console.anthropic.com/)
2. Add it to your repository secrets as `ANTHROPIC_API_KEY`:
   - Go to Settings > Secrets and variables > Actions
   - Click "New repository secret"
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your API key

### 3. Create a Pull Request

PR Agent will automatically analyze your PR and post a comment with:
- High-level summary
- Key files changed
- Detected risks by category
- Review focus areas checklist

## Configuration

### Option 1: Configuration File

Create `.pr-agent.yml` in your repository root:

```yaml
analysis:
  max_files_full_analysis: 50
  max_diff_size_per_file: 1000
  enable_security_check: true
  enable_performance_check: true
  enable_breaking_change_check: true
  enable_test_coverage_check: true

comment:
  include_summary: true
  include_key_files: true
  include_risks: true
  collapse_file_list: true
  max_key_files: 10

ai:
  model: "claude-sonnet-4-5-20250929"
  max_tokens: 4096
  temperature: 0.3
```

See [.pr-agent.yml.example](./.pr-agent.yml.example) for all options.

### Option 2: Workflow Inputs

Override settings via workflow inputs:

```yaml
- name: Run PR Agent
  uses: yourusername/pr-agent@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    max-files: '30'
    enable-security: 'true'
    enable-performance: 'true'
    log-level: 'DEBUG'
```

### Available Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `github-token` | GitHub token for API access | `${{ github.token }}` |
| `anthropic-api-key` | Anthropic API key (required) | - |
| `config-path` | Path to config file | `.pr-agent.yml` |
| `max-files` | Max files to analyze | `50` |
| `enable-security` | Enable security checks | `true` |
| `enable-performance` | Enable performance checks | `true` |
| `enable-breaking` | Enable breaking change detection | `true` |
| `enable-test-coverage` | Enable test coverage checks | `true` |
| `log-level` | Logging level | `INFO` |

## Example Output

PR Agent posts comments like this:

```markdown
## 🤖 PR Analysis

### Summary
This PR refactors the authentication system to use JWT tokens instead of
sessions, improving scalability and enabling stateless API authentication.

### Key Files Changed
| File | Changes | Impact |
|------|---------|--------|
| 📝 `src/auth/jwt_handler.py` | +120, -0 | High |
| 📝 `src/auth/middleware.py` | +45, -67 | Medium |

### Risk Analysis

#### 🔒 Security
- **HIGH**: Hardcoded secret detected
  - File: `src/config/settings.py:42`
  - Suggestion: Use environment variables for sensitive data

#### ⚠️ Breaking Changes
- **MEDIUM**: Authentication middleware interface changed
  - File: `src/auth/middleware.py:89`
  - Suggestion: Provide migration guide

### Review Focus Areas
- [ ] Verify JWT secret is loaded from environment variable
- [ ] Check backwards compatibility for existing API consumers
- [ ] Review token expiration and refresh logic
```

## How It Works

1. **Fetch PR Data**: Retrieves PR metadata and file diffs via GitHub API
2. **Process Files**: Filters out binary/generated files, prioritizes important files
3. **Pattern Detection**: Runs regex-based security and risk detection
4. **AI Analysis**: Sends context to Claude for intelligent insights
5. **Format & Post**: Generates formatted markdown comment and posts/updates on PR

## Graceful Degradation

If Claude API fails, PR Agent falls back to pattern-based analysis:
- Still detects common security issues
- Still identifies breaking changes
- Posts partial analysis with warning

## Large PR Handling

For PRs with many files:
- Prioritizes security-sensitive files (auth, crypto, API)
- Truncates large diffs
- Adds warning to comment
- Ensures analysis completes within reasonable time

## Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/pr-agent.git
cd pr-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing
```

### Run Locally

```bash
# Set environment variables
export GITHUB_TOKEN=your_github_token
export ANTHROPIC_API_KEY=your_api_key
export GITHUB_REPOSITORY=owner/repo
export GITHUB_EVENT_NUMBER=123  # PR number

# Run analysis
python -m src.main
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_analyzer.py -v
```

## Architecture

```
pr-agent/
├── src/
│   ├── main.py                      # Entry point
│   ├── config/
│   │   └── settings.py              # Configuration management
│   ├── github_client/
│   │   ├── client.py                # GitHub API wrapper
│   │   └── models.py                # Data models
│   ├── analysis/
│   │   ├── analyzer.py              # Main orchestrator
│   │   ├── diff_processor.py        # File processing
│   │   └── risk_detector.py         # Pattern-based detection
│   ├── ai/
│   │   ├── claude_client.py         # Claude API integration
│   │   └── prompts.py               # AI prompts
│   ├── formatters/
│   │   └── comment_formatter.py     # Markdown generation
│   └── utils/
│       ├── logger.py                # Logging setup
│       └── exceptions.py            # Custom exceptions
├── tests/                           # Test suite
├── action.yml                       # GitHub Action definition
└── .pr-agent.yml.example           # Example configuration
```

## Security Patterns Detected

- SQL injection (string concatenation in queries)
- XSS vulnerabilities (innerHTML usage)
- Hardcoded secrets (passwords, API keys, tokens)
- Unsafe deserialization (pickle, unsafe YAML)
- Command injection (os.system, shell=True)
- Weak cryptography (MD5, SHA-1)
- Eval usage

## Troubleshooting

### "No ANTHROPIC_API_KEY"

Make sure you've added the API key to repository secrets.

### "Failed to fetch PR"

Check that `GITHUB_TOKEN` has `pull-requests: write` permission.

### "Rate limit exceeded"

Claude API has rate limits. The action includes retry logic with exponential backoff.

### Large PRs timeout

Increase `max_files_full_analysis` or reduce `max_diff_size_per_file` in config.

### AI analysis disabled

Check that `ANTHROPIC_API_KEY` is set correctly. PR Agent will still work with pattern-based analysis.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure tests pass: `pytest tests/`
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [Anthropic's Claude API](https://www.anthropic.com/)
- Uses [PyGithub](https://github.com/PyGithub/PyGithub) for GitHub integration
- Inspired by various PR automation tools

## Support

- Report issues: [GitHub Issues](https://github.com/yourusername/pr-agent/issues)
- Documentation: [Wiki](https://github.com/yourusername/pr-agent/wiki)
