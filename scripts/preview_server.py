"""
Standalone preview server for capturing VRAJA AI Client Portal screenshots.
Serves NastaGhar/frontend/dist and mocks authenticated session & shared-profile endpoints.
"""

import http.server
import json
import os
import sys

DIST_DIR = os.path.abspath("NastaGhar/frontend/dist")

SESSION_DATA = {
    "authenticated": True,
    "user": {
        "id": "user-owner-001",
        "email": "owner@nastaghar.com",
        "display_name": "Tushar Kacha",
        "is_platform_admin": False
    },
    "active_tenant": {
        "id": "nasta-ghar",
        "business_name": "Nasta Ghar (Main Branch)",
        "role": "owner"
    },
    "available_tenants": [
        {
            "id": "nasta-ghar",
            "business_name": "Nasta Ghar (Main Branch)",
            "role": "owner"
        },
        {
            "id": "cafe-alpha",
            "business_name": "Cafe Alpha (Downtown)",
            "role": "manager"
        }
    ]
}

SHARED_PROFILE_DATA = {
    "tenant_id": "nasta-ghar",
    "display_name": "Nasta Ghar",
    "branch_name": "Main Branch",
    "category": "Authentic Gujarati & Indian Dining",
    "description": "Authentic Gujarati breakfast and snacks prepared fresh daily.",
    "tagline": "Pure authentic taste, freshly prepared",
    "logo_path": "/api/businesses/nasta-ghar/shared-profile/logo",
    "phone_number": "+91 98765 43210",
    "email": "contact@nastaghar.com",
    "address": "Opp. Railway Station, Navrangpura, Ahmedabad",
    "website_url": "https://nastaghar.com",
    "opening_hours": "07:00 AM - 11:00 PM",
    "map_url": "https://maps.google.com/?cid=12345",
    "brand_accent": "#174D3A",
    "timezone": "Asia/Kolkata",
    "entitlements": ["review_manager", "digital_card"],
    "created_at": 1730000000.0,
    "updated_at": 1730000000.0
}


class PortalPreviewHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)

    def do_GET(self):
        path = self.path.split("?")[0]

        # 1. API: Session endpoint
        if path == "/api/auth/session":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(SESSION_DATA).encode("utf-8"))
            return

        # 2. API: Shared profile endpoint
        if "/shared-profile" in path and not path.endswith(".png"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(SHARED_PROFILE_DATA).encode("utf-8"))
            return

        # 3. Static assets
        file_path = os.path.join(DIST_DIR, path.lstrip("/"))
        if os.path.isfile(file_path):
            return super().do_GET()

        # 4. Fallback to index.html for SPA client routes
        index_file = os.path.join(DIST_DIR, "index.html")
        if os.path.isfile(index_file):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open(index_file, "rb") as f:
                self.wfile.write(f.read())
            return

        self.send_error(404, "File not found")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5192
    server = http.server.HTTPServer(("127.0.0.1", port), PortalPreviewHandler)
    print(f"Portal Preview Server listening on http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
