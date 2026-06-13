"""
EXOBRIEF — Auto-Capture API
Receives form submissions from the landing page
Adds subscriber to Supabase
Triggers immediate brief generation and delivery
Zero human involvement required
"""

import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from brief_engine import generate_brief
from subscriber_manager import create_subscriber, get_previous_briefs_summary, save_brief, mark_brief_delivered
from email_delivery import send_brief

PORT = int(os.getenv("PORT", 8080))

# ── CORS headers for requests from exobrief.com ──
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "https://exobrief.com",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json"
}


def generate_and_send_brief(subscriber_data: dict):
    """
    Background thread — generates brief and sends it
    Runs after subscriber is saved so response is instant
    """
    email = subscriber_data.get("email", "")
    company = subscriber_data.get("company_name", "")

    print(f"[AUTO-CAPTURE] Generating brief for {company} ({email})")

    try:
        profile = {
            "company_name": company,
            "company_url": subscriber_data.get("company_url", ""),
            "sector": subscriber_data.get("sector", "Technology"),
            "geography": subscriber_data.get("geography", "United Kingdom"),
            "competitors": subscriber_data.get("competitors", []),
            "strategic_priorities": subscriber_data.get("strategic_priorities", ""),
            "biggest_concern": subscriber_data.get("biggest_concern", ""),
            "customer_type": "B2B",
            "previous_briefs_summary": "First brief — welcome to EXOBRIEF"
        }

        brief = generate_brief(profile)

        sub_id = subscriber_data.get("id", "")
        if sub_id:
            save_brief(email, sub_id, brief)

        delivered = send_brief(email, company, brief)

        if delivered:
            mark_brief_delivered(email)
            print(f"[AUTO-CAPTURE] ✓ Brief delivered to {email}")
        else:
            print(f"[AUTO-CAPTURE] ✗ Delivery failed for {email}")

    except Exception as e:
        print(f"[AUTO-CAPTURE] Error: {str(e)}")


class ExobriefHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[API] {format % args}")

    def send_json(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(204)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        """Health check"""
        if self.path == "/health":
            self.send_json(200, {"status": "ok", "service": "EXOBRIEF API"})
        else:
            self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/subscribe":
            self.handle_subscribe()
        else:
            self.send_json(404, {"error": "Not found"})

    def handle_subscribe(self):
        """
        Handle new subscriber submission from landing page
        Expected JSON body:
        {
            "email": "founder@company.com",
            "company_name": "Acme SaaS",
            "sector": "B2B SaaS",
            "geography": "United Kingdom",
            "competitors": ["Competitor A", "Competitor B"]
        }
        """
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body.decode())

            email = data.get("email", "").strip().lower()
            company = data.get("company_name", "").strip()
            sector = data.get("sector", "").strip()
            competitors = data.get("competitors", [])
            geography = data.get("geography", "United Kingdom").strip()

            # Validate required fields
            if not email or not company or not sector:
                self.send_json(400, {"error": "Email, company name and sector are required"})
                return

            if "@" not in email:
                self.send_json(400, {"error": "Invalid email address"})
                return

            # Clean competitors list
            competitors = [c.strip() for c in competitors if c.strip()][:5]

            # Build subscriber record
            subscriber_record = {
                "email": email,
                "company_name": company,
                "sector": sector,
                "geography": geography,
                "competitors": competitors,
                "strategic_priorities": data.get("strategic_priorities", ""),
                "biggest_concern": data.get("biggest_concern", ""),
                "customer_type": "B2B",
                "subscription_status": "trial"
            }

            # Save to Supabase
            saved = create_subscriber(subscriber_record)

            if saved:
                subscriber_record["id"] = saved.get("id", "")
                # Trigger brief generation in background thread
                thread = threading.Thread(
                    target=generate_and_send_brief,
                    args=(subscriber_record,),
                    daemon=True
                )
                thread.start()

                self.send_json(200, {
                    "success": True,
                    "message": f"Your brief is being generated and will arrive in {email} within 10 minutes."
                })
            else:
                # Subscriber may already exist
                self.send_json(200, {
                    "success": True,
                    "message": f"We already have your details. Check {email} for your brief."
                })

        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON"})
        except Exception as e:
            print(f"[API] Error in handle_subscribe: {str(e)}")
            self.send_json(500, {"error": "Server error — please try again"})


def run_api():
    server = HTTPServer(("0.0.0.0", PORT), ExobriefHandler)
    print(f"[API] EXOBRIEF API running on port {PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run_api()
