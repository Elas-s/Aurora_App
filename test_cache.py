from datetime import datetime, timedelta, timezone

from cache import CACHE, read_note, write_note


def test_old_note_is_too_old():
    long_ago = datetime.now(timezone.utc) - timedelta(minutes=15)
    CACHE["test"] = (long_ago, "old data")
    assert read_note("test",15) is None


def test_writing_new_note():
    write_note("test", "new data")
    result = read_note("test", 15)
    assert result == "new data"