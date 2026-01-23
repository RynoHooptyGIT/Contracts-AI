# Testing Guide - AI-Powered Contract Redlining System

**Version**: 0.4.0 (Phase 3)
**Date**: 2026-01-19
**Status**: Phase 1 & 2 Complete, Phase 3 Backend Complete

---

## Prerequisites

Before testing, ensure you have:
- Docker and Docker Compose installed
- At least 8GB RAM available
- ~10GB disk space for Ollama models
- Sample PDF or DOCX contracts for testing

---

## Quick Start

### 1. Start the Application

```bash
cd "/Users/ryan.hooley@bmcjax.com/Documents/VS Projects/Contracts-AI"

# Start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

**Expected Output:**
```
✅ Database schema initialized
✅ Database ready
✅ Document manager ready
✅ Template manager ready
✅ Clause extractor ready
✅ Redlining service ready
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 2. Pull Ollama Model (First Time Only)

```bash
# Pull Mistral model
docker exec contracts-ai-ollama ollama pull mistral

# Verify model is available
docker exec contracts-ai-ollama ollama list
```

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs (FastAPI Swagger UI)

---

## Testing Phase 1: Golden Templates System

### Test 1.1: Upload Documents

**Goal**: Upload contract documents to serve as golden templates

**Steps:**
1. Open frontend at http://localhost:5173
2. Click "Manage Documents" toggle in header
3. Click "Upload ZIP" button
4. Upload a ZIP file containing PDF or DOCX contracts
5. Wait for processing to complete

**Expected Result:**
- Documents appear in the document list
- Status shows "processed"
- Document count increases in Quick Stats

**API Test:**
```bash
# Upload a single document via API
curl -X POST http://localhost:8001/api/documents/upload \
  -F "file=@contracts.zip" \
  -H "Content-Type: multipart/form-data"

# List all documents
curl http://localhost:8001/api/documents | jq
```

### Test 1.2: Create Golden Template

**Goal**: Mark a document as a golden template

**Steps:**
1. In the document list, find a well-written contract
2. Click the "⭐ Mark as Template" button
3. Select category (e.g., "NDA", "Employment")
4. Optionally add notes
5. Click "Create Template"

**Expected Result:**
- Document gets gold border
- Template badge appears
- Template appears in TemplateManager

**API Test:**
```bash
# Create template from document
curl -X POST http://localhost:8001/api/templates/create \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "YOUR_DOCUMENT_ID",
    "category": "NDA",
    "notes": "Standard NDA template v1.0"
  }'

# List all templates
curl http://localhost:8001/api/templates | jq
```

### Test 1.3: Approve Template (Admin Only)

**Goal**: Approve template for use in redlining

**Steps:**
1. Click "Template Manager" in sidebar (if available)
2. Find the pending template
3. Click "Approve" button
4. Enter approver name
5. Confirm approval

**Expected Result:**
- Template status changes to "Approved"
- Badge color changes from gray to blue
- Template becomes active for matching

**API Test:**
```bash
# Approve template
curl -X POST http://localhost:8001/api/templates/YOUR_TEMPLATE_ID/approve \
  -H "Content-Type: application/json" \
  -d '{
    "approved_by": "Admin User"
  }'

# Get template details
curl http://localhost:8001/api/templates/YOUR_TEMPLATE_ID | jq
```

---

## Testing Phase 2: Clause Extraction

### Test 2.1: Extract Clauses from Template

**Goal**: Extract structured clauses from golden template

**Steps:**
1. Select a template document
2. Click "Extract Clauses" button (if available in UI)
3. Wait for processing (may take 10-30 seconds for large documents)

**Expected Result:**
- Clauses extracted and stored
- Clause count displayed
- Clauses viewable in database

**API Test:**
```bash
# Extract clauses from document
curl -X POST http://localhost:8001/api/documents/YOUR_DOCUMENT_ID/extract-clauses

# Expected response
{
  "success": true,
  "document_id": "...",
  "clause_count": 15,
  "clauses": [
    {
      "id": "...",
      "title": "Payment Terms",
      "type": "Payment",
      "text": "Payment shall be made...",
      "terms": {"period": "30 days", "amount": "$50,000"},
      "index": 1
    },
    ...
  ]
}
```

### Test 2.2: Verify Chunked Processing

**Goal**: Test that large documents are processed in chunks

**Steps:**
1. Upload a large contract (50+ pages, >100k characters)
2. Extract clauses from it
3. Monitor backend logs

**Expected Behavior:**
```
INFO: Processing 4 text chunks
INFO: Processing chunk 1/4 (25000 chars)
INFO: Extracted 8 clauses from chunk 1
INFO: Processing chunk 2/4 (25000 chars)
INFO: Extracted 6 clauses from chunk 2
...
INFO: Removed 2 duplicate clauses
INFO: Total unique clauses after deduplication: 20
```

**Verification:**
```bash
# Check backend logs
docker logs contracts-ai-backend | grep "CLAUSE_EXTRACTOR"

# Query database for clauses
docker exec contracts-ai-backend sqlite3 /app/data/documents.db \
  "SELECT document_id, COUNT(*) as clause_count FROM document_clauses GROUP BY document_id"
```

---

## Testing Phase 3: Redlining Session (NEW!)

### Test 3.1: Start Redlining Session

**Goal**: Upload new contract and automatically redline against golden template

**Prerequisites:**
- At least one approved template exists
- Clauses extracted from the template

**Steps via API:**
```bash
# Step 1: Upload a new contract and note its document_id
curl -X POST http://localhost:8001/api/documents/upload \
  -F "file=@new_contract.zip"

# Step 2: Start redlining session
curl -X POST http://localhost:8001/api/redlining/start \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "YOUR_NEW_DOCUMENT_ID",
    "category": "NDA"
  }' | jq

# Expected response
{
  "success": true,
  "session_id": "...",
  "status": "completed",
  "template_id": "...",
  "template_match_score": 0.75,
  "overall_risk_score": 0.42,
  "deviation_count": 8,
  "summary": {
    "matched": 10,
    "modified": 5,
    "missing": 2,
    "extra": 1
  }
}
```

**What Happens:**
1. ✅ System extracts clauses from new contract
2. ✅ Finds best matching golden template (RAG similarity)
3. ✅ Extracts clauses from template (if not already done)
4. ✅ Compares clause-by-clause using semantic matching
5. ✅ Analyzes deviations using LLM
6. ✅ Calculates risk scores
7. ✅ Stores session and comparison results

**Monitor Progress:**
```bash
# Watch backend logs in real-time
docker logs -f contracts-ai-backend | grep "REDLINING"

# Expected log sequence:
# INFO: Starting redlining session for document: abc123
# INFO: Step 1: Extracting clauses from uploaded document
# INFO: Step 2: Finding best matching template
# INFO: Found matching template def456 with score 0.753
# INFO: Step 3: Extracting clauses from template
# INFO: Step 4: Comparing documents clause-by-clause
# INFO: Matched 15 clause pairs, 3 extra, 2 missing
# SUCCESS: Comparison complete: 8 deviations, risk score 0.42
# INFO: Step 5: Storing session results
# SUCCESS: Redlining session created: session789
```

### Test 3.2: Retrieve Session Details

**Goal**: Get full redlining session results

```bash
# Get session with all comparisons
curl http://localhost:8001/api/redlining/session/YOUR_SESSION_ID | jq

# Expected response structure
{
  "success": true,
  "session": {
    "id": "...",
    "uploaded_document_id": "...",
    "template_id": "...",
    "template_match_score": 0.75,
    "category": "NDA",
    "status": "completed",
    "overall_risk_score": 0.42,
    "deviation_count": 8,
    "created_at": "2026-01-19T...",
    "comparisons": [
      {
        "id": "...",
        "new_clause_id": "...",
        "template_clause_id": "...",
        "comparison_type": "modified",
        "similarity_score": 0.82,
        "risk_level": "Medium",
        "deviation_summary": "Payment period changed from net-30 to net-60"
      },
      ...
    ]
  }
}
```

### Test 3.3: Get Comparison Results Only

**Goal**: Retrieve just the clause comparisons

```bash
# Get comparisons for a session
curl http://localhost:8001/api/redlining/session/YOUR_SESSION_ID/comparisons | jq

# Response includes all comparison types:
# - matched: Clauses that are very similar (similarity > 0.9)
# - modified: Clauses with differences (similarity 0.6-0.9)
# - missing: Template clauses not found in new contract
# - extra: New clauses not in template
```

### Test 3.4: Verify Database State

**Goal**: Confirm data is correctly stored

```bash
# Check redlining sessions
docker exec contracts-ai-backend sqlite3 /app/data/documents.db \
  "SELECT id, status, overall_risk_score, deviation_count FROM redlining_sessions ORDER BY created_at DESC LIMIT 5"

# Check clause comparisons
docker exec contracts-ai-backend sqlite3 /app/data/documents.db \
  "SELECT comparison_type, COUNT(*) FROM clause_comparisons GROUP BY comparison_type"

# Expected output:
# matched|10
# modified|5
# missing|2
# extra|1

# View specific comparison details
docker exec contracts-ai-backend sqlite3 /app/data/documents.db \
  "SELECT comparison_type, risk_level, deviation_summary FROM clause_comparisons WHERE session_id='YOUR_SESSION_ID' LIMIT 10"
```

---

## Testing Edge Cases

### Edge Case 1: No Templates Available

**Test:**
```bash
# Start session without any templates
curl -X POST http://localhost:8001/api/redlining/start \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "YOUR_DOCUMENT_ID"
  }'

# Expected response
{
  "success": true,
  "session_id": "...",
  "status": "no_template",
  "message": "No matching golden template found for this document"
}
```

### Edge Case 2: Very Large Document

**Test:**
```bash
# Upload 100+ page contract
# Verify chunked processing works
# Should see multiple chunks in logs
docker logs contracts-ai-backend | grep "Processing chunk"
```

### Edge Case 3: LLM Failure

**Test:**
```bash
# Stop Ollama temporarily
docker stop contracts-ai-ollama

# Try to extract clauses (should fail gracefully)
curl -X POST http://localhost:8001/api/documents/YOUR_DOC_ID/extract-clauses

# Expected: 500 error with clear message
# Restart Ollama
docker start contracts-ai-ollama
```

---

## Performance Testing

### Test Response Times

```bash
# Time clause extraction (expect 10-30 seconds for typical contract)
time curl -X POST http://localhost:8001/api/documents/YOUR_DOC_ID/extract-clauses

# Time redlining session (expect 30-60 seconds total)
time curl -X POST http://localhost:8001/api/redlining/start \
  -H "Content-Type: application/json" \
  -d '{"document_id": "YOUR_DOC_ID", "category": "NDA"}'

# Time template matching (expect 1-3 seconds)
# This is internal but reflected in session creation time
```

### Monitor Resource Usage

```bash
# Check Docker container stats
docker stats contracts-ai-backend contracts-ai-ollama

# Expected:
# Backend: <500MB RAM, <5% CPU (idle)
# Ollama: 2-4GB RAM, 50-90% CPU (during LLM inference)
```

---

## Debugging

### View All Logs

```bash
# Backend logs
docker logs -f contracts-ai-backend

# Ollama logs
docker logs -f contracts-ai-ollama

# Frontend logs
docker logs -f contracts-ai-frontend
```

### Check Database State

```bash
# Connect to database
docker exec -it contracts-ai-backend sqlite3 /app/data/documents.db

# Useful queries:
sqlite> .tables
sqlite> SELECT COUNT(*) FROM documents;
sqlite> SELECT COUNT(*) FROM golden_templates WHERE is_active=1;
sqlite> SELECT COUNT(*) FROM document_clauses;
sqlite> SELECT COUNT(*) FROM redlining_sessions;
sqlite> SELECT COUNT(*) FROM clause_comparisons;
sqlite> .quit
```

### API Health Check

```bash
# Test backend is running
curl http://localhost:8001/

# Get API documentation
open http://localhost:8001/docs

# Test RAG system
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [{"role": "user", "content": "What is the payment term in the uploaded contracts?"}]
  }'
```

---

## Common Issues & Solutions

### Issue 1: "No module named 'services.redlining_service'"

**Solution:**
```bash
# Rebuild backend container
docker-compose build backend
docker-compose up -d backend
```

### Issue 2: "Template not found" during redlining

**Check:**
1. Templates exist: `curl http://localhost:8001/api/templates`
2. Template is approved: Check `is_approved=1` in database
3. Clauses extracted: Check `document_clauses` table

### Issue 3: LLM returns malformed JSON

**Debug:**
```bash
# Check Ollama logs for errors
docker logs contracts-ai-ollama | tail -50

# Test Ollama directly
docker exec contracts-ai-ollama ollama run mistral "Respond with JSON: {\"test\": true}"
```

### Issue 4: Slow performance

**Optimize:**
1. Reduce LLM context window (already set to 25k chars per chunk)
2. Use smaller model: `ollama pull mistral:7b-instruct`
3. Limit template count: Only keep active templates
4. Add more RAM to Docker

---

## Cleanup

```bash
# Stop all containers
docker-compose down

# Remove volumes (deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Full cleanup
docker-compose down -v --rmi all --remove-orphans
```

---

## Next Steps

After verifying Phase 3 backend works:

1. **Build Frontend UI**: SessionStatus.jsx component
2. **Add Visualizations**: Risk charts, deviation highlights
3. **Implement Phase 4**: AI suggestions for clause rewrites
4. **Add Document Rendering**: HTML conversion for side-by-side view
5. **Export to DOCX**: With Microsoft Word track changes

---

## Test Checklist

### Phase 1 Tests
- [ ] Upload documents via ZIP
- [ ] Create golden template from document
- [ ] Approve template (admin)
- [ ] List templates by category
- [ ] Deactivate template

### Phase 2 Tests
- [ ] Extract clauses from single document
- [ ] Extract clauses from large document (chunked)
- [ ] Verify deduplication works
- [ ] Check clause storage in database
- [ ] Query extracted clauses

### Phase 3 Tests
- [ ] Start redlining session
- [ ] Verify template matching (RAG)
- [ ] Check clause-by-clause comparison
- [ ] Verify deviation analysis (LLM)
- [ ] Check risk score calculation
- [ ] Retrieve session details
- [ ] Get comparison results
- [ ] Delete session
- [ ] Test edge cases (no templates, failures)

### Performance Tests
- [ ] Time clause extraction (<30s for typical contract)
- [ ] Time redlining session (<60s total)
- [ ] Monitor resource usage (RAM, CPU)
- [ ] Test concurrent requests

### Integration Tests
- [ ] Full workflow: Upload → Template → Extract → Redline
- [ ] Multiple templates per category
- [ ] Multiple sessions per document
- [ ] Database integrity after operations

---

**Last Updated**: 2026-01-19
**Version**: Phase 3 Backend Complete
**Status**: Ready for Testing ✅
