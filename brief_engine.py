"""
EXOBRIEF — Brief Generation Engine v2
Rewritten for specificity — named competitor intelligence, not generic market commentary
"""

import anthropic
import os
import requests
import json
from datetime import datetime, timezone
from typing import Optional

# ============================================================
# CONFIGURATION
# ============================================================

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
MODEL = "claude-sonnet-4-6"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ============================================================
# SIGNAL GATHERING
# ============================================================

def fetch_competitor_signals(competitor_names: list, sector: str) -> dict:
    """
    Fetch public signals for each named competitor individually.
    Returns a dict keyed by competitor name with their signals.
    If no signal found for a competitor, records that explicitly — silence is data.
    """
    results = {}

    for competitor in competitor_names:
        competitor_signals = []

        if NEWS_API_KEY:
            # Search 1: Direct competitor news
            try:
                response = requests.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": f'"{competitor}"',
                        "sortBy": "publishedAt",
                        "pageSize": 5,
                        "apiKey": NEWS_API_KEY,
                        "language": "en"
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    articles = response.json().get("articles", [])
                    for article in articles[:3]:
                        title = article.get("title", "")
                        desc = article.get("description", "")
                        source = article.get("source", {}).get("name", "Unknown")
                        date = article.get("publishedAt", "")[:10]
                        url = article.get("url", "")
                        if title:
                            competitor_signals.append(
                                f"SIGNAL: {title}\n"
                                f"DETAIL: {desc}\n"
                                f"SOURCE: {source} · {date}\n"
                                f"URL: {url}"
                            )
            except Exception as e:
                competitor_signals.append(f"Signal fetch error: {str(e)}")

            # Search 2: Competitor pricing/product news
            try:
                response = requests.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": f'"{competitor}" pricing OR product OR launch OR funding OR hire',
                        "sortBy": "publishedAt",
                        "pageSize": 3,
                        "apiKey": NEWS_API_KEY,
                        "language": "en"
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    articles = response.json().get("articles", [])
                    for article in articles[:2]:
                        title = article.get("title", "")
                        desc = article.get("description", "")
                        source = article.get("source", {}).get("name", "Unknown")
                        date = article.get("publishedAt", "")[:10]
                        url = article.get("url", "")
                        if title and title not in str(competitor_signals):
                            competitor_signals.append(
                                f"PRODUCT/COMMERCIAL SIGNAL: {title}\n"
                                f"DETAIL: {desc}\n"
                                f"SOURCE: {source} · {date}\n"
                                f"URL: {url}"
                            )
            except Exception as e:
                pass

        if competitor_signals:
            results[competitor] = "\n\n".join(competitor_signals)
        else:
            results[competitor] = "NO SIGNALS DETECTED THIS WEEK — no public announcements, pricing changes, or press mentions found. Note this in the brief as confirmed quiet week for this competitor."

    return results


def fetch_market_signals(sector: str, geography: str) -> str:
    """Market and regulatory signals for the subscriber's sector."""
    signals = []

    if NEWS_API_KEY:
        queries = [
            f"{sector} {geography} market",
            f"{geography} SaaS regulation OR compliance OR policy 2026",
            f"{sector} AI trends buyers 2026"
        ]
        for q in queries:
            try:
                response = requests.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": q,
                        "sortBy": "publishedAt",
                        "pageSize": 3,
                        "apiKey": NEWS_API_KEY,
                        "language": "en"
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    articles = response.json().get("articles", [])
                    for article in articles[:2]:
                        title = article.get("title", "")
                        desc = article.get("description", "")
                        source = article.get("source", {}).get("name", "Unknown")
                        date = article.get("publishedAt", "")[:10]
                        if title and title not in str(signals):
                            signals.append(f"[{source} · {date}] {title} — {desc}")
            except Exception:
                pass

    return "\n".join(signals) if signals else f"Market monitoring active for {sector} in {geography}. No breaking signals this week."


# ============================================================
# CLAUDE BRIEF GENERATION — REWRITTEN PROMPT
# ============================================================

def generate_brief(subscriber: dict) -> str:
    """
    Generate a personalised weekly decision brief.
    
    Key change from v1: competitor intelligence is now structured per-competitor,
    not dumped as a single block. Claude is instructed to be specific or honest
    about silence — never to manufacture generic commentary.
    """

    company = subscriber.get("company_name", "Your Company")
    sector = subscriber.get("sector", "Technology")
    geography = subscriber.get("geography", "United Kingdom")
    competitors = subscriber.get("competitors", [])
    priorities = subscriber.get("strategic_priorities", "Growth and competitive positioning")
    concern = subscriber.get("biggest_concern", "Market competition")
    customer_type = subscriber.get("customer_type", "B2B")
    previous_briefs = subscriber.get("previous_briefs_summary", "First brief — no previous context")

    print(f" → Fetching signals for {len(competitors)} named competitors...")
    competitor_signals = fetch_competitor_signals(competitors, sector)

    print(f" → Fetching market signals...")
    market_signals = fetch_market_signals(sector, geography)

    current_date = datetime.now(timezone.utc).strftime("%A %d %B %Y")

    # Format competitor signals for prompt — one block per competitor
    competitor_intelligence_block = ""
    for i, (competitor, signals) in enumerate(competitor_signals.items(), 1):
        competitor_intelligence_block += f"""
COMPETITOR {i}: {competitor}
{'-' * 40}
{signals}

"""

    prompt = f"""You are EXOBRIEF — an autonomous intelligence engine delivering weekly decision briefs to tech founders.

Today is {current_date}.

SUBSCRIBER PROFILE:
- Company: {company}
- Sector: {sector}
- Geography: {geography}
- Named competitors being monitored: {', '.join(competitors) if competitors else 'None specified — brief cannot include competitor radar without named competitors'}
- Top strategic priorities: {priorities}
- Biggest current concern: {concern}
- Customer type: {customer_type}

PREVIOUS BRIEF CONTEXT (company memory):
{previous_briefs}

---
INTELLIGENCE GATHERED THIS WEEK
---

COMPETITOR-BY-COMPETITOR SIGNALS:
{competitor_intelligence_block}

MARKET & REGULATORY SIGNALS:
{market_signals}

---
BRIEF GENERATION INSTRUCTIONS
---

Generate a weekly intelligence brief for {company}. Follow this exact structure.

CRITICAL RULES — read before writing a single word:

1. SPECIFICITY OR HONESTY — pick one. Never manufacture generic commentary.
   If you have a real signal about a named competitor → use it, cite it, say when it happened.
   If you have no signal for a competitor → say "No public signals detected for [name] this week" 
   and move to the next one. Do NOT fill gaps with generic market observations about that competitor.

2. EVERY COMPETITOR SECTION must name the competitor explicitly.
   Never write "a competitor" or "some players in the market." 
   Always: "[Competitor Name] did X on [date]."

3. DECISIONS must be tied to actual signals found above.
   No floating advice. Every decision = one signal + one specific action.

4. IF SIGNALS ARE THIN — be honest and useful:
   "Signal data is limited this week for [competitor]. 
   Based on their known strategy of [X], watch for [Y] in the next 30 days."
   That is better than inventing commentary.

---
OUTPUT FORMAT — use exactly this structure:
---

⚠️ REVENUE RISK THIS WEEK
Risk Band: [HIGH / MEDIUM-HIGH / MEDIUM / LOW]

What changed: [2-3 sentences max. Specific. What actually happened this week that affects {company}'s revenue.]

Direct impact on {company}: [What this means for their pipeline, customers, or competitive position specifically — not generally.]

Act within: [Specific timeframe — e.g. "Before your next 3 prospect conversations this week"]

---

🔭 COMPETITOR RADAR

[For each named competitor, write one block:]

[COMPETITOR NAME] — [THREAT / WATCH / OPPORTUNITY / QUIET THIS WEEK]
Signal: [What they did, or "No public signals detected this week"]
Source: [Publication · Date · URL if available — or "No public signal found"]
Impact on {company}: [Specific implication — or if quiet: what that silence might mean]
Counter-move: [One specific action {company} can take — or "Monitor for X next week"]

[Repeat for each named competitor]

---

📈 MARKET MOVEMENT
What shifted: [One specific market signal — sourced]
The {company} angle: [What this means for their positioning or sales this week — specific]

---

🌐 RISK HORIZON — 30-60 days
Signal: [Regulatory, macro, or competitive development on the horizon]
Why {company} must act now: [Specific consequence if they don't — not generic]

---

✅ THIS WEEK'S DECISIONS

DECISION 01 — IMMEDIATE
Title: [Action name]
Tied to: [Which signal above]
Why: [Consequence of not acting]
How: [Specific steps — completable this week]

DECISION 02 — THIS WEEK  
Title: [Action name]
Tied to: [Which signal above]
Why: [Consequence of not acting]
How: [Specific steps]

DECISION 03 — BEFORE NEXT BRIEF
Title: [Action name]
Tied to: [Which signal above]
Why: [Consequence of not acting]
How: [Specific steps]

---

⚡ IF YOU DO ONE THING THIS WEEK
[Single sentence. Specific. Completable in under 2 hours. Tied to the most urgent signal above.]
Complete by: [Day of week]

---

Remember: A founder reading this brief should think "I could not have found this myself in 60 minutes." 
If every line could apply to any company in any market — rewrite it until it can't."""

    print(f" → Generating brief with Claude for {company}...")

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=2500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text

    except Exception as e:
        print(f" ✗ Claude API error: {str(e)}")
        return f"Brief generation error for {company}: {str(e)}"


# ============================================================
# EMAIL HTML WRAPPER — wraps brief text in the dark template
# ============================================================

def wrap_brief_in_html(brief_text: str, subscriber: dict, brief_number: int = 1) -> str:
    """
    Wraps the plain text brief in the EXOBRIEF HTML email template.
    Converts the structured text output into formatted HTML sections.
    """
    company = subscriber.get("company_name", "Your Company")
    current_date = datetime.now(timezone.utc).strftime("%d %B %Y")
    next_date_obj = datetime.now(timezone.utc)
    from datetime import timedelta
    next_date = (next_date_obj + timedelta(days=7)).strftime("%d %B %Y")

    # Convert plain text brief to HTML — preserve structure
    brief_html = brief_text\
        .replace("⚠️ REVENUE RISK THIS WEEK", '<div class="section-header"><div class="section-icon">⚠️</div><div class="section-title">REVENUE RISK THIS WEEK</div></div>')\
        .replace("🔭 COMPETITOR RADAR", '<div class="section-header"><div class="section-icon">🔭</div><div class="section-title">COMPETITOR RADAR</div></div>')\
        .replace("📈 MARKET MOVEMENT", '<div class="section-header"><div class="section-icon">📈</div><div class="section-title">MARKET MOVEMENT</div></div>')\
        .replace("🌐 RISK HORIZON", '<div class="section-header"><div class="section-icon">🌐</div><div class="section-title">RISK HORIZON</div></div>')\
        .replace("✅ THIS WEEK'S DECISIONS", '<div class="section-header"><div class="section-icon">✅</div><div class="section-title">THIS WEEK\'S DECISIONS</div></div>')\
        .replace("⚡ IF YOU DO ONE THING THIS WEEK", '<div class="one-thing-label">⚡ IF YOU DO ONE THING THIS WEEK</div>')\
        .replace("---", '<hr style="border:none;border-top:1px solid #1E1E2A;margin:20px 0;">')\
        .replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EXOBRIEF — {company} — {current_date}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
  * {{ margin:0;padding:0;box-sizing:border-box; }}
  body {{ background:#0A0A0F;color:#E8E6E0;font-family:'IBM Plex Sans',sans-serif;font-size:15px;line-height:1.65; }}
  .wrapper {{ max-width:680px;margin:0 auto; }}
  .header {{ padding:40px 40px 0; }}
  .logo-row {{ display:flex;align-items:center;justify-content:space-between;margin-bottom:28px; }}
  .logo {{ font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:600;letter-spacing:0.2em;color:#C8FF00; }}
  .issue-meta {{ font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4A4A5A;letter-spacing:0.1em;text-align:right; }}
  .hook {{ background:#0E0E1A;border-left:3px solid #C8FF00;padding:24px 28px;margin:0 0 0; }}
  .hook-label {{ font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:0.15em;color:#C8FF00;margin-bottom:10px; }}
  .hook-headline {{ font-size:18px;font-weight:600;color:#FFFFFF;line-height:1.3;margin-bottom:8px; }}
  .hook-sub {{ font-size:12px;color:#7A7A8A;font-family:'IBM Plex Mono',monospace; }}
  .brief-body {{ padding:32px 40px;background:#0A0A0F; }}
  .brief-body br + br {{ display:none; }}
  .section-header {{ display:flex;align-items:center;gap:12px;margin:28px 0 16px; }}
  .section-icon {{ font-size:16px; }}
  .section-title {{ font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:0.15em;color:#C8FF00;text-transform:uppercase; }}
  .one-thing-label {{ font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:0.15em;color:#C8FF00;margin:28px 0 12px;display:block; }}
  hr {{ border:none;border-top:1px solid #1E1E2A;margin:20px 0; }}
  .footer {{ padding:24px 40px;border-top:1px solid #1E1E2A;display:flex;align-items:center;justify-content:space-between; }}
  .footer-brand {{ font-family:'IBM Plex Mono',monospace;font-size:11px;color:#3A3A4A;letter-spacing:0.1em; }}
  .footer-next {{ font-family:'IBM Plex Mono',monospace;font-size:10px;color:#3A3A4A;text-align:right; }}
  .footer-next span {{ color:#C8FF00; }}
  a {{ color:#C8FF00;text-decoration:none; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <div class="logo-row">
      <div class="logo">EXOBRIEF</div>
      <div class="issue-meta">
        BRIEF #{brief_number} · {company}<br>
        WEEK OF {current_date} · CONFIDENTIAL
      </div>
    </div>
    <div class="hook">
      <div class="hook-label">Intelligence Summary — {company}</div>
      <div class="hook-headline">Your weekly competitive intelligence brief is ready.</div>
      <div class="hook-sub">Competitor signals · Revenue risks · 3 decisions · Action required</div>
    </div>
  </div>
  <div class="brief-body">
    {brief_html}
  </div>
  <div class="footer">
    <div class="footer-brand">EXOBRIEF · hello@exobrief.com</div>
    <div class="footer-next">
      Next brief: <span>{next_date}</span><br>
      Intelligence compounds weekly.
    </div>
  </div>
</div>
</body>
</html>"""


# ============================================================
# TEST
# ============================================================

def test_brief_generation():
    test_subscriber = {
        "company_name": "Meridian Analytics",
        "sector": "B2B SaaS / Data Analytics",
        "geography": "United Kingdom",
        "competitors": ["Tableau", "Looker", "Power BI", "Qlik"],
        "strategic_priorities": "Expanding into mid-market enterprise, launching AI reporting features, growing ARR from £2M to £5M",
        "biggest_concern": "Microsoft Power BI bundling with M365 is making it harder to justify standalone pricing",
        "customer_type": "B2B",
        "previous_briefs_summary": "First brief — establishing baseline competitive intelligence"
    }

    print("=" * 60)
    print("EXOBRIEF v2 — Brief Generation Test")
    print("=" * 60)

    brief = generate_brief(test_subscriber)

    print("\nGENERATED BRIEF:")
    print("=" * 60)
    print(brief)

    with open("/tmp/test_brief_output.txt", "w") as f:
        f.write(f"EXOBRIEF TEST — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Subscriber: {test_subscriber['company_name']}\n")
        f.write("=" * 60 + "\n")
        f.write(brief)

    print("\n✓ Brief saved to /tmp/test_brief_output.txt")
    return brief


if __name__ == "__main__":
    test_brief_generation()
