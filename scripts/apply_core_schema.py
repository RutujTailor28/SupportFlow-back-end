#!/usr/bin/env python3
"""Apply the Phase 2 core schema migration to Supabase PostgreSQL.

Requires SUPABASE_DB_URL in backend/.env — find it in Supabase Dashboard:
  Project Settings → Database → Connection string → URI

Usage:
    cd backend
    source venv/bin/activate
    python scripts/apply_core_schema.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SQL_FILE = BACKEND_ROOT / "sql" / "001_core_schema.sql"


def main() -> int:
    sys.path.insert(0, str(BACKEND_ROOT))

    from app.core.config import settings

    if not settings.SUPABASE_DB_URL:
        print("ERROR: SUPABASE_DB_URL is not set in backend/.env")
        print()
        print("Add your Supabase Postgres connection string, for example:")
        print("  SUPABASE_DB_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres")
        print()
        print("Or run the SQL manually in Supabase Dashboard → SQL Editor:")
        print(f"  {SQL_FILE}")
        return 1

    if not SQL_FILE.exists():
        print(f"ERROR: Migration file not found: {SQL_FILE}")
        return 1

    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 is required. Run: pip install psycopg2-binary")
        return 1

    sql = SQL_FILE.read_text(encoding="utf-8")
    print(f"Applying migration: {SQL_FILE.name}")

    try:
        with psycopg2.connect(settings.SUPABASE_DB_URL) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql)
        print("✓ Migration applied successfully")
    except Exception as exc:
        print(f"✗ Migration failed: {exc}")
        return 1

    from app.db.schema import verify_core_schema
    from app.db.supabase import init_supabase_clients

    init_supabase_clients()
    result = verify_core_schema()
    print("Schema verification:", result)
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
