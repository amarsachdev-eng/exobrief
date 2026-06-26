"""
EXOBRIEF Follow-up Engine
=========================
Sends a follow-up to all previously contacted firms.
New offer: reply with client name + 3 competitors, get a free brief within the hour.
Run once manually: /opt/venv/bin/python followup_engine.py
"""

import os, json, urllib.request
from datetime import datetime, timezone

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SENDGRID_KEY = os.environ.get("SENDGRID_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

FOLLOWUP_SUBJECT = "one more thing — a free brief for your client"

FOLLOWUP_BODY = """Hi {name},

I reached out earlier this week about EXOBRIEF — weekly competitive intelligence for your SME clients, white-labelled under your brand.

I wanted to make this as easy as possible to evaluate.

If you'd like to see exactly what one of your clients would receive — just reply to this email with:

1. Their company name
2. Their top 3 competitors

I'll generate their brief and send it directly to you within the hour. No page to visit, no form to fill in. Just a reply.

If it's not relevant, no problem at all — just ignore this.

Shruti
EXOBRIEF · exobrief.com"""

def get_contacted_firms():
    """Get all firms from outreach_log — excluding bounced ones."""
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/outreach_log?select=email,firm,contact,region&subject=neq.BOUNCED&replied=eq.false",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def already_followed_up(email):
    """Check if we already sent a follow-up to this email."""
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/followup_log?select=email&email=eq.{email}",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return len(data) > 0
    except:
        return False

def log_followup(email, firm):
    """Log the follow-up send."""
    payload = json.dumps({
        "email": email,
        "firm": firm,
        "sent_at": datetime.now(timezone.utc).isoformat()
    }).encode()
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/followup_log",
        data=payload,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return True

def send_followup(to_email, to_name, firm):
    """Send follow-up via SendGrid."""
    # Extract first name
    first_name = to_name.split()[0] if to_name and to_name not in ["Managing Partner", "Managing Director", "CEO", "Bounced"] else ""
    
    body = FOLLOWUP_BODY.format(name=first_name if first_name else "")
    # Clean up greeting if no name
    if not first_name:
        body = body.replace("Hi ,", "Hi,")

    full_body_text = body
    html_body = body.replace(
        "exobrief.com",
        '<a href="https://exobrief.com">exobrief.com</a>'
    ).replace("\n", "<br>")

    payload = json.dumps({
        "personalizations": [{"to": [{"email": to_email, "name": to_name}]}],
        "from": {"email": "hello@exobrief.com", "name": "Shruti"},
        "reply_to": {"email": "hello@exobrief.com", "name": "Shruti"},
        "subject": FOLLOWUP_SUBJECT,
        "content": [
            {"type": "text/plain", "value": full_body_text},
            {"type": "text/html", "value": html_body}
        ]
    }).encode()

    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {SENDGRID_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status == 202

def run_followups():
    print("\n" + "="*60)
    print(f"EXOBRIEF Follow-up Engine — {datetime.now().strftime('%Y-%m-%d %H:%M BST')}")
    print("="*60 + "\n")

    firms = get_contacted_firms()
    print(f"Total firms in outreach log: {len(firms)}")

    sent = 0
    skipped = 0

    for firm in firms:
        email = firm["email"]
        name = firm.get("contact", "")
        firm_name = firm.get("firm", "")

        # Skip bounced
        if "BOUNCED" in name or not email:
            skipped += 1
            continue

        # Skip already followed up
        if already_followed_up(email):
            print(f"  → Already followed up: {firm_name}")
            skipped += 1
            continue

        print(f"\n→ Following up: {firm_name} — {email}")

        try:
            success = send_followup(email, name, firm_name)
            if success:
                log_followup(email, firm_name)
                sent += 1
                print(f"  ✓ Sent ({sent})")
                import time
                time.sleep(2)
            else:
                print(f"  ✗ Send failed")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print(f"\n{'='*60}")
    print(f"Follow-up complete: {sent} sent, {skipped} skipped")
    print("="*60)

if __name__ == "__main__":
    run_followups()
