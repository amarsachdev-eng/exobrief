"""
EXOBRIEF — Outreach Tracker (Supabase-backed)
Replaces contacted.json with a persistent Supabase table.
Survives Railway redeploys.

SETUP (one-time):
1. Go to Supabase → SQL Editor → run the SQL below to create the table
2. Use this module instead of contacted.json in outreach_engine.py

CREATE TABLE outreach_contacted (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text UNIQUE NOT NULL,
    company text,
    batch text,
    contacted_at timestamptz DEFAULT now()
);
"""

import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")


def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def load_contacted() -> list:
    """Return list of email addresses already contacted"""
    client = get_client()
    try:
        result = client.table("outreach_contacted").select("email").execute()
        return [row["email"] for row in result.data]
    except Exception as e:
        print(f"[TRACKER] Error loading contacted list: {e}")
        print(f"[TRACKER] If table doesn't exist, run the CREATE TABLE SQL in the docstring")
        return []


def mark_contacted(email: str, company: str = "", batch: str = ""):
    """Record that an email was contacted — persists across redeploys"""
    client = get_client()
    try:
        client.table("outreach_contacted").insert({
            "email": email,
            "company": company,
            "batch": batch,
        }).execute()
        return True
    except Exception as e:
        print(f"[TRACKER] Error marking {email} as contacted: {e}")
        return False


def get_stats() -> dict:
    """Quick summary of outreach activity"""
    client = get_client()
    try:
        result = client.table("outreach_contacted").select("*").execute()
        rows = result.data
        
        batches = {}
        for row in rows:
            batch = row.get("batch", "unknown")
            batches[batch] = batches.get(batch, 0) + 1
        
        return {
            "total_contacted": len(rows),
            "by_batch": batches,
            "companies": [row["company"] for row in rows]
        }
    except Exception as e:
        print(f"[TRACKER] Error getting stats: {e}")
        return {"total_contacted": 0, "by_batch": {}, "companies": []}


if __name__ == "__main__":
    print("\n[OUTREACH TRACKER] Current status:\n")
    stats = get_stats()
    print(f"Total founders contacted: {stats['total_contacted']}")
    print(f"By batch: {stats['by_batch']}")
    print(f"\nCompanies contacted:")
    for c in stats['companies']:
        print(f"  - {c}")
