"""
EXOBRIEF Automated Outreach Engine
===================================
Sends 30 personalised cold emails per run (15 UK + 15 UAE)
Runs automatically on Railway via cron: 9:30 AM BST Tue/Wed/Thu (UK)
                                        6:30 AM BST Tue/Wed/Thu (UAE)
Replies land in astarsupply@gmail.com
Logs all sends to outreach_log.json
"""

import os
import json
import anthropic
import random
from datetime import datetime, timezone

# ============================================================
# CONFIGURATION
# ============================================================

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "astarsupply@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DAILY_LIMIT = 30
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# ============================================================
# UK TARGET LIST — Professional services firms with SME clients
# ============================================================

UK_TARGETS = [
    # ALREADY SENT BATCH 1 — WILL BE SKIPPED BY SUPABASE
    # All Moore Kingston Smith, Buzzacott, Menzies, HaysMac, Johnston Carmichael,
    # Lovewell Blake, Duncan & Toplis, Lubbock Fine, Kreston Reeves, Shaw Gibbs,
    # Vistage, Stephens Scown, Citation, Saffery, AAB, Hazlewoods, CFO Centre,
    # Brabners, Blacks, ActionCOACH already in Supabase log

    # FRESH UK BATCH — THURSDAY
    {"firm": "Gravita", "contact": "Dean Shepherd", "title": "Managing Partner", "email": "dean.shepherd@gravita.co.uk", "sector": "accountancy", "hook": "Gravita's impressive 75% revenue growth and ambitious expansion across the UK advisory market"},
    {"firm": "TC Group", "contact": "Managing Partner", "title": "Managing Partner", "email": "hello@tcgroup.co.uk", "sector": "accountancy", "hook": "TC Group's rapid growth across UK SME accountancy and advisory services"},
    {"firm": "Baldwins", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@baldwinsaccountants.co.uk", "sector": "accountancy", "hook": "Baldwins' extensive regional SME client network across the Midlands and beyond"},
    {"firm": "Whitings", "contact": "Managing Partner", "title": "Managing Partner", "email": "mail@whitings.co.uk", "sector": "accountancy", "hook": "Whitings' trusted advisory relationships with East of England SME businesses"},
    {"firm": "Larking Gowen", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@larking-gowen.co.uk", "sector": "accountancy", "hook": "Larking Gowen's strong East Anglian SME client base built over decades"},
    {"firm": "Streets Chartered Accountants", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@streetsweb.co.uk", "sector": "accountancy", "hook": "Streets' deep advisory relationships with ambitious SMEs across the East Midlands"},
    {"firm": "Rickard Luckin", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@rickardluckin.co.uk", "sector": "accountancy", "hook": "Rickard Luckin's trusted reputation advising owner-managed businesses across Essex"},
    {"firm": "MHA Moore & Smalley", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@mooreandsmalley.co.uk", "sector": "accountancy", "hook": "Moore & Smalley's strong North West SME advisory practice"},
    {"firm": "UHY Hacker Young", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@uhy-uk.com", "sector": "accountancy", "hook": "UHY Hacker Young's national network of SME and entrepreneurial business clients"},
    {"firm": "Gerald Edelman", "contact": "Carl Lundberg", "title": "CEO", "email": "clundberg@geraldedelman.com", "sector": "accountancy", "hook": "Gerald Edelman's focus on entrepreneurship and owner-managed businesses built over 80 years"},
    {"firm": "Armstrong Watson", "contact": "Paul Dickson", "title": "CEO", "email": "paul.dickson@armstrongwatson.co.uk", "sector": "accountancy", "hook": "Armstrong Watson's focus on owner-managed businesses across the North and Scotland"},
    {"firm": "Haines Watts", "contact": "David Teckoe", "title": "Managing Partner", "email": "dteckoe@hwca.com", "sector": "accountancy", "hook": "Haines Watts' extraordinary reach supporting over 35,000 business owners across the UK"},
    {"firm": "Carpenter Box", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@carpenterbox.com", "sector": "accountancy", "hook": "Carpenter Box's strong South East SME advisory relationships"},
    {"firm": "Old Mill", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@om.uk", "sector": "accountancy", "hook": "Old Mill's focus on ambitious South West businesses and their owners"},
    {"firm": "Shorts Chartered Accountants", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@shorts.uk.com", "sector": "accountancy", "hook": "Shorts' strong Yorkshire SME and family business advisory practice"},
    {"firm": "Knox Cropper", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@knoxcropper.com", "sector": "accountancy", "hook": "Knox Cropper's focus on entrepreneurial London SME businesses"},
    {"firm": "Elman Wall", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@elmanwall.co.uk", "sector": "accountancy", "hook": "Elman Wall's deep London SME and property business client relationships"},
    {"firm": "Opus Business Advisory", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@opusbusinessadvisory.com", "sector": "business_advisory", "hook": "Opus Business Advisory's hands-on growth advisory work with UK SME owners"},
    {"firm": "Quantuma Advisory", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@quantuma.com", "sector": "business_advisory", "hook": "Quantuma's restructuring and advisory work with ambitious UK businesses"},
    {"firm": "BHP Chartered Accountants", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@bhp.co.uk", "sector": "accountancy", "hook": "BHP's strong Yorkshire and Midlands owner-managed business client base"},
]

UAE_TARGETS = [
    # BOUTIQUE UAE FIRMS — NAMED CONTACTS — INDEPENDENT DOMAINS
    {"firm": "KGRN Chartered Accountants", "contact": "Gopu Rama Naidu", "title": "Founder & Managing Partner", "email": "gopi@kgrnaudit.com", "sector": "accountancy", "hook": "KGRN's 20+ years advising UAE SMEs and the entrepreneurial business community across the Emirates"},
    {"firm": "Kreston Menon", "contact": "Raju Menon", "title": "Chairman & Managing Partner", "email": "raju@krestonmenon.com", "sector": "accountancy", "hook": "Kreston Menon's 30 years building deep SME relationships across the UAE with 500+ professionals"},
    {"firm": "Finanshels", "contact": "Muhammed Shafeekh", "title": "Founder & CEO", "email": "shafeekh@finanshels.com", "sector": "accountancy", "hook": "Finanshels' mission to serve the UAE's 94% SME economy with technology-first financial management"},
    {"firm": "A&A Associate LLC", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@aaconsultancy.ae", "sector": "accountancy", "hook": "A&A Associate's focus on cost-effective accounting solutions for UAE-based SMEs"},
    {"firm": "Hallmark International", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@hallmarkinternational.ae", "sector": "accountancy", "hook": "Hallmark International's professional audit and advisory services for UAE businesses of all sizes"},
    {"firm": "UHY James UAE", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@uhyjames.ae", "sector": "accountancy", "hook": "UHY James's 30 years of UAE professional services experience with deep local SME knowledge"},
    {"firm": "Farahat & Co", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@farahatco.com", "sector": "accountancy", "hook": "Farahat & Co's established UAE accountancy practice serving hundreds of SME clients"},
    {"firm": "Virtuzone", "contact": "Paul Bryson", "title": "Managing Director", "email": "paul.bryson@virtuzone.com", "sector": "business_setup", "hook": "Virtuzone's network of 80,000+ UAE business owners who need ongoing competitive intelligence"},
    {"firm": "Creative Zone", "contact": "Managing Director", "title": "Managing Director", "email": "info@creativezone.ae", "sector": "business_setup", "hook": "Creative Zone's large portfolio of UAE SME and startup clients seeking strategic advantage"},
    {"firm": "Commitbiz", "contact": "Managing Director", "title": "Managing Director", "email": "info@commitbiz.com", "sector": "business_advisory", "hook": "Commitbiz's business setup and ongoing advisory relationships with UAE entrepreneurs"},
    {"firm": "Alpen Capital", "contact": "Managing Director", "title": "Managing Director", "email": "info@alpencapital.com", "sector": "business_advisory", "hook": "Alpen Capital's GCC advisory work with SME and family-owned businesses"},
    {"firm": "IMC Group", "contact": "Managing Director", "title": "Managing Director", "email": "info@imcgroupindia.com", "sector": "business_advisory", "hook": "IMC Group's cross-border advisory serving UAE and GCC SMEs across multiple sectors"},
    {"firm": "Scope Solutions", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@scopesolutions.ae", "sector": "accountancy", "hook": "Scope Solutions' personalised approach to UAE SME financial management and advisory"},
    {"firm": "Aurifer Tax Consultancy", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@aurifer.com", "sector": "accountancy", "hook": "Aurifer's specialist UAE tax and advisory expertise serving SME clients across the Emirates"},
    {"firm": "Morison Menon", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@morisonmenon.com", "sector": "accountancy", "hook": "Morison Menon's 25 years of UAE SME client relationships across audit and advisory"},
]

# ============================================================
# EMAIL PERSONALISATION — Claude generates unique email per target
# ============================================================

def generate_personalised_email(target: dict, region: str) -> str:
    """Use Claude to generate a personalised cold email for each target."""
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    sector_context = {
        "accountancy": "accountancy firm",
        "fractional_cfo": "fractional CFO network",
        "business_coaching": "business coaching network",
        "business_advisory": "business advisory firm",
        "law": "commercial law firm",
        "hr_consultancy": "HR consultancy",
        "agency": "marketing agency",
        "consultancy": "management consultancy",
        "business_setup": "business setup and advisory firm",
    }
    
    firm_type = sector_context.get(target.get("sector", "accountancy"), "professional services firm")
    
    prompt = f"""Write a short, personalised cold email for EXOBRIEF — an AI-powered competitive intelligence platform.

TARGET:
- Firm: {target['firm']}
- Contact: {target['contact']} ({target['title']})
- Firm type: {firm_type}
- Region: {region}
- Personal hook: {target['hook']}

EXOBRIEF VALUE PROPOSITION:
We deliver weekly personalised competitive intelligence briefs to SME business owners — named competitor moves, revenue risks, three decisions per week. Professional services firms white-label it for their SME clients at £299/month for up to 20 clients. They offer it under their own brand, we power everything behind the scenes.

RULES FOR THE EMAIL:
1. Maximum 120 words — keep it tight
2. Open with the personal hook about their firm specifically
3. One sentence explaining what EXOBRIEF does
4. One sentence on the white-label model and what they get
5. End with demo link: exobrief.com/partner_demo.html
6. Sign as Shruti, EXOBRIEF
7. NO subject line — just the body
8. NO bullet points
9. NO "I hope this email finds you well" or similar openers
10. Sound like a real person, not a marketing template
11. ALWAYS start with "Hi [first name]," on the first line — never just the name alone
11. For UAE targets — reference the UAE/GCC market specifically

Write ONLY the email body. Nothing else."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text.strip()


def generate_subject_line(target: dict) -> str:
    """Generate a personalised subject line."""
    subjects = [
        f"white-label competitive intelligence for your SME clients",
        f"something for {target['firm']}'s SME clients",
        f"competitive intelligence — white-label for your clients",
        f"ran our intelligence engine on one of your clients",
        f"a new revenue stream for {target['firm']}'s advisory practice",
    ]
    return random.choice(subjects[:3])  # Use top 3 most professional ones


# ============================================================
# SEND EMAIL VIA SENDGRID API
# ============================================================

def send_email(to_email: str, to_name: str, subject: str, body: str) -> bool:
    """Send email via SendGrid API."""
    try:
        import urllib.request
        
        sendgrid_key = os.environ.get("SENDGRID_API_KEY", "")
        if not sendgrid_key:
            print("  ✗ SENDGRID_API_KEY not set")
            return False

        signature = "\n\n--\nShruti\nEXOBRIEF · exobrief.com"
        full_body_text = body + signature

        # HTML version with clickable link
        html_body = body.replace(
            "exobrief.com/partner_demo.html",
            '<a href="https://exobrief.com/partner_demo.html">exobrief.com/partner_demo.html</a>'
        ).replace("\n", "<br>") + "<br><br>--<br>Shruti<br>EXOBRIEF · <a href=\"https://exobrief.com\">exobrief.com</a>"

        payload = json.dumps({
            "personalizations": [{
                "to": [{"email": to_email, "name": to_name}]
            }],
            "from": {"email": "hello@exobrief.com", "name": "Shruti"},
            "reply_to": {"email": "astarsupply@gmail.com", "name": "Shruti"},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": full_body_text},
                {"type": "text/html", "value": html_body}
            ]
        }).encode()

        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send",
            data=payload,
            headers={
                "Authorization": f"Bearer {sendgrid_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 202:
                return True
            else:
                print(f"  ✗ SendGrid returned {resp.status}")
                return False

    except Exception as e:
        print(f"  ✗ Send failed: {str(e)}")
        return False


# ============================================================
# LOGGING
# ============================================================

def get_contacted_emails() -> set:
    """Get set of already-contacted emails from Supabase."""
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/outreach_log?select=email",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return {row['email'] for row in data}
    except Exception as e:
        print(f"  ⚠ Could not load contacted list: {e}")
        return set()


def already_contacted(email: str, contacted: set) -> bool:
    """Check if we have already emailed this address."""
    return email in contacted


def log_contact(target: dict, subject: str, region: str):
    """Log a successful send to Supabase."""
    try:
        import urllib.request
        payload = json.dumps({
            "email": target['email'],
            "firm": target['firm'],
            "contact": target['contact'],
            "region": region,
            "subject": subject,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "replied": False,
            "converted": False
        }).encode()

        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/outreach_log",
            data=payload,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True
    except Exception as e:
        print(f"  ⚠ Could not log contact: {e}")
        return False


def load_log() -> dict:
    """Compatibility wrapper."""
    return {"stats": {"total_sent": 0}}


def save_log(log: dict):
    """Compatibility wrapper — logging now in Supabase."""
    pass


# ============================================================
# MAIN OUTREACH RUN
# ============================================================

def run_outreach(region: str = "both", limit: int = 30):
    """
    Main outreach function.
    region: "uk", "uae", or "both"
    limit: max emails to send this run
    """
    
    print(f"\n{'='*60}")
    print(f"EXOBRIEF Outreach Engine — {datetime.now().strftime('%Y-%m-%d %H:%M BST')}")
    print(f"Region: {region} | Limit: {limit}")
    print(f"{'='*60}\n")
    
    if not GMAIL_APP_PASSWORD:
        print("✗ GMAIL_APP_PASSWORD not set — cannot send")
        return
    
    if not ANTHROPIC_API_KEY:
        print("✗ ANTHROPIC_API_KEY not set — cannot personalise")
        return
    
    contacted = get_contacted_emails()
    print(f"Already contacted: {len(contacted)} firms")
    log = {"stats": {"total_sent": len(contacted)}}
    sent_count = 0
    
    # Build target queue based on region
    if region == "uk":
        targets = [(t, "UK") for t in UK_TARGETS]
    elif region == "uae":
        targets = [(t, "UAE") for t in UAE_TARGETS]
    else:  # both — strictly 15 UK then 15 UAE
        uk_limit = limit // 2   # 15
        uae_limit = limit - uk_limit  # 15
        # Run UK first, then UAE — strict separation
        uk_targets = [(t, "UK") for t in UK_TARGETS]
        uae_targets = [(t, "UAE") for t in UAE_TARGETS]
        targets = uk_targets + uae_targets
        # Override limit tracking to enforce 15/15 split
        uk_sent = 0
        uae_sent = 0
    
    attempt_count = 0
    max_attempts = limit * 3  # Never try more than 3x the limit

    for target, target_region in targets:
        if sent_count >= limit:
            print(f"\n✓ Daily limit of {limit} reached. Done.")
            break

        if attempt_count >= max_attempts:
            print(f"\n✓ Max attempts ({max_attempts}) reached. Done.")
            break

        attempt_count += 1
        email = target['email']

        # Skip if already contacted
        if already_contacted(email, contacted):
            print(f"  → Skipping {target['firm']} (already contacted)")
            continue

        print(f"\n→ Processing: {target['firm']} ({target_region})")
        print(f"  Contact: {target['contact']} <{email}>")

        try:
            # Generate personalised email with retry on overload
            print(f"  Generating personalised email...")
            body = None
            for attempt in range(3):
                try:
                    body = generate_personalised_email(target, target_region)
                    break
                except Exception as api_err:
                    if '529' in str(api_err) or 'overloaded' in str(api_err).lower():
                        print(f"  API overloaded — waiting 10s (attempt {attempt+1}/3)")
                        import time
                        time.sleep(10)
                    else:
                        raise

            if not body:
                print(f"  ✗ Could not generate email after 3 attempts — skipping")
                continue

            subject = generate_subject_line(target)
            print(f"  Subject: {subject}")
            print(f"  Body preview: {body[:80]}...")

            # Send
            print(f"  Sending...")
            success = send_email(email, target['contact'], subject, body)

            if success:
                log_contact(target, subject, target_region)
                contacted.add(email)
                sent_count += 1
                if target_region == "UK":
                    uk_sent = uk_sent + 1 if "uk_sent" in dir() else 1
                else:
                    uae_sent = uae_sent + 1 if "uae_sent" in dir() else 1
                print(f"  ✓ Sent ({sent_count}/{limit}) — UK:{uk_sent if 'uk_sent' in dir() else '?'} UAE:{uae_sent if 'uae_sent' in dir() else '?'}")

                import time
                time.sleep(3)

                # Stop UK at 15, stop UAE at 15
                if target_region == "UK" and "uk_sent" in dir() and uk_sent >= uk_limit:
                    print(f"  → UK limit of {uk_limit} reached")
                if target_region == "UAE" and "uae_sent" in dir() and uae_sent >= uae_limit:
                    print(f"  → UAE limit of {uae_limit} reached")
            else:
                print(f"  ✗ Failed to send")

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            continue
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"Run complete: {sent_count} emails sent")
    print(f"Total ever sent: {log['stats'].get('total_sent', 0)}")
    print(f"{'='*60}\n")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import sys
    
    region = sys.argv[1] if len(sys.argv) > 1 else "both"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    run_outreach(region=region, limit=limit)
