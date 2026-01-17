# Documentation Workflow Guide

This guide explains how to use the documentation system in the Contracts-AI project, including the automated documentation agent and pre-commit hooks.

## Overview

The Contracts-AI project uses an automated documentation agent to ensure all code changes are properly documented. The agent runs before every git commit to:

- Check for missing documentation
- Validate documentation completeness
- Create directory structure automatically
- Remind developers to update changelog

## Quick Start

### 1. Install Pre-Commit Hook

Run these commands from the repository root:

```bash
# Make the hook script executable
chmod +x .claude/hooks/pre-commit

# Copy to git hooks directory
cp .claude/hooks/pre-commit .git/hooks/pre-commit
```

Verify installation:
```bash
# Check if hook exists and is executable
ls -la .git/hooks/pre-commit
```

### 2. Make Your Changes

Work on your feature or bug fix as normal:

```bash
# Edit files
vim frontend/src/App.jsx

# Test your changes
npm run dev  # in frontend directory
```

### 3. Document Your Changes

Before committing, ensure you've documented your changes:

#### For New Features

Create feature documentation:
```bash
# Copy template
cp docs/templates/FEATURE_TEMPLATE.md docs/features/my-new-feature.md

# Edit the file and fill in details
vim docs/features/my-new-feature.md

# Stage the documentation
git add docs/features/my-new-feature.md
```

#### For API Changes

Create or update API documentation:
```bash
# Copy template
cp docs/templates/API_TEMPLATE.md docs/api/my-endpoint.md

# Edit the file
vim docs/api/my-endpoint.md

# Stage the documentation
git add docs/api/my-endpoint.md
```

#### Update CHANGELOG.md

Add your changes to the changelog:
```bash
# Edit CHANGELOG.md
vim CHANGELOG.md

# Add under [Unreleased] section:
# ### Added
# - Your new feature description
#
# ### Changed
# - What you modified
#
# ### Fixed
# - Bug you fixed

# Stage the changelog
git add CHANGELOG.md
```

### 4. Commit with Documentation

Stage your code changes and commit:

```bash
# Stage your changes
git add frontend/src/App.jsx
git add backend/main.py

# Commit (pre-commit hook will run automatically)
git commit -m "Add new feature: export chat history

- Added export button to chat interface
- Implemented JSON download functionality
- Updated UI styling for export button"
```

The pre-commit hook will:
1. Analyze your staged files
2. Check for documentation
3. Remind you if documentation is missing
4. Create docs structure if needed
5. Allow the commit to proceed

## Documentation Agent Features

### Automatic Checks

When you commit, the agent checks:

✅ **Frontend Changes**:
- App.jsx modifications → Feature docs recommended
- Complex UI logic → Code comments required

✅ **Backend Changes**:
- main.py modifications → API docs recommended
- New endpoints → API documentation required

✅ **Changelog**:
- Code changes → CHANGELOG.md update recommended

### Directory Auto-Creation

The agent automatically creates:
```
docs/
├── features/
├── api/
├── architecture/
└── guides/
```

### CHANGELOG Auto-Creation

If CHANGELOG.md doesn't exist, it's created automatically with proper structure.

## Documentation Workflow Examples

### Example 1: Adding Export Feature

```bash
# 1. Implement the feature
vim frontend/src/App.jsx

# 2. Create feature documentation
cp docs/templates/FEATURE_TEMPLATE.md docs/features/export-chat-history.md
vim docs/features/export-chat-history.md

# 3. Update changelog
vim CHANGELOG.md
# Add under "### Added":
# - Export chat history as JSON file with download functionality

# 4. Stage all changes
git add frontend/src/App.jsx
git add docs/features/export-chat-history.md
git add CHANGELOG.md

# 5. Commit
git commit -m "Add chat history export feature"

# Pre-commit hook runs and validates documentation
# ✅ All checks pass, commit succeeds
```

### Example 2: Modifying API Endpoint

```bash
# 1. Modify backend
vim backend/main.py

# 2. Update API documentation
vim docs/api/chat.md
# Update request/response formats, add new parameters

# 3. Update changelog
vim CHANGELOG.md
# Add under "### Changed":
# - Modified /api/chat to accept optional 'temperature' parameter

# 4. Stage and commit
git add backend/main.py docs/api/chat.md CHANGELOG.md
git commit -m "Add temperature parameter to chat endpoint"

# ✅ Documentation complete, commit proceeds
```

### Example 3: Bug Fix

```bash
# 1. Fix the bug
vim frontend/src/App.jsx

# 2. Update changelog (feature docs not needed for bug fixes)
vim CHANGELOG.md
# Add under "### Fixed":
# - Message input now clears properly after sending

# 3. Stage and commit
git add frontend/src/App.jsx CHANGELOG.md
git commit -m "Fix: Message input not clearing after send"

# ✅ Minimal documentation required, commit proceeds
```

## Pre-Commit Hook Output

### Successful Commit with Documentation

```
📚 Documentation Agent - Pre-Commit Check
==========================================

📋 Analyzing staged files...

  • Frontend: frontend/src/App.jsx
  • Documentation: docs/features/export-chat-history.md
  • Documentation: CHANGELOG.md

📊 Summary:
  Frontend files: 1
  Backend files: 0
  Documentation files: 2

✅ Documentation checks completed

📌 Remember to:
  • Add meaningful commit messages
  • Document complex logic with comments
  • Update CHANGELOG.md for notable changes
```

### Warning: Missing Documentation

```
📚 Documentation Agent - Pre-Commit Check
==========================================

📋 Analyzing staged files...

  • Frontend: frontend/src/App.jsx

📊 Summary:
  Frontend files: 1
  Backend files: 0
  Documentation files: 0

🔍 Checking documentation requirements...

⚠️  Warning: Code changes detected but CHANGELOG.md not updated
   Consider documenting this change in CHANGELOG.md

ℹ️  App.jsx modified - ensure feature documentation exists
   Location: docs/features/

📝 Documentation Recommendations:

  1. Update CHANGELOG.md with your changes
  2. Add feature docs in docs/features/ if adding new functionality
  3. Update docs/api/ if modifying endpoints
  4. Ensure code has appropriate comments

💡 Tip: You can commit now, but consider adding documentation

✅ Documentation checks completed
```

## Best Practices

### 1. Document as You Code

Don't wait until commit time. Create documentation while implementing:

```bash
# Good workflow:
# 1. Plan feature
# 2. Create docs/features/feature-name.md (from template)
# 3. Implement code
# 4. Fill in documentation as you go
# 5. Update tests section after testing
# 6. Commit everything together
```

### 2. Use Meaningful Commit Messages

Follow conventional commit format:

```bash
# Feature
git commit -m "feat: Add export chat history button"

# Bug fix
git commit -m "fix: Resolve message clearing issue after send"

# Documentation
git commit -m "docs: Update API documentation for chat endpoint"

# Refactor
git commit -m "refactor: Simplify message handling logic"
```

### 3. Keep Documentation Current

When modifying existing features:

```bash
# Don't just update code
vim frontend/src/App.jsx

# Also update the feature documentation
vim docs/features/existing-feature.md

# And note it in changelog
vim CHANGELOG.md
```

### 4. Add Code Comments for Complex Logic

```javascript
// ❌ Bad: No explanation
const result = messages.reduce((acc, m) =>
  m.role === 'user' ? [...acc, m] : acc, []);

// ✅ Good: Explains why and what
// Filter messages to show only user messages in export
// This excludes assistant responses to reduce export file size
const userMessages = messages.reduce((acc, m) =>
  m.role === 'user' ? [...acc, m] : acc, []);
```

## Troubleshooting

### Hook Not Running

**Problem**: Pre-commit hook doesn't execute

**Solution**:
```bash
# Check if hook exists
ls -la .git/hooks/pre-commit

# Make it executable
chmod +x .git/hooks/pre-commit

# Verify it's in the right location
cat .git/hooks/pre-commit | head -5
```

### Hook Runs But Shows Errors

**Problem**: Permission or script errors

**Solution**:
```bash
# Check the script has proper line endings (Unix, not Windows)
file .git/hooks/pre-commit

# Should show: "Bourne-Again shell script, ASCII text executable"

# If it shows "with CRLF line terminators", fix it:
dos2unix .git/hooks/pre-commit
# or
sed -i 's/\r$//' .git/hooks/pre-commit
```

### Want to Skip Documentation Check

**Problem**: Emergency commit, will document later

**Solution**:
```bash
# Skip all pre-commit hooks (use sparingly!)
git commit --no-verify -m "Emergency fix"

# Then remember to add documentation:
# 1. Create the docs
# 2. Commit them separately
git add docs/
git commit -m "docs: Add documentation for emergency fix"
```

### Documentation Template Not Found

**Problem**: Can't find template file

**Solution**:
```bash
# Verify templates exist
ls docs/templates/

# If missing, they should be in:
# docs/templates/FEATURE_TEMPLATE.md
# docs/templates/API_TEMPLATE.md

# Check you're in the repository root
pwd
# Should show: /Users/[username]/Documents/VS Projects/Contracts-AI
```

## Manual Documentation Commands

While the pre-commit hook is automatic, you can also run manual checks:

### Validate Documentation

```bash
# Check if documentation is complete (future feature)
doc validate

# Check specific areas
doc validate frontend
doc validate backend
doc validate api
```

### Generate Documentation

```bash
# Generate missing documentation (future feature)
doc generate feature "Feature Name"
doc generate api "/api/endpoint"
doc generate changelog
```

### View Documentation Status

```bash
# See documentation coverage (future feature)
doc status
doc report
```

## Advanced Usage

### Custom Documentation Location

If you need to document something that doesn't fit the templates:

```bash
# Create architecture decision
vim docs/architecture/proxy-pattern-decision.md

# Create custom guide
vim docs/guides/testing-with-ollama.md

# Just ensure it's in the docs/ directory
git add docs/
```

### Linking Between Documents

Use relative paths for cross-references:

```markdown
<!-- In docs/features/export.md -->
See also: [Chat API Documentation](../api/chat.md)

<!-- In docs/api/chat.md -->
This endpoint is used by: [Export Feature](../features/export.md)

<!-- Reference to root files -->
For setup instructions, see: [CLAUDE.md](../../CLAUDE.md)
```

## Summary

1. **Install pre-commit hook** once: `cp .claude/hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`
2. **Document as you code**: Use templates from `docs/templates/`
3. **Update CHANGELOG.md**: For every notable change
4. **Commit with docs**: Stage code + documentation together
5. **Hook validates**: Automatic check on every commit

The documentation agent makes it easy to maintain high-quality, up-to-date documentation without adding friction to your development workflow.

---

**See Also**:
- [Documentation Agent Specification](../../.claude/agents/documentation.md)
- [Documentation Directory README](../README.md)
- [Feature Template](../templates/FEATURE_TEMPLATE.md)
- [API Template](../templates/API_TEMPLATE.md)

**Last Updated**: 2026-01-17
