"""
EXOBRIEF — Subscriber Management
Handles subscriber profiles, brief history, and company memory
Uses Supabase as the database layer
"""

import os
from supabase import create_client, Client
from datetime import datetime, timezone

# ============================================================
# SUPABASE CONFIGURATION
# Add these to Railway environment variables
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================================
# DATABASE SCHEMA — Run this SQL in Supabase SQL Editor
# ============================================================

SCHEMA_SQL = """
-- EXOBRIEF Subscribers Table
CREATE TABLE IF NOT EXISTS subscribers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    company_url TEXT,
    sector TEXT NOT NULL,
    geography TEXT NOT NULL,
    competitors TEXT[],
    strategic_priorities TEXT,
    biggest_concern TEXT,
    customer_type TEXT DEFAULT 'B2B',
    stripe_customer_id TEXT,
    subscription_status TEXT DEFAULT 'trial',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_brief_at TIMESTAMP WITH TIME ZONE,
    brief_count INTEGER DEFAULT 0
);

-- EXOBRIEF Briefs Table (Company Memory Layer)
CREATE TABLE IF NOT EXISTS briefs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    subscriber_id UUID REFERENCES subscribers(id),
    email TEXT NOT NULL,
    brief_content TEXT NOT NULL,
    brief_summary TEXT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered BOOLEAN DEFAULT FALSE,
    week_number INTEGER,
    year INTEGER
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
CREATE INDEX IF NOT EXISTS idx_briefs_subscriber ON briefs(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_briefs_email ON briefs(email);
"""


# ============================================================
# SUBSCRIBER OPERATIONS
# ============================================================

def get_all_active_subscribers() -> list:
    """Get all subscribers who should receive a brief this week"""
    try:
        supabase = get_supabase()
        result = supabase.table("subscribers")\
            .select("*")\
            .in_("subscription_status", ["trial", "active"])\
            .execute()
        return result.data
    except Exception as e:
        print(f"Error fetching subscribers: {str(e)}")
        return []


def get_subscriber_by_email(email: str) -> dict:
    """Get a single subscriber by email"""
    try:
        supabase = get_supabase()
        result = supabase.table("subscribers")\
            .select("*")\
            .eq("email", email)\
            .single()\
            .execute()
        return result.data
    except Exception as e:
        print(f"Error fetching subscriber {email}: {str(e)}")
        return {}


def create_subscriber(subscriber_data: dict) -> dict:
    """Create a new subscriber after Stripe payment"""
    try:
        supabase = get_supabase()
        result = supabase.table("subscribers")\
            .insert(subscriber_data)\
            .execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        print(f"Error creating subscriber: {str(e)}")
        return {}


def update_subscriber_brief_count(email: str):
    """Update brief count and last brief timestamp"""
    try:
        supabase = get_supabase()
        # Get current count
        subscriber = get_subscriber_by_email(email)
        current_count = subscriber.get("brief_count", 0)

        supabase.table("subscribers")\
            .update({
                "brief_count": current_count + 1,
                "last_brief_at": datetime.now(timezone.utc).isoformat()
            })\
            .eq("email", email)\
            .execute()
    except Exception as e:
        print(f"Error updating brief count for {email}: {str(e)}")


# ============================================================
# COMPANY MEMORY LAYER — The core moat
# ============================================================

def save_brief(email: str, subscriber_id: str, brief_content: str):
    """Save generated brief to database — builds company memory"""
    try:
        supabase = get_supabase()
        now = datetime.now(timezone.utc)

        # Generate a short summary for the memory layer
        summary = brief_content[:500] + "..." if len(brief_content) > 500 else brief_content

        supabase.table("briefs").insert({
            "subscriber_id": subscriber_id,
            "email": email,
            "brief_content": brief_content,
            "brief_summary": summary,
            "generated_at": now.isoformat(),
            "week_number": now.isocalendar()[1],
            "year": now.year,
            "delivered": False
        }).execute()

        print(f"  ✓ Brief saved to database for {email}")
    except Exception as e:
        print(f"  ✗ Error saving brief for {email}: {str(e)}")


def get_previous_briefs_summary(email: str, limit: int = 4) -> str:
    """
    Retrieve last N brief summaries for company memory context
    This is what makes EXOBRIEF smarter over time
    """
    try:
        supabase = get_supabase()
        result = supabase.table("briefs")\
            .select("brief_summary, generated_at, week_number")\
            .eq("email", email)\
            .order("generated_at", desc=True)\
            .limit(limit)\
            .execute()

        if not result.data:
            return "First brief — no previous context available"

        summaries = []
        for brief in reversed(result.data):
            week = brief.get("week_number", "?")
            date = brief.get("generated_at", "")[:10]
            summary = brief.get("brief_summary", "")
            summaries.append(f"[Week {week} — {date}]: {summary}")

        return "\n\n".join(summaries)
    except Exception as e:
        print(f"Error fetching previous briefs for {email}: {str(e)}")
        return "Previous brief history unavailable"


def mark_brief_delivered(email: str):
    """Mark the latest brief as delivered"""
    try:
        supabase = get_supabase()
        # Get the latest undelivered brief
        result = supabase.table("briefs")\
            .select("id")\
            .eq("email", email)\
            .eq("delivered", False)\
            .order("generated_at", desc=True)\
            .limit(1)\
            .execute()

        if result.data:
            brief_id = result.data[0]["id"]
            supabase.table("briefs")\
                .update({"delivered": True})\
                .eq("id", brief_id)\
                .execute()
    except Exception as e:
        print(f"Error marking brief delivered for {email}: {str(e)}")


# ============================================================
# PRINT SCHEMA FOR SETUP
# ============================================================

if __name__ == "__main__":
    print("EXOBRIEF — Supabase Schema")
    print("=" * 60)
    print("Run this SQL in your Supabase SQL Editor:")
    print("=" * 60)
    print(SCHEMA_SQL)
