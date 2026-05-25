"""Shared Pydantic schemas for agent inputs and outputs.

Every agent decision is validated against one of these before being persisted.
This is enforced by the chat_json helper in `agent.common.openrouter`.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentCategory(StrEnum):
    IDENTITY = "identity"
    HOST = "host"
    NETWORK = "network"
    CLOUD = "cloud"
    LLM_APP = "llm_app"
    UNKNOWN = "unknown"


# ---------- Triage agent output ----------


class TuningSuggestion(BaseModel):
    """Suggested change to a Sigma detection rule."""

    rule_id: str = Field(..., description="Sigma rule UUID this tuning applies to")
    change_type: Literal["broaden", "narrow", "new_filter", "new_rule", "deprecate"]
    rationale: str = Field(..., min_length=20, max_length=1000)
    sigma_patch_yaml: str | None = Field(
        None,
        description="Suggested YAML diff/patch. Optional — sometimes rationale is enough.",
    )


class EvidenceCitation(BaseModel):
    """Pointer to a specific row of evidence the triage agent inspected."""

    source: Literal["wazuh_alert", "loki_log", "keycloak_event", "caddy_access"]
    id: str = Field(..., description="Alert ID, log row ID, or event ID")
    summary: str = Field(..., max_length=300)


class TriageResult(BaseModel):
    """The triage agent's structured verdict on a Wazuh alert."""

    model_config = ConfigDict(extra="forbid")

    alert_id: str
    classified_at: datetime
    category: IncidentCategory
    severity: Severity
    is_false_positive_likely: bool
    fp_confidence_pct: int = Field(..., ge=0, le=100)
    mitre_techniques: list[str] = Field(
        default_factory=list,
        description="MITRE ATT&CK technique IDs, e.g. T1078.004",
    )
    suspected_actor: str | None = Field(
        None,
        description="e.g. UNC3944, APT41, unattributed",
    )
    narrative: str = Field(..., min_length=50, max_length=2000)
    evidence: list[EvidenceCitation] = Field(..., min_length=1)
    suggested_tuning: TuningSuggestion | None = None
    next_steps: list[str] = Field(..., min_length=1, max_length=10)


# ---------- Red team agent output ----------


class AttackOutcome(StrEnum):
    EXECUTED = "executed"  # attack ran successfully against the lab
    BLOCKED = "blocked"  # a defense (preventive) stopped it
    PARTIAL = "partial"  # some steps ran, some didn't
    SKIPPED = "skipped"  # planner decided not to run this round
    ERROR = "error"  # bug or infra issue


class GroundTruthEntry(BaseModel):
    """One row of the red-team ground truth log.

    Appended to `ground_truth.jsonl`. The triage agent's accuracy is scored
    against this — did blue correctly identify what red did?
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., description="UUID for this run")
    scenario: str = Field(..., description="e.g. mfa_fatigue, oauth_consent_grant")
    started_at: datetime
    ended_at: datetime
    outcome: AttackOutcome
    target: str = Field(..., description="What was targeted, e.g. keycloak-admin")
    mitre_techniques: list[str] = Field(..., min_length=1)
    expected_alerts: list[str] = Field(
        default_factory=list,
        description="Sigma rule IDs that should fire",
    )
    actor_emulated: str = Field("UNC3944", description="Threat actor TTPs emulated")
    parameters: dict = Field(default_factory=dict)
    notes: str | None = None


class RedTeamPlan(BaseModel):
    """The red-team planner's choice of what to run this round."""

    model_config = ConfigDict(extra="forbid")

    round_id: str
    rationale: str = Field(..., min_length=20, max_length=500)
    chosen_scenarios: list[str] = Field(..., min_length=1, max_length=5)
    parameter_overrides: dict[str, dict] = Field(default_factory=dict)
    expected_to_be_caught: list[str] = Field(
        default_factory=list,
        description="Scenarios planner expects blue to catch (informs eval)",
    )
