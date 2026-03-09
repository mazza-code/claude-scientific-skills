#!/usr/bin/env python3
"""Safe output controls for file writes.

Provides:
- Optional output root enforcement to prevent path traversal/misplacement.
- Redaction of common secret patterns before persistence.
- Atomic writes with restrictive file permissions.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


class SafeOutputError(ValueError):
    """Raised when safe output constraints are violated."""


_MASK = "[REDACTED]"

_TOKEN_PATTERNS: Iterable[re.Pattern[str]] = (
    re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?i)\b(?:bearer)\s+[A-Za-z0-9._-]{16,}\b"),
)

_AUTH_HEADER_PATTERN = re.compile(
    r"(?i)\b(authorization\s*:\s*bearer\s+)([A-Za-z0-9._-]{16,})\b"
)

_KV_SECRET_PATTERN = re.compile(
    r"(?i)\b("
    r"openrouter_api_key|parallel_api_key|ncbi_api_key|api_key|"
    r"access_token|refresh_token|token|secret|password"
    r")\b(\s*[:=]\s*)([\"']?)([^\"'\s,;]+)([\"']?)"
)

_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)


def _redact_text(text: str, mode: str) -> Tuple[str, int]:
    if mode == "off":
        return text, 0

    redactions = 0
    sanitized = text

    for pattern in _TOKEN_PATTERNS:
        sanitized, count = pattern.subn(_MASK, sanitized)
        redactions += count

    sanitized, count = _AUTH_HEADER_PATTERN.subn(r"\1" + _MASK, sanitized)
    redactions += count

    def _replace_kv(match: re.Match[str]) -> str:
        key, separator, q1, _, q2 = match.groups()
        quote_left = q1 or ""
        quote_right = q2 or ""
        return f"{key}{separator}{quote_left}{_MASK}{quote_right}"

    sanitized, count = _KV_SECRET_PATTERN.subn(_replace_kv, sanitized)
    redactions += count

    sanitized, count = _EMAIL_PATTERN.subn(_MASK, sanitized)
    redactions += count

    if mode == "strict":
        for pattern in _TOKEN_PATTERNS:
            if pattern.search(sanitized):
                raise SafeOutputError("Strict safe output blocked unresolved token pattern.")
        if _AUTH_HEADER_PATTERN.search(sanitized) or _KV_SECRET_PATTERN.search(sanitized):
            raise SafeOutputError("Strict safe output blocked unresolved secret key/value pattern.")

    return sanitized, redactions


def sanitize_obj(value: Any, mode: str) -> Tuple[Any, int]:
    """Recursively sanitize an object and return (sanitized, redaction_count)."""
    if isinstance(value, str):
        return _redact_text(value, mode)

    if isinstance(value, list):
        total = 0
        out = []
        for item in value:
            sanitized, count = sanitize_obj(item, mode)
            out.append(sanitized)
            total += count
        return out, total

    if isinstance(value, dict):
        total = 0
        out: Dict[Any, Any] = {}
        for key, item in value.items():
            sanitized, count = sanitize_obj(item, mode)
            out[key] = sanitized
            total += count
        return out, total

    return value, 0


def resolve_output_path(
    path: str,
    allowed_root: str | None = None,
    allow_outside: bool = False,
) -> Path:
    """Resolve output path and optionally enforce it stays under allowed_root."""
    output_path = Path(path).expanduser()
    if not output_path.is_absolute():
        output_path = (Path.cwd() / output_path).resolve()
    else:
        output_path = output_path.resolve()

    if allowed_root and not allow_outside:
        root = Path(allowed_root).expanduser()
        if not root.is_absolute():
            root = (Path.cwd() / root).resolve()
        else:
            root = root.resolve()

        try:
            output_path.relative_to(root)
        except ValueError as exc:
            raise SafeOutputError(
                f"Refusing to write outside safe root: {output_path} (root: {root})"
            ) from exc

    return output_path


def _atomic_write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def safe_write_text(
    path: str,
    text: str,
    mode: str = "standard",
    allowed_root: str | None = None,
    allow_outside: bool = False,
) -> Dict[str, Any]:
    if mode not in {"off", "standard", "strict"}:
        raise SafeOutputError(f"Unknown safe output mode: {mode}")

    sanitized, redactions = _redact_text(text, mode)
    resolved = resolve_output_path(path, allowed_root=allowed_root, allow_outside=allow_outside)
    _atomic_write(resolved, sanitized)
    return {"path": str(resolved), "redactions": redactions, "bytes": len(sanitized.encode("utf-8"))}


def safe_write_json(
    path: str,
    obj: Any,
    mode: str = "standard",
    allowed_root: str | None = None,
    allow_outside: bool = False,
) -> Dict[str, Any]:
    if mode not in {"off", "standard", "strict"}:
        raise SafeOutputError(f"Unknown safe output mode: {mode}")

    sanitized_obj, redactions = sanitize_obj(obj, mode)
    payload = json.dumps(sanitized_obj, indent=2, ensure_ascii=False, default=str) + "\n"
    resolved = resolve_output_path(path, allowed_root=allowed_root, allow_outside=allow_outside)
    _atomic_write(resolved, payload)
    return {"path": str(resolved), "redactions": redactions, "bytes": len(payload.encode("utf-8"))}

