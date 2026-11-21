"""Upload validation: size limits, extension + magic-byte allowlist."""
from __future__ import annotations

import os

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet"}
DEFAULT_MAX_MB = 200

# Magic-byte prefixes per format.
MAGIC: dict[str, list[bytes]] = {
    ".parquet": [b"PAR1"],
    ".xlsx": [b"PK\x03\x04"],
    ".xls": [b"\xD0\xCF\x11\xE0"],
    ".json": [b"{", b"["],
    # CSV has no magic; validated by extension + parse probe.
}


def validate_file(path: str, max_mb: int = DEFAULT_MAX_MB) -> dict[str, object]:
    """Validate size, extension, and magic bytes. Returns info dict or raises."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"extension {ext} not allowed; use {sorted(ALLOWED_EXTENSIONS)}")
    size = os.path.getsize(path)
    if size > max_mb * 1024 * 1024:
        raise ValueError(f"file {size} bytes exceeds {max_mb} MB limit")
    if size == 0:
        raise ValueError("empty file")
    with open(path, "rb") as fh:
        head = fh.read(8)
    if ext in MAGIC and not any(head.startswith(m) for m in MAGIC[ext]):
        # JSON may start with whitespace/BOM.
        if ext == ".json":
            with open(path, "rb") as fh:
                raw = fh.read(256).lstrip(b"\xef\xbb\xbf \t\r\n")
            if not (raw.startswith(b"{") or raw.startswith(b"[")):
                raise ValueError("invalid JSON magic bytes")
        else:
            raise ValueError(f"magic bytes mismatch for {ext}")
    return {"extension": ext, "size_bytes": size, "ok": True}
