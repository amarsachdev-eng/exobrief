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
import smtplib
import anthropic
import random
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "astarsupply@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
LOG_FILE = "/opt/exobrief/outreach_log.json"
TARGETS_FILE = "/opt/exobrief/targets.json"
DAILY_LIMIT = 30

# ============================================================
# UK TARGET LIST — Professional services firms with SME clients
# ============================================================

UK_TARGETS = [
    # ACCOUNTANCY FIRMS
    {"firm": "Xeinadin", "contact": "Tim Halford", "title": "Chief Commercial Officer", "email": "tim.halford@xeinadin.com", "sector": "accountancy", "hook": "Xeinadin's mission to serve over 100,000 SME clients nationwide"},
    {"firm": "James Cowper Kreston", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@jamescowper.co.uk", "sector": "accountancy", "hook": "James Cowper Kreston's advisory focus on owner-managed businesses"},
    {"firm": "Moore Kingston Smith", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@mooreks.co.uk", "sector": "accountancy", "hook": "Moore Kingston Smith's strength in entrepreneurial and growth businesses"},
    {"firm": "Buzzacott", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@buzzacott.co.uk", "sector": "accountancy", "hook": "Buzzacott's deep focus on SMEs and family businesses across the UK"},
    {"firm": "Menzies", "contact": "Managing Partner", "title": "Managing Partner", "email": "enquiries@menzies.co.uk", "sector": "accountancy", "hook": "Menzies' strong advisory practice serving ambitious UK businesses"},
    {"firm": "Haysmacintyre", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@haysmacintyre.com", "sector": "accountancy", "hook": "Haysmacintyre's focus on entrepreneurial businesses and their owners"},
    {"firm": "BKL", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@bkl.co.uk", "sector": "accountancy", "hook": "BKL's reputation for personal service to growing UK businesses"},
    {"firm": "Kreston Reeves", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@krestonreeves.com", "sector": "accountancy", "hook": "Kreston Reeves' deep roots in South East SME advisory"},
    {"firm": "Wilkins Kennedy", "contact": "Managing Partner", "title": "Managing Partner", "email": "wk@wilkinskennedy.com", "sector": "accountancy", "hook": "Wilkins Kennedy's focus on owner-managed businesses across the South"},
    {"firm": "Shaw Gibbs", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@shawgibbs.com", "sector": "accountancy", "hook": "Shaw Gibbs' entrepreneurial client base across the Thames Valley"},
    {"firm": "Lubbock Fine", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@lubbockfine.co.uk", "sector": "accountancy", "hook": "Lubbock Fine's strong private business and entrepreneur client base"},
    {"firm": "TC Group", "contact": "Managing Partner", "title": "Managing Partner", "email": "hello@tcgroup.co.uk", "sector": "accountancy", "hook": "TC Group's rapidly growing SME advisory practice"},
    {"firm": "Baldwins", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@baldwinsaccountants.co.uk", "sector": "accountancy", "hook": "Baldwins' extensive regional SME client network"},
    {"firm": "Hazlewoods", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@hazlewoods.co.uk", "sector": "accountancy", "hook": "Hazlewoods' focus on ambitious and entrepreneurial businesses"},
    {"firm": "Saffery", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@saffery.com", "sector": "accountancy", "hook": "Saffery's private business advisory strength across the UK"},
    {"firm": "Johnston Carmichael", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@jcca.co.uk", "sector": "accountancy", "hook": "Johnston Carmichael's leading position in Scottish SME advisory"},
    {"firm": "AAB", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@aab.uk", "sector": "accountancy", "hook": "AAB's comprehensive SME advisory across UK and Ireland"},
    {"firm": "Lovewell Blake", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@lovewell-blake.co.uk", "sector": "accountancy", "hook": "Lovewell Blake's strong East Anglian SME client base"},
    {"firm": "Duncan & Toplis", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@duntop.co.uk", "sector": "accountancy", "hook": "Duncan & Toplis' deep Midlands owner-managed business relationships"},
    {"firm": "Whitings", "contact": "Managing Partner", "title": "Managing Partner", "email": "mail@whitings.co.uk", "sector": "accountancy", "hook": "Whitings' trusted advisory relationships with East of England SMEs"},

    # FRACTIONAL CFO / BUSINESS ADVISORY
    {"firm": "The CFO Centre", "contact": "UK Managing Director", "title": "Managing Director", "email": "uk@cfocentre.com", "sector": "fractional_cfo", "hook": "The CFO Centre's network of fractional CFOs serving hundreds of UK SMEs"},
    {"firm": "Liberis", "contact": "Managing Director", "title": "Managing Director", "email": "hello@liberis.com", "sector": "business_advisory", "hook": "Liberis' focus on helping UK SMEs access growth capital and advice"},
    {"firm": "ActionCOACH UK", "contact": "Managing Director", "title": "Managing Director", "email": "enquiries@actioncoach.co.uk", "sector": "business_coaching", "hook": "ActionCOACH's network of coaches serving thousands of UK SME owners"},
    {"firm": "Vistage UK", "contact": "Managing Director", "title": "Managing Director", "email": "info@vistage.co.uk", "sector": "business_advisory", "hook": "Vistage's peer advisory groups serving UK CEO and MD communities"},
    {"firm": "Grant Thornton Advisory", "contact": "Head of Growth Advisory", "title": "Partner", "email": "info@uk.gt.com", "sector": "business_advisory", "hook": "Grant Thornton's growth advisory practice for ambitious mid-market businesses"},

    # LAW FIRMS WITH SME CLIENTS
    {"firm": "Stephens Scown", "contact": "Managing Partner", "title": "Managing Partner", "email": "enquiries@stephens-scown.co.uk", "sector": "law", "hook": "Stephens Scown's strong reputation advising South West SMEs and entrepreneurs"},
    {"firm": "Blacks Solicitors", "contact": "Managing Partner", "title": "Managing Partner", "email": "enquiries@blacks.co.uk", "sector": "law", "hook": "Blacks Solicitors' focus on Yorkshire and Northern England SME businesses"},
    {"firm": "Penningtons Manches Cooper", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@penningtonslaw.com", "sector": "law", "hook": "Penningtons Manches Cooper's strong commercial client base across the South"},
    {"firm": "Brabners", "contact": "Managing Partner", "title": "Managing Partner", "email": "enquiries@brabners.com", "sector": "law", "hook": "Brabners' focus on North West entrepreneur and SME clients"},
    {"firm": "Gateley", "contact": "CEO", "title": "CEO", "email": "info@gateleyplc.com", "sector": "law", "hook": "Gateley's broad SME and mid-market commercial client base"},

    # HR CONSULTANCIES
    {"firm": "Citation", "contact": "CEO", "title": "CEO", "email": "hello@citation.co.uk", "sector": "hr_consultancy", "hook": "Citation's network of 25,000+ SME clients across the UK"},
    {"firm": "Peninsula Group", "contact": "CEO", "title": "CEO", "email": "info@peninsulagrouplimited.com", "sector": "hr_consultancy", "hook": "Peninsula Group's enormous SME client base across the UK and Ireland"},
    {"firm": "Croner", "contact": "Managing Director", "title": "Managing Director", "email": "info@croner.co.uk", "sector": "hr_consultancy", "hook": "Croner's comprehensive HR and advisory services to UK SMEs"},

    # MARKETING AGENCIES SERVING SMES
    {"firm": "Propeller", "contact": "Managing Director", "title": "Managing Director", "email": "hello@propeller.co.uk", "sector": "agency", "hook": "Propeller's strong B2B client relationships across UK SMEs"},
    {"firm": "Cognition Agency", "contact": "Managing Director", "title": "Managing Director", "email": "hello@cognitionagency.co.uk", "sector": "agency", "hook": "Cognition Agency's B2B focus on growth-stage UK businesses"},

    # MANAGEMENT CONSULTANCIES
    {"firm": "Altitude Partners", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@altitudepartners.co.uk", "sector": "consultancy", "hook": "Altitude Partners' strategic advisory focus on UK SME growth"},
    {"firm": "Watertight Marketing", "contact": "Founder", "title": "Founder", "email": "hello@watertightmarketing.com", "sector": "consultancy", "hook": "Watertight Marketing's deep SME client relationships across the UK"},
    {"firm": "Unleashed", "contact": "Managing Director", "title": "Managing Director", "email": "hello@unleashedapp.com", "sector": "business_advisory", "hook": "Unleashed's focus on product and inventory management for growing SMEs"},
    {"firm": "Tenzing", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@tenzing.io", "sector": "consultancy", "hook": "Tenzing's PE-backed SME growth advisory model"},
    {"firm": "Innovate UK Business Connect", "contact": "Managing Director", "title": "Managing Director", "email": "info@iuk.ktn-uk.org", "sector": "business_advisory", "hook": "Innovate UK's support for high-growth UK SMEs and scaleups"},
]

# ============================================================
# UAE TARGET LIST
# ============================================================

UAE_TARGETS = [
    # ACCOUNTANCY / BUSINESS ADVISORY IN UAE
    {"firm": "Crowe UAE", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@crowe-uae.com", "sector": "accountancy", "hook": "Crowe UAE's strong SME and mid-market advisory client base across the Emirates"},
    {"firm": "BDO UAE", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@bdo.ae", "sector": "accountancy", "hook": "BDO UAE's extensive SME advisory network across Dubai and Abu Dhabi"},
    {"firm": "RSM UAE", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@rsmae.com", "sector": "accountancy", "hook": "RSM UAE's focus on entrepreneurial businesses and family-owned enterprises"},
    {"firm": "Grant Thornton UAE", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@ae.gt.com", "sector": "accountancy", "hook": "Grant Thornton UAE's strong advisory practice for growing Dubai businesses"},
    {"firm": "PKF UAE", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@pkfuae.com", "sector": "accountancy", "hook": "PKF UAE's deep relationships with SME clients across the Emirates"},
    {"firm": "Nexia UAE", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@nexiauae.com", "sector": "accountancy", "hook": "Nexia UAE's advisory work with UAE's growing SME community"},
    {"firm": "HLB UAE", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@hlbuae.com", "sector": "accountancy", "hook": "HLB UAE's focus on entrepreneurial and owner-managed businesses in the UAE"},
    {"firm": "Morison Menon", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@morisonmenon.com", "sector": "accountancy", "hook": "Morison Menon's extensive UAE SME client base built over 25 years"},
    {"firm": "KPMG Lower Gulf", "contact": "Head of Advisory", "title": "Partner", "email": "aedubai@kpmg.com", "sector": "accountancy", "hook": "KPMG Lower Gulf's mid-market advisory strength across the UAE"},
    {"firm": "Deloitte Middle East", "contact": "Head of SME Advisory", "title": "Partner", "email": "me-info@deloitte.com", "sector": "accountancy", "hook": "Deloitte Middle East's growing SME advisory practice"},
    {"firm": "Mazars UAE", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@mazars.ae", "sector": "accountancy", "hook": "Mazars UAE's strong track record advising entrepreneurial businesses"},
    {"firm": "Moore Stephens UAE", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@moorestephens.ae", "sector": "accountancy", "hook": "Moore Stephens UAE's focus on Dubai and Abu Dhabi SME clients"},
    {"firm": "Alpen Capital", "contact": "Managing Director", "title": "Managing Director", "email": "info@alpencapital.com", "sector": "business_advisory", "hook": "Alpen Capital's advisory work with UAE and GCC businesses"},
    {"firm": "Business Registration UAE", "contact": "Managing Director", "title": "Managing Director", "email": "info@businessregistrationuae.com", "sector": "business_setup", "hook": "Business Registration UAE's large base of SME entrepreneur clients"},
    {"firm": "Virtuzone", "contact": "CEO", "title": "CEO", "email": "info@vz.ae", "sector": "business_setup", "hook": "Virtuzone's network of 15,000+ UAE business owners and entrepreneurs"},
    {"firm": "Creative Zone", "contact": "CEO", "title": "CEO", "email": "info@creativezone.ae", "sector": "business_setup", "hook": "Creative Zone's large portfolio of UAE SME and startup clients"},
    {"firm": "Commitbiz", "contact": "Managing Director", "title": "Managing Director", "email": "info@commitbiz.com", "sector": "business_advisory", "hook": "Commitbiz's business setup and advisory services for UAE entrepreneurs"},
    {"firm": "Farahat & Co", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@farahatco.com", "sector": "accountancy", "hook": "Farahat & Co's established UAE accountancy practice serving SMEs"},
    {"firm": "Tresfort Asset Management", "contact": "Managing Director", "title": "Managing Director", "email": "info@tresfort.ae", "sector": "business_advisory", "hook": "Tresfort's advisory work with UAE family businesses and SMEs"},
    {"firm": "Aurifer Tax Consultancy", "contact": "Managing Partner", "title": "Managing Partner", "email": "info@aurifer.com", "sector": "accountancy", "hook": "Aurifer's specialist UAE tax and advisory work for SME clients"},
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
# SEND EMAIL VIA GMAIL SMTP
# ============================================================

def send_email(to_email: str, to_name: str, subject: str, body: str) -> bool:
    """Send email via Gmail SMTP."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Shruti <{GMAIL_ADDRESS}>"
        msg['To'] = f"{to_name} <{to_email}>"
        msg['Reply-To'] = GMAIL_ADDRESS
        
        # Plain text version
        text_part = MIMEText(body + "\n\n--\nShruti\nEXOBRIEF · exobrief.com", 'plain')
        msg.attach(text_part)
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"  ✗ Send failed: {str(e)}")
        return False


# ============================================================
# LOGGING
# ============================================================

def load_log() -> dict:
    """Load the outreach log."""
    try:
        if Path(LOG_FILE).exists():
            with open(LOG_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"contacted": [], "stats": {"total_sent": 0, "total_replied": 0}}


def save_log(log: dict):
    """Save the outreach log."""
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)


def already_contacted(email: str, log: dict) -> bool:
    """Check if we've already emailed this address."""
    contacted_emails = [c['email'] for c in log.get('contacted', [])]
    return email in contacted_emails


def log_contact(target: dict, subject: str, region: str, log: dict):
    """Log a successful send."""
    log['contacted'].append({
        "email": target['email'],
        "firm": target['firm'],
        "contact": target['contact'],
        "region": region,
        "subject": subject,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "replied": False,
        "converted": False
    })
    log['stats']['total_sent'] = log['stats'].get('total_sent', 0) + 1


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
    
    log = load_log()
    sent_count = 0
    
    # Build target queue based on region
    if region == "uk":
        targets = [(t, "UK") for t in UK_TARGETS]
    elif region == "uae":
        targets = [(t, "UAE") for t in UAE_TARGETS]
    else:  # both
        # Split limit 50/50
        uk_limit = limit // 2
        uae_limit = limit - uk_limit
        targets = (
            [(t, "UK") for t in UK_TARGETS[:uk_limit * 3]] +  # Extra to account for already-contacted
            [(t, "UAE") for t in UAE_TARGETS[:uae_limit * 3]]
        )
    
    for target, target_region in targets:
        if sent_count >= limit:
            print(f"\n✓ Daily limit of {limit} reached. Done.")
            break
        
        email = target['email']
        
        # Skip if already contacted
        if already_contacted(email, log):
            print(f"  → Skipping {target['firm']} (already contacted)")
            continue
        
        print(f"\n→ Processing: {target['firm']} ({target_region})")
        print(f"  Contact: {target['contact']} <{email}>")
        
        try:
            # Generate personalised email
            print(f"  Generating personalised email...")
            body = generate_personalised_email(target, target_region)
            subject = generate_subject_line(target)
            
            print(f"  Subject: {subject}")
            print(f"  Body preview: {body[:80]}...")
            
            # Send
            print(f"  Sending...")
            success = send_email(email, target['contact'], subject, body)
            
            if success:
                log_contact(target, subject, target_region, log)
                save_log(log)
                sent_count += 1
                print(f"  ✓ Sent ({sent_count}/{limit})")
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
