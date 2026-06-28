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
    # RECRUITMENT & HR SECTOR — NAMED DECISION MAKERS
    {"firm": "Tiger Recruitment", "contact": "David Morel", "title": "Founder & CEO", "email": "david.morel@tiger-recruitment.com", "sector": "recruitment", "hook": "Tiger Recruitment's 25-year track record placing exceptional talent across London's most competitive businesses", "competitors": ["Crone Corkill", "Love Success", "Office Angels", "Reed Specialist Recruitment"]},
    {"firm": "Crone Corkill", "contact": "Abby Jordan", "title": "Director", "email": "abby.jordan@cronecorkill.co.uk", "sector": "recruitment", "hook": "Crone Corkill's 45-year heritage placing business support talent across London's most demanding firms", "competitors": ["Tiger Recruitment", "Love Success", "Hays", "Office Angels"]},
    {"firm": "Investigo", "contact": "Rob Brouwer", "title": "Founder & CEO", "email": "rob.brouwer@investigo.co.uk", "sector": "recruitment", "hook": "Investigo's impressive growth as one of the UK's fastest-growing specialist recruitment firms", "competitors": ["Frazer Jones", "Marks Sattin", "Michael Page", "Heidrick & Struggles"]},
    {"firm": "Frazer Jones", "contact": "Charlotte Faktor", "title": "UK Managing Director", "email": "charlotte.faktor@frazerjones.com", "sector": "recruitment", "hook": "Frazer Jones' global HR recruitment specialism and growing UK presence", "competitors": ["Investigo", "Oakleaf Partnership", "Henlee Resourcing", "Annapurna HR"]},
    {"firm": "Oakleaf Partnership", "contact": "Nicola Grimshaw", "title": "CEO", "email": "nicola.grimshaw@oakleafpartnership.com", "sector": "recruitment", "hook": "Oakleaf Partnership's specialist HR and business change recruitment across financial services", "competitors": ["Frazer Jones", "Annapurna HR", "Investigo", "Sellick Partnership"]},
    {"firm": "Annapurna HR", "contact": "James Cumming", "title": "Founder & MD", "email": "james.cumming@annapurna-hr.com", "sector": "recruitment", "hook": "Annapurna HR's growing reputation as the go-to HR recruitment specialist for transformation roles", "competitors": ["Frazer Jones", "Oakleaf Partnership", "Henlee Resourcing", "Digby Morgan"]},
    {"firm": "Henlee Resourcing", "contact": "Mark Wilcox", "title": "Director", "email": "mark@henlee.co.uk", "sector": "recruitment", "hook": "Henlee Resourcing's strong South West HR recruitment market position", "competitors": ["Annapurna HR", "Frazer Jones", "Hays HR", "Reed HR"]},
    {"firm": "Sellick Partnership", "contact": "Jo Sellick", "title": "Managing Director", "email": "jo.sellick@sellickpartnership.co.uk", "sector": "recruitment", "hook": "Sellick Partnership's impressive growth across finance, legal and HR recruitment in the North", "competitors": ["Marks Sattin", "Robert Half", "Michael Page", "Morgan Hunt"]},
    {"firm": "Macildowie", "contact": "Kevin Draycott", "title": "Managing Director", "email": "kevin.draycott@macildowie.com", "sector": "recruitment", "hook": "Macildowie's dominant position in East Midlands HR and finance recruitment", "competitors": ["Hays", "Michael Page", "Reed", "Robert Half"]},
    {"firm": "Marks Sattin", "contact": "Matthew Wilcox", "title": "Managing Director", "email": "matthew.wilcox@markssattin.com", "sector": "recruitment", "hook": "Marks Sattin's strong finance and HR recruitment presence across the UK", "competitors": ["Robert Half", "Sellick Partnership", "Michael Page", "Investigo"]},
    {"firm": "Portfolio HR", "contact": "David Beamer", "title": "Managing Director", "email": "david.beamer@portfoliohr.co.uk", "sector": "hr_consultancy", "hook": "Portfolio HR's specialist HR and employment law advisory work with UK businesses", "competitors": ["Citation", "Peninsula", "Croner", "Ellis Whittam"]},
    {"firm": "Ellis Whittam", "contact": "James Potts", "title": "CEO", "email": "james.potts@elliswhittam.com", "sector": "hr_consultancy", "hook": "Ellis Whittam's growing HR and employment law advisory business serving UK SMEs", "competitors": ["Citation", "Peninsula", "Croner", "Portfolio HR"]},
    {"firm": "Jaluch HR", "contact": "Helen Jamieson", "title": "Founder & MD", "email": "helen@jaluch.co.uk", "sector": "hr_consultancy", "hook": "Jaluch HR's boutique approach to HR consultancy serving ambitious UK businesses", "competitors": ["Ellis Whittam", "Portfolio HR", "Citation", "Croner"]},
    {"firm": "Pure Human Resources", "contact": "Stephanie Kelly", "title": "Founder & MD", "email": "stephanie@purehumanresources.co.uk", "sector": "hr_consultancy", "hook": "Pure Human Resources' strong South East HR advisory client base", "competitors": ["Ellis Whittam", "Jaluch HR", "Citation", "Croner"]},
    {"firm": "HR Dept", "contact": "Morag Ofili", "title": "CEO", "email": "morag.ofili@hrdept.co.uk", "sector": "hr_consultancy", "hook": "HR Dept's national franchise network of outsourced HR advisors serving thousands of UK SMEs", "competitors": ["Citation", "Peninsula", "Ellis Whittam", "Croner"]},
    {"firm": "WorkNest", "contact": "Tom Hadley", "title": "CEO", "email": "tom.hadley@worknest.com", "sector": "hr_consultancy", "hook": "WorkNest's rapid growth as one of the UK's leading employment law and HR support businesses", "competitors": ["Citation", "Peninsula", "Ellis Whittam", "Croner"]},
    {"firm": "Digby Morgan", "contact": "Managing Director", "title": "Managing Director", "email": "info@digbymorgan.com", "sector": "hr_consultancy", "hook": "Digby Morgan's strong UK HR recruitment and advisory presence serving growing businesses", "competitors": ["Frazer Jones", "Oakleaf Partnership", "Annapurna HR", "Henlee Resourcing"]},
    {"firm": "Aspire Recruiting", "contact": "Lee Biggins", "title": "Founder & MD", "email": "lee.biggins@aspirerecruiting.co.uk", "sector": "recruitment", "hook": "Aspire Recruiting's growing digital and marketing recruitment presence across the UK", "competitors": ["Tiger Recruitment", "Sphere Digital", "Forward Role", "Major Players"]},
    {"firm": "Forward Role", "contact": "Mike Doyle", "title": "Managing Director", "email": "mike.doyle@forwardrole.com", "sector": "recruitment", "hook": "Forward Role's specialist digital and marketing recruitment across the North of England", "competitors": ["Aspire Recruiting", "Sphere Digital", "Major Players", "Hays Digital"]},
    {"firm": "Sphere Digital Recruitment", "contact": "Daniel Bolter", "title": "Managing Director", "email": "daniel.bolter@spheredr.com", "sector": "recruitment", "hook": "Sphere Digital's specialist technology and digital recruitment presence across London", "competitors": ["Forward Role", "Aspire Recruiting", "Major Players", "Tiger Recruitment"]},
]

UAE_TARGETS = [
    {"firm": "Charterhouse Middle East", "contact": "Jennifer Campori", "title": "Managing Director", "email": "jennifer.campori@charterhouseme.ae", "sector": "recruitment", "hook": "Charterhouse's 20-year track record placing talent across the GCC's most competitive markets", "competitors": ["BAC Middle East", "Hays UAE", "Michael Page UAE", "Inspire Selection"]},
    {"firm": "Inspire Selection", "contact": "Claire Donnelly", "title": "Managing Director", "email": "claire.donnelly@inspireselection.com", "sector": "recruitment", "hook": "Inspire Selection's boutique executive search reputation across the UAE and GCC", "competitors": ["Charterhouse", "BAC Middle East", "Guildhall", "Kershaw Leonard"]},
    {"firm": "Kershaw Leonard", "contact": "Graham Doyle", "title": "Managing Director", "email": "graham.doyle@kershawleonard.net", "sector": "recruitment", "hook": "Kershaw Leonard's 30-year track record in UAE executive and professional recruitment", "competitors": ["BAC Middle East", "Charterhouse", "Inspire Selection", "Guildhall"]},
    {"firm": "KGRN Chartered Accountants", "contact": "Gopu Rama Naidu", "title": "Founder & Managing Partner", "email": "gopi@kgrnaudit.com", "sector": "accountancy", "hook": "KGRN's 20+ years advising UAE SMEs and the entrepreneurial business community", "competitors": ["Kreston Menon", "Farahat & Co", "UHY James UAE", "Morison Menon"]},
    {"firm": "Kreston Menon", "contact": "Raju Menon", "title": "Chairman & Managing Partner", "email": "raju@krestonmenon.com", "sector": "accountancy", "hook": "Kreston Menon's 30 years building deep SME relationships across the UAE", "competitors": ["KGRN", "Farahat & Co", "HLB HAMT", "Morison Menon"]},
    {"firm": "Finanshels", "contact": "Muhammed Shafeekh", "title": "Founder & CEO", "email": "shafeekh@finanshels.com", "sector": "accountancy", "hook": "Finanshels' mission to serve the UAE's 94% SME economy with technology-first financial management", "competitors": ["Pemo", "Xero UAE", "Zoho Books UAE", "QuickBooks UAE"]},
    {"firm": "Virtuzone", "contact": "Paul Bryson", "title": "Managing Director", "email": "paul.bryson@virtuzone.com", "sector": "business_setup", "hook": "Virtuzone's network of 80,000+ UAE business owners who compete daily in the UAE market", "competitors": ["Creative Zone", "Commitbiz", "Business Setup Worldwide", "Shuraa"]},
    {"firm": "Nadia Global", "contact": "Nadia Bastaki", "title": "CEO", "email": "nadia@nadiaglobal.com", "sector": "recruitment", "hook": "Nadia Global's 40-year track record as one of the UAE's original recruitment and training partners", "competitors": ["BAC Middle East", "Kershaw Leonard", "Charterhouse", "Guildhall"]},
    {"firm": "TASC Outsourcing", "contact": "Sandeep Chauhan", "title": "CEO", "email": "sandeep.chauhan@tascoutsourcing.com", "sector": "hr_consultancy", "hook": "TASC Outsourcing's market-leading HR outsourcing business serving UAE corporations and SMEs", "competitors": ["Manpower UAE", "Adecco UAE", "Crescent HR", "Ignite HR"]},
    {"firm": "GulfTalent", "contact": "Oliver Vella", "title": "CEO", "email": "oliver.vella@gulftalent.com", "sector": "recruitment", "hook": "GulfTalent's position as the Gulf region's leading professional recruitment platform", "competitors": ["Bayt.com", "Naukrigulf", "Dubizzle Jobs", "Indeed UAE"]},
    {"firm": "BAC Middle East", "contact": "Mark Robilliard", "title": "Managing Director", "email": "mark.robilliard@bacme.com", "sector": "recruitment", "hook": "BAC Middle East's 40-year heritage as one of the Gulf's most trusted recruitment partners", "competitors": ["Charterhouse", "Inspire Selection", "Kershaw Leonard", "Guildhall"]},
    {"firm": "Guildhall Agency", "contact": "Julia Kurlik", "title": "Managing Director", "email": "julia.kurlik@guildhall.ae", "sector": "recruitment", "hook": "Guildhall's specialist business support and HR recruitment across the UAE financial district", "competitors": ["Tiger Dubai", "BAC Middle East", "Inspire Selection", "Charterhouse"]},
    {"firm": "Alpen Capital", "contact": "Sanjay Grewal", "title": "Managing Director", "email": "sanjay.grewal@alpencapital.com", "sector": "business_advisory", "hook": "Alpen Capital's GCC advisory work with SME and family-owned businesses across the Emirates", "competitors": ["KPMG Lower Gulf", "Deloitte ME", "EY UAE", "PwC UAE"]},
    {"firm": "Farahat & Co", "contact": "Mohamed Farahat", "title": "Managing Partner", "email": "mohamed.farahat@farahatco.com", "sector": "accountancy", "hook": "Farahat & Co's established UAE accountancy practice serving hundreds of SME clients since 1985", "competitors": ["KGRN", "Kreston Menon", "Morison Menon", "UHY James UAE"]},
    {"firm": "Morison Menon", "contact": "Raju Menon", "title": "Managing Partner", "email": "raju.menon@morisonmenon.com", "sector": "accountancy", "hook": "Morison Menon's 25 years of UAE SME client relationships across audit and advisory", "competitors": ["KGRN", "Farahat & Co", "Kreston Menon", "HLB HAMT"]},
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
    
    competitors = target.get('competitors', ['key competitors'])
    prompt = f"""Write a short, personalised cold email for EXOBRIEF — an AI-powered competitive intelligence platform.

TARGET:
- Firm: {target['firm']}
- Contact: {target['contact']} ({target['title']})
- Firm type: {firm_type}
- Region: {region}
- Personal hook: {target['hook']}
- Their known competitors: {competitors}
- Their known competitors: {target.get('competitors', [])}

EXOBRIEF VALUE PROPOSITION:
We deliver weekly personalised competitive intelligence briefs to businesses — named competitor moves, revenue risks, three decisions per week. We're offering recruitment and HR firms the ability to offer this to their own business clients as a value-add service at £299/month for up to 20 clients. Under their brand, powered by us.

RULES FOR THE EMAIL:
1. Maximum 5 sentences total — brutally short
2. ALWAYS start with "Hi [first name]," on the first line. BUT if the contact is "Managing Director", "CEO", "Managing Partner" or any generic title rather than a real name — start with just "Hi," with no name
3. SECOND LINE — urgency/competitive threat: make them feel their competitors are already ahead. Use a variation of: "Several [sector] firms are now receiving weekly intelligence on exactly what their rivals are doing. [Their firm] isn't one of them yet." Adapt naturally to their specific sector and firm.
4. THIRD LINE — what it is in one sentence: "We built an AI that tracks competitor moves weekly and delivers a brief every Sunday — named signals, revenue risks, three decisions."
5. FOURTH LINE — single frictionless ask: "Want to see what your rivals have been doing this week? Just reply."
6. Sign as Shruti, EXOBRIEF · exobrief.com
7. NO subject line — just the body
8. NO bullet points  
9. NO pricing mention
10. NO demo page link
11. NO "I hope this finds you well" or any filler
12. Sound like a real person who knows their market
13. The ONLY goal is to get a reply. One word reply is a win.
14. The competitive threat line must feel specific to their sector — not generic
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
    sector = target.get('sector', 'accountancy')
    firm = target['firm']
    
    sector_subjects = {
        'recruitment': [
            f"what your competitors are doing this week",
            f"your rivals just made some moves",
            f"competitor intelligence for {firm}",
        ],
        'hr_consultancy': [
            f"what HR firms in your market are doing",
            f"your competitors this week",
            f"intelligence brief for {firm}",
        ],
        'accountancy': [
            f"your SME clients' competitors",
            f"what rival firms are offering SME clients",
            f"competitive intelligence — {firm}",
        ],
        'law': [
            f"what competing firms are doing this week",
            f"your rivals just made moves",
            f"competitor intelligence for {firm}",
        ],
    }
    
    default_subjects = [
        f"your competitors this week",
        f"what rivals in your market are doing",
        f"competitor intelligence — {firm}",
    ]
    
    subjects = sector_subjects.get(sector, default_subjects)
    return random.choice(subjects)


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
            "reply_to": {"email": "hello@exobrief.com", "name": "Shruti"},
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
