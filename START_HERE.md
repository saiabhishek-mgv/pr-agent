# 🚀 START HERE - Test Your PR Agent in 5 Minutes

## Copy-Paste Commands (Replace YOUR_USERNAME with your GitHub username)

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
gh repo create pr-agent-test --public --clone
cd pr-agent-test
echo "# PR Agent Test" > README.md
git add README.md
git commit -m "Initial commit"
git push origin main
```

### Step 3: Add Workflow

```bash
mkdir -p .github/workflows
```

Create `.github/workflows/pr-agent.yml` with this content (⚠️ Replace YOUR_USERNAME!):

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
        with:
          repository: YOUR_USERNAME/pr-agent  # ⚠️ CHANGE THIS
          ref: main
          path: pr-agent
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: cd pr-agent && pip install -r requirements.txt
      - env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_EVENT_NUMBER: ${{ github.event.pull_request.number }}
        run: cd pr-agent && python -m src.main
```

Then:

```bash
git add .github/workflows/
git commit -m "Add PR Agent workflow"
git push origin main
```

### Step 4: Add Your API Key

```bash
gh secret set ANTHROPIC_API_KEY --repo YOUR_USERNAME/pr-agent-test
# Paste your API key from https://console.anthropic.com/
```

### Step 5: Create Test PR

```bash
git checkout -b test/security-issues

cat > app.py << 'EOF'
import sqlite3
API_KEY = "sk_live_1234567890"  # Hardcoded secret - will be detected!
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id  # SQL injection!
    return sqlite3.connect('db').execute(query)
EOF

git add app.py
git commit -m "Add test file"
git push origin test/security-issues

gh pr create --title "Test PR" --body "Testing PR Agent"
```

### Step 6: Check Results

```bash
gh pr view --web
# Wait 30-60 seconds, then refresh the page
# You should see a PR Agent comment with detected security issues!
```

---

## Expected Output

Within 60 seconds, you should see:

✅ **GitHub Actions check**: "PR Agent Analysis" ✓
✅ **Comment on PR** with:
- 🤖 PR Analysis header
- Security issues detected (hardcoded secret, SQL injection)
- AI-generated summary
- Review focus areas

---

## Troubleshooting

**Action doesn't run?**
→ Make sure you replaced YOUR_USERNAME in the workflow file

**"ANTHROPIC_API_KEY not set"?**
→ Run: `gh secret set ANTHROPIC_API_KEY --repo YOUR_USERNAME/pr-agent-test`

**Import errors?**
→ Check all files pushed: `gh repo view YOUR_USERNAME/pr-agent`

**View logs:**
```bash
gh run list --repo YOUR_USERNAME/pr-agent-test
gh run view --log
```

---

## 🎉 Success?

If you see the PR Agent comment → **Congratulations! It works!**

Now you can:
1. Add PR Agent to your real repositories
2. Customize with `.pr-agent.yml`
3. Check the full docs in `README.md`

---

## Full Documentation

- 📋 **Quick Checklist**: `TEST_CHECKLIST.md`
- 📖 **Detailed Guide**: `TESTING_GUIDE.md`
- 🚀 **Quick Start**: `QUICKSTART_TEST.md`
- 📚 **Main Docs**: `README.md`

**Go test it now! 🚀**
