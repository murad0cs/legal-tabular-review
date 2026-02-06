# Legal Tabular Review

Extract key fields from legal documents and compare them side-by-side in a structured table.

Built for legal teams who need to review multiple contracts, NDAs, or lease agreements efficiently.

## What It Does

- Upload PDF/DOCX legal documents
- Define custom field templates (parties, dates, amounts, clauses)
- Extract fields using AI or pattern matching
- Review extracted values with confidence scores and citations
- Export results to CSV or Excel

## Project Structure

```
legal-tabular-review/
├── backend/                 # Python FastAPI server
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routes/          # API endpoints
│   │   ├── schemas/         # Request/response schemas
│   │   └── services/        # Business logic
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # React + Vite app
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Route pages
│   │   └── api/             # API client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

**Note:** If your project folder is named something generic like "New folder", rename it to `legal-tabular-review` for clarity.

## Quick Start

### Using Docker (recommended)

```bash
docker-compose up -d
```

Then open:
- App: http://localhost:3000
- API docs: http://localhost:8000/docs

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
pnpm install
pnpm dev
```

## Configuration

Set these in `.env` or pass to Docker:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite or PostgreSQL connection | `sqlite:///./legal_review.db` |
| `OPENAI_API_KEY` | Enables AI extraction (optional) | - |
| `UPLOAD_DIR` | Where uploaded files are stored | `./uploads` |

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/documents/upload` | Upload PDF/DOCX files |
| `GET /api/templates` | List extraction templates |
| `POST /api/projects/{id}/extract` | Run field extraction |
| `GET /api/projects/{id}/values` | Get extracted values |
| `GET /api/projects/{id}/export/excel` | Download as Excel |

Full API docs at `/docs` when running.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **Frontend:** React 18, Vite, TailwindCSS
- **AI:** OpenAI API (optional, falls back to pattern matching)

## License

MIT
