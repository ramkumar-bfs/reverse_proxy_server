"""
Sample script: fetch projects from ShotGrid using shotgun_api3.

Connects directly to the ShotGrid server (no local proxy process needed).
The network path is:  this script → firewall → ShotGrid at SG_URL.

Requirements:
    pip install shotgun_api3

Environment variables (required):
    SG_SCRIPT_NAME  - ShotGrid script name  (Admin > Scripts)
    SG_SCRIPT_KEY   - ShotGrid API key for the script above
"""

import os
import sys

import shotgun_api3

# ── ShotGrid server URL ───────────────────────────────────────────────────────
# Direct address of the ShotGrid server accessible via the firewall.
SG_URL = "http://production-tracker.localhost:8080/"  # Must match the proxy's Host()-based mount (production-tracker.<PROXY_BASE_DOMAIN>, default "localhost"). Trailing slash required for shotgun_api3's urljoin-based path building.

# ── Credentials (from environment) ───────────────────────────────────────────
SCRIPT_NAME = os.getenv("SG_SCRIPT_NAME")
SCRIPT_KEY  = os.getenv("SG_SCRIPT_KEY")

missing = [k for k, v in {"SG_SCRIPT_NAME": SCRIPT_NAME, "SG_SCRIPT_KEY": SCRIPT_KEY}.items() if not v]
if missing:
    sys.exit(f"Missing required environment variables: {', '.join(missing)}")

# ── Connect ───────────────────────────────────────────────────────────────────
sg = shotgun_api3.Shotgun(
    SG_URL,
    script_name=SCRIPT_NAME,
    api_key=SCRIPT_KEY,
)

# ── Fields to retrieve for each project ──────────────────────────────────────
PROJECT_FIELDS = [
    "id",
    "name",
    "sg_status",
    "start_date",
    "end_date",
    "sg_description",
]

# ── Fetch all active projects ─────────────────────────────────────────────────
filters = [["sg_status", "is", "Active"]]

projects = sg.find(
    entity_type="Project",
    filters=filters,
    fields=PROJECT_FIELDS,
    order=[{"field_name": "name", "direction": "asc"}],
)

# ── Print results ─────────────────────────────────────────────────────────────
print(f"Found {len(projects)} active project(s):\n")

for project in projects:
    print(f"  ID          : {project['id']}")
    print(f"  Name        : {project['name']}")
    print(f"  Status      : {project.get('sg_status')}")
    print(f"  Start date  : {project.get('start_date')}")
    print(f"  End date    : {project.get('end_date')}")
    print(f"  Description : {project.get('sg_description')}")
    print()
