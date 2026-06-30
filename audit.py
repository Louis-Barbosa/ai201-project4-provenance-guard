"""Structured audit logging for Provenance-Guard.

Every submission (and later, every appeal) writes one JSON object per line
to audit_log.jsonl. Using JSON-lines keeps each entry structured and easy to
append without rewriting the whole file.
"""

import json
import os

LOG_PATH = os.path.join(os.path.dirname(__file__), "audit_log.jsonl")


def write_entry(entry):
    """Append one structured entry (a dict) to the audit log."""
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_log(limit=50):
    """Return the most recent log entries (newest last), up to `limit`."""
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    entries = [json.loads(line) for line in lines]
    return entries[-limit:]


def find_latest_classification(content_id):
    """Return the most recent 'classified' entry for a content_id, or None.

    The log is append-only, so the original submission's classification is
    found by scanning for the latest classified entry with this content_id.
    """
    match = None
    for entry in get_log(limit=10000):
        if entry.get("content_id") == content_id and entry.get("status") == "classified":
            match = entry
    return match
