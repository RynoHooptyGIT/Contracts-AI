---
auto_open_browser: false
last_updated: 2026-01-17
---

# Using the Plan Agent

Complete guide to using the Plan Agent for implementation planning, code review, and architecture analysis in Contracts-AI.

## Overview

The Plan Agent is a strategic planning tool that helps you:
- 📋 **Design** implementation strategies for features
- 👀 **Review** code changes and commits
- 🏗️ **Analyze** architecture and design decisions
- ✅ **Verify** changes maintain project simplicity

**Critical**: All plans require **user approval** before implementation begins.

## Quick Start

### Plan a New Feature

```bash
plan "add export chat history button"
```

This will create a complete implementation plan including:
- Files to modify
- Step-by-step tasks
- Testing checklist
- Risk assessment
- Approval gate

### Review Recent Changes

```bash
plan --mode=review "latest commit"
```

Returns code review with:
- Quality assessment
- Issues found
- Recommendations
- Approval verdict

### Analyze Architecture

```bash
plan --mode=architecture "state management"
```

Provides analysis of:
- Current patterns
- Alignment with principles
- Improvement opportunities

### Check Simplicity

```bash
plan --mode=simplicity "add user authentication"
```

Verifies if proposal:
- Maintains stateless architecture
- Avoids unnecessary complexity
- Offers simpler alternatives

## Modes Explained

### 1. Default Mode (Implementation Planning)

**Purpose**: Design implementation strategy for features

**When to Use**:
- Adding new functionality
- Modifying existing features
- Planning complex changes
- Before writing code

**Example Commands**:
```bash
plan "add message export feature"
plan "implement dark mode"
plan "add model selection dropdown"
plan "improve error messages"
```

**Output Includes**:
- Implementation approach
- File changes required
- Step-by-step tasks
- Testing criteria
- Risk assessment
- Architecture alignment check

### 2. Review Mode (Code Review)

**Purpose**: Review code changes for quality and correctness

**When to Use**:
- After making changes
- Before committing
- Reviewing pull requests
- Quality assurance

**Example Commands**:
```bash
plan --mode=review "HEAD"
plan --mode=review "last commit"
plan --mode=review "frontend changes"
plan --mode=review "abc123"  # specific commit
```

**Output Includes**:
- File-by-file analysis
- Code quality assessment
- Issues found (critical/warning)
- Architecture alignment
- Recommendations
- Approval verdict

### 3. Architecture Mode (Design Analysis)

**Purpose**: Analyze and document architectural patterns

**When to Use**:
- Understanding current design
- Planning refactoring
- Documenting decisions
- Identifying technical debt

**Example Commands**:
```bash
plan --mode=architecture "chat interface"
plan --mode=architecture "API integration"
plan --mode=architecture "error handling"
plan --mode=architecture "state management"
```

**Output Includes**:
- Current architecture overview
- Pattern identification
- Alignment with principles
- Concerns and risks
- Improvement opportunities
- Architecture diagrams

### 4. Simplicity Mode (Complexity Check)

**Purpose**: Ensure changes maintain simple architecture

**When to Use**:
- Evaluating feature proposals
- Before adding complexity
- Challenging requirements
- Seeking simpler alternatives

**Example Commands**:
```bash
plan --mode=simplicity "add database persistence"
plan --mode=simplicity "implement user authentication"
plan --mode=simplicity "add Redis caching"
plan --mode=simplicity "split into microservices"
```

**Output Includes**:
- Complexity assessment
- Architecture impact analysis
- Simpler alternatives
- Red flags
- Verdict (approve/modify/reject)
- Minimal implementation approach

## Real-World Examples

### Example 1: Planning a Simple Feature

**Scenario**: Add button to export chat history

**Command**:
```bash
plan "add export chat history button"
```

**Expected Plan**:
```markdown
# Implementation Plan: Export Chat History

## Overview
Add a button that exports the current chat history as a JSON file for user download.

## Approach
Frontend-only feature using browser download API. No backend changes needed.

## Files to Modify

### Frontend
- `frontend/src/App.jsx` - Add export button and handler
- `frontend/src/App.css` - Style export button

## Implementation Steps

### Step 1: Create Export Function
**Complexity**: Low

**Changes**:
- [ ] Add `exportChat()` function after `handleSubmit()`
- [ ] Create JSON from messages state
- [ ] Generate downloadable blob
- [ ] Trigger browser download

**Code Snippet**:
```javascript
const exportChat = () => {
  const chatData = {
    timestamp: new Date().toISOString(),
    messages: messages
  };

  const blob = new Blob([JSON.stringify(chatData, null, 2)], {
    type: 'application/json'
  });

  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `chat-export-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
};
```

**Testing**:
- [ ] Button appears in UI
- [ ] Click triggers download
- [ ] JSON file contains all messages
- [ ] Multiple exports work
- [ ] Empty chat handled gracefully

### Step 2: Add UI Button
**Complexity**: Low

**Changes**:
- [ ] Add button next to Send button
- [ ] Style to match existing buttons
- [ ] Disable when no messages

**Code Snippet**:
```javascript
<button
  onClick={exportChat}
  disabled={messages.length === 0}
  className="export-button"
>
  Export
</button>
```

## Testing Checklist

### Manual Testing
- [ ] Start chat, send messages
- [ ] Click Export button
- [ ] Verify JSON file downloads
- [ ] Open JSON, verify format
- [ ] Test with empty chat (button disabled)
- [ ] Test with many messages

## Risk Assessment

**Complexity**: Low
**Potential Issues**: None significant
**Breaking Changes**: No
**Rollback**: Simply remove button and function

## Alignment with Architecture

**Stateless Backend**: ✅ No backend changes
**Simple Frontend**: ✅ Simple function, minimal code
**Proxy Pattern**: ✅ No impact
**Minimal Dependencies**: ✅ Uses browser APIs only

## Documentation Updates

- [ ] Create `docs/features/export-chat-history.md`
- [ ] Update `CHANGELOG.md`
- [ ] Add code comments

---

**Status**: ⏳ Awaiting User Approval
**Estimated Complexity**: Low
**Files Changed**: 2
```

**User Response**: "approved"

**Next**: Plan agent hands off to Code agent for implementation

### Example 2: Complexity Check (Feature Rejected)

**Scenario**: User wants to add user accounts with database

**Command**:
```bash
plan --mode=simplicity "add user accounts with PostgreSQL database"
```

**Expected Report**:
```markdown
# Simplicity Check: User Accounts with Database

## Proposal Analyzed
Add user authentication with accounts stored in PostgreSQL database.

## Complexity Assessment

**Current Complexity**: Low
**Proposed Complexity**: High
**Delta**: ⬆️⬆️ Significant Increase

## Architecture Impact

### Stateless Backend
**Impact**: ❌ **Violated**

Adding a database fundamentally breaks the stateless architecture principle. The backend would need to:
- Manage database connections
- Handle sessions/tokens
- Store user credentials
- Manage state across requests

### Simple Frontend
**Impact**: ⚠️ **Significant**

Would require:
- Login/signup forms
- Session management
- Protected routes
- User state management

### Minimal Dependencies
**Impact**: ❌ **Violated**

New dependencies:
- PostgreSQL driver (e.g., psycopg2, asyncpg)
- ORM (SQLAlchemy or similar)
- Authentication library (e.g., passlib, python-jose)
- Frontend: Auth state library

## Simpler Alternatives

### Alternative 1: No Authentication
**Complexity**: Current (Low)
**Trade-offs**:
- Pro: Maintains simplicity
- Pro: No setup required
- Con: No user-specific features
**Recommendation**: ✅ **Use** if user-specific features not critical

### Alternative 2: Client-Side Only (localStorage)
**Complexity**: Low
**Trade-offs**:
- Pro: No backend changes
- Pro: No database needed
- Pro: Works with current architecture
- Con: Not secure (no real authentication)
- Con: Local to single browser/device
**Recommendation**: ✅ **Use** for demo/development

### Alternative 3: Simple Token-Based (No DB)
**Complexity**: Medium
**Trade-offs**:
- Pro: Stateless (JWT tokens)
- Pro: No database needed
- Con: Still adds significant complexity
- Con: No user data persistence
**Recommendation**: ⚠️ **Consider** if auth truly needed

## Complexity Indicators

**Lines of Code**: +500-1000
**New Files**: 5-10
**New State Variables**: 5-8
**New Dependencies**: 4-6
**Abstraction Layers**: 3 (Auth, DB, User Management)

## Red Flags

- [x] Adds database or persistence layer
- [x] Introduces global state management
- [x] Requires authentication/authorization
- [ ] Splits single component into many
- [x] Adds heavy external dependencies
- [x] Breaks proxy pattern
- [ ] Requires complex configuration

**5 out of 7 red flags** ⚠️

## Verdict

**Simplicity Rating**: ❌ **Too Complex**

**Recommendation**: **Reject** - Fundamentally incompatible with project architecture

**Rationale**:
This feature would transform the project from a simple, stateless chat application into a complex, stateful web application with database management. It violates the core architectural principle of being stateless and simple.

## Alternative Approach

If user-specific features are truly needed, consider:

1. **Keep current architecture** - Use as a template/demo
2. **Fork for production** - Create separate production-ready version
3. **Use external auth** - OAuth with external provider (still complex)
4. **Browser-based only** - Store "preferences" in localStorage (not real auth)

---

**Checked By**: Plan Agent
**Decision**: ❌ Reject proposal, suggest alternatives
```

**User Response**: "understood, let's go with localStorage approach"

**Next**: Create new plan for localStorage implementation

### Example 3: Code Review

**Scenario**: Review changes from last commit

**Command**:
```bash
plan --mode=review "HEAD"
```

**Expected Review**:
```markdown
# Code Review Report

## Changes Analyzed
Commit: 4e988e9 - "docs: Add comprehensive README.md"

## Summary

- **Files Changed**: 1
- **Lines Added**: +320
- **Lines Removed**: -0
- **Overall Assessment**: ✅ **Approved**

## File Analysis

### README.md
**Changes**: Created comprehensive project README

**✅ Good**:
- Clear installation instructions
- Complete project overview
- Technology stack documented
- Troubleshooting section
- Architecture diagram
- Contributing guidelines

**⚠️ Minor Suggestions**:
- Consider adding badges (build status, license)
- Could add screenshots of UI
- Might add "Star History" for GitHub

## Code Quality Assessment

**Documentation Quality**: ✅ Excellent
- Comprehensive coverage
- Clear examples
- Good structure
- Appropriate length

**Accuracy**: ✅ Accurate
- Commands verified
- Ports correct (5173, 8001, 11434)
- Dependencies listed correctly

**Completeness**: ✅ Complete
- All major sections covered
- Quick start included
- Troubleshooting provided

## Recommendations

### Suggested Improvements
1. **Add Screenshots**
   - Add image of chat interface
   - Show example conversation
   - Location: After "Features" section

2. **Add Status Badges**
   ```markdown
   [![License](badge-url)](LICENSE)
   [![React](badge-url)](react-url)
   ```

## Decision

**Verdict**: ✅ **Approved**

**Rationale**: High-quality documentation that accurately describes the project. No critical issues. Suggestions are optional enhancements.

---

**Reviewer**: Plan Agent
**Date**: 2026-01-17
```

## Approval Workflow

### How Approval Works

```
Plan Agent Creates Plan
         ↓
User Reviews Plan
         ↓
    ┌────┴────┐
    │         │
Approved  Needs Changes
    │         │
    │    Plan Revised
    │         │
    └────┬────┘
         ↓
  Code Agent Implements
```

### Approval Signals

The plan agent recognizes these as approval:

**Explicit Approval**:
- "approved"
- "approve"
- "yes"
- "proceed"
- "go ahead"
- "green light"
- "implement it"
- "looks good"
- "lgtm"
- "ship it"

**Implicit Approval with Action**:
- "implement this"
- "start implementation"
- "code this"

### Rejection Signals

**Explicit Rejection**:
- "no"
- "reject"
- "don't proceed"
- "hold"
- "stop"

**Request for Changes**:
- "needs changes"
- "revise"
- "modify"
- "change [aspect]"
- Providing specific feedback

### Revision Cycle

If changes are requested:

1. **User**: "The export button should be in the header, not footer"
2. **Plan Agent**: Revises plan with button in header
3. **User**: Reviews updated plan
4. **User**: "approved"
5. **Code Agent**: Implements approved plan

## Best Practices

### 1. Use Explore First

```bash
# Good workflow:
explore "chat feature"      # Understand current state
plan "improve chat feature" # Design improvements
# Review plan, approve
# Code agent implements
```

### 2. Be Specific in Requests

❌ Bad: `plan "make it better"`
✅ Good: `plan "add loading indicator during AI response"`

❌ Bad: `plan "fix bugs"`
✅ Good: `plan "fix message input not clearing after send"`

### 3. Review Plans Carefully

Before approving, verify:
- [ ] Approach makes sense
- [ ] Files to change are correct
- [ ] Testing is comprehensive
- [ ] Risk assessment is acceptable
- [ ] Architecture alignment is good

### 4. Use Simplicity Check for Big Features

```bash
# Before planning complex features:
plan --mode=simplicity "add WebSocket real-time sync"

# If approved:
plan "add WebSocket real-time sync"
```

### 5. Request Changes When Needed

Don't approve if you disagree:
```
User: plan "add export feature"
Plan Agent: [presents plan with backend endpoint]
User: "I don't think we need a backend endpoint. Can we do this frontend-only?"
Plan Agent: [revises plan for frontend-only approach]
User: "approved"
```

## Common Use Cases

### Feature Development

```bash
# 1. Understand current code
explore "chat interface"

# 2. Plan the feature
plan "add message timestamps"

# 3. Review plan, approve
# "approved"

# 4. Code agent implements
# 5. Review implementation
plan --mode=review "HEAD"

# 6. If good, commit
# git commit...
```

### Bug Fixing

```bash
# 1. Debug the issue
explore --mode=debug "messages not clearing"

# 2. Plan the fix
plan "fix message input clearing issue"

# 3. Approve and implement
# "approved"

# 4. Verify fix
plan --mode=review "HEAD"
```

### Architecture Review

```bash
# Periodic architecture review
plan --mode=architecture "entire application"

# Review recommendations
# Decide what to address

# Plan improvements
plan "refactor error handling based on architecture review"
```

### Quality Assurance

```bash
# Before merging PR
plan --mode=review "feature-branch"

# Address any issues found
# Re-review after fixes
plan --mode=review "HEAD"
```

## Tips for Effective Planning

### 1. Provide Context

```bash
# Include "why" in your request
plan "add model selection dropdown so users can choose between Mistral and Llama2"
```

### 2. Break Down Large Features

Instead of:
```bash
plan "complete chat application overhaul"
```

Do:
```bash
plan "add message persistence"
plan "add export feature"
plan "improve error handling"
```

### 3. Use Architecture Mode for Learning

```bash
# Understand before changing
plan --mode=architecture "state management"

# Then plan changes
plan "optimize state updates based on architecture analysis"
```

### 4. Leverage Simplicity Checks

```bash
# Before investing time in complex features
plan --mode=simplicity "add real-time collaboration"

# If too complex, reconsider or simplify
```

## Troubleshooting

### Plan Too Generic

**Problem**: Plan lacks specific details

**Solution**:
- Provide more context in request
- Use explore agent first to gather context
- Ask plan agent to be more specific

### Plan Too Complex

**Problem**: Plan seems overly complicated

**Solution**:
```bash
plan --mode=simplicity "[feature]"
# Review simpler alternatives suggested
```

### Disagree with Approach

**Problem**: Plan's approach doesn't match your vision

**Solution**:
- Request revision: "Can we do this without adding a new state variable?"
- Provide alternative: "Instead of X, let's do Y"
- Plan agent will revise

### Missing Testing Steps

**Problem**: Plan doesn't include enough tests

**Solution**:
- Request addition: "Add more comprehensive testing steps"
- Specify: "Include error case testing"

## Integration with Other Agents

### Complete Workflow

```bash
# 1. EXPLORE: Understand the codebase
explore "feature area"

# 2. PLAN: Design implementation
plan "add new feature"

# 3. REVIEW: Check plan
# Read plan, ask questions, approve

# 4. CODE: Implement
# Code agent executes plan

# 5. DOCUMENTATION: Auto-generated
# Pre-commit hook validates docs

# 6. REVIEW: Verify implementation
plan --mode=review "HEAD"

# 7. COMMIT: Save changes
git commit -m "feat: Add new feature"
```

## Next Steps

After using the plan agent:

1. **If Approved**: Code agent implements the plan
2. **If Rejected**: Revise requirements or abandon feature
3. **If Modified**: Review updated plan and re-approve
4. **After Implementation**: Review with `plan --mode=review`

## See Also

- [Plan Agent Specification](../../.claude/agents/plan.md)
- [Code Agent Guide](../../.claude/agents/code.md)
- [Explore Agent Guide](using-explore-agent.md)
- [CLAUDE.md](../../CLAUDE.md)

---

**Last Updated**: 2026-01-17
