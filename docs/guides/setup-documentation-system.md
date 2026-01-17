# Setup Documentation System

Quick guide to set up the automated documentation system for Contracts-AI.

## One-Time Setup

### 1. Install Pre-Commit Hook

From the repository root:

```bash
# Make the hook executable
chmod +x .claude/hooks/pre-commit

# Copy to git hooks directory
cp .claude/hooks/pre-commit .git/hooks/pre-commit

# Verify installation
ls -la .git/hooks/pre-commit
```

**Expected output**:
```
-rwxr-xr-x  1 user  staff  3845 Jan 17 12:00 .git/hooks/pre-commit
```

### 2. Verify Documentation Structure

The documentation system should have created:

```bash
# Check directory structure
ls -la docs/
```

**Expected**:
```
docs/
├── README.md
├── api/
│   └── chat.md
├── features/
│   └── chat-interface.md
├── guides/
│   ├── documentation-workflow.md
│   └── setup-documentation-system.md
└── templates/
    ├── API_TEMPLATE.md
    └── FEATURE_TEMPLATE.md
```

### 3. Verify CHANGELOG.md Exists

```bash
# Check for changelog
cat CHANGELOG.md
```

If it doesn't exist, it will be created automatically on your next commit.

## Test the System

### Test 1: Make a Small Change

```bash
# Edit a file
echo "// Test comment" >> frontend/src/App.jsx

# Stage the change
git add frontend/src/App.jsx

# Try to commit (hook will run)
git commit -m "Test documentation system"
```

**Expected output**:
```
📚 Documentation Agent - Pre-Commit Check
==========================================

📋 Analyzing staged files...

  • Frontend: frontend/src/App.jsx

📊 Summary:
  Frontend files: 1
  Backend files: 0
  Documentation files: 0

⚠️  Warning: Code changes detected but CHANGELOG.md not updated
   Consider documenting this change in CHANGELOG.md

✅ Documentation checks completed
```

### Test 2: Commit with Documentation

```bash
# Update changelog
vim CHANGELOG.md
# Add: - Test documentation system

# Stage both
git add frontend/src/App.jsx CHANGELOG.md

# Commit (should pass cleanly)
git commit -m "Test documentation system"
```

**Expected output**:
```
📚 Documentation Agent - Pre-Commit Check
==========================================

📋 Analyzing staged files...

  • Frontend: frontend/src/App.jsx
  • Documentation: CHANGELOG.md

📊 Summary:
  Frontend files: 1
  Backend files: 0
  Documentation files: 1

✅ Documentation checks completed

📌 Remember to:
  • Add meaningful commit messages
  • Document complex logic with comments
  • Update CHANGELOG.md for notable changes
```

### Test 3: Undo Test Changes

```bash
# Reset the test changes
git reset HEAD~1
git checkout frontend/src/App.jsx
```

## Usage Workflow

### For New Features

1. Create feature documentation:
```bash
cp docs/templates/FEATURE_TEMPLATE.md docs/features/my-feature.md
vim docs/features/my-feature.md
```

2. Implement the feature:
```bash
vim frontend/src/App.jsx
```

3. Update changelog:
```bash
vim CHANGELOG.md
# Add under "### Added":
# - My new feature description
```

4. Commit:
```bash
git add frontend/src/App.jsx docs/features/my-feature.md CHANGELOG.md
git commit -m "feat: Add my new feature"
```

### For API Changes

1. Update API documentation:
```bash
cp docs/templates/API_TEMPLATE.md docs/api/my-endpoint.md
vim docs/api/my-endpoint.md
```

2. Implement backend changes:
```bash
vim backend/main.py
```

3. Update changelog:
```bash
vim CHANGELOG.md
```

4. Commit:
```bash
git add backend/main.py docs/api/my-endpoint.md CHANGELOG.md
git commit -m "feat: Add new API endpoint"
```

### For Bug Fixes

1. Fix the bug:
```bash
vim [file-to-fix]
```

2. Update changelog:
```bash
vim CHANGELOG.md
# Add under "### Fixed":
# - Bug description
```

3. Commit:
```bash
git add [file-to-fix] CHANGELOG.md
git commit -m "fix: Description of fix"
```

## Troubleshooting

### Hook Not Executing

**Problem**: Pre-commit hook doesn't run

**Check**:
```bash
# 1. Verify hook exists
ls .git/hooks/pre-commit

# 2. Check permissions
ls -la .git/hooks/pre-commit

# 3. Make executable if needed
chmod +x .git/hooks/pre-commit
```

### Hook Shows Errors

**Problem**: Bash errors when committing

**Check**:
```bash
# Verify correct shebang
head -1 .git/hooks/pre-commit
# Should show: #!/bin/bash

# Check for Windows line endings (CRLF)
file .git/hooks/pre-commit
# Should show: "Bourne-Again shell script, ASCII text executable"

# If CRLF detected, fix with:
dos2unix .git/hooks/pre-commit
# or
sed -i 's/\r$//' .git/hooks/pre-commit
```

### Want to Skip Hook

**Temporary bypass** (use sparingly):
```bash
git commit --no-verify -m "Emergency commit"

# Then add documentation later:
git add docs/
git commit -m "docs: Add missing documentation"
```

### Can't Find Templates

**Problem**: Template files not found

**Solution**:
```bash
# Verify you're in repository root
pwd
# Should show: /Users/[user]/Documents/VS Projects/Contracts-AI

# Check templates exist
ls docs/templates/
# Should show: API_TEMPLATE.md  FEATURE_TEMPLATE.md

# If missing, create them from:
# .claude/agents/documentation.md (contains template content)
```

## Uninstall (If Needed)

To remove the pre-commit hook:

```bash
# Remove the hook
rm .git/hooks/pre-commit

# Verify removal
ls .git/hooks/pre-commit
# Should show: No such file or directory
```

Documentation files remain and can be updated manually.

## Summary

✅ **One-time setup**: Install pre-commit hook
✅ **Every commit**: Hook runs automatically
✅ **Documentation**: Use templates from `docs/templates/`
✅ **Changelog**: Update for every notable change

The system is designed to be helpful, not restrictive. It reminds you to document but doesn't block commits if you need to push quickly.

---

**See Also**:
- [Documentation Workflow Guide](documentation-workflow.md)
- [Documentation Agent Specification](../../.claude/agents/documentation.md)
- [Pre-commit Hook Script](../../.claude/hooks/pre-commit)

**Last Updated**: 2026-01-17
