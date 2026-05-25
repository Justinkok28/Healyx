"""Tests for the shared Pydantic schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from agent.common import (
    AttackOutcome,
    EvidenceCitation,
    GroundTruthEntry,
    IncidentCategory,
    RedTeamPlan,
    Severity,
    TriageResult,
    TuningSuggestion,
)


def _valid_evidence() -> list[EvidenceCitation]:
    return [
        EvidenceCitation(
            source="wazuh_alert",
            id="alert-123",
            summary="MFA challenge spam from same IP",
        )
    ]


def test_triage_result_minimal_valid():
    r = TriageResult(
        alert_id="a-1",
        classified_at=datetime.now(UTC),
        category=IncidentCategory.IDENTITY,
        severity=Severity.MEDIUM,
        is_false_positive_likely=False,
        fp_confidence_pct=15,
        mitre_techniques=["T1621", "T1078.004"],
        suspected_actor="UNC3944",
        narrative="A" * 60,
        evidence=_valid_evidence(),
        next_steps=["Disable the affected account session", "Notify the user via verified channel"],
    )
    assert r.category is IncidentCategory.IDENTITY


def test_triage_result_rejects_short_narrative():
    with pytest.raises(ValidationError):
        TriageResult(
            alert_id="a-1",
            classified_at=datetime.now(UTC),
            category=IncidentCategory.IDENTITY,
            severity=Severity.LOW,
            is_false_positive_likely=False,
            fp_confidence_pct=15,
            narrative="too short",
            evidence=_valid_evidence(),
            next_steps=["something"],
        )


def test_triage_result_rejects_extra_fields():
    with pytest.raises(ValidationError):
        TriageResult(
            alert_id="a-1",
            classified_at=datetime.now(UTC),
            category=IncidentCategory.HOST,
            severity=Severity.LOW,
            is_false_positive_likely=True,
            fp_confidence_pct=80,
            narrative="x" * 60,
            evidence=_valid_evidence(),
            next_steps=["x"],
            extra_unknown_field="banned",
        )


def test_triage_result_fp_pct_clamped():
    with pytest.raises(ValidationError):
        TriageResult(
            alert_id="a-1",
            classified_at=datetime.now(UTC),
            category=IncidentCategory.HOST,
            severity=Severity.LOW,
            is_false_positive_likely=True,
            fp_confidence_pct=120,  # out of range
            narrative="x" * 60,
            evidence=_valid_evidence(),
            next_steps=["x"],
        )


def test_ground_truth_entry_minimal():
    g = GroundTruthEntry(
        run_id="r1",
        scenario="mfa_fatigue",
        started_at=datetime.now(UTC),
        ended_at=datetime.now(UTC),
        outcome=AttackOutcome.EXECUTED,
        target="keycloak:halcyon-care:alice",
        mitre_techniques=["T1621"],
        expected_alerts=["ouroboros-keycloak-mfa-fatigue-v1"],
    )
    assert g.actor_emulated == "UNC3944"


def test_red_team_plan_requires_at_least_one_scenario():
    with pytest.raises(ValidationError):
        RedTeamPlan(
            round_id="rd1",
            rationale="x" * 30,
            chosen_scenarios=[],
        )


def test_tuning_suggestion_requires_decent_rationale():
    with pytest.raises(ValidationError):
        TuningSuggestion(
            rule_id="abc",
            change_type="broaden",
            rationale="too short",
        )
