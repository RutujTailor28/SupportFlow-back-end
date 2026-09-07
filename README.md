# AI Support Ticket Triage & Reply Assistant — Backend

FastAPI backend for the AI Support Ticket Triage & Reply Assistant.

## Tech Stack

- FastAPI
- Python
- Supabase
- PostgreSQL

## Setup Instructions

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate on macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy the environment file:

```bash
cp .env.example .env
```

Run the server:

```bash
uvicorn app.main:app --reload
```

## Endpoints

| Resource | URL |
| --- | --- |
| Server | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

### API prefixes

- `GET /api/v1/tickets`
- `GET /api/v1/kb-articles`
- `GET /api/v1/routing-rules`
- `GET /api/v1/analytics`

## Project Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── schemas/
│   ├── core/
│   └── db/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Notes

- Supabase credentials are optional for local startup.
- Authentication, RAG, and AI classification are not implemented in this foundation setup.
