# ✅ PR Agent Testing Checklist

## Quick 5-Minute Test

Follow these steps exactly:

### 1️⃣ Push PR Agent to GitHub (2 minutes)

```bash
cd /Users/saiabhishek/Documents/AIENGINNERING/pr-agent

# Login to GitHub if needed
gh auth login

# Create and push repository
git init
git add .
git commit -m "Initial commit: PR Agent"
gh repo create pr-agent --public --source=. --push
```

**✅ Verify:** Visit https://github.com/YOUR_USERNAME/pr-agent

---

### 2️⃣ Create Test Repository (1 minute)

```bash
# Create test repo
gh repo create pr-agent-test --public --clone
cd pr-agent-test

# Add README
echo "# PR Agent Test" > README.md
git add README.md
git commit -m "Initial commit"
git push origin main
```

**✅ Verify:** Visit https://github.com/YOUR_USERNAME/pr-agent-test

---

### 3️⃣ Add PR Agent Workflow (1 minute)

```bash
# Create workflow directory
mkdir -p .github/workflows

# Create workflow (replace YOUR_USERNAME with your GitHub username!)
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
      - uses: actions/checkout@v4
        with:
          repository: YOUR_USERNAME/pr-agent
          ref: main
          path: pr-agent
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: cd pr-agent && pip install -r requirements.txt
      - name: Run PR Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_EVENT_NUMBER: ${{ github.event.pull_request.number }}
        run: cd pr-agent && python -m src.main
EOF

# IMPORTANT: Replace YOUR_USERNAME with your actual GitHub username
# Example: sed -i '' 's/YOUR_USERNAME/johndoe/g' .github/workflows/pr-agent.yml
nano .github/workflows/pr-agent.yml  # Or use your preferred editor

# Commit workflow
git add .github/workflows/
git commit -m "Add PR Agent workflow"
git push origin main
```

**✅ Verify:** File exists at `.github/workflows/pr-agent.yml` with correct username

---

### 4️⃣ Add Anthropic API Key (30 seconds)

```bash
# Set secret (you'll be prompted to paste your API key)
gh secret set ANTHROPIC_API_KEY --repo YOUR_USERNAME/pr-agent-test
```

**Or manually:**
1. Go to: https://github.com/YOUR_USERNAME/pr-agent-test/settings/secrets/actions
2. Click "New repository secret"
3. Name: `ANTHROPIC_API_KEY`
4. Value: Your API key from https://console.anthropic.com/
5. Click "Add secret"

**✅ Verify:**
```bash
gh secret list --repo YOUR_USERNAME/pr-agent-test
# Should show: ANTHROPIC_API_KEY
```

---

### 5️⃣ Create Test PR with Security Issues (1 minute)

```bash
# Create test branch
git checkout -b test/security-issues

# Create test file with security vulnerabilities
cat > app.py << 'EOF'
import sqlite3
import os

# Hardcoded secret - should be detected!
API_KEY = "sk_live_1234567890abcdef"
PASSWORD = "admin123"

# SQL Injection - should be detected!
def get_user(user_id):
    conn = sqlite3.connect('db.sqlite')
    query = "SELECT * FROM users WHERE id = " + user_id
    return conn.execute(query)

# Command Injection - should be detected!
def run_cmd(filename):
    os.system("cat " + filename)

# Weak crypto - should be detected!
import hashlib
def hash_pw(password):
    return hashlib.md5(password.encode()).hexdigest()
EOF

# Commit and push
git add app.py
git commit -m "Add test file with security vulnerabilities"
git push origin test/security-issues
```

---

### 6️⃣ Create Pull Request (30 seconds)

```bash
gh pr create \
  --title "Test: Security vulnerabilities for PR Agent" \
  --body "Testing PR Agent detection capabilities" \
  --base main \
  --head test/security-issues
```

**✅ Verify:** PR is created - note the URL printed

---

### 7️⃣ Watch PR Agent in Action! (30-60 seconds)

1. **Open the PR** in your browser (use the URL from previous step)
2. **Watch the "Checks" section** - you should see "PR Agent Analysis" appear
3. **Wait 30-60 seconds** for the analysis to complete
4. **Look for the comment** from PR Agent

---

## Expected Result ✨

You should see a comment like this:

```markdown
## 🤖 PR Analysis

### Summary
This PR introduces authentication functionality with several security
vulnerabilities that need to be addressed...

### Key Files Changed
| File | Changes | Impact |
|------|---------|--------|
| 📝 `app.py` | +18, -0 | High |

### Risk Analysis

#### 🔒 Security
- **HIGH**: Hardcoded API key detected
  - File: `app.py:6`
  - Suggestion: Use environment variables for sensitive data

- **HIGH**: Hardcoded password detected
  - File: `app.py:7`
  - Suggestion: Use environment variables for sensitive data

- **HIGH**: Potential SQL injection
  - File: `app.py:12`
  - Suggestion: Use parameterized queries

- **MEDIUM**: MD5 is cryptographically weak
  - File: `app.py:20`
  - Suggestion: Use SHA-256 or stronger

#### ⚠️ Breaking Changes
[If any detected]

### Review Focus Areas
- [ ] Replace all hardcoded secrets with environment variables
- [ ] Fix SQL injection vulnerability
- [ ] Upgrade from MD5 to SHA-256

---
*Analysis generated on ... | Powered by Claude AI*
```

---

## Success Criteria ✅

Check all that apply:

- [ ] GitHub Action "PR Agent Analysis" appears in PR checks
- [ ] Action completes successfully (green checkmark)
- [ ] PR Agent posts a comment on the PR
- [ ] Comment includes "🤖 PR Analysis" header
- [ ] Hardcoded API_KEY is detected (HIGH risk)
- [ ] Hardcoded PASSWORD is detected (HIGH risk)
- [ ] SQL injection is detected (HIGH risk)
- [ ] MD5 usage is detected (MEDIUM risk)
- [ ] AI-generated summary is present
- [ ] Review focus areas are listed
- [ ] Markdown formatting looks good

If all checked: **🎉 SUCCESS! Your PR Agent is working perfectly!**

---

## Troubleshooting

### ❌ Action doesn't run

**Check:**
```bash
# Verify workflow file
cat .github/workflows/pr-agent.yml | grep "YOUR_USERNAME"
# Should show your actual username, not "YOUR_USERNAME"
```

**Fix:**
```bash
# Edit and replace YOUR_USERNAME
nano .github/workflows/pr-agent.yml
git add .github/workflows/pr-agent.yml
git commit -m "Fix workflow username"
git push origin main
# Close and reopen PR
```

### ❌ "ANTHROPIC_API_KEY not set"

**Fix:**
```bash
gh secret set ANTHROPIC_API_KEY --repo YOUR_USERNAME/pr-agent-test
# Paste your API key when prompted
```

### ❌ Action fails with import errors

**Check PR Agent has all files:**
```bash
cd /Users/saiabhishek/Documents/AIENGINNERING/pr-agent
ls -la src/
# Should show all .py files and __init__.py files
```

### ❌ No comment appears

**Check logs:**
```bash
gh run list --repo YOUR_USERNAME/pr-agent-test
gh run view LATEST_RUN_ID --log
```

**Common fixes:**
- Make sure GitHub Actions is enabled in repository settings
- Check that workflow has `pull-requests: write` permission
- Verify ANTHROPIC_API_KEY is correct

---

## Quick Command Reference

```bash
# View PR
gh pr view --web

# View workflow runs
gh run list --repo YOUR_USERNAME/pr-agent-test

# View workflow logs
gh run view --log

# List secrets
gh secret list --repo YOUR_USERNAME/pr-agent-test

# Delete test repo (when done)
gh repo delete pr-agent-test --yes
```

---

## What's Next?

After successful testing:

1. **Add to Real Repos**: Use PR Agent in your actual projects
2. **Customize**: Create `.pr-agent.yml` config file
3. **Share**: Add PR Agent to team repositories
4. **Iterate**: Improve detection patterns as needed

---

## Need More Help?

- 📖 Full guide: `TESTING_GUIDE.md`
- 🚀 Quick start: `QUICKSTART_TEST.md`
- 📝 Main docs: `README.md`
- 🐛 Issues: GitHub Issues

**You're all set! Go test your PR Agent! 🚀**
