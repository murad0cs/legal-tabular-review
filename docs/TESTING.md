# Testing & Evaluation

## Extraction Accuracy

### Evaluation Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Precision** | Correct extractions / Total extractions | > 85% |
| **Recall** | Correct extractions / Expected extractions | > 80% |
| **F1 Score** | Harmonic mean of precision and recall | > 82% |
| **Confidence Correlation** | Correlation between confidence and accuracy | > 0.7 |

### Per-Field Accuracy Targets

| Field Type | AI Extraction Target | Pattern Extraction Target |
|------------|---------------------|--------------------------|
| Party names | 95% | 85% |
| Dates | 98% | 90% |
| Currency | 95% | 88% |
| Clauses | 80% | 60% |
| Free text | 75% | 50% |

### Test Procedure

1. **Ground Truth Dataset**
   - Use documents in `/data/` folder
   - Create expected values JSON for each document
   - Include edge cases: missing values, ambiguous text

2. **Extraction Test**
   ```bash
   # Run extraction on test documents
   curl -X POST http://localhost:8000/api/projects/1/extract
   
   # Get extracted values
   curl http://localhost:8000/api/projects/1/values
   ```

3. **Compare Results**
   - Match extracted values against ground truth
   - Calculate precision, recall, F1
   - Log confidence scores for correlation analysis

## Coverage Testing

### Template Coverage

| Test Case | Expected Result |
|-----------|-----------------|
| All field types used | Each type extracts correctly |
| Required vs optional fields | Required fields flagged if missing |
| Normalization rules applied | Dates/currency properly formatted |
| Validation rules enforced | Invalid values flagged |

### Document Coverage

| Test Case | Expected Result |
|-----------|-----------------|
| Standard NDA | All NDA template fields extracted |
| Service Agreement | All contract fields extracted |
| Commercial Lease | All lease fields extracted |
| Edge case: empty document | Graceful handling, all values null |
| Edge case: wrong document type | Extraction attempts with low confidence |

### API Coverage

| Endpoint Category | Test Count | Description |
|-------------------|------------|-------------|
| Documents | 5 | Upload, list, get, content, delete |
| Templates | 10 | CRUD + fields + import/export |
| Projects | 12 | CRUD + documents + extraction + values |
| Search | 3 | Search, field types, suggestions |
| Validation | 2 | Validate, summary |
| Export | 2 | CSV, Excel |

## Review QA Checklist

### Pre-Review Checks

- [ ] All documents processed successfully (status = "ready")
- [ ] Extraction completed without errors
- [ ] All required fields have values (or flagged as missing)
- [ ] Confidence scores populated for all values
- [ ] Citations present where extracted

### Review Interface Checks

- [ ] Side-by-side table renders correctly
- [ ] All documents appear as columns
- [ ] All fields appear as rows
- [ ] Values display with proper formatting
- [ ] Confidence badges show correct colors:
  - 🟢 Green: ≥ 80%
  - 🟡 Yellow: 50-79%
  - 🔴 Red: < 50%
- [ ] Status badges show correct states
- [ ] Citation links work (show source text)
- [ ] Validation errors displayed for invalid values

### Action Checks

- [ ] Single value approval works
- [ ] Single value rejection works
- [ ] Bulk approval works
- [ ] Bulk rejection works
- [ ] Edit value modal opens
- [ ] Edited values save correctly
- [ ] Status changes reflect immediately
- [ ] Audit log captures all actions

### Export Checks

- [ ] CSV export downloads
- [ ] CSV contains all fields and documents
- [ ] CSV includes value, citation, confidence
- [ ] Excel export downloads
- [ ] Excel formatting correct
- [ ] No data loss in export

### Navigation Checks

- [ ] Keyboard shortcuts work (A, R, E, arrows)
- [ ] Cell focus navigation works
- [ ] Filter dropdown works
- [ ] Sort by status works
- [ ] Search within table works

## Sample Test Data

### `/data/sample_nda.txt`

Expected extractions:
```json
{
  "disclosing_party": {
    "value": "ACME CORPORATION",
    "expected_confidence": ">0.9"
  },
  "receiving_party": {
    "value": "BETA TECHNOLOGIES INC",
    "expected_confidence": ">0.9"
  },
  "effective_date": {
    "value": "2024-01-15",
    "normalized": "2024-01-15",
    "expected_confidence": ">0.95"
  },
  "term_duration": {
    "value": "3 years",
    "expected_confidence": ">0.8"
  }
}
```

### `/data/sample_contract.txt`

Expected extractions:
```json
{
  "party_a": {
    "value": "GLOBAL SERVICES LLC",
    "expected_confidence": ">0.9"
  },
  "party_b": {
    "value": "ENTERPRISE CORP",
    "expected_confidence": ">0.9"
  },
  "effective_date": {
    "value": "2024-03-01",
    "expected_confidence": ">0.95"
  },
  "contract_value": {
    "value": "$150,000.00",
    "normalized": "$150,000.00",
    "expected_confidence": ">0.9"
  }
}
```

### `/data/sample_lease.txt`

Expected extractions:
```json
{
  "landlord": {
    "value": "PROPERTY HOLDINGS LLC",
    "expected_confidence": ">0.9"
  },
  "tenant": {
    "value": "STARTUP INNOVATIONS INC",
    "expected_confidence": ">0.9"
  },
  "monthly_rent": {
    "value": "$5,500.00",
    "normalized": "$5,500.00",
    "expected_confidence": ">0.9"
  },
  "security_deposit": {
    "value": "$11,000.00",
    "expected_confidence": ">0.85"
  }
}
```

## Automated Testing Commands

### Backend Tests

```bash
# Run all backend tests
docker exec legal-review-backend pytest

# Run with coverage
docker exec legal-review-backend pytest --cov=app

# Run specific test file
docker exec legal-review-backend pytest tests/test_extraction.py
```

### API Integration Tests

```bash
# Health check
curl http://localhost:8000/health

# Upload test document
curl -X POST http://localhost:8000/api/documents/upload \
  -F "files=@data/sample_nda.txt"

# Create project with template
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "template_id": 1}'

# Run extraction
curl -X POST http://localhost:8000/api/projects/1/extract

# Get values
curl http://localhost:8000/api/projects/1/values

# Export CSV
curl -o test_export.csv http://localhost:8000/api/projects/1/export/csv
```

### Frontend E2E Tests

```bash
# Run Playwright tests (if configured)
cd frontend && npx playwright test

# Visual regression tests
npx playwright test --update-snapshots
```

## Performance Benchmarks

| Operation | Target Time | Max Documents |
|-----------|-------------|---------------|
| Document upload | < 2s per file | 50 files |
| Single extraction | < 5s (AI), < 1s (pattern) | - |
| Full project extraction | < 30s | 10 documents |
| Values API response | < 500ms | 1000 values |
| CSV export | < 3s | 1000 values |
| Search query | < 200ms | 10000 values |

## Error Scenarios to Test

| Scenario | Expected Behavior |
|----------|-------------------|
| Upload invalid file type | 400 error, descriptive message |
| Create project without template | 400 error |
| Extract with no documents | 400 error |
| Approve non-existent value | 404 error |
| Search with empty query | 400 error |
| Export empty project | Empty file with headers |
| Network timeout during extraction | Partial results saved, status = error |
| Database connection lost | 500 error, graceful recovery |

## Validation Test Cases

| Field | Value | Rule | Expected Result |
|-------|-------|------|-----------------|
| Effective Date | "2025-01-01" | min_date: "2020-01-01" | ✅ Valid |
| Effective Date | "2019-12-31" | min_date: "2020-01-01" | ❌ Invalid |
| Contract Value | "$50,000" | min: 0 | ✅ Valid |
| Contract Value | "-$1,000" | positive_only: true | ❌ Invalid |
| Party Name | "ACME" | pattern: "^[A-Z]+" | ✅ Valid |
| Party Name | "acme" | pattern: "^[A-Z]+" | ❌ Invalid |
| Description | "Short" | min_length: 10 | ❌ Invalid |


