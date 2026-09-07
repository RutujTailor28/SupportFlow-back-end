# SupportFlow Backend — Complete File Guide

This document explains **every file** in the `backend/` folder, including what each line does.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Folder Structure](#folder-structure)
3. [Root Files](#root-files)
4. [app/main.py](#appmainpy)
5. [app/core/](#appcore)
6. [app/db/](#appdb)
7. [app/api/](#appapi)
8. [app/schemas/](#appschemas)
9. [app/services/](#appservices)
10. [sql/](#sql)
11. [scripts/](#scripts)
12. [API Endpoints Summary](#api-endpoints-summary)
13. [Request Flow](#request-flow)

---

## Architecture Overview

```text
Client (Postman / Next.js)
        ↓
   app/main.py          ← FastAPI app, CORS, error handlers
        ↓
   app/api/*.py         ← Thin route handlers (validate → call service → respond)
        ↓
   app/services/*.py    ← Business logic (no FastAPI imports)
        ↓
   app/db/supabase.py   ← Supabase PostgreSQL client
        ↓
   Supabase PostgreSQL
```

**Naming convention:**
- Database & Python internal: `snake_case`
- API JSON responses: `camelCase` (via `app/schemas/mappers.py`)

---

## Folder Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 ← FastAPI entry point
│   ├── api/                    ← HTTP routes
│   │   ├── tickets.py          ← Tickets, messages, classification
│   │   ├── system.py           ← Health / DB checks
│   │   ├── knowledge_base.py   ← Placeholder (Phase 8)
│   │   ├── rules.py            ← Placeholder (Phase 7)
│   │   └── analytics.py        ← Placeholder (Phase 10)
│   ├── core/                   ← Config, deps, errors, security
│   ├── db/                     ← Supabase client + schema checks
│   ├── schemas/                ← Pydantic models + mappers
│   └── services/               ← Business logic
├── sql/                        ← Database migrations
├── scripts/                    ← Migration runners
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── BACKEND_GUIDE.md            ← This file
```

---

## Root Files

### `requirements.txt`

| Line | Content | Purpose |
|------|---------|---------|
| 1 | `fastapi` | Web framework for building the REST API |
| 2 | `uvicorn[standard]` | ASGI server to run FastAPI |
| 3 | `pydantic` | Data validation and schema models |
| 4 | `pydantic-settings` | Load settings from `.env` file |
| 5 | `python-dotenv` | Read environment variables from `.env` |
| 6 | `supabase` | Official Supabase Python client |
| 7 | `python-jose[cryptography]` | JWT handling (future auth) |
| 8 | `passlib[bcrypt]` | Password hashing (future auth) |
| 9 | `httpx` | Async HTTP client (Supabase connection test) |
| 10 | `psycopg2-binary` | PostgreSQL driver (run SQL migrations) |

---

### `.env.example`

| Variable | Purpose |
|----------|---------|
| `APP_NAME` | API title shown in Swagger docs |
| `ENVIRONMENT` | `development` / `production` |
| `DEBUG` | Enable FastAPI debug mode |
| `HOST` | Server bind address (`0.0.0.0` = all interfaces) |
| `PORT` | Server port (8000) |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Public/publishable key (frontend-safe) |
| `SUPABASE_SERVICE_ROLE_KEY` | Secret key — **backend only**, bypasses RLS |
| `SUPABASE_DB_URL` | Optional Postgres URI for running migrations |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) |

Copy to `.env` and fill in your Supabase values. **Never commit `.env`.**

---

### `.gitignore`

Ignores Python cache (`__pycache__`), virtual env (`venv/`), secrets (`.env`), IDE files, and logs.

---

### `README.md`

Quick start: create venv, install deps, copy `.env`, run `uvicorn app.main:app --reload`.

---

## `app/main.py`

FastAPI application entry point (100 lines).

| Lines | Code | Explanation |
|-------|------|-------------|
| 1 | Module docstring | Describes this file's purpose |
| 3-4 | `asynccontextmanager`, `AsyncIterator` | For startup/shutdown lifecycle |
| 6-9 | FastAPI imports | Framework, validation errors, CORS, JSON responses |
| 11-14 | App imports | Routers, settings, Supabase helpers |
| 17-28 | `lifespan()` | Runs on server start: initializes Supabase, prints connection status |
| 31-35 | `FastAPI(...)` | Creates app with title from settings and lifespan hook |
| 37-43 | `CORSMiddleware` | Allows Next.js frontend (`localhost:3000`) to call the API |
| 46-59 | `app_error_handler` | Catches `AppError` → returns `{success: false, error: {...}}` |
| 62-76 | `validation_error_handler` | Catches invalid JSON/body → returns 422 with field errors |
| 79-83 | `include_router` | Registers all API routers under `/api/v1` |
| 86-89 | `GET /` | Root endpoint — confirms API is running |
| 92-99 | `GET /health` | Health check — `{success, status, service}` |

---

## `app/core/`

### `app/core/config.py`

Central configuration loaded from `.env`.

| Lines | Explanation |
|-------|-------------|
| 3 | `lru_cache` — settings loaded once and cached |
| 9-17 | `Settings` class config — reads `.env`, ignores unknown vars |
| 19-29 | All environment variables with defaults |
| 33-36 | `cors_origins_list` — splits `"http://localhost:3000,..."` into a list |
| 39-44 | `get_settings()` cached singleton → `settings` used everywhere |

---

### `app/core/deps.py`

FastAPI dependency injection for database clients.

| Lines | Function | Explanation |
|-------|----------|-------------|
| 10-21 | `get_db()` | Returns Supabase **admin** client (service role). Used by all services. Raises 503 if not configured. |
| 24-35 | `get_public_db()` | Returns Supabase **anon** client (respects RLS). For future user-scoped operations. |

---

### `app/core/exceptions.py`

Custom error classes with HTTP status codes.

| Class | Status | When used |
|-------|--------|-----------|
| `AppError` | 400 (default) | General application errors |
| `NotFoundError` | 404 | Resource not found |
| `TicketNotFoundError` | 404 | Ticket ID doesn't exist |
| `DatabaseError` | 500 | Supabase insert/update failed |

Each stores `message`, `code`, and `status_code` for the global error handler.

---

### `app/core/security.py`

**Placeholder** for future JWT authentication. Returns `{authenticated: false}`. Will later validate Supabase JWT tokens.

---

## `app/db/`

### `app/db/supabase.py`

Supabase client initialization (126 lines).

| Lines | Function | Explanation |
|-------|----------|-------------|
| 14-15 | `_supabase_client`, `_supabase_admin_client` | Singleton cached clients |
| 18-20 | `is_supabase_configured()` | True if URL + at least one key exist |
| 23-27 | `_create_client()` | Creates supabase-py client with given API key |
| 30-49 | `get_supabase_client()` | Anon/publishable key client (RLS enforced) |
| 52-71 | `get_supabase_admin_client()` | Service role client (bypasses RLS — backend use only) |
| 74-113 | `check_supabase_connection()` | HTTP GET to `/rest/v1/` to verify credentials work |
| 116-125 | `init_supabase_clients()` | Called on startup to eagerly create both clients |

---

### `app/db/schema.py`

Verifies database tables exist.

| Lines | Explanation |
|-------|-------------|
| 9-16 | `CORE_TABLES` — list of required table names |
| 19-48 | `verify_core_schema()` — tries `SELECT id LIMIT 1` on each table; returns `"ok"` or `"missing"` |

Tables checked: `profiles`, `customers`, `tickets`, `ticket_messages`, `ticket_classifications`, `classification_corrections`.

---

## `app/api/`

### `app/api/system.py`

Infrastructure test endpoints.

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/v1/system/database-test` | GET | `{success, database: "connected"}` |
| `/api/v1/system/schema-test` | GET | `{success, schema, tables: {...}}` |

---

### `app/api/tickets.py`

Main ticket API (165 lines). **Routes are thin** — they only call services and shape JSON responses.

| Lines | Endpoint | Method | Service |
|-------|----------|--------|---------|
| 19-21 | — | — | `get_ticket_service()` dependency |
| 24-26 | — | — | `get_message_service()` dependency |
| 29-31 | — | — | `get_classification_service()` dependency |
| 34-48 | `/api/v1/tickets` | POST | Create ticket + customer + first message |
| 51-77 | `/api/v1/tickets` | GET | List tickets with filters |
| 80-94 | `/api/v1/tickets/{id}/messages` | GET | List messages |
| 97-112 | `/api/v1/tickets/{id}/messages` | POST | Add message |
| 115-130 | `/api/v1/tickets/{id}/classification` | PATCH | Create/correct classification |
| 133-146 | `/api/v1/tickets/{id}` | GET | Full ticket detail |
| 149-164 | `/api/v1/tickets/{id}` | PATCH | Partial ticket update |

**Query filters for GET /tickets:** `status`, `category`, `urgency`, `sentiment`, `assignedTeam`, `search`

---

### `app/api/knowledge_base.py` *(placeholder)*

| Line | Explanation |
|------|-------------|
| 5 | Router prefix: `/kb-articles` |
| 8-11 | `GET /api/v1/kb-articles` — returns placeholder message (Phase 8) |

---

### `app/api/rules.py` *(placeholder)*

| Line | Explanation |
|------|-------------|
| 5 | Router prefix: `/routing-rules` |
| 8-11 | `GET /api/v1/routing-rules` — placeholder (Phase 7) |

---

### `app/api/analytics.py` *(placeholder)*

| Line | Explanation |
|------|-------------|
| 5 | Router prefix: `/analytics` |
| 8-11 | `GET /api/v1/analytics` — placeholder (Phase 10) |

---

## `app/schemas/`

Pydantic models for **request validation** and type safety.

### `app/schemas/ticket.py`

| Class | Purpose |
|-------|---------|
| `TicketStatus` | Enum: `new`, `open`, `pending`, `resolved`, `closed` |
| `TicketPriority` | Enum: `critical`, `high`, `normal`, `low` |
| `TicketChannel` | Enum: `web`, `email`, `chat`, `phone`, `api` |
| `TicketCreateRequest` | POST body — accepts camelCase (`customerName`, etc.) |
| `TicketUpdateRequest` | PATCH body — partial update fields |
| `CustomerSummary` | Customer object in responses |
| `MessageResponse` | Message object in responses |
| `TicketSummaryResponse` | Ticket in list/create responses |
| `TicketDetailResponse` | Full ticket detail shape |

`model_config = ConfigDict(populate_by_name=True)` allows both `customerName` (JSON) and `customer_name` (Python).

---

### `app/schemas/message.py`

| Class | Purpose |
|-------|---------|
| `MessageDirection` | `in` (customer → support) or `out` (support → customer) |
| `MessageSenderType` | `customer`, `agent`, `system`, `ai` |
| `MessageCreateRequest` | POST body: `direction`, `author`, `body` |

---

### `app/schemas/classification.py`

| Class | Purpose |
|-------|---------|
| `ClassificationUpdateRequest` | PATCH body: `category`, `subcategory`, `urgency`, `sentiment`, `language`, `intentSummary`, `entities`, `confidence`, `humanCorrected`, `notes` |

---

### `app/schemas/mappers.py`

Converts database rows (`snake_case`) → API JSON (`camelCase`).

| Function | Input | Output |
|----------|-------|--------|
| `map_customer()` | `customers` row | `{id, name, email, avatar, plan, isVip, ...}` |
| `map_message()` | `ticket_messages` row | `{senderType, senderName, content, timestamp, ...}` |
| `map_classification()` | classification + optional correction | `{category, urgency, humanCorrected, originalClassification, ...}` |
| `map_ticket_summary()` | ticket + customer rows | Ticket list item with camelCase |
| `map_ticket_detail()` | ticket + customer + messages + classification | Full detail object with `aiClassification` |

---

### `app/schemas/common.py`

Reusable response envelope types (`SuccessResponse`, `ErrorResponse`, `ListResponse`) for future use.

---

## `app/services/`

Business logic layer. **No FastAPI imports here.**

### `app/services/ticket_service.py` (209 lines)

| Method | What it does |
|--------|--------------|
| `_get_customer_by_email()` | Lookup customer by email |
| `_get_customer_by_id()` | Lookup customer by UUID |
| `_find_or_create_customer()` | Reuse existing customer or insert new one |
| `create_ticket()` | 1) Find/create customer 2) Insert ticket 3) Insert first message 4) Return summary |
| `get_tickets()` | Query tickets with filters, join customer data, return list |
| `get_ticket()` | Fetch ticket + customer + messages + classification |
| `update_ticket()` | Partial update; sets `resolved_at` when status → `resolved` |

---

### `app/services/message_service.py` (84 lines)

| Method | What it does |
|--------|--------------|
| `_get_ticket()` | Verify ticket exists (404 if not) |
| `_resolve_sender_type()` | `in` → customer, `out` → agent (unless overridden) |
| `create_message()` | Insert message; on first agent reply sets `first_response_at` and status `new` → `open` |
| `get_messages()` | List messages chronologically |

---

### `app/services/classification_service.py` (197 lines)

| Method | What it does |
|--------|--------------|
| `_get_classification()` | Get classification row for ticket |
| `_get_latest_correction()` | Get most recent human correction |
| `_sync_ticket_from_effective()` | Copy category/sentiment/urgency onto `tickets` table |
| `get_classification()` | Return effective classification (AI + corrections merged) |
| `update_classification()` | Create new OR record human correction (preserves original AI) |
| `create_ai_classification()` | For Phase 9 AI — creates AI-sourced classification |

**Correction logic:** Original AI row is never overwritten. Corrections go to `classification_corrections` table. Response includes `originalClassification`.

---

### Stub services *(not implemented yet)*

| File | Phase | Future purpose |
|------|-------|----------------|
| `escalation_service.py` | 6 | Churn risk, legal language, SLA detection |
| `routing_service.py` | 7 | Rule-based team assignment |
| `rag_service.py` | 8-9 | Knowledge base search, AI replies |
| `analytics_service.py` | 10 | Dashboard metrics |

Each method raises `NotImplementedError` until its phase is built.

---

## `sql/`

### `sql/001_core_schema.sql` (176 lines)

Creates Phase 2 tables:

| Table | Key columns |
|-------|-------------|
| `profiles` | App users (agents/admins): `email`, `full_name`, `role` |
| `customers` | Support customers: `name`, `email`, `plan`, `is_vip` |
| `tickets` | Core tickets: `ticket_number`, `subject`, `body`, `status`, `priority`, `sla_due_at` |
| `ticket_messages` | Conversation: `sender_type`, `body`, `direction` |

Also creates:
- `ticket_number_seq` — auto-generates `#TK-48291` format
- Triggers for `updated_at` and ticket number generation
- Indexes for performance
- Row Level Security (enabled; service role bypasses)

---

### `sql/002_classification_schema.sql` (71 lines)

Creates Phase 5 tables:

| Table | Purpose |
|-------|---------|
| `ticket_classifications` | One AI/manual classification per ticket (`ticket_id` UNIQUE) |
| `classification_corrections` | Human corrections (many per ticket allowed) |

---

## `scripts/`

### `scripts/apply_core_schema.py`

Runs `sql/001_core_schema.sql` via `psycopg2` if `SUPABASE_DB_URL` is set. Verifies schema after.

### `scripts/apply_migration.py`

Generic runner: `python scripts/apply_migration.py sql/002_classification_schema.sql`

---

## API Endpoints Summary

### Implemented ✅

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | API running check |
| GET | `/health` | Health check |
| GET | `/api/v1/system/database-test` | Supabase connection test |
| GET | `/api/v1/system/schema-test` | Database tables check |
| POST | `/api/v1/tickets` | Create ticket |
| GET | `/api/v1/tickets` | List tickets |
| GET | `/api/v1/tickets/{id}` | Get ticket detail |
| PATCH | `/api/v1/tickets/{id}` | Update ticket |
| GET | `/api/v1/tickets/{id}/messages` | List messages |
| POST | `/api/v1/tickets/{id}/messages` | Add message |
| PATCH | `/api/v1/tickets/{id}/classification` | Set/correct classification |

### Placeholder ⏳

| Method | URL | Phase |
|--------|-----|-------|
| GET | `/api/v1/kb-articles` | 8 |
| GET | `/api/v1/routing-rules` | 7 |
| GET | `/api/v1/analytics` | 10 |

---

## Request Flow

Example: **Create a ticket**

```text
POST /api/v1/tickets
  Body: { customerName, customerEmail, subject, body, channel }
        ↓
  tickets.py → create_ticket()
        ↓
  TicketService.create_ticket()
    1. Find or create customer in `customers` table
    2. Insert row in `tickets` table (ticket_number auto-generated)
    3. Insert first message in `ticket_messages` table
    4. map_ticket_summary() → camelCase JSON
        ↓
  Response: { success: true, data: { id, ticketNumber, customerName, ... } }
```

Example: **Human classification correction**

```text
PATCH /api/v1/tickets/{id}/classification
  Body: { category: "Technical", humanCorrected: true }
        ↓
  ClassificationService.update_classification()
    1. Verify ticket exists
    2. Load existing AI classification (NOT overwritten)
    3. Insert correction into `classification_corrections`
    4. Set human_corrected=true flag on classification row
    5. Sync category/sentiment/priority onto `tickets` table
    6. Return effective classification with originalClassification
```

---

## How to Run

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in Supabase keys
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## Implementation Phases

| Phase | Status | What was built |
|-------|--------|----------------|
| 0 | ✅ | FastAPI foundation, health endpoints |
| 1 | ✅ | Supabase connection |
| 2 | ✅ | Core DB tables (customers, tickets, messages) |
| 3 | ✅ | Ticket CRUD API |
| 4 | ✅ | Messages API |
| 5 | ✅ | Classification API |
| 6 | ⏳ | Escalations |
| 7 | ⏳ | Routing rules |
| 8 | ⏳ | Knowledge base CRUD |
| 9 | ⏳ | AI features (draft, similar tickets) |
| 10 | ⏳ | Analytics |

---

*Generated for SupportFlow backend — last updated Phase 5.*
