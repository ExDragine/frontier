"""Frontier-specific Deep Agents harness behavior."""

from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    register_harness_profile,
)

FRONTIER_HARNESS_PROVIDERS = ("openai", "anthropic", "google_genai", "deepseek")


def register_frontier_harness_profiles() -> None:
    """Disable the redundant auto-added general-purpose subagent."""
    profile = HarnessProfile(
        general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
    )
    for provider in FRONTIER_HARNESS_PROVIDERS:
        register_harness_profile(provider, profile)
