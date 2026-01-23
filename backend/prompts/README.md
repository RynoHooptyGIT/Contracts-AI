# LLM Prompt Templates

This directory contains all LLM prompt templates used in the Contracts-AI redlining system.

## Available Prompts

### 1. Clause Extraction (`clause_extraction.txt`)
**Used by**: `services/clause_extractor.py`

Extracts structured clauses from contract text with the following fields:
- `title`: Clause title (e.g., "Payment Terms")
- `type`: Clause type (Payment, Liability, Termination, Confidentiality, IP, Dispute, Warranty, Indemnification, Other)
- `text`: Full clause text
- `terms`: Key terms as dictionary (amounts, dates, durations, parties)
- `index`: Position in document

**Temperature**: 0.2 (structured output)
**Output format**: JSON

### 2. Deviation Analysis (`deviation_analysis.txt`)
**Used by**: `services/comparison_engine.py`

Compares two contract clauses and identifies differences:
- `material_differences`: Changes affecting legal rights/obligations
- `missing_provisions`: Important terms present in template but not in new clause
- `added_provisions`: New terms not in template
- `term_changes`: Specific term modifications (amounts, dates, etc.)
- `risk_level`: Low, Medium, High, or Critical
- `risk_rationale`: Explanation of risk assessment
- `summary`: Brief deviation summary

**Temperature**: 0.2 (structured output)
**Output format**: JSON

### 3. Clause Rewrite (Future - Phase 4)
**Used by**: `services/suggestion_generator.py`

Generates AI-powered clause rewrite suggestions with:
- Multiple rewrite options
- Rationale for each option
- Changes made
- Risk improvement assessment
- Confidence score

**Temperature**: 0.3 (creative but controlled)
**Output format**: JSON

### 4. Missing Clause Generation (Future - Phase 4)
**Used by**: `services/suggestion_generator.py`

Suggests clauses to add when template clauses are missing from new contract.

## Usage Guidelines

### Best Practices
1. **Temperature Settings**:
   - 0.1-0.2: Structured JSON output (extraction, analysis)
   - 0.3-0.5: Creative generation with constraints (suggestions)
   - 0.7-0.9: Open-ended generation (not used in this system)

2. **Prompt Structure**:
   - Clear role definition ("You are a legal contract analyzer...")
   - Specific task description
   - Example output format
   - Constraints and validation rules

3. **Error Handling**:
   - Always validate JSON schema
   - Strip markdown code blocks (```json)
   - Implement retry logic (3 attempts with exponential backoff)
   - Log failures for analysis

4. **Context Window Management**:
   - Keep prompts under 2,000 tokens
   - For large contracts, use chunking (see clause_extractor.py)
   - Use first 3,000 chars for template matching
   - Preserve important context in overlapping chunks

### Testing Prompts

When modifying prompts, test with:
1. Typical contracts (10-50 pages)
2. Edge cases (very short, very long, unusual clauses)
3. Different contract types (NDA, Employment, MSA, etc.)
4. Various quality levels (well-written vs. poorly-written)

### Prompt Versioning

When updating prompts:
1. Document changes in commit message
2. Test against existing contracts to ensure no regressions
3. Update corresponding service files if output format changes
4. Add migration code if schema changes

## Model Configuration

**Current Model**: Mistral 7B (via Ollama)
- Context window: 8k tokens (~25k characters)
- Best for: Structured output, analysis, extraction
- Temperature: 0.2 for all production prompts

**Alternative Models** (Future):
- Claude Opus 4.5: Better reasoning for complex deviation analysis
- GPT-4: Strong at legal language understanding
- Local models: Privacy-focused deployments

## Performance Metrics

Target metrics for prompt quality:
- **Extraction Accuracy**: >90% clause identification
- **JSON Parse Rate**: >95% valid JSON responses
- **Deviation Detection**: >85% material differences caught
- **False Positive Rate**: <10% for risk classification

Monitor via logs and user feedback.
