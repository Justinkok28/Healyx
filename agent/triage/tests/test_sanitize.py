"""Tests for sanitize.py — the only thing standing between secrets and OpenRouter."""

import pytest

from agent.triage.sanitize import sanitize_alert


def test_redacts_bearer_token():
    alert = {"headers": {"authorization": "Bearer eyJabcdefghijklmnopqrstuvwxyz1234"}}
    out = sanitize_alert(alert)
    assert "eyJabcdefghijklmnopqrstuvwxyz1234" not in str(out)


def test_redacts_aws_key():
    alert = {"detail": "saw key AKIA1234567890ABCDEF in env"}
    out = sanitize_alert(alert)
    assert "AKIA1234567890ABCDEF" not in str(out)


def test_redacts_jwt_in_freeform_string():
    jwt = "eyJ" + "A" * 30 + ".eyJ" + "B" * 30 + ".CC" + "D" * 20
    alert = {"log": f"token leaked: {jwt}"}
    out = sanitize_alert(alert)
    assert jwt not in str(out)


def test_redacts_by_key_name():
    alert = {"user": "alice", "password": "hunter2", "session_token": "abc123"}
    out = sanitize_alert(alert)
    assert out["password"] == "[REDACTED_BY_KEY]"
    assert out["session_token"] == "[REDACTED_BY_KEY]"
    assert out["user"] == "alice"


def test_redacts_email():
    alert = {"src": "alice@halcyon.care.example logged in"}
    out = sanitize_alert(alert)
    assert "alice@halcyon.care.example" not in str(out)


def test_nested_redaction():
    alert = {
        "rule": {"id": 5503},
        "data": {
            "auth": {"password": "secret", "user": "alice"},
            "headers": {"Authorization": "Bearer " + "x" * 40},
        },
    }
    out = sanitize_alert(alert)
    assert out["data"]["auth"]["password"] == "[REDACTED_BY_KEY]"
    assert "x" * 40 not in str(out)
    assert out["rule"]["id"] == 5503  # non-sensitive data preserved


def test_does_not_mutate_input():
    alert = {"password": "secret"}
    original = dict(alert)
    sanitize_alert(alert)
    assert alert == original


def test_lists_get_walked():
    alert = {"events": [{"password": "secret1"}, {"password": "secret2"}]}
    out = sanitize_alert(alert)
    assert out["events"][0]["password"] == "[REDACTED_BY_KEY]"
    assert out["events"][1]["password"] == "[REDACTED_BY_KEY]"
