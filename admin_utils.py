"""
Admin utilities: visitor logging (IP, city, timestamp), save uploads, list data for admin panel.
Uses /tmp for storage so it works on Streamlit Cloud (data may not persist across restarts).
"""

import os
import csv
import time
from pathlib import Path
from typing import Optional

# Storage under /tmp for deployed apps (Streamlit Cloud)
BASE_DIR = Path(os.environ.get("ADMIN_DATA_DIR", "/tmp"))
VISITOR_LOG = BASE_DIR / "sentiment_visitor_log.csv"
UPLOADS_DIR = BASE_DIR / "sentiment_uploads"


def _ensure_dirs():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def get_client_ip() -> Optional[str]:
    """Get client IP from Streamlit context or request headers."""
    try:
        import streamlit as _st
        if hasattr(_st, "context") and hasattr(_st.context, "ip_address"):
            return getattr(_st.context, "ip_address", None)
    except Exception:
        pass
    try:
        import streamlit as _st
        if hasattr(_st, "request") and _st.request and hasattr(_st.request, "headers"):
            headers = _st.request.headers
            for key in ("x-forwarded-for", "x-real-ip", "x-client-ip"):
                if key in headers:
                    val = headers[key]
                    if isinstance(val, str) and val.strip():
                        return val.strip().split(",")[0].strip()
    except Exception:
        pass
    return None


def get_ip_location(ip: Optional[str]) -> str:
    """Get city/location string for IP using ipinfo.io (no token needed for basic)."""
    if not ip or ip in ("127.0.0.1", "localhost", "::1"):
        return "Local"
    try:
        import urllib.request
        url = f"https://ipinfo.io/{ip}/json"
        req = urllib.request.Request(url, headers={"User-Agent": "StreamlitApp/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            import json
            data = json.loads(resp.read().decode())
            city = data.get("city") or ""
            region = data.get("region") or ""
            country = data.get("country") or ""
            parts = [p for p in (city, region, country) if p]
            return ", ".join(parts) if parts else data.get("loc", "Unknown")
    except Exception:
        return "Unknown"


def log_visitor():
    """Append current visitor IP, location, and timestamp to log. Call once per session."""
    ip = get_client_ip()
    if ip is None:
        ip = "unknown"
    city = get_ip_location(ip)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    _ensure_dirs()
    file_exists = VISITOR_LOG.exists()
    with open(VISITOR_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(["timestamp", "ip", "city"])
        w.writerow([timestamp, ip, city])


def save_upload(uploaded_file, original_name: str) -> str:
    """Save a copy of uploaded file to admin storage. Returns stored filename."""
    _ensure_dirs()
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in original_name)
    stored_name = f"{safe_name}_{int(time.time())}"
    path = UPLOADS_DIR / stored_name
    path.write_bytes(uploaded_file.getvalue())
    return stored_name


def get_visitor_log() -> list:
    """Return list of dicts: timestamp, ip, city."""
    if not VISITOR_LOG.exists():
        return []
    rows = []
    with open(VISITOR_LOG, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


def get_uploaded_files() -> list:
    """Return list of (filename, path) for admin download."""
    _ensure_dirs()
    if not UPLOADS_DIR.exists():
        return []
    return [(p.name, p) for p in sorted(UPLOADS_DIR.iterdir(), key=lambda x: -x.stat().st_mtime)]
