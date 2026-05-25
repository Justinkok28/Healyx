"""Strip sensitive material from alert payloads before they hit the LLM.

The triage agent must never send secrets to an external API. Wazuh alerts
can contain bearer tokens, full credentials, internal IPs, and PII. We
redact known patterns before sending anything to OpenRouter.

This is defense-in-depth: the *source* of the leak should be fixed (don't
log secrets in the first place), but redaction is a cheap safety net.
"""

from __future__ import annotations

import copy
import re
from typing import Any

# Patterns are intentionally aggressive — false positives (over-redaction)
# are fine; false negatives (leaks) are not.
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("BEARER_REDACTED", re.compile(r"(?i)Bearer\s+[A-Za-z0-9._\-+/=]{20,}")),
    ("BASIC_REDACTED", re.compile(r"(?i)Basic\s+[A-Za-z0-9+/=]{20,}")),
    ("AWS_KEY_REDACTED", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("PRIVATE_KEY_REDACTED", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
    ("JWT_REDACTED", re.compile(r"eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+")),
    ("EMAIL_REDACTED", re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b")),
    # Credit-card-like numeric run (basic Luhn-ish width)
    ("CC_REDACTED", re.compile(r"\b(?:\d[ \-]?){13,19}\b")),
)

REDACT_KEY_SUBSTRINGS = (
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "token",
    "authorization",
    "session",
    "cookie",
    "private_key",
)


def _redact_string(s: str) -> str:
    for placeholder, pattern in PATTERNS:
        s = pattern.sub(f"[{placeholder}]", s)
    return s


def _key_should_be_redacted(key: str) -> bool:
    k = key.lower()
    return any(sub in k for sub in REDACT_KEY_SUBSTRINGS)


def sanitize_alert(alert: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of the alert with sensitive values redacted."""
    cleaned = copy.deepcopy(alert)
    _scrub(cleaned)
    return cleaned


def _scrub(node: Any) -> None:
    if isinstance(node, dict):
        for k in list(node.keys()):
            v = node[k]
            if _key_should_be_redacted(k) and isinstance(v, str):
                node[k] = "[REDACTED_BY_KEY]"
            elif isinstance(v, str):
                node[k] = _redact_string(v)
            else:
                _scrub(v)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            if isinstance(item, str):
                node[i] = _redact_string(item)
            else:
                _scrub(item)
