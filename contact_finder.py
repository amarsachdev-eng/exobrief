"""
EXOBRIEF Automated Contact Finder & Sender
==========================================
Runs on Railway. Every hour:
1. Uses Claude web search to find UK SME business owners
2. Extracts name, company, email from public websites  
3. Generates personalised brief-first email
4. Sends via SendGrid from rotating addresses
5. Logs to Supabase
"""

import os
import json
import time
import random
import urllib.request
from datetime import datetime, timezone

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SENDGRID_KEY = os.environ.get("SENDGRID_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Rotating sender addresses
SENDERS = [
    {"email": "hello@exobrief.com", "name": "Shruti"},
    {"email": "outreach@exobrief.com", "name": "Shruti"},
    {"email": "intelligence@exobrief.com", "name": "Shruti"},
]

# Target sectors with search queries
SEARCH_QUERIES = [
    # UK Recruitment
    "site:uk recruitment agency managing director email -jobs -apply",
    "UK HR consultancy founder CEO email contact site:.co.uk",
    "UK independent recruitment firm director email about us",
    # UK Professional Services  
    "UK management consultancy SME clients managing partner email",
    "UK fractional CFO firm founder email contact",
    "UK business advisory firm director email about",
    # UK Hospitality/Retail
    "UK independent hotel group owner director email contact",
    "UK restaurant group founder CEO email about us",
    "UK retail chain founder managing director email",
    # UK Construction/Property
    "UK construction firm managing director email contact site:.co.uk",
    "UK property developer CEO founder email about",
    # UAE sectors
    "UAE recruitment firm managing director email contact site:.ae",
    "Dubai HR consultancy CEO founder email about us",
    "UAE business advisory firm director email contact",
]

def find_contacts_via_claude(query: str) -> list:
    """Use Claude with web search to find business contacts."""
    import anthropic
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    
    prompt = f"""Search for this query and find real business contacts: "{query}"

For each result found, extract:
1. Person's full name (must be a real named person, not "Managing Director")
2. Their job title
3. Company name
4. Their direct email address (only if publicly listed on their website)
5. Company sector
6. 3 named competitors

Return ONLY a JSON array. Each item must have: name, title, company, email, sector, competitors (array of 3).
Only include entries where you found a REAL named person with a REAL email address publicly listed.
Maximum 5 contacts per search.
Return empty array [] if nothing found.
Return JSON only, no other text."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Extract text from response
    text = ""
    for block in message.content:
        if hasattr(block, 'text'):
            text += block.text
    
    # Parse JSON
    try:
        # Find JSON array in response
        start = text.find('[')
        end = text.rfind(']') + 1
        if start >= 0 and end > start:
            contacts = json.loads(text[start:end])
            return contacts
    except:
        pass
    return []

def already_contacted(email: str) -> bool:
    """Check Supabase if already contacted."""
    try:
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/outreach_log?select=email&email=eq.{email}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return len(data) > 0
    except:
        return False

def generate_email(contact: dict) -> dict:
    """Generate personalised urgency email."""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    
    first_name = contact['name'].split()[0]
    sector = contact.get('sector', 'professional services')
    company = contact['company']
    competitors = contact.get('competitors', ['key competitors'])
    
    prompt = f"""Write a cold email for EXOBRIEF competitive intelligence platform.

TARGET:
- Name: {first_name}
- Company: {company}
- Sector: {sector}
- Their competitors: {competitors}

RULES:
1. Maximum 5 sentences
2. Start: "Hi {first_name},"
3. Sentence 2: Several {sector} firms are now receiving weekly intelligence on exactly what their rivals are doing. {company} isn't one of them yet.
4. Sentence 3: One sentence on what EXOBRIEF does — tracks competitor moves weekly, delivers brief every Sunday
5. Sentence 4: "Want to see what {competitors[0] if competitors else 'your rivals'} have been doing this week? Just reply."
6. Sign: Shruti / EXOBRIEF · exobrief.com
7. NO pricing. NO links. NO bullet points.

Write email body only."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    body = message.content[0].text.strip()
    
    # Subject line
    subjects = [
        f"what your competitors are doing this week",
        f"your rivals just made some moves",
        f"competitor intelligence — {company}",
        f"what {sector} firms are tracking right now",
    ]
    
    return {
        "subject": random.choice(subjects),
        "body": body
    }

def send_email(contact: dict, email_content: dict, sender: dict) -> bool:
    """Send via SendGrid."""
    try:
        html_body = email_content['body'].replace('\n', '<br>')
        
        payload = json.dumps({
            "personalizations": [{
                "to": [{"email": contact['email'], "name": contact['name']}]
            }],
            "from": {"email": sender['email'], "name": sender['name']},
            "reply_to": {"email": "hello@exobrief.com", "name": "Shruti"},
            "subject": email_content['subject'],
            "content": [
                {"type": "text/plain", "value": email_content['body']},
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
    except Exception as e:
        print(f"  Send error: {e}")
        return False

def log_contact(contact: dict, subject: str, sender: str):
    """Log to Supabase."""
    try:
        payload = json.dumps({
            "email": contact['email'],
            "firm": contact['company'],
            "contact": contact['name'],
            "region": "UK" if ".co.uk" in contact['email'] or "uk" in contact.get('sector','').lower() else "UAE",
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
        with urllib.request.urlopen(req, timeout=10) as r:
            return True
    except Exception as e:
        print(f"  Log error: {e}")
        return False

def run_hourly_batch(max_sends: int = 20):
    """Find contacts and send emails — runs every hour."""
    print(f"\n{'='*60}")
    print(f"EXOBRIEF Auto-Finder — {datetime.now().strftime('%Y-%m-%d %H:%M BST')}")
    print(f"{'='*60}\n")
    
    sent = 0
    sender_index = 0
    
    # Pick random search queries for this hour
    queries = random.sample(SEARCH_QUERIES, min(5, len(SEARCH_QUERIES)))
    
    for query in queries:
        if sent >= max_sends:
            break
            
        print(f"→ Searching: {query[:60]}")
        
        try:
            contacts = find_contacts_via_claude(query)
            print(f"  Found {len(contacts)} contacts")
            
            for contact in contacts:
                if sent >= max_sends:
                    break
                
                # Validate contact
                email = contact.get('email', '')
                name = contact.get('name', '')
                
                if not email or not name or '@' not in email:
                    continue
                if any(title in name for title in ['Managing Director', 'CEO', 'Director', 'Manager']):
                    print(f"  → Skipping generic title: {name}")
                    continue
                if already_contacted(email):
                    print(f"  → Already contacted: {email}")
                    continue
                
                print(f"\n  → Processing: {name} at {contact.get('company', '')} <{email}>")
                
                # Generate email
                email_content = generate_email(contact)
                
                # Rotate sender
                sender = SENDERS[sender_index % len(SENDERS)]
                sender_index += 1
                
                print(f"  Subject: {email_content['subject']}")
                print(f"  From: {sender['email']}")
                
                # Send
                if send_email(contact, email_content, sender):
                    log_contact(contact, email_content['subject'], sender['email'])
                    sent += 1
                    print(f"  ✓ Sent ({sent}/{max_sends})")
                    time.sleep(3)
                else:
                    print(f"  ✗ Send failed")
                    
        except Exception as e:
            print(f"  Error: {e}")
            continue
        
        time.sleep(5)
    
    print(f"\n{'='*60}")
    print(f"Batch complete: {sent} emails sent")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run_hourly_batch(max_sends=20)
