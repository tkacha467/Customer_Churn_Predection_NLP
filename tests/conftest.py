import os
import tempfile
from pathlib import Path

# Stable local credentials for isolated API tests; never used by app deployments.
os.environ["ENVIRONMENT"] = "test"
os.environ["OWNER_PASSWORD"] = "test-only-owner-password"
os.environ["OWNER_SESSION_SECRET"] = "test-only-signing-secret-at-least-32-characters"
os.environ["REVIEW_DB_PATH"] = str(Path(tempfile.gettempdir()) / f"nasta-gh-test-{os.getpid()}.sqlite3")
os.environ["BUSINESS_LINKS_PATH"] = str(Path(tempfile.gettempdir()) / f"nasta-gh-links-{os.getpid()}.json")
