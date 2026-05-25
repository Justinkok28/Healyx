"""Smoke tests for the red-team scenario registry."""

from agent.redteam.scenarios import REGISTRY


def test_registry_has_all_expected_scenarios():
    expected = {
        "mfa_fatigue",
        "helpdesk_password_reset",
        "oauth_consent_grant",
        "priv_role_burst",
        "sp_credential_addition",
        "port_scan_then_ssh_bf",
        "cloud_storage_exfil",
        "chatbot_prompt_injection",
    }
    assert set(REGISTRY.keys()) == expected


def test_stub_scenarios_return_valid_shape():
    """All stub scenarios should return a dict with the required keys."""
    required_keys = {"outcome", "target", "mitre_techniques", "expected_alerts"}
    for name, fn in REGISTRY.items():
        if name == "mfa_fatigue":
            continue  # this one makes real HTTP calls
        result = fn({})
        assert required_keys.issubset(result.keys()), f"{name} missing keys"
        assert isinstance(result["mitre_techniques"], list)
