#!/usr/bin/env python3
"""Apply a SQL migration file to Supabase PostgreSQL.

Usage:
    python scripts/apply_migration.py sql/002_classification_schema.sql
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/apply_migration.py <sql-file>")
        return 1

    sys.path.insert(0, str(BACKEND_ROOT))
    from app.core.config import settings

    sql_path = Path(sys.argv[1])
    if not sql_path.is_absolute():
        sql_path = BACKEND_ROOT / sql_path

    if not settings.SUPABASE_DB_URL:
        print("ERROR: SUPABASE_DB_URL is not set in backend/.env")
        print(f"Or run manually in Supabase SQL Editor: {sql_path}")
        return 1

    if not sql_path.exists():
        print(f"ERROR: Migration file not found: {sql_path}")
        return 1

    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 is required. Run: pip install psycopg2-binary")
        return 1

    sql = sql_path.read_text(encoding="utf-8")
    print(f"Applying migration: {sql_path.name}")

    try:
        with psycopg2.connect(settings.SUPABASE_DB_URL) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql)
        print("✓ Migration applied successfully")
        return 0
    except Exception as exc:
        print(f"✗ Migration failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
