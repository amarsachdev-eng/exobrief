"""
EXOBRIEF — Demo Brief Rate Limiter (Supabase-backed)
Persists rate limit counts so they survive Railway redeploys/restarts.
Replaces the old in-memory _rate_limit_store dict, which reset on every deploy
and had a NameError bug (ExoBriefHandler vs ExobriefHandler) that broke the
endpoint entirely from 23 June onward.
 
SETUP (one-time):
Go to Supabase → SQL Editor → run:
 
CREATE TABLE demo_brief_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address text NOT NULL,
    requested_at timestamptz DEFAULT now()
);
CREATE INDEX idx_demo_brief_ip_time ON demo_brief_requests (ip_address, requested_at);
"""
 
import os
from datetime import datetime, timezone, timedelta
from supabase import create_client
 
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
 
PER_IP_DAILY_LIMIT = 3
GLOBAL_DAILY_LIMIT = 100  # hard cap across ALL IPs combined — stops distributed abuse
 
 
def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)
 
 
def _since_midnight_utc() -> str:
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.isoformat()
 
 
def check_and_record(ip_address: str) -> dict:
    """
    Checks whether this IP (and the global pool) is within limits.
    If allowed, records the request immediately (so concurrent requests
    can't race past the limit) and returns {"allowed": True, "remaining": N}.
    If not allowed, returns {"allowed": False, "reason": "..."} and does NOT
    call Claude — caller should return 429 without generating a brief.
    """
    client = get_client()
    since = _since_midnight_utc()
 
    try:
        # Global cap first — cheapest check, stops distributed/bot abuse
        global_result = client.table("demo_brief_requests") \
            .select("id", count="exact") \
            .gte("requested_at", since) \
            .execute()
        global_count = global_result.count or 0
 
        if global_count >= GLOBAL_DAILY_LIMIT:
            return {"allowed": False, "reason": "global_limit_reached"}
 
        # Per-IP cap
        ip_result = client.table("demo_brief_requests") \
            .select("id", count="exact") \
            .eq("ip_address", ip_address) \
            .gte("requested_at", since) \
            .execute()
        ip_count = ip_result.count or 0
 
        if ip_count >= PER_IP_DAILY_LIMIT:
            return {"allowed": False, "reason": "ip_limit_reached"}
 
        # Record this request now, before generation, so a slow/failed
        # generation can't be retried indefinitely to bypass the limit
        client.table("demo_brief_requests").insert({
            "ip_address": ip_address
        }).execute()
 
        return {
            "allowed": True,
            "remaining": PER_IP_DAILY_LIMIT - ip_count - 1
        }
 
    except Exception as e:
        # Fail CLOSED, not open — if Supabase is unreachable, block the
        # request rather than silently allowing unlimited Claude calls
        print(f"[RATE LIMIT] Error checking limits: {e}")
        return {"allowed": False, "reason": "rate_limit_check_failed"}
 
 
if __name__ == "__main__":
    print("[RATE LIMIT] Testing check_and_record for 127.0.0.1...")
    result = check_and_record("127.0.0.1")
    print(result)
