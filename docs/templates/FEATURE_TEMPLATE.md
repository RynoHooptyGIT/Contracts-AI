# Feature: [Feature Name]

> **Template Usage**: Copy this file to `docs/features/[feature-name].md` and fill in the sections below.

## Overview

[Brief description of what this feature does and why it was added]

## Implementation

### Frontend Changes

- **File**: `frontend/src/App.jsx`
- **Changes**:
  - [What was modified]
  - [New state variables if any]
  - [New UI elements]

### Backend Changes

- **File**: `backend/main.py`
- **Changes**:
  - [What was modified]
  - [New endpoints or modified endpoints]
  - [New Pydantic models]

## User Experience

### How to Use

1. [Step 1 - User action]
2. [Step 2 - User action]
3. [Expected result]

### Screenshots

[If applicable, add screenshots showing the feature in action]

## Technical Details

### Request Format

```json
{
  "field": "value",
  "description": "type"
}
```

### Response Format

```json
{
  "field": "value",
  "description": "type"
}
```

### State Management

[Explain any new state variables and how they're managed]

```javascript
const [stateName, setStateName] = useState(initialValue);
```

## Testing

### Manual Testing Checklist

- [ ] Feature loads correctly
- [ ] User can interact with feature
- [ ] Success case works as expected
- [ ] Error handling displays appropriate messages
- [ ] No console errors
- [ ] UI remains responsive

### Test Cases

1. **Test Case 1**: [Description]
   - **Input**: [User input]
   - **Expected**: [Expected outcome]
   - **Result**: ✅ Pass / ❌ Fail

2. **Test Case 2**: [Description]
   - **Input**: [User input]
   - **Expected**: [Expected outcome]
   - **Result**: ✅ Pass / ❌ Fail

## Dependencies

- **Ollama**: [Any specific requirements]
- **Model**: Mistral (default)
- **Browser**: [Any specific browser requirements]
- **External APIs**: [If applicable]

## Configuration

[Any configuration changes needed]

```bash
# Environment variables (if added)
VARIABLE_NAME=value
```

## Known Limitations

- [Limitation 1]
- [Limitation 2]

## Future Enhancements

- [ ] [Possible improvement 1]
- [ ] [Possible improvement 2]

## Related Documentation

- [Link to related API docs if applicable]
- [Link to architecture decisions]

---

**Created**: [Date]
**Author**: [Your name or team]
**Status**: ✅ Implemented / 🚧 In Progress / 📋 Planned
