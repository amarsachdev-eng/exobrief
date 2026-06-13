"""
EXOBRIEF — Target List Builder
Finds real UK tech founders with publicly available contact info
Sources: Hunter.io, Apollo.io free tier, manual curated list
Run: python build_target_list.py
"""

import json
import requests
import os
import time

# ============================================================
# MANUALLY CURATED STARTER LIST
# Real UK B2B SaaS companies, founder emails from public sources
# This is your seed list — expand weekly
# ============================================================

SEED_TARGETS = [
    # These are real UK SaaS companies — find founder emails via:
    # 1. Company website About/Contact page
    # 2. Hunter.io domain search (free tier: 25/month)
    # 3. LinkedIn public profile
    # Format: fill in email once found
    
    {"company": "Pleo", "sector": "B2B SaaS · Finance · UK", "competitor1": "Expensify", "competitor2": "Soldo", "email": "", "name": "Founder"},
    {"company": "Hopin", "sector": "B2B SaaS · Events · UK", "competitor1": "Zoom", "competitor2": "Eventbrite", "email": "", "name": "Founder"},
    {"company": "Wayve", "sector": "AI · Autonomous · UK", "competitor1": "Waymo", "competitor2": "Mobileye", "email": "", "name": "Founder"},
    {"company": "Moneyhub", "sector": "B2B SaaS · Fintech · UK", "competitor1": "Plaid", "competitor2": "TrueLayer", "email": "", "name": "Founder"},
    {"company": "Cleo", "sector": "B2C SaaS · Fintech · UK", "competitor1": "Monzo", "competitor2": "Revolut", "email": "", "name": "Founder"},
    {"company": "Tractable", "sector": "AI · Insurance · UK", "competitor1": "Snapsheet", "competitor2": "Mitchell", "email": "", "name": "Founder"},
    {"company": "Tessian", "sector": "B2B SaaS · Security · UK", "competitor1": "Proofpoint", "competitor2": "Mimecast", "email": "", "name": "Founder"},
    {"company": "Butternut Box", "sector": "D2C · Subscription · UK", "competitor1": "Tails.com", "competitor2": "Pure Pet Food", "email": "", "name": "Founder"},
    {"company": "Onfido", "sector": "B2B SaaS · Identity · UK", "competitor1": "Jumio", "competitor2": "Veriff", "email": "", "name": "Founder"},
    {"company": "Marshmallow", "sector": "Insurtech · UK", "competitor1": "By Miles", "competitor2": "Zego", "email": "", "name": "Founder"},
]


def enrich_with_hunter(domain: str, hunter_api_key: str) -> str:
    """
    Find email for a domain using Hunter.io
    Free tier: 25 searches/month
    Get key at hunter.io
    """
    url = f"https://api.hunter.io/v2/domain-search"
    params = {
        "domain": domain,
        "api_key": hunter_api_key,
        "limit": 1,
        "type": "personal"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        emails = data.get("data", {}).get("emails", [])
        if emails:
            return emails[0].get("value", "")
    except Exception as e:
        print(f"Hunter error for {domain}: {e}")
    
    return ""


def save_targets(targets, filename="targets.json"):
    with open(filename, "w") as f:
        json.dump(targets, f, indent=2)
    print(f"Saved {len(targets)} targets to {filename}")


def load_targets(filename="targets.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return SEED_TARGETS


if __name__ == "__main__":
    print("\n[TARGET BUILDER] Loading seed list...")
    targets = load_targets()
    
    hunter_key = os.environ.get("HUNTER_API_KEY", "")
    
    if hunter_key:
        print(f"[TARGET BUILDER] Hunter.io key found — enriching emails...")
        for target in targets:
            if not target.get("email"):
                domain = target["company"].lower().replace(" ", "") + ".com"
                email = enrich_with_hunter(domain, hunter_key)
                if email:
                    target["email"] = email
                    print(f"  ✓ {target['company']}: {email}")
                time.sleep(2)
    else:
        print("[TARGET BUILDER] No Hunter.io key — add HUNTER_API_KEY to Railway vars")
        print("[TARGET BUILDER] Or manually add emails to targets.json")
    
    # Filter to only targets with emails
    ready = [t for t in targets if t.get("email")]
    pending = [t for t in targets if not t.get("email")]
    
    print(f"\n[TARGET BUILDER] Ready to contact: {len(ready)}")
    print(f"[TARGET BUILDER] Needs email: {len(pending)}")
    
    save_targets(targets)
