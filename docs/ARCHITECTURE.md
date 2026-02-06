# Architecture Design

## System Overview

Legal Tabular Review is a full-stack application for extracting key fields from legal documents and presenting them in a structured table for side-by-side comparison and review.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Dashboard  │  │  Templates  │  │  Projects   │  │  Review Table       │ │
│  │  Overview   │  │  Editor     │  │  Manager    │  │  (Side-by-Side)     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                              │                                               │
│                     [Axios API Client + React Context]                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                              [HTTP REST API]
                                      │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI + Python)                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          API Routes Layer                             │   │
│  │  /documents  /templates  /projects  /search  /validation  /exports   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Services Layer                                │   │
│  │  DocumentService │ TemplateService │ ExtractionService │ Normalizer  │   │
│  │  ProjectService  │ SearchService   │ ValidationService │ ExportService│   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          Data Layer (SQLAlchemy)                      │   │
│  │  Document │ Template │ TemplateField │ Project │ ExtractedValue      │   │
│  │  Comment  │ AuditLog │ ProjectSettings                                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                              [SQLite Database]
                                      │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            STORAGE                                           │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │  /uploads       │    │  /data          │    │  legal_review.db        │  │
│  │  (Documents)    │    │  (Sample Data)  │    │  (SQLite Database)      │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Boundaries

### Frontend Components

| Component | Responsibility | Dependencies |
|-----------|----------------|--------------|
| `Dashboard` | Overview stats, quick actions | API client |
| `Templates` | Template listing and management | API client |
| `TemplateEditor` | Field configuration, validation rules | API client |
| `Projects` | Project listing and creation | API client |
| `ProjectView` | Project details, document management | API client |
| `ReviewTable` | Side-by-side comparison, approval workflow | API client, Analytics |
| `Analytics` | Extraction statistics visualization | Recharts |
| `DocumentPreview` | Document viewer with citation highlighting | API client |

### Backend Services

| Service | Responsibility | Dependencies |
|---------|----------------|--------------|
| `DocumentService` | File upload, content extraction, storage | SQLAlchemy |
| `TemplateService` | Template CRUD, field management | SQLAlchemy |
| `ProjectService` | Project lifecycle, document association | SQLAlchemy |
| `ExtractionService` | AI/Pattern extraction, normalization | OpenAI API (optional), Normalizer |
| `ValidationService` | Field validation against rules | SQLAlchemy |
| `SearchService` | Cross-project value search | SQLAlchemy |
| `ExportService` | CSV/Excel generation | pandas, openpyxl |
| `Normalizer` | Date, currency, text normalization | - |
| `AuditService` | Activity logging | SQLAlchemy |

## Data Flow

### Document Upload Flow
```
1. User uploads file(s) → Frontend FileUpload component
2. POST /api/documents/upload → Backend DocumentService
3. File saved to /uploads directory
4. Content extracted (text parsing)
5. Document record created in DB
6. Response returned to frontend
```

### Extraction Flow
```
1. User triggers extraction → POST /api/projects/{id}/extract
2. ExtractionService retrieves project documents
3. For each document:
   a. Load document content
   b. For each template field:
      - If OpenAI configured: AI extraction with prompt
      - Else: Pattern-based regex extraction
   c. Normalize extracted values
   d. Calculate confidence scores
   e. Store ExtractedValue records
4. Run ValidationService to check values against rules
5. Return extraction summary
```

### Review Workflow
```
1. User opens ReviewTable → GET /api/projects/{id}/values
2. Values displayed in side-by-side grid (documents as columns)
3. User actions:
   - Approve: POST /api/projects/values/{id}/approve
   - Reject: POST /api/projects/values/{id}/reject
   - Edit: PUT /api/projects/values/{id}
   - Bulk approve/reject: POST /api/projects/values/bulk/approve
4. Changes logged to AuditLog
5. Real-time UI updates
```

### Export Flow
```
1. User clicks Export → GET /api/projects/{id}/export/csv (or /excel)
2. ExportService builds data matrix:
   - Rows: Template fields
   - Columns: Documents
   - Cells: value | citation | confidence
3. Generate file (CSV or XLSX)
4. Return as downloadable blob
```

## Storage Design

### Database Schema (SQLite)

```sql
-- Core tables
documents (id, original_filename, file_type, file_path, content, status, ...)
templates (id, name, description, document_type, version, ...)
template_fields (id, template_id, field_name, field_label, field_type, 
                 normalization_rule, validation_rules, is_required, order_index)
projects (id, name, description, template_id, status, ...)
project_documents (id, project_id, document_id, added_at)
extracted_values (id, document_id, template_field_id, project_id,
                  raw_value, normalized_value, confidence, 
                  citation, citation_text, status, validation_errors, ...)

-- Supporting tables
comments (id, extracted_value_id, user_name, text, ...)
audit_logs (id, project_id, action, user_name, details, timestamp)
project_settings (id, project_id, auto_approve_enabled, auto_approve_threshold)
```

### File Storage

```
/uploads/
  ├── {uuid}_original_filename.txt
  ├── {uuid}_contract.pdf
  └── ...

/data/
  ├── sample_contract.txt
  ├── sample_lease.txt
  └── sample_nda.txt
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 18 + Vite | UI framework |
| Styling | Tailwind CSS | Utility-first CSS |
| Charts | Recharts | Analytics visualization |
| HTTP Client | Axios | API communication |
| Backend | FastAPI | REST API framework |
| ORM | SQLAlchemy | Database abstraction |
| Database | SQLite | Data persistence |
| AI (Optional) | OpenAI GPT-4 | Intelligent extraction |
| Export | pandas, openpyxl | CSV/Excel generation |
| Containerization | Docker, Docker Compose | Deployment |

## Security Considerations

1. **Input Validation**: All API inputs validated via Pydantic schemas
2. **CORS**: Configured for specific origins
3. **File Upload**: Type validation, size limits
4. **SQL Injection**: Prevented via SQLAlchemy ORM
5. **Error Handling**: Generic error messages to clients

## Scalability Notes

For production deployment:
- Replace SQLite with PostgreSQL
- Add Redis for caching
- Use S3/blob storage for documents
- Implement JWT authentication
- Add rate limiting
- Use background job queue (Celery) for extractions


