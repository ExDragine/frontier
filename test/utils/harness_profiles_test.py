# ruff: noqa: S101

from utils import harness_profiles


def test_frontier_harness_profiles_disable_general_purpose(monkeypatch):
    registrations = []
    monkeypatch.setattr(
        harness_profiles,
        "register_harness_profile",
        lambda provider, profile: registrations.append((provider, profile)),
    )

    harness_profiles.register_frontier_harness_profiles()

    assert [provider for provider, _profile in registrations] == [
        "openai",
        "anthropic",
        "google_genai",
        "deepseek",
    ]
    assert all(profile.general_purpose_subagent.enabled is False for _provider, profile in registrations)
