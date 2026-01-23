# 🎯 Redlining Demo Guide - Clean UI Walkthrough

**Date**: January 21, 2026
**Status**: Ready to Test ✅

---

## 📁 Demo Files Created

I've created two NDA contracts for testing:

1. **`golden_template_nda.txt`** - Your company's standard template (shorter, 2-year term)
2. **`demo_nda_contract.txt`** - New contract to review (longer, 3-year term, more clauses)

**Key Differences to Watch For:**
- ✏️ **Term**: Demo = 3 years, Template = 2 years
- ✏️ **Survival**: Demo = 5 years, Template = 3 years
- ✏️ **Termination Notice**: Demo = 60 days, Template = 30 days
- ✏️ **Governing Law**: Demo = California, Template = Delaware
- ✏️ **Arbitration Venue**: Different cities
- ✏️ **Clause Wording**: Some provisions are more detailed in demo

---

## 🚀 Step-by-Step Testing Guide

### **STEP 1: Set Up the Golden Template**

First, let's mark the standard template as your "golden template":

```bash
# Navigate to your project
cd "/Users/ryan.hooley@bmcjax.com/Documents/VS Projects/Contracts-AI"

# Create ZIP for template
zip golden_template_nda.zip golden_template_nda.txt
```

**Then in the browser (http://localhost:5173):**
1. Click **"📁 Manage Documents"** in header
2. Scroll to **"Upload Documents"** section
3. Upload `golden_template_nda.zip`
4. Wait for processing to complete
5. Find the uploaded document in the list
6. Click **"⭐ Mark as Template"** button
7. Select category: **"NDA"**
8. Add note: "Company Standard NDA Template v2.1"
9. Click **"Create Template"**
10. Click **"Approve"** (enter your name as approver)
11. ✅ You now have an approved golden template!

---

### **STEP 2: Start the Redlining Workflow**

Now let's redline a new contract against your template:

**In the browser:**

1. **Click** the purple **"🔍 Start Redlining"** button (top right)

   👁️ **What you'll see:**
   - Beautiful purple gradient screen
   - 4-step progress bar at top
   - Large upload drop zone
   - Category selector pills
   - Three info cards explaining the process

2. **Upload the Demo Contract:**
   - Drag `demo_nda.zip` to the drop zone OR click to browse
   - Select file: `demo_nda.zip`

   👁️ **What you'll see:**
   - File icon appears with filename and size
   - Category pills appear below

3. **Select Category:**
   - Click the **"NDA"** pill (it will turn purple)

4. **Start Processing:**
   - Click the big **"Start Redlining →"** button

   👁️ **What happens next:**
   - Screen transitions to "Processing" step
   - Four animated stages appear:
     1. ⏳ Extraction (spinning, purple background)
     2. ○ Matching (gray, waiting)
     3. ○ Comparison (gray, waiting)
     4. ○ Analysis (gray, waiting)

---

### **STEP 3: Watch the Processing (30-60 seconds)**

**Stage 1: Extraction** ⏳ → ✅
- Extracts clauses from your demo contract
- Background turns green when complete

**Stage 2: Matching** ⏳ → ✅
- Finds your golden template (NDA)
- Calculates similarity score

**Stage 3: Comparison** ⏳ → ✅
- Compares clause-by-clause
- Identifies differences

**Stage 4: Analysis** ⏳ → ✅
- Analyzes deviations
- Calculates risk scores

---

### **STEP 4: View the Results Dashboard**

After processing completes, you'll automatically see the **Results** screen:

**📊 Summary Cards (Top Row):**

1. **Overall Risk Card** (colored)
   - Expected: **Medium** (yellow/orange)
   - Score: ~40-60%
   - Why: Several term differences but no critical issues

2. **Template Match Card**
   - Expected: **75-85%** similarity
   - Both are NDAs with similar structure

3. **Deviations Found Card**
   - Expected: **8-12** differences
   - Different terms, venues, durations

**📈 Clause Breakdown Grid:**

Expected results:
- 🟢 **Matched**: ~6-8 clauses (identical or very similar)
- 🟡 **Modified**: ~5-8 clauses (similar but different terms)
- 🔴 **Missing**: ~2-3 clauses (in template but not in new contract)
- 🔵 **Extra**: ~1-2 clauses (in new contract but not in template)

---

### **STEP 5: Explore the Interface**

**Action Buttons:**
- **"Review Clause-by-Clause →"**: View detailed comparison (coming soon)
- **"Export Report"**: Download summary (coming soon)
- **"← Back to Documents"**: Return to document list

**Navigation:**
- Click **✕** (top right corner) to exit redlining mode
- Returns you to the main chat interface

---

## 🎨 UI Features You'll Love

✅ **Visual Progress** - Always know what's happening
✅ **Color-Coded Risk** - Instant understanding of severity
✅ **Animated Stages** - Engaging feedback during processing
✅ **Clean Design** - No more confusing terminal commands
✅ **Easy Navigation** - One-click exit back to chat

---

## 🔍 What the System Detects

The redlining engine will automatically identify:

1. **Term Changes**
   - Demo: 3-year term vs Template: 2-year term
   - Demo: 5-year survival vs Template: 3-year survival

2. **Notice Period Changes**
   - Demo: 60-day termination notice
   - Template: 30-day termination notice

3. **Jurisdiction Differences**
   - Demo: California law, San Francisco arbitration
   - Template: Delaware law, Wilmington arbitration

4. **Clause Wording**
   - Demo has more detailed confidentiality provisions
   - Different indemnification language
   - Varying warranty disclaimers

5. **Structural Differences**
   - Demo has additional subsections
   - More comprehensive definitions
   - Extra provisions in some sections

---

## 📸 Expected Visual Flow

```
┌─────────────────────────────────────────────────┐
│  Step 1: UPLOAD                                  │
│  • Purple gradient background                    │
│  • Drop zone with file icon                      │
│  • Category pills (NDA selected = purple)        │
│  • "Start Redlining →" button                    │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Step 2: PROCESSING                              │
│  • White card with 4 stages                      │
│  • ✅ Extraction (green background)              │
│  • ⏳ Matching (purple, spinning)                │
│  • ○ Comparison (gray)                           │
│  • ○ Analysis (gray)                             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Step 3: RESULTS                                 │
│  • 3 big summary cards                           │
│    - Overall Risk: MEDIUM (yellow)               │
│    - Template Match: 80%                         │
│    - Deviations: 10 differences                  │
│  • Clause breakdown grid                         │
│    - 7 Matched (green)                           │
│    - 6 Modified (yellow)                         │
│    - 2 Missing (red)                             │
│    - 1 Extra (blue)                              │
│  • Action buttons at bottom                      │
└─────────────────────────────────────────────────┘
```

---

## ⚡ Quick Test (30 seconds)

**Fastest way to see the UI:**

1. Open http://localhost:5173
2. Click **"🔍 Start Redlining"**
3. See the beautiful upload screen
4. Click **✕** to exit

**That's it!** You've seen the new clean interface.

---

## 🛠️ Troubleshooting

**If you see an error:**
- Check that backend is running: `docker ps | grep backend`
- Verify template is approved: Visit http://localhost:5173 → Manage Documents
- Check backend logs: `docker logs contracts-ai-backend | tail -20`

**If processing takes too long:**
- Normal time: 30-60 seconds
- Check Ollama is running: `docker ps | grep ollama`
- Monitor logs: `docker logs -f contracts-ai-backend`

---

## 🎯 Next Steps

After testing the demo:

1. **Upload your real templates** - Mark your actual company templates
2. **Test with real contracts** - Upload contracts you want to review
3. **Request features** - Let me know what else you'd like to see!

---

**Ready to test?** Open http://localhost:5173 and click the purple **"🔍 Start Redlining"** button! 🚀
