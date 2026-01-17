#!/bin/bash

# Setup script for PR Agent test repository
# This script helps you quickly set up a test repository

set -e

echo "🤖 PR Agent Test Repository Setup"
echo "=================================="
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Get GitHub username
echo "Enter your GitHub username:"
read GITHUB_USERNAME

# Repository name
REPO_NAME="pr-agent-test"

echo ""
echo "Creating repository: $GITHUB_USERNAME/$REPO_NAME"
echo ""

# Create repository
gh repo create $REPO_NAME --public --clone --gitignore Python --license MIT

cd $REPO_NAME

echo ""
echo "✅ Repository created and cloned"
echo ""

# Create workflow directory
mkdir -p .github/workflows

# Create PR Agent workflow
cat > .github/workflows/pr-agent.yml << 'EOF'
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
          repository: GITHUB_USERNAME/pr-agent
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
EOF

# Replace GITHUB_USERNAME in workflow
sed -i.bak "s/GITHUB_USERNAME/$GITHUB_USERNAME/g" .github/workflows/pr-agent.yml
rm .github/workflows/pr-agent.yml.bak

# Commit workflow
git add .github/workflows/pr-agent.yml
git commit -m "Add PR Agent workflow"
git push origin main

echo ""
echo "✅ PR Agent workflow added"
echo ""

echo "📝 Next steps:"
echo ""
echo "1. Add your Anthropic API key to repository secrets:"
echo "   gh secret set ANTHROPIC_API_KEY --repo $GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "2. Or visit: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/secrets/actions"
echo ""
echo "3. Create a test branch with security issues:"
echo "   cd $REPO_NAME"
echo "   git checkout -b test/security-issues"
echo "   # Copy test files from pr-agent/test_files/"
echo "   git add ."
echo "   git commit -m 'Add test files with security issues'"
echo "   git push origin test/security-issues"
echo ""
echo "4. Create a Pull Request:"
echo "   gh pr create --title 'Test PR with security issues' --body 'Testing PR Agent'"
echo ""
echo "Done! 🎉"
