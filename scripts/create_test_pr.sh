#!/bin/bash

# Script to create a test PR with security issues

set -e

echo "🤖 Creating Test PR for PR Agent"
echo "================================"
echo ""

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Get the PR Agent directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PR_AGENT_DIR="$(dirname "$SCRIPT_DIR")"

# Create new branch
BRANCH_NAME="test/security-issues-$(date +%s)"
echo "Creating branch: $BRANCH_NAME"
git checkout -b $BRANCH_NAME

# Copy test files
echo "Copying test files with security vulnerabilities..."
cp "$PR_AGENT_DIR/test_files/app.py" .
cp "$PR_AGENT_DIR/test_files/auth.py" .
cp "$PR_AGENT_DIR/test_files/database.py" .

# Add and commit
git add app.py auth.py database.py
git commit -m "Add test files with security vulnerabilities

This PR contains intentional security issues for testing:
- Hardcoded secrets (API keys, passwords)
- SQL injection vulnerabilities
- Command injection
- XSS vulnerabilities
- Weak cryptography (MD5)
- Unsafe deserialization (pickle)
- Performance issues (N+1 queries)
"

# Push
echo "Pushing to remote..."
git push origin $BRANCH_NAME

# Create PR
echo ""
echo "Creating Pull Request..."
gh pr create \
  --title "Test: Security vulnerabilities for PR Agent testing" \
  --body "This PR contains intentional security vulnerabilities to test PR Agent detection:

## Expected Detections

### Security Issues
- 🔴 Hardcoded API_KEY in app.py
- 🔴 Hardcoded DATABASE_PASSWORD in app.py
- 🔴 SQL injection in get_user() function
- 🔴 Command injection in run_command()
- 🔴 XSS vulnerability in display_user_input()
- 🔴 Unsafe eval() usage
- 🔴 Unsafe YAML loading
- 🔴 Unsafe pickle deserialization
- 🟡 Weak MD5 hashing

### Performance Issues
- 🟡 N+1 query pattern
- 🟡 Large loop without pagination

### Breaking Changes
- 🟡 Changed method signature (username → email)

PR Agent should detect and report all of these issues.
" \
  --base main \
  --head $BRANCH_NAME

echo ""
echo "✅ Test PR created successfully!"
echo ""
echo "🔍 Check the PR for PR Agent analysis (this may take 30-60 seconds)"
echo ""
