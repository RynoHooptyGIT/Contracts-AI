# Documentation Directory

This directory contains all documentation for the Contracts-AI project, organized by category.

## Directory Structure

```
docs/
├── README.md              # This file
├── templates/             # Documentation templates
│   ├── FEATURE_TEMPLATE.md    # Template for feature documentation
│   └── API_TEMPLATE.md        # Template for API endpoint documentation
├── features/              # Feature documentation
│   └── [feature-name].md
├── api/                   # API endpoint documentation
│   └── [endpoint-name].md
├── architecture/          # Architecture decisions and patterns
│   └── [decision-name].md
├── guides/                # User and developer guides
│   └── [guide-name].md
└── examples/              # Example documentation and exploration reports
    └── [example-name].md
```

## Documentation Types

### 1. Feature Documentation (`features/`)

Documents user-facing features and functionality.

**When to create**:
- Adding a new user-facing feature
- Significantly modifying existing functionality
- Adding complex UI interactions

**Template**: `templates/FEATURE_TEMPLATE.md`

**Example**: `features/export-chat-history.md`

### 2. API Documentation (`api/`)

Documents backend API endpoints.

**When to create**:
- Adding a new API endpoint
- Modifying an existing endpoint's contract
- Changing request/response formats

**Template**: `templates/API_TEMPLATE.md`

**Example**: `api/chat.md`

### 3. Architecture Documentation (`architecture/`)

Documents significant architectural decisions and patterns.

**When to create**:
- Making architectural decisions (new patterns, technology choices)
- Documenting design trade-offs
- Explaining why certain approaches were chosen

**Format**: Free-form markdown, but should include:
- Decision context
- Options considered
- Decision made
- Rationale

**Example**: `architecture/proxy-pattern.md`

### 4. User/Developer Guides (`guides/`)

Step-by-step guides for common tasks.

**When to create**:
- Onboarding new developers
- Documenting development workflows
- Explaining setup procedures

**Example**: `guides/getting-started.md`

### 5. Examples (`examples/`)

Example documentation and exploration reports demonstrating best practices.

**Purpose**:
- Show real exploration outputs
- Demonstrate documentation quality
- Provide templates by example
- Help new developers understand codebase

**Example**: `examples/exploration-chat-interface.md`

## Using Templates

### Creating Feature Documentation

1. Copy the template:
   ```bash
   cp docs/templates/FEATURE_TEMPLATE.md docs/features/your-feature-name.md
   ```

2. Fill in all sections marked with `[brackets]`

3. Remove or mark N/A for non-applicable sections

4. Add the file to git:
   ```bash
   git add docs/features/your-feature-name.md
   ```

### Creating API Documentation

1. Copy the template:
   ```bash
   cp docs/templates/API_TEMPLATE.md docs/api/your-endpoint-name.md
   ```

2. Fill in endpoint details, request/response formats, examples

3. Include curl commands for testing

4. Add the file to git:
   ```bash
   git add docs/api/your-endpoint-name.md
   ```

## Documentation Standards

### File Naming

- Use lowercase with hyphens: `feature-name.md`
- Be descriptive but concise
- Match the feature or endpoint name

### Content Guidelines

1. **Be Specific**: Include exact file paths, line numbers, code snippets
2. **Be Current**: Update documentation when code changes
3. **Be Complete**: Fill in all template sections or mark as N/A
4. **Include Examples**: Show real code, requests, responses
5. **Link Related Docs**: Cross-reference related documentation

### Code Blocks

Always specify the language for syntax highlighting:

````markdown
```javascript
// JavaScript code
```

```python
# Python code
```

```bash
# Shell commands
```

```json
{
  "example": "json"
}
```
````

## Documentation Agent

The documentation agent runs before every commit to ensure:
- Documentation exists for new features
- API changes are documented
- CHANGELOG.md is updated
- Code has appropriate comments

See [.claude/agents/documentation.md](../.claude/agents/documentation.md) for details.

## Pre-Commit Hook

Install the pre-commit hook to automatically check documentation:

```bash
# Make the hook executable
chmod +x .claude/hooks/pre-commit

# Copy to git hooks
cp .claude/hooks/pre-commit .git/hooks/pre-commit
```

The hook will:
- Analyze staged files
- Check for missing documentation
- Create docs directory structure if needed
- Remind you to update CHANGELOG.md
- Auto-create CHANGELOG.md if missing

## Quick Reference

### Before Committing

- [ ] Added/updated feature docs for new functionality
- [ ] Added/updated API docs for endpoint changes
- [ ] Updated CHANGELOG.md with your changes
- [ ] Added code comments for complex logic
- [ ] Ran `npm run lint` (frontend)
- [ ] Verified documentation is accurate

### Documentation Checklist

For **new features**:
- [ ] Feature documentation created
- [ ] Screenshots added (if UI change)
- [ ] Testing checklist completed
- [ ] CHANGELOG.md updated

For **API changes**:
- [ ] API documentation created/updated
- [ ] Request/response examples included
- [ ] Curl test commands provided
- [ ] Error cases documented

For **architectural changes**:
- [ ] Architecture decision documented
- [ ] CLAUDE.md updated if needed
- [ ] Rationale explained
- [ ] Trade-offs discussed

## Claude Code Agents

### Explore Agent

Use the explore agent to understand the codebase, debug issues, and search for code:

```bash
explore "chat interface"                    # Understand how it works
explore --mode=debug "messages not sending" # Debug an issue
explore --mode=search "error handling"      # Find specific code
explore --mode=flow "message submission"    # Trace data flow
explore --mode=api "/api/chat"              # Explore endpoints
```

See [guides/using-explore-agent.md](guides/using-explore-agent.md) for complete guide.

### Plan Agent

Create implementation plans, review code changes, and analyze architecture:

```bash
plan "add new feature"                     # Design implementation
plan --mode=review "latest commit"         # Code review
plan --mode=architecture "state mgmt"      # Architecture analysis
plan --mode=simplicity "add database"      # Complexity check
```

All plans require user approval before implementation begins.

See [guides/using-plan-agent.md](guides/using-plan-agent.md) for complete guide.

### Security Agent

Perform security audits, vulnerability scans, and NIST compliance checks:

```bash
security audit                             # Full security audit
security scan                              # Quick vulnerability scan
security deps                              # Check dependency CVEs
security secrets                           # Scan for exposed secrets
security compliance                        # NIST compliance check
```

Based on OWASP Top 10, NIST CSF, and CWE Top 25 standards.

See [guides/using-security-agent.md](guides/using-security-agent.md) for complete guide.

### Documentation Agent

Runs automatically before every commit to ensure documentation completeness.

See [.claude/agents/documentation.md](../.claude/agents/documentation.md) for details.

### Code Agent

Implementation agent for executing approved plans with project-specific workflows.

See [.claude/agents/code.md](../.claude/agents/code.md) for details.

## Need Help?

- Check templates in `docs/templates/`
- Review existing documentation for examples
- Review example explorations in `docs/examples/`
- See [CLAUDE.md](../CLAUDE.md) for project context
- Use explore agent: `explore "your question"`

---

**Maintained by**: Documentation Agent (Automated)
**Last Updated**: 2026-01-17
