import hashlib
from pathlib import Path

def apply(source, expected_digest, byte_range, completion):
    if hashlib.sha256(source).hexdigest() != expected_digest:
        raise ValueError("Stale source digest")
    start, end = byte_range
    if not 0 <= start <= end <= len(source):
        raise ValueError("Invalid byte range")
    source[:start].decode("utf-8")
    source[end:].decode("utf-8")
    return source[:start] + completion.encode("utf-8") + source[end:]
