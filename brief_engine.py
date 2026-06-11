"""
EXOBRIEF — Brief Generation Engine
Core AI agent that generates personalised weekly decision briefs
Architecture mirrors PRISM — same pattern, different purpose
"""

import anthropic
import requests
import json
from datetime import datetime, timezone
from typing import Optional

# ============================================================
# CONFIGURATION
# ============================================================

ANTHROPIC_API_KEY = "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"
NEWS_API_KEY = ""  # Add NewsAPI key when ready — newsapi.org free tier
MODEL = "claude-sonnet-4-6"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ============================================================
# DATA GATHERING — PUBLIC SIGNALS
# ============================================================

def fetch_competitor_signals(competitor_names: list, sector: str) -> str:
    """
    Fetch public signals about named competitors
    Uses NewsAPI for press mentions and announcements
    Falls back to sector news if NewsAPI key not set
    """
    signals = []

    if NEWS_API_KEY:
        for competitor in competitor_names:
            try:
                url = f"https://newsapi.org/v2/everything"
                params = {
                    "q": f'"{competitor}"',
                    "sortBy": "publishedAt",
                    "pageSize": 3,
                    "apiKey": NEWS_API_KEY,
                    "language": "en"
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    articles = response.json().get("articles", [])
                    for article in articles[:2]:
                        signals.append(f"[{competitor}] {article.get('title', '')} — {article.get('description', '')} (Source: {article.get('source', {}).get('name', 'Unknown')}, {article.get('publishedAt', '')[:10]})")
            except Exception as e:
                signals.append(f"[{competitor}] Signal fetch error: {str(e)}")
    else:
        # Fallback — sector news when no API key
        try:
            url = f"https://newsapi.org/v2/everything"
            # Use RSS feeds as fallback
            signals.append(f"[Sector Intelligence] Monitoring {sector} sector for competitor movements")
            signals.append(f"[Note] Add NewsAPI key to config for full competitor monitoring")
        except:
            pass

    return "\n".join(signals) if signals else f"Monitoring active for: {', '.join(competitor_names)}"


def fetch_market_signals(sector: str, geography: str) -> str:
    """
    Fetch market signals for subscriber's sector and geography
    """
    signals = []

    if NEWS_API_KEY:
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": f"{sector} market trends OR {sector} industry news OR {sector} regulatory",
                "sortBy": "publishedAt",
                "pageSize": 5,
                "apiKey": NEWS_API_KEY,
                "language": "en"
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                articles = response.json().get("articles", [])
                for article in articles[:3]:
                    signals.append(f"[Market] {article.get('title', '')} — {article.get('description', '')} (Source: {article.get('source', {}).get('name', 'Unknown')}, {article.get('publishedAt', '')[:10]})")
        except Exception as e:
            signals.append(f"[Market] Signal fetch error: {str(e)}")
    else:
        signals.append(f"[Market] Active monitoring for {sector} in {geography}")
        signals.append(f"[Note] Add NewsAPI key for full market signal monitoring")

    return "\n".join(signals) if signals else f"Market monitoring active for {sector} in {geography}"


def fetch_risk_signals(sector: str, geography: str) -> str:
    """
    Fetch regulatory and risk signals relevant to subscriber
    """
    signals = []

    if NEWS_API_KEY:
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": f"{geography} {sector} regulation OR {geography} {sector} policy OR {geography} business risk",
                "sortBy": "publishedAt",
                "pageSize": 5,
                "apiKey": NEWS_API_KEY,
                "language": "en"
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                articles = response.json().get("articles", [])
                for article in articles[:3]:
                    signals.append(f"[Risk] {article.get('title', '')} — {article.get('description', '')} (Source: {article.get('source', {}).get('name', 'Unknown')}, {article.get('publishedAt', '')[:10]})")
        except Exception as e:
            signals.append(f"[Risk] Signal fetch error: {str(e)}")
    else:
        signals.append(f"[Risk Horizon] Active monitoring for {geography} {sector} regulatory signals")

    return "\n".join(signals) if signals else f"Risk monitoring active for {sector} in {geography}"


# ============================================================
# CLAUDE BRIEF GENERATION — THE CORE ENGINE
# ============================================================

def generate_brief(subscriber: dict) -> str:
    """
    Generate a personalised weekly decision brief for a subscriber
    This is the heart of EXOBRIEF — the McKinsey-grade intelligence engine

    subscriber dict structure:
    {
        "company_name": str,
        "company_url": str,
        "sector": str,
        "geography": str,
        "competitors": list,
        "strategic_priorities": str,
        "biggest_concern": str,
        "customer_type": str,  # B2B or B2C
        "previous_briefs_summary": str  # Company memory layer
    }
    """

    company = subscriber.get("company_name", "Your Company")
    sector = subscriber.get("sector", "Technology")
    geography = subscriber.get("geography", "United Kingdom")
    competitors = subscriber.get("competitors", [])
    priorities = subscriber.get("strategic_priorities", "Growth and competitive positioning")
    concern = subscriber.get("biggest_concern", "Market competition")
    customer_type = subscriber.get("customer_type", "B2B")
    previous_briefs = subscriber.get("previous_briefs_summary", "First brief — no previous context")

    # Gather all signals
    print(f"  → Fetching competitor signals for {company}...")
    competitor_signals = fetch_competitor_signals(competitors, sector)

    print(f"  → Fetching market signals for {sector} in {geography}...")
    market_signals = fetch_market_signals(sector, geography)

    print(f"  → Fetching risk signals for {geography}...")
    risk_signals = fetch_risk_signals(sector, geography)

    # Build the prompt
    current_date = datetime.now(timezone.utc).strftime("%A %d %B %Y")

    prompt = f"""You are EXOBRIEF — an autonomous Chief Intelligence Officer delivering McKinsey-grade weekly strategic intelligence to growth company founders.

Today is {current_date}.

SUBSCRIBER PROFILE:
- Company: {company}
- Sector: {sector}
- Geography: {geography}
- Competitors being monitored: {', '.join(competitors) if competitors else 'None specified'}
- Top strategic priorities: {priorities}
- Biggest current concern: {concern}
- Customer type: {customer_type}

COMPANY MEMORY (previous brief context):
{previous_briefs}

RAW INTELLIGENCE GATHERED THIS WEEK:

COMPETITOR SIGNALS:
{competitor_signals}

MARKET SIGNALS:
{market_signals}

RISK & REGULATORY SIGNALS:
{risk_signals}

---

Generate a weekly EXOBRIEF intelligence brief for {company}. 

STRICT FORMAT REQUIREMENTS:

1. REVENUE RISK THIS WEEK
Identify the most significant external threat to {company}'s revenue this week based on the signals above.
Express impact as a risk band: Low / Medium / Medium-High / High
Always include: what happened, what it means for {company} specifically, and recommended response timeframe.
Never use precise £ figures — use risk bands with rationale only.

2. COMPETITOR RADAR
The single most significant competitor signal this week.
Must be specific to a named competitor if signals exist.
Include: what they did, why it matters to {company}, what advantage or risk this creates.

3. MARKET MOVEMENT  
One specific market signal relevant to {company}'s sector and geography.
Must answer: what shifted, what it means for {company}'s positioning this week.

4. RISK HORIZON
One regulatory, geopolitical, or macroeconomic signal that could affect {company} in the next 30-90 days.
Must be specific to their geography and sector.

5. THIS WEEK'S DECISIONS
Exactly 3 specific actions {company}'s leadership team should take this week.
Each action must be tied directly to one of the signals above.
Format: Action → Why → How

6. IF YOU DO ONE THING THIS WEEK
Single highest-priority action. One sentence. No hedging. No qualifications.

QUALITY STANDARDS:
- Every insight must answer: "What is this costing us and what do we do about it?"
- Never use generic statements. Every line must be specific to {company}'s situation.
- If signal data is thin, acknowledge it honestly and focus on what IS known.
- Tone: confident, precise, senior analyst. Not a newsletter. Not a summary. A decision brief.
- Length: concise but complete. No padding. No filler.

This brief must contain at least one insight {company}'s leadership team could not have found themselves in 60 minutes of manual research."""

    print(f"  → Generating brief with Claude for {company}...")

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        brief_content = message.content[0].text
        return brief_content

    except Exception as e:
        print(f"  ✗ Claude API error: {str(e)}")
        return f"Brief generation error for {company}: {str(e)}"


# ============================================================
# TEST RUN — SINGLE SUBSCRIBER
# ============================================================

def test_brief_generation():
    """
    Test brief generation with a sample subscriber profile
    Run this to verify the engine works before full deployment
    """

    test_subscriber = {
        "company_name": "Meridian Analytics",
        "company_url": "meridiananalytics.io",
        "sector": "B2B SaaS / Data Analytics",
        "geography": "United Kingdom",
        "competitors": ["Tableau", "Looker", "Power BI"],
        "strategic_priorities": "Expanding into mid-market enterprise accounts, launching new AI reporting features, growing ARR from £2M to £5M",
        "biggest_concern": "Microsoft Power BI bundling with M365 is making it harder to justify our standalone pricing",
        "customer_type": "B2B",
        "previous_briefs_summary": "First brief — establishing baseline competitive intelligence"
    }

    print("=" * 60)
    print("EXOBRIEF — Brief Generation Engine Test")
    print("=" * 60)
    print(f"Generating brief for: {test_subscriber['company_name']}")
    print(f"Sector: {test_subscriber['sector']}")
    print(f"Geography: {test_subscriber['geography']}")
    print(f"Competitors: {', '.join(test_subscriber['competitors'])}")
    print("-" * 60)

    brief = generate_brief(test_subscriber)

    print("\n" + "=" * 60)
    print("GENERATED BRIEF:")
    print("=" * 60)
    print(brief)
    print("=" * 60)

    # Save to file for review
    with open("/home/claude/exobrief/test_brief_output.txt", "w") as f:
        f.write(f"EXOBRIEF TEST — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Subscriber: {test_subscriber['company_name']}\n")
        f.write("=" * 60 + "\n")
        f.write(brief)

    print("\n✓ Brief saved to test_brief_output.txt")
    return brief


if __name__ == "__main__":
    test_brief_generation()
