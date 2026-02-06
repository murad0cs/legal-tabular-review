# Functional Design

## User Flows

### 1. Template Creation Flow

```
┌─────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Start  │───▶│  Templates  │───▶│   Create     │───▶│  Add Fields │
│         │    │    List     │    │   Template   │    │  Configure  │
└─────────┘    └─────────────┘    └──────────────┘    └─────────────┘
                                                             │
                     ┌──────────────────────────────────────┘
                     ▼
         ┌─────────────────────┐    ┌─────────────────┐
         │  Set Validation     │───▶│  Save Template  │
         │  Rules (optional)   │    │                 │
         └─────────────────────┘    └─────────────────┘
```

**Steps:**
1. Navigate to Templates page
2. Click "New Template"
3. Enter template name, description, document type
4. Add fields with:
   - Field name (internal identifier)
   - Field label (display name)
   - Field type (text, date, currency, party, clause, number)
   - Normalization rule (iso_date, currency_usd, uppercase, etc.)
   - Validation rules (pattern, min/max values, required)
5. Reorder fields via drag-and-drop
6. Save template

### 2. Document Upload Flow

```
┌─────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Start  │───▶│  Documents  │───▶│   Upload     │───▶│  Processing │
│         │    │    Page     │    │   Files      │    │   Queue     │
└─────────┘    └─────────────┘    └──────────────┘    └─────────────┘
                                                             │
                                                             ▼
                                                   ┌─────────────────┐
                                                   │  Document Ready │
                                                   │  (Content Parsed)│
                                                   └─────────────────┘
```

**Supported Formats:**
- Text files (.txt)
- PDF files (.pdf) - text extraction
- Future: DOCX, images with OCR

### 3. Project Setup Flow

```
┌─────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Start  │───▶│  Projects   │───▶│   Create     │───▶│   Select    │
│         │    │    List     │    │   Project    │    │  Template   │
└─────────┘    └─────────────┘    └──────────────┘    └─────────────┘
                                                             │
                     ┌──────────────────────────────────────┘
                     ▼
         ┌─────────────────────┐    ┌─────────────────┐
         │  Add Documents      │───▶│  Run Extraction │
         │  to Project         │    │                 │
         └─────────────────────┘    └─────────────────┘
```

### 4. Extraction & Review Flow

```
┌───────────────┐    ┌─────────────────┐    ┌───────────────────────┐
│  Project View │───▶│  Run Extraction │───▶│  Review Table         │
│               │    │  (AI/Pattern)   │    │  (Side-by-Side View)  │
└───────────────┘    └─────────────────┘    └───────────────────────┘
                                                      │
        ┌──────────────────────────────────────────────┤
        │                    │                         │
        ▼                    ▼                         ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────────────┐
│  Approve Value│    │  Reject Value │    │  Edit Value           │
│               │    │               │    │  (Manual Correction)  │
└───────────────┘    └───────────────┘    └───────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Export       │
                    │  (CSV/Excel)  │
                    └───────────────┘
```

## API Behaviors

### Documents API

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/documents` | GET | List all documents | `{ documents: [...] }` |
| `/api/documents/{id}` | GET | Get document details | Document object |
| `/api/documents/{id}/content` | GET | Get document text content | `{ content: "..." }` |
| `/api/documents/upload` | POST | Upload files (multipart) | `{ documents: [...] }` |
| `/api/documents/{id}` | DELETE | Delete document | `{ message: "..." }` |

### Templates API

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/templates` | GET | List all templates | `{ templates: [...] }` |
| `/api/templates/{id}` | GET | Get template with fields | Template object |
| `/api/templates` | POST | Create template | Template object |
| `/api/templates/{id}` | PUT | Update template | Template object |
| `/api/templates/{id}` | DELETE | Delete template | `{ message: "..." }` |
| `/api/templates/{id}/fields` | POST | Add field | Field object |
| `/api/templates/{id}/fields/{fid}` | PUT | Update field | Field object |
| `/api/templates/{id}/fields/{fid}` | DELETE | Delete field | `{ message: "..." }` |
| `/api/templates/{id}/export` | GET | Export as JSON | Template JSON |
| `/api/templates/import` | POST | Import from JSON | Template object |

### Projects API

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/projects` | GET | List all projects | `{ projects: [...] }` |
| `/api/projects/{id}` | GET | Get project with details | Project object |
| `/api/projects` | POST | Create project | Project object |
| `/api/projects/{id}` | PUT | Update project | Project object |
| `/api/projects/{id}` | DELETE | Delete project | `{ message: "..." }` |
| `/api/projects/{id}/documents` | POST | Add documents | `{ message: "...", document_ids: [...] }` |
| `/api/projects/{id}/documents/{did}` | DELETE | Remove document | `{ message: "..." }` |
| `/api/projects/{id}/extract` | POST | Run extraction | `{ message: "...", count: N }` |
| `/api/projects/{id}/re-extract` | POST | Re-run extraction | `{ message: "...", validation: {...} }` |
| `/api/projects/{id}/values` | GET | Get all extracted values | `{ values: [...], validation_summary: {...} }` |
| `/api/projects/values/{vid}` | PUT | Update value | ExtractedValue object |
| `/api/projects/values/{vid}/approve` | POST | Approve value | ExtractedValue object |
| `/api/projects/values/{vid}/reject` | POST | Reject value | ExtractedValue object |
| `/api/projects/values/bulk/approve` | POST | Bulk approve | `{ count: N, updated_ids: [...] }` |
| `/api/projects/values/bulk/reject` | POST | Bulk reject | `{ count: N, updated_ids: [...] }` |

### Search API

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/search?q=...` | GET | Search values | `{ results: [...], total: N }` |
| `/api/search/field-types` | GET | Get available field types | `{ field_types: [...] }` |
| `/api/search/suggestions?q=...` | GET | Get suggestions | `{ suggestions: [...] }` |

### Export API

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/projects/{id}/export/csv` | GET | Export as CSV | CSV file blob |
| `/api/projects/{id}/export/excel` | GET | Export as Excel | XLSX file blob |

## Status Transitions

### Document Status

```
┌──────────┐    ┌────────────┐    ┌─────────┐
│ uploaded │───▶│ processing │───▶│  ready  │
└──────────┘    └────────────┘    └─────────┘
                      │
                      ▼
               ┌────────────┐
               │   error    │
               └────────────┘
```

### Project Status

```
┌─────────┐    ┌─────────────┐    ┌──────────────┐    ┌───────────┐
│  draft  │───▶│ in_progress │───▶│ needs_review │───▶│ completed │
└─────────┘    └─────────────┘    └──────────────┘    └───────────┘
```

### ExtractedValue Status

```
┌─────────┐    ┌──────────┐
│ pending │───▶│ approved │
└─────────┘    └──────────┘
     │              ▲
     │              │
     ▼              │
┌──────────┐    ┌────────┐
│ rejected │    │ edited │
└──────────┘    └────────┘
```

## Edge Cases

### Document Upload
| Scenario | Handling |
|----------|----------|
| Unsupported file type | Return 400 with error message |
| Empty file | Accept with warning, content = "" |
| Large file (>50MB) | Return 413 Payload Too Large |
| Duplicate filename | Accept with UUID prefix |
| PDF with no text | Store with empty content, status = "error" |

### Extraction
| Scenario | Handling |
|----------|----------|
| No OpenAI API key | Fall back to pattern matching |
| Field not found in document | Store with null value, confidence = 0 |
| Multiple matches | Use first match, lower confidence |
| Invalid date format | Store raw value, normalization = null |
| Template has no fields | Return error, no extraction |

### Review
| Scenario | Handling |
|----------|----------|
| Approve already approved | No-op, return current state |
| Edit approved value | Change status to "edited" |
| Delete document in project | Cascade delete extracted values |
| Re-extract after edits | Clear previous values, fresh extraction |

### Validation
| Scenario | Handling |
|----------|----------|
| Required field missing | Add validation error |
| Value doesn't match pattern | Add validation error |
| Date outside range | Add validation error |
| Currency negative when positive_only | Add validation error |

## Field Types & Normalization

### Supported Field Types

| Type | Description | Normalization Options |
|------|-------------|----------------------|
| `text` | Free-form text | `uppercase`, `lowercase`, `trim` |
| `date` | Date values | `iso_date` (YYYY-MM-DD) |
| `currency` | Monetary amounts | `currency_usd` ($X,XXX.XX) |
| `party` | Party names | `uppercase` |
| `clause` | Contract clauses | `trim` |
| `number` | Numeric values | (none) |

### Validation Rules Schema

```json
{
  "pattern": "^[A-Z]{2}\\d{6}$",    // Regex pattern
  "min": 0,                          // Min value (number/currency)
  "max": 1000000,                    // Max value (number/currency)
  "min_date": "2020-01-01",          // Min date (YYYY-MM-DD)
  "max_date": "2030-12-31",          // Max date (YYYY-MM-DD)
  "min_length": 1,                   // Min text length
  "max_length": 1000,                // Max text length
  "positive_only": true              // Only positive numbers
}
```

## Keyboard Shortcuts (Review Table)

| Key | Action |
|-----|--------|
| `A` | Approve focused cell |
| `R` | Reject focused cell |
| `E` | Edit focused cell |
| `↑/↓` | Navigate rows |
| `←/→` | Navigate columns |
| `Ctrl+A` | Select all visible |
| `Escape` | Clear selection |
| `?` | Show shortcuts help |

## Export Format

### CSV Structure
```
Field,Document1_Value,Document1_Citation,Document1_Confidence,Document2_Value,...
Effective Date,2024-01-01,"Section 1.1",0.95,2024-02-15,"Paragraph 2",0.87
Contract Value,"$50,000.00","Article 3",0.92,"$75,000.00","Section 4.2",0.89
...
```

### Excel Structure
- Sheet 1: "Extracted Values" - Main data grid
- Header row with document names
- Each row is a field
- Cells contain: Value (Citation) [Confidence%]


