"""
EXOBRIEF — Email Delivery Engine
Sends beautifully formatted HTML briefs via SendGrid
McKinsey-meets-Morning-Brew design — premium, mobile-optimised
"""

import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from datetime import datetime

# ============================================================
# SENDGRID CONFIGURATION
# Add SENDGRID_API_KEY to Railway environment variables
# ============================================================

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL = "hello@exobrief.com"
FROM_NAME = "EXOBRIEF Intelligence"


# ============================================================
# EMAIL TEMPLATE — Premium HTML Design
# ============================================================

def build_html_email(brief_content: str, company_name: str, week_date: str) -> str:
    """
    Build a premium HTML email from the brief content
    Dark header, clean sections, mobile-optimised
    Feels like a Bloomberg Brief meets Linear.app
    """

    # Convert markdown-style brief to clean HTML sections
    # Parse the brief content into sections
    html_brief = brief_content\
        .replace("\n\n", "</p><p>")\
        .replace("**", "")\
        .replace("##", "<br/><strong>")\
        .replace("---", "<hr style='border: 1px solid #1e293b; margin: 24px 0;'>")\
        .replace("→", "→")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EXOBRIEF — Weekly Intelligence Brief</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f1f5f9;
            color: #1e293b;
            line-height: 1.6;
        }}
        .wrapper {{
            max-width: 680px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        .header {{
            background-color: #08080f;
            padding: 32px 40px;
            border-bottom: 2px solid #6366f1;
        }}
        .header-brand {{
            color: #ffffff;
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 0.08em;
        }}
        .header-brand span {{
            color: #6366f1;
        }}
        .header-meta {{
            color: #64748b;
            font-size: 12px;
            margin-top: 8px;
            font-family: 'Courier New', monospace;
            letter-spacing: 0.05em;
        }}
        .header-company {{
            color: #22d3ee;
            font-size: 13px;
            margin-top: 6px;
            font-weight: 600;
        }}
        .priority-bar {{
            background-color: #0f172a;
            padding: 12px 40px;
            color: #94a3b8;
            font-size: 11px;
            font-family: 'Courier New', monospace;
            letter-spacing: 0.1em;
        }}
        .content {{
            padding: 40px;
        }}
        .section {{
            margin-bottom: 32px;
            padding-bottom: 32px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section-label {{
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.15em;
            color: #6366f1;
            text-transform: uppercase;
            margin-bottom: 12px;
            font-family: 'Courier New', monospace;
        }}
        .section-content {{
            font-size: 15px;
            color: #334155;
            line-height: 1.7;
        }}
        .section-content p {{
            margin-bottom: 12px;
        }}
        .risk-band {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.08em;
            margin-bottom: 12px;
        }}
        .risk-high {{ background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }}
        .risk-medium-high {{ background: #fff7ed; color: #ea580c; border: 1px solid #fdba74; }}
        .risk-medium {{ background: #fefce8; color: #ca8a04; border: 1px solid #fde047; }}
        .risk-low {{ background: #f0fdf4; color: #16a34a; border: 1px solid #86efac; }}
        .decision-block {{
            background: #f8fafc;
            border-left: 3px solid #6366f1;
            padding: 16px 20px;
            margin-bottom: 16px;
            border-radius: 0 8px 8px 0;
        }}
        .decision-number {{
            font-size: 11px;
            font-weight: 700;
            color: #6366f1;
            letter-spacing: 0.1em;
            margin-bottom: 8px;
            font-family: 'Courier New', monospace;
        }}
        .priority-action {{
            background: #08080f;
            color: #ffffff;
            padding: 24px 28px;
            border-radius: 8px;
            margin-top: 8px;
        }}
        .priority-action-label {{
            font-size: 10px;
            color: #22d3ee;
            letter-spacing: 0.15em;
            font-weight: 700;
            margin-bottom: 10px;
            font-family: 'Courier New', monospace;
        }}
        .priority-action-text {{
            font-size: 16px;
            font-weight: 600;
            line-height: 1.5;
        }}
        .footer {{
            background: #f8fafc;
            padding: 32px 40px;
            border-top: 1px solid #e2e8f0;
        }}
        .footer-brand {{
            font-size: 13px;
            font-weight: 700;
            color: #1e293b;
            letter-spacing: 0.05em;
        }}
        .footer-text {{
            font-size: 12px;
            color: #94a3b8;
            margin-top: 8px;
            line-height: 1.6;
        }}
        .footer-links {{
            margin-top: 16px;
            font-size: 12px;
            color: #64748b;
        }}
        .footer-links a {{
            color: #6366f1;
            text-decoration: none;
        }}
        hr {{
            border: none;
            border-top: 1px solid #e2e8f0;
            margin: 24px 0;
        }}
        @media (max-width: 600px) {{
            .content {{ padding: 24px 20px; }}
            .header {{ padding: 24px 20px; }}
            .footer {{ padding: 24px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <!-- Header -->
        <div class="header">
            <div class="header-brand">EXO<span>BRIEF</span></div>
            <div class="header-company">Intelligence Brief — {company_name}</div>
            <div class="header-meta">WEEK OF {week_date.upper()} · FOUNDER EYES ONLY · CONFIDENTIAL</div>
        </div>

        <!-- Priority Bar -->
        <div class="priority-bar">
            ◈ COMPETITIVE INTELLIGENCE &nbsp;&nbsp;·&nbsp;&nbsp; MARKET SIGNALS &nbsp;&nbsp;·&nbsp;&nbsp; RISK HORIZON &nbsp;&nbsp;·&nbsp;&nbsp; DECISION BRIEF
        </div>

        <!-- Main Content -->
        <div class="content">
            <div class="section-content">
                {html_brief}
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="footer-brand">EXOBRIEF</div>
            <div class="footer-text">
                This brief was prepared autonomously by EXOBRIEF's intelligence engine.<br>
                Signals are sourced from public data and processed through AI analysis.<br>
                This is intelligence, not financial or legal advice.
            </div>
            <div class="footer-links">
                <a href="https://exobrief.com">exobrief.com</a> &nbsp;·&nbsp;
                <a href="mailto:hello@exobrief.com">hello@exobrief.com</a> &nbsp;·&nbsp;
                <a href="https://exobrief.com/unsubscribe">Unsubscribe</a>
            </div>
        </div>
    </div>
</body>
</html>"""


def build_plain_text_email(brief_content: str, company_name: str, week_date: str) -> str:
    """Plain text fallback version"""
    return f"""EXOBRIEF — Weekly Intelligence Brief
{company_name} | Week of {week_date}
{'=' * 60}

{brief_content}

{'=' * 60}
EXOBRIEF | exobrief.com | hello@exobrief.com
This is intelligence, not financial or legal advice.
To unsubscribe: https://exobrief.com/unsubscribe
"""


# ============================================================
# SEND BRIEF
# ============================================================

def send_brief(to_email: str, company_name: str, brief_content: str) -> bool:
    """
    Send the weekly brief to a subscriber via SendGrid
    Returns True if successful, False if failed
    """
    if not SENDGRID_API_KEY:
        print(f"  ✗ SendGrid API key not configured — brief not sent to {to_email}")
        return False

    week_date = datetime.now().strftime("%d %B %Y")
    subject = f"Your EXOBRIEF — {week_date} | {company_name}"

    html_content = build_html_email(brief_content, company_name, week_date)
    plain_content = build_plain_text_email(brief_content, company_name, week_date)

    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

        message = Mail(
            from_email=Email(FROM_EMAIL, FROM_NAME),
            to_emails=To(to_email),
            subject=subject,
            plain_text_content=Content("text/plain", plain_content),
            html_content=Content("text/html", html_content)
        )

        response = sg.send(message)

        if response.status_code in [200, 201, 202]:
            print(f"  ✓ Brief delivered to {to_email} (Status: {response.status_code})")
            return True
        else:
            print(f"  ✗ SendGrid error for {to_email}: Status {response.status_code}")
            return False

    except Exception as e:
        print(f"  ✗ Email delivery error for {to_email}: {str(e)}")
        return False


def send_test_email(to_email: str) -> bool:
    """Send a test email to verify SendGrid setup"""
    test_brief = """# EXOBRIEF TEST BRIEF

This is a test brief to verify your EXOBRIEF delivery system is working correctly.

## 1. REVENUE RISK THIS WEEK
**Risk Band: LOW**
This is a system test. No actual intelligence data in this brief.

## 2. COMPETITOR RADAR
System test — competitor monitoring is active and will populate with real data when NewsAPI key is configured.

## 3. MARKET MOVEMENT
System test — market signal monitoring is active.

## 4. RISK HORIZON
System test — risk monitoring is active.

## 5. THIS WEEK'S DECISIONS
**ACTION 1:** Verify EXOBRIEF delivery is working → Confirmed → You're reading this.
**ACTION 2:** Add NewsAPI key to Railway environment variables → Enables real competitor and market signals.
**ACTION 3:** Add Supabase credentials to Railway → Enables subscriber management and company memory.

## IF YOU DO ONE THING THIS WEEK
Configure your environment variables in Railway to activate full intelligence monitoring."""

    return send_brief(to_email, "EXOBRIEF Test", test_brief)


if __name__ == "__main__":
    # Test the email template generation
    week_date = datetime.now().strftime("%d %B %Y")
    html = build_html_email("Test brief content", "Test Company", week_date)
    print("✓ HTML email template generated successfully")
    print(f"Template length: {len(html)} characters")

    # Save template preview
    with open("/home/claude/exobrief/email_preview.html", "w") as f:
        f.write(html)
    print("✓ Email preview saved to email_preview.html")
