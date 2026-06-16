"""
EXOBRIEF — Intent Monitor
Daily automated scan for people actively asking about competitor tracking,
competitive intelligence, or market monitoring tools — across Hacker News
and Reddit. Outputs a ranked shortlist with suggested reply angles,
emailed to Shruti each morning.

Free, no-auth APIs only:
- HN: Algolia Search API (hn.algolia.com)
- Reddit: public JSON search endpoint

Run: python intent_monitor.py
Schedule: daily, e.g. 07:00 BST via the `schedule` package in main.py
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta, timezone

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
FROM_EMAIL = "hello@exobrief.com"
DIGEST_RECIPIENT = os.environ.get("DIGEST_RECIPIENT", "")  # Shruti's email — set in Railway vars

# ============================================================
# KEYWORDS — what counts as "high intent"
# Covers UK + global + UAE/Gulf founder language
# ============================================================
KEYWORDS = [
    "how do you track what competitors are doing",
    "keep track of competitors",
    "missed competitor launch",
    "found out competitor",
    "competitor changed pricing",
    "how to stay on top of competitors",
    "competitor monitoring recommend",
    "tool recommend competitor",
    "best way to monitor competitors",
    "lost deal to competitor",
    "competitor beat us",
    "how founders track competition",
]

# Reddit RSS subreddits — bypasses IP blocking on JSON API
REDDIT_SUBREDDITS = [
    "SaaS", "startups", "Entrepreneur", "microsaas",
    "ProductManagement", "marketing", "smallbusiness"
]

LOOKBACK_HOURS = 36


# ============================================================
# HACKER NEWS — Algolia Search API (free, no auth)
# ============================================================
def search_hn(keyword: str, since_ts: int) -> list:
    url = "https://hn.algolia.com/api/v1/search_by_date"
    params = {
        "query": keyword,
        "tags": "(story,comment)",
        "numericFilters": f"created_at_i>{since_ts}",
        "hitsPerPage": 5,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        results = []
        for hit in data.get("hits", []):
            text = hit.get("story_text") or hit.get("comment_text") or hit.get("title") or ""
            if not text.strip():
                continue
            object_id = hit.get("story_id") or hit.get("objectID")
            results.append({
                "platform": "Hacker News",
                "keyword": keyword,
                "text": text[:500],
                "url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "created": hit.get("created_at", ""),
            })
        return results
    except Exception as e:
        print(f"  [HN] Error for '{keyword}': {e}")
        return []


# ============================================================
# REDDIT — RSS feed (bypasses IP blocking on JSON API)
# ============================================================
def search_reddit_rss(subreddit: str, keyword: str) -> list:
    """Search a subreddit's new posts via RSS — no auth, less likely to be blocked"""
    url = f"https://www.reddit.com/r/{subreddit}/search.rss"
    params = {"q": keyword, "sort": "new", "restrict_sr": "on", "t": "day"}
    headers = {"User-Agent": "EXOBRIEF-Monitor/1.0 (contact: hello@exobrief.com)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code != 200:
            return []
        # Parse RSS manually — no extra library needed
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        results = []
        for entry in root.findall("atom:entry", ns)[:3]:
            title = entry.findtext("atom:title", default="", namespaces=ns)
            content = entry.findtext("atom:content", default="", namespaces=ns)
            link = entry.find("atom:link", ns)
            url_out = link.get("href", "") if link is not None else ""
            text = f"{title} — {content}"[:500]
            if text.strip():
                results.append({
                    "platform": f"Reddit (r/{subreddit})",
                    "keyword": keyword,
                    "text": text,
                    "url": url_out,
                    "created": "",
                })
        return results
    except Exception as e:
        return []


def search_reddit(keyword: str) -> list:
    """Search across multiple subreddits via RSS"""
    all_results = []
    for sub in REDDIT_SUBREDDITS:
        all_results.extend(search_reddit_rss(sub, keyword))
        time.sleep(0.5)
    return all_results


# ============================================================
# RANK & SUGGEST REPLIES — Claude filters noise, drafts angles
# ============================================================
def rank_and_suggest(raw_results: list) -> list:
    if not raw_results:
        return []

    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Dedup by URL
    seen = set()
    unique = []
    for r in raw_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    if not unique:
        return []

    items_text = "\n\n".join([
        f"[{i+1}] Platform: {r['platform']}\nText: {r['text']}\nURL: {r['url']}"
        for i, r in enumerate(unique)
    ])

    prompt = f"""You are screening posts/comments for EXOBRIEF, a £29/month automated competitive intelligence tool for B2B SaaS founders (monitors named competitors, delivers weekly decision brief).

Below are {len(unique)} posts/comments found today matching search terms. Most will be NOISE (unrelated, spam, or low-intent). A few might be GENUINE — someone actually asking for a tool like this, or expressing the exact pain EXOBRIEF solves.

{items_text}

Return ONLY a JSON array of the genuinely high-intent items (max 5). For each, include:
- "index": the [N] number from above
- "reason": one sentence on why this is high-intent
- "suggested_reply": a short, genuine, non-salesy reply (under 60 words) that helps first and mentions EXOBRIEF only if it's the actual answer to what they asked. No link unless directly relevant.

If NOTHING is genuinely high-intent, return an empty array [].
Return ONLY the JSON array, no other text."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        ranked = json.loads(text)

        results = []
        for item in ranked:
            idx = item.get("index", 0) - 1
            if 0 <= idx < len(unique):
                results.append({
                    **unique[idx],
                    "reason": item.get("reason", ""),
                    "suggested_reply": item.get("suggested_reply", ""),
                })
        return results
    except Exception as e:
        print(f"  [RANK] Error: {e}")
        return []


# ============================================================
# EMAIL DIGEST — send via SendGrid
# ============================================================
def send_digest(shortlist: list):
    if not DIGEST_RECIPIENT:
        print("[DIGEST] No DIGEST_RECIPIENT set — printing to console instead\n")
        print_digest(shortlist)
        return

    if not shortlist:
        body = "No high-intent conversations found today. Nothing to action — check back tomorrow."
    else:
        sections = []
        for i, item in enumerate(shortlist, 1):
            sections.append(
                f"{i}. {item['platform']}\n"
                f"   Why: {item['reason']}\n"
                f"   Post: {item['text'][:200]}...\n"
                f"   Link: {item['url']}\n"
                f"   Suggested reply: {item['suggested_reply']}\n"
            )
        body = (
            f"EXOBRIEF — Today's Intent Shortlist ({len(shortlist)} items)\n"
            f"{'='*50}\n\n"
            + "\n".join(sections)
            + "\n\nReply to these directly on the platform. Genuine first, mention EXOBRIEF only where it's the real answer.\n"
            + "Takes ~15-30 min total."
        )

    payload = {
        "personalizations": [{
            "to": [{"email": DIGEST_RECIPIENT}],
            "subject": f"EXOBRIEF Daily Intent Shortlist — {datetime.now().strftime('%d %b')}"
        }],
        "from": {"email": FROM_EMAIL, "name": "EXOBRIEF Growth Engine"},
        "content": [{"type": "text/plain", "value": body}],
    }

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post("https://api.sendgrid.com/v3/mail/send", headers=headers, json=payload)
        if r.status_code == 202:
            print(f"[DIGEST] Sent to {DIGEST_RECIPIENT} — {len(shortlist)} items")
        else:
            print(f"[DIGEST] SendGrid error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"[DIGEST] Send error: {e}")


def print_digest(shortlist: list):
    if not shortlist:
        print("No high-intent items found today.")
        return
    for i, item in enumerate(shortlist, 1):
        print(f"\n{i}. [{item['platform']}] {item['reason']}")
        print(f"   {item['text'][:150]}")
        print(f"   {item['url']}")
        print(f"   Reply: {item['suggested_reply']}")


# ============================================================
# MAIN
# ============================================================
def run():
    print(f"\n[INTENT MONITOR] Starting run — {datetime.now(timezone.utc).isoformat()}")
    since_ts = int((datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)).timestamp())

    all_results = []

    for kw in KEYWORDS:
        print(f"  Searching: '{kw}'")
        all_results.extend(search_hn(kw, since_ts))
        all_results.extend(search_reddit(kw))
        time.sleep(1)  # courtesy delay

    print(f"\n[INTENT MONITOR] Found {len(all_results)} raw matches — ranking with Claude...")
    shortlist = rank_and_suggest(all_results)
    print(f"[INTENT MONITOR] {len(shortlist)} high-intent items after filtering")

    send_digest(shortlist)
    print("[INTENT MONITOR] Run complete.\n")


if __name__ == "__main__":
    run()
