"""A tiny in-memory cache: reuse fetched data for a few minutes."""

from datetime import datetime, timedelta, timezone

CACHE = {} # name -> (saved_at, data)


def read_note(name, ttl_minutes):
    """Return the saved data if it's younger than ttl_minutes, else None."""
    note = CACHE.get(name)   # None if no note yet
    if note is None:
        return None
    saved_at, data = note
    if datetime.now(timezone.utc) - saved_at < timedelta(minutes=ttl_minutes):
        return data  # still fresh
    return None      # too old


def write_note(name, data):
    """Save data with the current time."""
    CACHE[name] = (datetime.now(timezone.utc), data)

