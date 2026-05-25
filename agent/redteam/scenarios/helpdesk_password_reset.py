"""helpdesk_password_reset — UNC3944 scenario stub.

TODO(weeks 10-12): implement the actual attack steps. For now this is a
placeholder that logs its existence and returns 'skipped' so the planner
can still reference it.

See docs/weeks/week-11-attacks.md for the implementation playbook.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run(params: dict) -> dict:
    logger.warning("helpdesk_password_reset not implemented yet — returning 'skipped'")
    return {
        "outcome": "skipped",
        "target": "halcyon-care-lab",
        "mitre_techniques": ["T1078"],
        "expected_alerts": [],
        "notes": "scenario stub — implement in weeks 10-12",
    }
