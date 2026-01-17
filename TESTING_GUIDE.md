# PR Agent Testing Guide

Complete guide to test your PR Agent installation.

## Prerequisites

- GitHub account
- Anthropic API key (get from https://console.anthropic.com/)
- Git installed locally

## Step 1: Create Test Repository on GitHub

### Option A: Using GitHub Web Interface

1. Go to https://github.com/new
2. Repository name: `pr-agent-test`
3. Description: "Test repository for PR Agent"
4. Visibility: Public (or Private with appropriate permissions)
5. ✅ Check "Add a README file"
6. ✅ Check "Add .gitignore" → Select "Python"
7. Click "Create repository"

### Option B: Using GitHub CLI

```bash
# Install GitHub CLI if needed: https://cli.github.com/
gh repo create pr-agent-test --public --clone --gitignore Python --license MIT
cd pr-agent-test
```

## Step 2: Add PR Agent to Your Test Repository

### 2.1: Clone Your Test Repository

```bash
cd ~/Documents
git clone https://github.com/YOUR_USERNAME/pr-agent-test.git
cd pr-agent-test
```

### 2.2: Copy PR Agent Files

```bash
# Create necessary directories
mkdir -p .github/workflows

# Copy the PR Agent workflow
cp /Users/saiabhishek/Documents/AIENGINNERING/pr-agent/.github/workflows/pr-agent.yml .github/workflows/

# Optional: Copy example config
cp /Users/saiabhishek/Documents/AIENGINNERING/pr-agent/.pr-agent.yml.example .pr-agent.yml
```

### 2.3: Update Workflow to Use Your PR Agent

Edit `.github/workflows/pr-agent.yml`:

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
    name: Analyze Pull Request

    steps:
      - name: Checkout PR Agent
        uses: actions/checkout@v4
        with:
          repository: YOUR_USERNAME/pr-agent  # Your PR Agent repo
          ref: main
          path: pr-agent

      - name: Checkout PR code
        uses: actions/checkout@v4
        with:
          path: repo

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install PR Agent dependencies
        run: |
          cd pr-agent
          pip install -r requirements.txt

      - name: Run PR Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_EVENT_NUMBER: ${{ github.event.pull_request.number }}
        run: |
          cd pr-agent
          python -m src.main
```

### 2.4: Commit and Push Workflow

```bash
git add .github/workflows/pr-agent.yml
git commit -m "Add PR Agent workflow"
git push origin main
```

## Step 3: Add Anthropic API Key to Repository Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `ANTHROPIC_API_KEY`
5. Value: Your Anthropic API key
6. Click **Add secret**

## Step 4: Create Test Files with Intentional Issues

### 4.1: Create a New Branch

```bash
git checkout -b test/security-issues
```

### 4.2: Create Test Python Files

Create `app.py` with security issues:

```python
# app.py - Contains intentional security vulnerabilities for testing

import os
import sqlite3

# Security Issue 1: Hardcoded secrets
API_KEY = "sk_live_1234567890abcdef"
DATABASE_PASSWORD = "admin123"
SECRET_TOKEN = "my_secret_token_12345"

# Security Issue 2: SQL Injection vulnerability
def get_user(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Vulnerable to SQL injection
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return cursor.fetchone()

# Security Issue 3: Command injection
def run_command(filename):
    # Vulnerable to command injection
    os.system("cat " + filename)

# Security Issue 4: Using MD5 (weak crypto)
import hashlib
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# Performance Issue: N+1 query pattern
def get_all_user_posts():
    users = User.objects.all()
    for user in users:
        posts = Post.objects.filter(user=user)  # N+1 problem
        print(posts)

# Breaking change: Removing a public method
# def old_authenticate(username, password):
#     # This method was removed - breaking change!
#     pass

# New authentication method with different signature
def authenticate(email, password, remember_me=False):
    # Changed from username to email - breaking change
    pass
```

Create `auth.py`:

```python
# auth.py - Authentication module with issues

from flask import request

# Security Issue: XSS vulnerability
def display_user_input():
    user_input = request.args.get('name')
    # Vulnerable to XSS
    return f"<div>{user_input}</div>"

# Security Issue: Using eval
def calculate(expression):
    # Dangerous use of eval
    return eval(expression)

# Security Issue: Unsafe YAML loading
import yaml
def load_config(config_file):
    with open(config_file) as f:
        # Should use yaml.safe_load()
        return yaml.load(f)
```

Create `database.py`:

```python
# database.py - Database operations

import pickle

# Security Issue: Unsafe deserialization
def load_user_session(session_data):
    # Vulnerable to arbitrary code execution
    return pickle.loads(session_data)

# Performance Issue: Large loop without pagination
def process_all_records():
    for i in range(10000):  # Large iteration
        process_record(i)

def process_record(i):
    pass
```

### 4.3: Commit and Push

```bash
git add app.py auth.py database.py
git commit -m "Add test files with security vulnerabilities"
git push origin test/security-issues
```

## Step 5: Create a Pull Request

### Option A: Using GitHub Web Interface

1. Go to your repository on GitHub
2. You should see a banner "Compare & pull request"
3. Click it
4. Title: "Test PR with security issues"
5. Description: "This PR contains intentional security vulnerabilities to test PR Agent"
6. Click "Create pull request"

### Option B: Using GitHub CLI

```bash
gh pr create \
  --title "Test PR with security issues" \
  --body "This PR contains intentional security vulnerabilities to test PR Agent:
  - Hardcoded secrets
  - SQL injection
  - XSS vulnerabilities
  - Weak cryptography
  - Performance issues" \
  --base main \
  --head test/security-issues
```

## Step 6: Verify PR Agent is Working

### 6.1: Check GitHub Actions

1. Go to your PR on GitHub
2. Scroll to the checks section at the bottom
3. You should see "PR Agent Analysis" running
4. Click "Details" to see logs

### 6.2: Wait for Analysis

The PR Agent will:
1. Fetch PR data
2. Analyze files
3. Detect security issues
4. Call Claude API for AI analysis
5. Post a comment on the PR

This typically takes 30-60 seconds.

### 6.3: Check the PR Comment

You should see a comment like this:

```markdown
## 🤖 PR Analysis

### Summary
This PR introduces authentication and database functionality but contains several
critical security vulnerabilities that must be addressed before merging.

### Key Files Changed
| File | Changes | Impact |
|------|---------|--------|
| 📝 `app.py` | +45, -0 | High |
| 📝 `auth.py` | +20, -0 | High |
| 📝 `database.py` | +15, -0 | Medium |

### Risk Analysis

#### 🔒 Security
- **HIGH**: Hardcoded API key detected
  - File: `app.py:6`
  - Suggestion: Use environment variables for sensitive data

- **HIGH**: Hardcoded password detected
  - File: `app.py:7`
  - Suggestion: Use environment variables for sensitive data

- **HIGH**: Potential SQL injection
  - File: `app.py:14`
  - Suggestion: Use parameterized queries instead of string concatenation

- **HIGH**: Using eval() - security risk
  - File: `auth.py:12`
  - Suggestion: Avoid eval(), use safer alternatives like JSON.parse()

- **HIGH**: Unsafe deserialization with pickle
  - File: `database.py:7`
  - Suggestion: Use safer serialization formats like JSON

- **MEDIUM**: MD5 is cryptographically weak
  - File: `app.py:22`
  - Suggestion: Use SHA-256 or stronger hash algorithms

- **MEDIUM**: Potential XSS via innerHTML
  - File: `auth.py:8`
  - Suggestion: Use textContent or sanitize input

#### ⚡ Performance
- **MEDIUM**: Large loop iteration
  - File: `database.py:12`
  - Suggestion: Consider pagination or batch processing

### Review Focus Areas
- [ ] Replace all hardcoded secrets with environment variables
- [ ] Fix SQL injection vulnerability in user query
- [ ] Remove eval() usage and use safer alternatives
- [ ] Switch from pickle to JSON for serialization
- [ ] Upgrade from MD5 to SHA-256 for password hashing
- [ ] Add XSS protection for user input display

---
*Analysis generated on 2026-01-17 14:30:00 UTC | Powered by Claude AI*
```

## Step 7: Verify Detection Results

Check that PR Agent detected:

✅ **Security Issues:**
- Hardcoded API_KEY
- Hardcoded DATABASE_PASSWORD
- SQL injection in `get_user()`
- Command injection in `run_command()`
- XSS vulnerability in `display_user_input()`
- Unsafe eval usage
- Unsafe YAML loading
- Unsafe pickle deserialization
- Weak MD5 hashing

✅ **Performance Issues:**
- N+1 query pattern
- Large loop without pagination

✅ **Breaking Changes:**
- Changed method signature (username → email)

## Step 8: Test AI Features

Create another test PR without the Anthropic API key to test graceful degradation:

1. Remove the `ANTHROPIC_API_KEY` secret temporarily
2. Create another branch with changes
3. Open a PR
4. Verify PR Agent still works with pattern-based analysis only
5. Add the API key back

## Troubleshooting

### Issue: PR Agent doesn't run

**Check:**
- Workflow file is in `.github/workflows/`
- Workflow is valid YAML
- Repository has Actions enabled (Settings → Actions)

### Issue: "ANTHROPIC_API_KEY not set"

**Solution:**
- Verify secret name is exactly `ANTHROPIC_API_KEY`
- Check secret was added to correct repository
- Try re-adding the secret

### Issue: "Failed to fetch PR"

**Solution:**
- Check workflow has `pull-requests: write` permission
- Verify `GITHUB_TOKEN` has correct permissions

### Issue: Comment not posted

**Check GitHub Actions logs:**
```bash
# View workflow runs
gh run list --workflow=pr-agent.yml

# View specific run logs
gh run view RUN_ID --log
```

## Testing Checklist

- [ ] Repository created
- [ ] PR Agent workflow added
- [ ] Anthropic API key added to secrets
- [ ] Test PR created with security issues
- [ ] GitHub Action runs successfully
- [ ] PR Agent posts comment
- [ ] Security issues detected
- [ ] Performance issues detected
- [ ] AI summary generated
- [ ] Review focus areas listed

## Next Steps

Once testing is successful:

1. **Publish PR Agent**: Push your pr-agent repo to GitHub
2. **Use in Real Projects**: Add PR Agent to your actual repositories
3. **Customize Configuration**: Adjust `.pr-agent.yml` for your needs
4. **Monitor Usage**: Check Anthropic API usage and costs

## Test Variations

### Test 1: Small, Safe PR
- Create PR with documentation changes only
- Should result in "No significant risks detected"

### Test 2: Large PR
- Create PR with 60+ files
- Should trigger file prioritization warning

### Test 3: No Tests Added
- Modify source files without test changes
- Should detect test coverage gaps

### Test 4: Breaking Changes
- Remove or rename public methods
- Should detect breaking changes

## Clean Up

After testing:

```bash
# Delete test repository
gh repo delete pr-agent-test --yes

# Or keep it for future testing
```

## Success Criteria

Your PR Agent is working correctly if:

1. ✅ GitHub Action completes without errors
2. ✅ Comment appears on the PR
3. ✅ Security vulnerabilities are detected
4. ✅ AI summary is generated (when API key is set)
5. ✅ Review focus areas are listed
6. ✅ Markdown formatting looks good
7. ✅ Comment updates instead of creating duplicates

Congratulations! Your PR Agent is now operational! 🎉
