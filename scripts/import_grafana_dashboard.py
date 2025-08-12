#!/usr/bin/env python
"""Import a Grafana dashboard JSON via HTTP API.

Usage:
  GRAFANA_URL=http://localhost:3000 GRAFANA_TOKEN=xxxxx \
  python scripts/import_grafana_dashboard.py docs/grafana_dashboard_example.json

If env vars missing, prints instructions and exits 0 (non-failing in CI).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

API_PATH = "/api/dashboards/db"

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: import_grafana_dashboard.py path/to/dashboard.json", file=sys.stderr)
        return 1
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"Dashboard introuvable: {path}", file=sys.stderr)
        return 2
    url = os.environ.get("GRAFANA_URL")
    token = os.environ.get("GRAFANA_TOKEN")
    if not url or not token:
        print("(Info) GRAFANA_URL ou GRAFANA_TOKEN absent: skip import.")
        return 0
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    payload = {"dashboard": data, "overwrite": True}
    req = urllib.request.Request(url.rstrip('/') + API_PATH, method='POST')
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    try:
        resp = urllib.request.urlopen(req, data=json.dumps(payload).encode('utf-8'))  # nosec B310
        print(f"Import OK: {resp.status}")
    except Exception as e:  # pragma: no cover
        print(f"Erreur import Grafana: {e}", file=sys.stderr)
        return 3
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
