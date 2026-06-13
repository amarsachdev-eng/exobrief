"""
EXOBRIEF — Automated Subscriber Acquisition Engine
Finds UK tech founders → generates personalised outreach → sends via SendGrid
Run: python outreach_engine.py
"""

import os
import json
import time
import random
import requests
from datetime import datetime, timezone
from typing import List, Dict

# ============================================================
# CONFIG — set these as environment variables on Railway
# ============================================================
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
FROM_EMAIL = "hello@exobrief.com"
FROM_NAME = "EXOBRIEF"

# ============================================================
# TARGET COMPANIES
# Manually curated UK tech founder targets — real companies,
# publicly available contact info from their websites
# Expand this list weekly
# ============================================================
TARGET_COMPANIES = [
    # Format: company, sector, competitor1, competitor2, founder_email, founder_name
    # These are example structures — populate with real scraped data
    {
        "company": "Paddle",
        "sector": "B2B SaaS · Payments · UK",
        "competitor1": "Stripe",
        "competitor2": "Chargebee",
        "email": "founders@paddle.com",
        "name": "Founder"
    },
]

# ============================================================
# OUTREACH COPY VARIANTS — rotated to avoid spam filters
# ============================================================
SUBJECT_LINES = [
    "Your competitor intelligence brief — free, no strings",
    "What {competitor1} did last week (and what to do about it)",
    "Free: weekly decision brief for {company}",
    "I built something that monitors {competitor1} for you automatically",
    "{company} — your market intelligence brief is ready",
]

EMAIL_BODIES = [
    """Hi {name},

I built EXOBRIEF — an automated intelligence engine that monitors your competitors and delivers a decision brief every Sunday morning.

For {company} in {sector}, that means:
→ What {competitor1} and {competitor2} did last week
→ Revenue risks hitting your market right now  
→ 3 specific decisions for the week ahead

First brief is completely free. No credit card. No signup friction.

Takes 60 seconds: exobrief.com

Happy to send you a sample brief for {company} right now if you'd rather see it first — just reply.

—
EXOBRIEF Intelligence Engine
exobrief.com""",

    """Hi {name},

Quick one — I built an automated tool that monitors {competitor1} and {competitor2} and delivers a weekly decision brief specifically for {company}.

Every Sunday morning:
· What your competitors moved on last week
· Market risks rated by revenue impact
· 3 actions tied to what actually happened

Free first brief. No card needed.

exobrief.com — takes 60 seconds to set up.

—
EXOBRIEF""",

    """Hi {name},

I run EXOBRIEF — we monitor competitor moves and market signals for UK tech founders and deliver a decision brief every Sunday.

For a {sector} company like {company}, we'd track {competitor1}, {competitor2}, and your market specifically.

First week is free. No commitment.

Would it be useful to see a sample brief built for {company} before you decide? Just say the word.

exobrief.com

—
EXOBRIEF Intelligence Engine"""
]

# ============================================================
# ANTHROPIC — personalise each email using Claude
# ============================================================
def personalise_email(company: str, sector: str, competitor1: str, 
                       competitor2: str, name: str) -> Dict:
    """Use Claude to generate a personalised subject + body"""
    
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    prompt = f"""Write a short, direct cold outreach email for EXOBRIEF targeting a founder at {company}.

Context:
- Company: {company}
- Sector: {sector}
- Competitors we'd monitor: {competitor1}, {competitor2}
- Founder name: {name}

EXOBRIEF is an automated competitive intelligence tool that:
1. Monitors named competitors automatically
2. Delivers a weekly decision brief every Sunday
3. First brief is completely free, no credit card
4. URL: exobrief.com

Rules:
- Max 120 words in the body
- No buzzwords, no hype
- One clear call to action: visit exobrief.com or reply for a sample brief
- Tone: direct, peer-to-peer, not salesy
- Subject line: max 8 words, specific to their company/competitors

Return JSON only:
{{"subject": "...", "body": "..."}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = response.content[0].text.strip()
    # Strip markdown if present
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


# ============================================================
# SENDGRID — send the email
# ============================================================
def send_email(to_email: str, to_name: str, subject: str, body: str) -> bool:
    """Send via SendGrid"""
    
    payload = {
        "personalizations": [{
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject
        }],
        "from": {"email": FROM_EMAIL, "name": FROM_NAME},
        "content": [{
            "type": "text/plain",
            "value": body
        }],
        "tracking_settings": {
            "click_tracking": {"enable": False},
            "open_tracking": {"enable": True}
        }
    }
    
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers=headers,
        json=payload
    )
    
    return response.status_code == 202


# ============================================================
# TRACKER — log who was contacted to avoid duplicates
# ============================================================
CONTACTED_FILE = "contacted.json"

def load_contacted() -> List[str]:
    if os.path.exists(CONTACTED_FILE):
        with open(CONTACTED_FILE, "r") as f:
            return json.load(f)
    return []

def save_contacted(emails: List[str]):
    with open(CONTACTED_FILE, "w") as f:
        json.dump(emails, f, indent=2)


# ============================================================
# MAIN OUTREACH LOOP
# ============================================================
def run_outreach(targets: List[Dict], max_per_run: int = 20, delay_seconds: int = 45):
    """
    Send personalised outreach to target list.
    max_per_run: cap per execution to stay under spam thresholds
    delay_seconds: pause between sends
    """
    
    contacted = load_contacted()
    sent_count = 0
    
    print(f"\n[EXOBRIEF OUTREACH] Starting run — {len(targets)} targets, max {max_per_run} sends")
    print(f"[EXOBRIEF OUTREACH] Already contacted: {len(contacted)} companies\n")
    
    for target in targets:
        if sent_count >= max_per_run:
            print(f"[EXOBRIEF OUTREACH] Reached max per run ({max_per_run}). Stopping.")
            break
            
        email = target.get("email", "").strip().lower()
        
        if not email or email in contacted:
            print(f"  SKIP: {target.get('company')} — already contacted or no email")
            continue
        
        company = target["company"]
        sector = target.get("sector", "B2B SaaS")
        competitor1 = target.get("competitor1", "competitor")
        competitor2 = target.get("competitor2", "competitor")
        name = target.get("name", "there")
        
        print(f"  → Personalising for {company} ({email})...")
        
        try:
            # Generate personalised email with Claude
            personalised = personalise_email(company, sector, competitor1, competitor2, name)
            subject = personalised["subject"]
            body = personalised["body"]
            
            print(f"    Subject: {subject}")
            
            # Send it
            success = send_email(email, name, subject, body)
            
            if success:
                print(f"    ✓ Sent to {email}")
                contacted.append(email)
                save_contacted(contacted)
                sent_count += 1
            else:
                print(f"    ✗ Failed to send to {email}")
                
        except Exception as e:
            print(f"    ✗ Error for {company}: {e}")
        
        # Delay between sends — avoid spam triggers
        if sent_count < max_per_run:
            time.sleep(delay_seconds + random.randint(0, 15))
    
    print(f"\n[EXOBRIEF OUTREACH] Run complete. Sent: {sent_count}")
    return sent_count


# ============================================================
# TARGET SCRAPER — Companies House free API
# Finds UK tech companies registered in last 12 months
# ============================================================
def scrape_companies_house(sector_keyword: str = "software", max_results: int = 50) -> List[Dict]:
    """
    Pull recently incorporated UK tech companies from Companies House API.
    These are young companies — likely founder-led, likely looking for tools.
    Free API, no key needed for basic search.
    """
    
    url = "https://api.company-information.service.gov.uk/search/companies"
    params = {
        "q": sector_keyword,
        "items_per_page": max_results,
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        companies = []
        for item in data.get("items", []):
            company_name = item.get("title", "")
            company_number = item.get("company_number", "")
            status = item.get("company_status", "")
            
            if status == "active" and company_name:
                companies.append({
                    "company": company_name,
                    "company_number": company_number,
                    "sector": f"Tech · UK",
                    "competitor1": "HubSpot",
                    "competitor2": "Salesforce",
                    "email": "",  # Needs enrichment step
                    "name": "Founder"
                })
        
        print(f"[SCRAPER] Found {len(companies)} companies from Companies House")
        return companies
        
    except Exception as e:
        print(f"[SCRAPER] Companies House error: {e}")
        return []


# ============================================================
# REDDIT POST GENERATOR
# ============================================================
def generate_reddit_posts() -> Dict:
    """Generate ready-to-post Reddit content for multiple subreddits"""
    
    posts = {
        "r/SaaS": {
            "title": "I built an automated competitive intelligence brief for SaaS founders — free to try",
            "body": """Been frustrated watching competitors make moves we only found out about weeks later.

Built EXOBRIEF to solve this for myself — it monitors named competitors automatically and delivers a weekly decision brief every Sunday morning. Specific signals, sourced links, 3 actions tied to what actually happened.

**What it does:**
- Monitors up to 5 competitors across 8 source categories (LinkedIn jobs, Companies House, earnings, product blogs, review sites)
- Weekly brief delivered every Sunday — competitor moves, revenue risks, market signals
- 3 specific decisions tied to what happened last week
- Gets smarter over time as it builds competitive memory for your market

**What it doesn't do:**
- It's not a chatbot. You don't have to remember to use it or know what to ask.
- It's not a dashboard to check. It arrives in your inbox.

First brief is completely free — takes 60 seconds to set up at exobrief.com

Happy to answer questions or send a sample brief if anyone wants to see what the output looks like before signing up."""
        },
        
        "r/microsaas": {
            "title": "Show r/microsaas: Automated weekly competitive intelligence brief for founders",
            "body": """**What I built:** EXOBRIEF — automated competitive intelligence for tech founders

**The problem:** Founders miss competitor moves until it's too late. Manually monitoring competitors is either a full-time job or doesn't get done.

**What it does:** Monitors your named competitors automatically. Delivers a decision brief every Sunday — what they did, what it means for your revenue, 3 specific actions.

**Tech stack:** Python on Railway, Supabase, SendGrid, Anthropic API, NewsAPI

**Business model:** £29/month founding member rate (first 100 subscribers), rising to £99/month after.

**Where I'm at:** Product is live and working. Looking for the first 10 real subscribers for validation.

**Free first brief:** exobrief.com — no credit card, takes 60 seconds.

Would genuinely value feedback from this community on positioning, pricing, or anything else."""
        },
        
        "r/Entrepreneur": {
            "title": "Built a tool that monitors your competitors automatically and emails you what to do about it every Sunday",
            "body": """Every Monday I'd find out something a competitor did the previous week that we should have known about and responded to immediately.

Spent 3 months building EXOBRIEF to fix this.

**How it works:**
1. You tell it your company, sector, and up to 5 competitors
2. It monitors them across hiring signals, product launches, pricing changes, funding, reviews
3. Every Sunday morning: a brief lands in your inbox with what happened, what it means for your business, and 3 specific actions

It's not AI you have to prompt. It runs while you don't and tells you things you didn't know to look for.

**First brief is free.** No credit card. 60 seconds to set up.

exobrief.com

Anyone else built systems for competitive monitoring? Curious what approaches have worked."""
        }
    }
    
    return posts


# ============================================================
# INDIE HACKERS POST
# ============================================================
def generate_indie_hackers_post() -> Dict:
    return {
        "title": "Show IH: I built automated competitive intelligence for founders — EXOBRIEF",
        "body": """**What I built**

EXOBRIEF — weekly competitive intelligence briefs, delivered automatically every Sunday.

**The problem it solves**

Founders need to monitor competitors but don't have time. Manual monitoring either doesn't happen or takes hours. By the time you find out a competitor launched something or changed pricing, you're already behind.

**How it works**

1. You enter your company, sector, and up to 5 competitors (takes 60 seconds)
2. EXOBRIEF monitors them automatically across 8 source categories
3. Every Sunday: a brief lands in your inbox with competitor moves, revenue risks, and 3 specific decisions

**What makes it different from ChatGPT / Perplexity**

It runs without you. You don't have to remember to ask. It builds competitive memory over time. It tells you things you didn't know to look for.

**Tech**

Python, Railway, Supabase, SendGrid, Anthropic API, NewsAPI. Solo-built in 3 weeks.

**Where I'm at**

Live and working. Looking for first 10 real subscribers for honest validation. First brief is free — no card needed.

**Try it:** exobrief.com

Would love feedback on positioning, pricing (currently £29/month founding rate), or anything the output is missing. Happy to share a sample brief if you want to see the output before signing up."""
    }


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python outreach_engine.py email      — run email outreach")
        print("  python outreach_engine.py posts      — print Reddit/IH posts")
        print("  python outreach_engine.py scrape     — scrape Companies House")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "email":
        run_outreach(TARGET_COMPANIES)
    
    elif command == "posts":
        print("\n" + "="*60)
        print("REDDIT POSTS — copy/paste to each subreddit")
        print("="*60)
        posts = generate_reddit_posts()
        for subreddit, post in posts.items():
            print(f"\n{'='*60}")
            print(f"SUBREDDIT: {subreddit}")
            print(f"TITLE: {post['title']}")
            print(f"\nBODY:\n{post['body']}")
        
        print("\n" + "="*60)
        print("INDIE HACKERS POST")
        print("="*60)
        ih = generate_indie_hackers_post()
        print(f"TITLE: {ih['title']}")
        print(f"\nBODY:\n{ih['body']}")
    
    elif command == "scrape":
        companies = scrape_companies_house("software", 100)
        print(f"\nFound {len(companies)} companies")
        print("NOTE: Email enrichment needed — Companies House doesn't provide emails")
        print("Next step: use Hunter.io API or manual enrichment for email addresses")
        with open("scraped_companies.json", "w") as f:
            json.dump(companies, f, indent=2)
        print("Saved to scraped_companies.json")
