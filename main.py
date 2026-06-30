"""
EXOBRIEF — Main Scheduler
Runs every Sunday at 17:00 UTC (6pm BST / 9pm GST)
Generates and delivers briefs to all active subscribers
Architecture mirrors PRISM's agent loop pattern
"""

import os
import time
import schedule
from datetime import datetime, timezone
from brief_engine import generate_brief
from subscriber_manager import (
    get_all_active_subscribers,
    get_previous_briefs_summary,
    save_brief,
    mark_brief_delivered,
    update_subscriber_brief_count
)
from email_delivery import send_brief
from intent_monitor import run as run_intent_monitor

# ============================================================
# CONFIGURATION
# ============================================================

BRIEF_RUN_TIME = "17:00"  # UTC — 6pm BST / 9pm GST
RUN_DAY = "sunday"


# ============================================================
# MAIN BRIEF CYCLE
# ============================================================

def run_brief_cycle():
    """
    Main function — runs every Sunday
    Generates and delivers briefs to all active subscribers
    """
    start_time = datetime.now(timezone.utc)
    print("\n" + "=" * 60)
    print(f"EXOBRIEF — Brief Cycle Starting")
    print(f"Time: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    # Get all active subscribers
    subscribers = get_all_active_subscribers()

    if not subscribers:
        print("No active subscribers found. Cycle complete.")
        return

    print(f"Found {len(subscribers)} active subscriber(s)")
    print("-" * 60)

    success_count = 0
    fail_count = 0

    for subscriber in subscribers:
        email = subscriber.get("email", "")
        company = subscriber.get("company_name", "Unknown")
        sub_id = subscriber.get("id", "")

        print(f"\nProcessing: {company} ({email})")

        try:
            # Build full subscriber profile with company memory
            subscriber_profile = {
                "company_name": company,
                "company_url": subscriber.get("company_url", ""),
                "sector": subscriber.get("sector", "Technology"),
                "geography": subscriber.get("geography", "United Kingdom"),
                "competitors": subscriber.get("competitors", []),
                "strategic_priorities": subscriber.get("strategic_priorities", ""),
                "biggest_concern": subscriber.get("biggest_concern", ""),
                "customer_type": subscriber.get("customer_type", "B2B"),
                "previous_briefs_summary": get_previous_briefs_summary(email)
            }

            # Generate the brief
            brief_content = generate_brief(subscriber_profile)

            if "error" in brief_content.lower() and len(brief_content) < 200:
                print(f"  ✗ Brief generation failed for {company}")
                fail_count += 1
                continue

            # Save to database (company memory layer)
            save_brief(email, sub_id, brief_content)

            # Deliver via email
            delivered = send_brief(email, company, brief_content)

            if delivered:
                mark_brief_delivered(email)
                update_subscriber_brief_count(email)
                success_count += 1
                print(f"  ✓ Complete — {company}")
            else:
                fail_count += 1
                print(f"  ✗ Delivery failed — {company}")

        except Exception as e:
            print(f"  ✗ Error processing {company}: {str(e)}")
            fail_count += 1

        # Brief pause between subscribers — avoids API rate limits
        time.sleep(2)

    # Cycle summary
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).seconds
    print("\n" + "=" * 60)
    print(f"EXOBRIEF — Brief Cycle Complete")
    print(f"Duration: {duration} seconds")
    print(f"Delivered: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total: {len(subscribers)}")
    print("=" * 60 + "\n")


# ============================================================
# SCHEDULER — Runs on Railway 24/7
# ============================================================

def start_scheduler():
    """
    Start the weekly scheduler
    Runs brief cycle every Sunday at 17:00 UTC
    """
    print("=" * 60)
    print("EXOBRIEF — Scheduler Active")
    print(f"Brief cycle scheduled: Every {RUN_DAY.capitalize()} at {BRIEF_RUN_TIME} UTC")
    print(f"Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    # Schedule Sunday delivery
    getattr(schedule.every(), RUN_DAY).at(BRIEF_RUN_TIME).do(run_brief_cycle)
    # Schedule daily intent monitor — 07:00 UTC (8am BST)
    schedule.every().day.at("07:00").do(run_intent_monitor)
    # Schedule outreach engine — 08:30 UTC Tue/Wed/Thu (9:30 BST)
    # Runs 15 UK + 15 UAE = 30 emails per day, 3 days per week
    from datetime import datetime as _dt
    def run_outreach_if_weekday():
        day = _dt.now().weekday()  # 1=Tue, 2=Wed, 3=Thu
        if day in [1, 2, 3]:
            print("[OUTREACH] Running scheduled outreach batch...")
            try:
                from outreach_engine import run_outreach
                run_outreach(region="both", limit=30)
            except Exception as e:
                print(f"[OUTREACH] Error: {e}")
        else:
            print(f"[OUTREACH] Skipping — not Tue/Wed/Thu (day={day})")
    schedule.every().day.at("08:30").do(run_outreach_if_weekday)
    print("Outreach engine scheduled: Tue/Wed/Thu at 08:30 UTC (30 emails/day)")

    # Follow-up engine — every Tuesday at 10:00 UTC (11:00 BST)
    # Only contacts firms 5+ days after first send
    def run_followup_tuesday():
        from datetime import datetime as _dt2
        if _dt2.now().weekday() == 1:  # Tuesday only
            print("[FOLLOWUP] Running weekly follow-up batch...")
            try:
                from followup_engine import run_followups
                run_followups()
            except Exception as e:
                print(f"[FOLLOWUP] Error: {e}")
    schedule.every().day.at("10:00").do(run_followup_tuesday)
    print("Follow-up engine scheduled: Tuesdays at 10:00 UTC")

    # Automated contact finder — DISABLED, was returning 0 contacts every run (broken web search parsing)
    print("Contact finder: DISABLED (was non-functional, wasting API credits)")

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


# ============================================================
# MANUAL RUN — for testing
# ============================================================

def run_now():
    """Run the brief cycle immediately — for testing"""
    print("EXOBRIEF — Manual Run Triggered")
    run_brief_cycle()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "now":
        # python main.py now — runs immediately
        run_now()
    else:
        # python main.py — starts scheduler
        start_scheduler()

# ============================================================
# COMBINED STARTUP — API + Scheduler
# ============================================================

def start_combined():
    """Start both API server and weekly scheduler"""
    import threading
    from api import run_api

    # Start API in background
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    print("[MAIN] EXOBRIEF API server started on background thread")

    # Start scheduler in main thread
    start_scheduler()
