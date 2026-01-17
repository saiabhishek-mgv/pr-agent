# Contributing to PR Agent

Thank you for your interest in contributing to PR Agent! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- GitHub account
- Anthropic API key (for testing AI features)

### Local Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/yourusername/pr-agent.git
cd pr-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
export GITHUB_TOKEN=your_github_token
export ANTHROPIC_API_KEY=your_api_key
```

## Development Workflow

### Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_analyzer.py -v
```

### Code Quality

Format code with Black:
```bash
black src/ tests/
```

Lint with Ruff:
```bash
ruff check src/ tests/
```

Type check with mypy:
```bash
mypy src/
```

Run all quality checks:
```bash
black src/ tests/
ruff check src/ tests/
mypy src/
pytest tests/ --cov=src
```

## Project Structure

```
pr-agent/
├── src/
│   ├── main.py              # Entry point
│   ├── config/              # Configuration management
│   ├── github_client/       # GitHub API integration
│   ├── analysis/            # Analysis logic
│   ├── ai/                  # AI integration
│   ├── formatters/          # Output formatting
│   └── utils/               # Utilities
├── tests/                   # Test suite
└── .github/workflows/       # CI/CD
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Use prefixes:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `test/` - Test improvements
- `refactor/` - Code refactoring

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add docstrings to functions and classes
- Update tests for your changes
- Update documentation if needed

### 3. Test Your Changes

```bash
# Run tests
pytest tests/ -v

# Check code quality
black src/ tests/
ruff check src/ tests/
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add support for custom risk patterns"
```

Commit message prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference any related issues
- Include screenshots if applicable
- Ensure CI checks pass

## Adding New Features

### Adding a New Risk Pattern

1. Add pattern to `src/analysis/risk_detector.py`:
```python
SECURITY_PATTERNS = [
    # ... existing patterns ...
    (r'your_pattern', RiskLevel.HIGH, "Title", "Suggestion"),
]
```

2. Add test in `tests/test_risk_detector.py`:
```python
def test_detect_your_pattern(self, risk_detector):
    file = FileChange(
        filename="test.py",
        patch="+vulnerable code here"
    )
    risks = risk_detector.detect_security_risks([file])
    assert len(risks) > 0
```

### Adding a New AI Prompt

1. Add prompt to `src/ai/prompts.py`:
```python
NEW_PROMPT = """Your prompt template here
{variable_1}
{variable_2}
"""
```

2. Add method to `src/ai/claude_client.py`:
```python
def new_analysis(self, data):
    prompt = NEW_PROMPT.format(variable_1=data.var1)
    return self._call_claude(prompt)
```

### Adding Configuration Options

1. Add to models in `src/config/settings.py`:
```python
class AnalysisConfig(BaseModel):
    # ... existing config ...
    new_option: bool = True
```

2. Update `.pr-agent.yml.example`

3. Update README.md with new option

## Testing Guidelines

### Writing Tests

- One test file per source file
- Use descriptive test names
- Test both success and failure cases
- Mock external API calls
- Aim for >80% code coverage

### Test Structure

```python
import pytest
from src.module import YourClass

@pytest.fixture
def your_fixture():
    """Create test fixture."""
    return YourClass()

class TestYourClass:
    """Test YourClass functionality."""

    def test_success_case(self, your_fixture):
        """Test successful operation."""
        result = your_fixture.method()
        assert result is not None

    def test_failure_case(self, your_fixture):
        """Test error handling."""
        with pytest.raises(Exception):
            your_fixture.method(invalid_input)
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description.

    Detailed description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When input is invalid
    """
    pass
```

### Updating Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples for new features
- Update configuration documentation

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Code is formatted (black)
- [ ] Linting passes (ruff)
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] No new warnings
```

## Code Review Process

1. Maintainer reviews PR
2. Address feedback
3. CI checks must pass
4. At least one approval required
5. Maintainer merges

## Release Process

1. Update version in `setup.py` and `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. GitHub Actions publishes release

## Getting Help

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and discussions
- Discord: Real-time chat (coming soon)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Follow GitHub's Community Guidelines

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to PR Agent!
