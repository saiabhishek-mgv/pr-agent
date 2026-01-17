# 🚀 Quick Start: Test Your PR Agent

The fastest way to test if your PR Agent is working correctly.

## Prerequisites

- GitHub account
- GitHub CLI installed: `brew install gh` (or from https://cli.github.com/)
- Anthropic API key (get from https://console.anthropic.com/)
- Git configured with your GitHub account

## Method 1: Automated Setup (Recommended)

### Step 1: Push PR Agent to GitHub

First, let's push your PR Agent code to GitHub:

```bash
cd /Users/saiabhishek/Documents/AIENGINNERING/pr-agent

# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: PR Agent implementation"

# Create GitHub repository and push
gh repo create pr-agent --public --source=. --remote=origin --push
```

### Step 2: Create Test Repository

Use the automated setup script:

```bash
# Run the setup script
./scripts/setup_test_repo.sh
```

This will:
- Create a new repository called `pr-agent-test`
- Add the PR Agent workflow
- Push to GitHub

### Step 3: Add Your Anthropic API Key

```bash
# Add your API key as a secret (you'll be prompted to paste it)
gh secret set ANTHROPIC_API_KEY --repo YOUR_USERNAME/pr-agent-test
```

Or manually:
1. Go to https://github.com/YOUR_USERNAME/pr-agent-test/settings/secrets/actions
2. Click "New repository secret"
3. Name: `ANTHROPIC_API_KEY`
4. Paste your API key
5. Click "Add secret"

### Step 4: Create Test PR

```bash
cd pr-agent-test

# Use the automated script
../pr-agent/scripts/create_test_pr.sh
```

This will:
- Create a test branch
- Add files with security vulnerabilities
- Push to GitHub
- Create a Pull Request

### Step 5: Check Results

1. Go to the PR URL (printed by the script)
2. Wait 30-60 seconds for PR Agent to analyze
3. You should see a comment with detected security issues!

## Method 2: Manual Setup

### Step 1: Push PR Agent to GitHub

```bash
cd /Users/saiabhishek/Documents/AIENGINNERING/pr-agent

git init
git add .
git commit -m "Initial commit: PR Agent"
gh repo create pr-agent --public --source=. --push
```

### Step 2: Create Test Repository

```bash
# Create new repo
gh repo create pr-agent-test --public --clone
cd pr-agent-test

# Create workflow directory
mkdir -p .github/workflows

# Create workflow file
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
    steps:
      - name: Checkout PR Agent
        uses: actions/checkout@v4
        with:
          repository: YOUR_USERNAME/pr-agent  # Replace with your username
          ref: main
          path: pr-agent

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
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

# Replace YOUR_USERNAME with your actual GitHub username
sed -i '' 's/YOUR_USERNAME/your-actual-username/g' .github/workflows/pr-agent.yml

# Commit and push
git add .github/workflows/pr-agent.yml
git commit -m "Add PR Agent workflow"
git push origin main
```

### Step 3: Add API Key

```bash
gh secret set ANTHROPIC_API_KEY --repo your-username/pr-agent-test
# Paste your Anthropic API key when prompted
```

### Step 4: Create Test Files

```bash
# Create test branch
git checkout -b test/security-issues

# Copy test files
cp /Users/saiabhishek/Documents/AIENGINNERING/pr-agent/test_files/*.py .

# Commit and push
git add *.py
git commit -m "Add test files with security vulnerabilities"
git push origin test/security-issues
```

### Step 5: Create Pull Request

```bash
gh pr create \
  --title "Test: Security vulnerabilities" \
  --body "Testing PR Agent with intentional security issues" \
  --base main \
  --head test/security-issues
```

## Expected Results

After creating the PR, within 30-60 seconds you should see:

### ✅ GitHub Actions
- "PR Agent Analysis" workflow runs
- Status: ✓ Success (green checkmark)

### ✅ PR Comment
A formatted comment from PR Agent with:

```markdown
## 🤖 PR Analysis

### Summary
[AI-generated summary of changes]

### Key Files Changed
| File | Changes | Impact |
|------|---------|--------|
| 📝 app.py | +X, -Y | High |
| ...

### Risk Analysis

#### 🔒 Security
- **HIGH**: Hardcoded API key detected
  - File: app.py:6
  - Suggestion: Use environment variables

[More security issues...]

#### ⚡ Performance
- **MEDIUM**: N+1 query pattern detected
  [...]

### Review Focus Areas
- [ ] Replace hardcoded secrets
- [ ] Fix SQL injection
- [...]
```

## Verification Checklist

✅ Repository created
✅ PR Agent workflow added
✅ ANTHROPIC_API_KEY secret set
✅ Test PR created
✅ GitHub Action runs successfully
✅ PR comment posted within 60 seconds
✅ Security issues detected:
  - Hardcoded secrets (3 instances)
  - SQL injection (1 instance)
  - Command injection (1 instance)
  - XSS vulnerability (1 instance)
  - Unsafe eval (1 instance)
  - Weak crypto (MD5)
  - Unsafe deserialization (pickle)
✅ Performance issues detected:
  - N+1 queries
  - Large loops
✅ AI summary generated
✅ Review focus areas listed

## Troubleshooting

### Issue: Workflow doesn't run

**Check:**
```bash
# Verify workflow file exists
ls -la .github/workflows/

# Check workflow syntax
cat .github/workflows/pr-agent.yml

# Check Actions are enabled
gh api repos/YOUR_USERNAME/pr-agent-test/actions/permissions
```

### Issue: "ANTHROPIC_API_KEY not found"

**Solution:**
```bash
# List secrets
gh secret list --repo YOUR_USERNAME/pr-agent-test

# Re-add the secret
gh secret set ANTHROPIC_API_KEY --repo YOUR_USERNAME/pr-agent-test
```

### Issue: No comment posted

**Check logs:**
```bash
# View recent workflow runs
gh run list --repo YOUR_USERNAME/pr-agent-test

# View specific run
gh run view RUN_ID --log
```

**Common causes:**
- API key is invalid
- GitHub token lacks permissions
- Python dependencies failed to install
- PR Agent code has errors

### Issue: "Module not found" errors

**Solution:**
Make sure all __init__.py files exist in your PR Agent repo:
```bash
cd /Users/saiabhishek/Documents/AIENGINNERING/pr-agent
find src -type d -exec touch {}/__init__.py \;
git add .
git commit -m "Add missing __init__.py files"
git push
```

## Testing Different Scenarios

### Test 1: Safe PR (No Issues)
```bash
git checkout -b test/safe-changes
echo "# Documentation" > README_NEW.md
git add README_NEW.md
git commit -m "Add documentation"
git push origin test/safe-changes
gh pr create --title "Safe PR" --body "No security issues"
```

Expected: "✅ No significant risks detected"

### Test 2: Without AI (Pattern-based only)
1. Remove ANTHROPIC_API_KEY temporarily
2. Create a new PR
3. Should still work with pattern-based detection
4. Re-add the key afterward

### Test 3: Large PR
Create a PR with 60+ files to test file prioritization

## Success! 🎉

If you see the PR Agent comment with detected security issues, congratulations! Your PR Agent is working perfectly.

## Next Steps

1. **Use in Real Projects**: Add PR Agent to your actual repositories
2. **Customize**: Create `.pr-agent.yml` with your preferences
3. **Share**: Share PR Agent with your team
4. **Monitor**: Keep an eye on Anthropic API usage

## Clean Up (Optional)

To remove test repository:
```bash
gh repo delete pr-agent-test --yes
```

## Need Help?

- Check logs: `gh run view --log`
- Review TESTING_GUIDE.md for detailed steps
- Check GitHub Actions tab in your repository
