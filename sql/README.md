# Phase 2 — Core database schema

## Tables

| Table | Purpose |
| --- | --- |
| `profiles` | Application users (support agents/admins) |
| `customers` | Support customers who submit tickets |
| `tickets` | Core support tickets |
| `ticket_messages` | Conversation messages on tickets |

## Relationships

```text
profiles
   └── assigned_agent_id on tickets

customers
   └── tickets (customer_id)
          └── ticket_messages (ticket_id)
```

## Apply migration

### Option A — Supabase SQL Editor (recommended if no DB URL)

1. Open [Supabase Dashboard](https://supabase.com/dashboard) → your project → **SQL Editor**
2. Paste the contents of `sql/001_core_schema.sql`
3. Click **Run**

### Option B — Python script

1. Add your Postgres connection string to `backend/.env`:

```env
SUPABASE_DB_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

Find it under **Project Settings → Database → Connection string → URI**.

2. Run:

```bash
cd backend
source venv/bin/activate
pip install psycopg2-binary
python scripts/apply_core_schema.py
```

## Verify

```bash
curl http://localhost:8000/api/v1/system/schema-test
```

Expected when tables exist:

```json
{
  "success": true,
  "schema": "ready",
  "tables": {
    "profiles": "ok",
    "customers": "ok",
    "tickets": "ok",
    "ticket_messages": "ok"
  }
}
```

Also check **Supabase → Table Editor** for the four tables.

## Phase 5 — Classification tables

Run `sql/002_classification_schema.sql` in Supabase SQL Editor (same process as Phase 2).

Verify:

```bash
curl http://localhost:8000/api/v1/system/schema-test
```

Expected additional tables:

- `ticket_classifications`
- `classification_corrections`

## Phase 6 — Escalation table

Run `sql/003_escalation_schema.sql` in Supabase SQL Editor.

Verify `ticket_escalations` appears as `"ok"` in schema-test.

## Phase 7 — Routing rules table

Run `sql/004_routing_rules_schema.sql` in Supabase SQL Editor.

Verify `routing_rules` appears as `"ok"` in schema-test.

## Phase 8 — Knowledge base table

Run `sql/005_kb_articles_schema.sql` in Supabase SQL Editor.

Verify `kb_articles` appears as `"ok"` in schema-test.

This phase is **CRUD only** — no embeddings, chunking, or RAG yet.
