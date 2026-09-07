"""Run a SQL migration file over SUPABASE_DB_URL (stdlib + psycopg).

Usage: python scripts/migrate.py db/migrations/001_porchlight_schema.sql
Prints only status lines and counts, never secret values.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_env(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/migrate.py <sql-file>")
        return 2
    import psycopg

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = load_env(os.path.join(root, ".env"))
    db_url = env.get("SUPABASE_DB_URL", "")
    if not db_url:
        print("migrate=BLOCKED missing SUPABASE_DB_URL in .env")
        return 2
    with open(os.path.join(root, sys.argv[1]), encoding="utf-8") as fh:
        sql = fh.read()
    try:
        with psycopg.connect(db_url, connect_timeout=20) as conn:
            conn.execute(sql)
            conn.commit()
            tables = sorted(
                r[0]
                for r in conn.execute(
                    "select tablename from pg_tables where schemaname='porchlight'"
                ).fetchall()
            )
    except Exception as exc:  # noqa: BLE001 - report class only, never values
        import re

        msg = re.sub(r"://[^@]*@", "://***@", str(exc))
        print(f"migrate=FAIL {type(exc).__name__} {msg[:300]}")
        return 1
    print("tables=" + str(len(tables)))
    print("migrate=" + ("PASS" if len(tables) == 9 else "CHECK:" + ",".join(tables)))
    return 0 if len(tables) == 9 else 1


if __name__ == "__main__":
    raise SystemExit(main())
