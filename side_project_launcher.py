"""
Side Project Launcher - Multi-agent system powered by LaunchDarkly AgentControl

This glue code connects your LaunchDarkly AgentControl configs to your application.
Based on the tutorial: LLM Product Development with LaunchDarkly Agent Skills
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from launchdarkly_ai_server import init_client, inspect_config, shutdown

SDK_KEY = os.environ.get('LAUNCHDARKLY_SDK_KEY')


def build_context(user_id: str, **attributes):
    """Build a LaunchDarkly context for targeting."""
    return {"kind": "user", "key": user_id, **attributes}


async def get_agent_config(config_key: str, user_id: str, variables: dict = None):
    """Read an agent-mode config from LaunchDarkly without calling a model.

    Returns the parsed config dict, or None when the variation is disabled or
    unavailable. This module only reads and reports configs, so inspect_config
    is the right entry point: it never raises and never calls a provider.

    Note that `variables` are applied when the SDK assembles a prompt, so they
    are not interpolated here. Pass them to `config().invoke()` at the point you
    actually run the agent.
    """
    context = build_context(user_id)
    inspected = await inspect_config(config_key, context)
    if not inspected["enabled"] or not inspected["config"]:
        return None
    return inspected["config"]


async def validate_idea(user_id: str, idea: str, target_audience: str, problem_statement: str):
    """Read the idea-validator agent config."""
    config = await get_agent_config("idea-validator", user_id, {
        "idea": idea,
        "target_audience": target_audience,
        "problem_statement": problem_statement
    })

    if config:
        print(f"[idea-validator] Model: {(config.get('model') or {}).get('name')}")
        return config

    print("[idea-validator] Config not enabled")
    return None


async def write_landing_page(user_id: str, idea: str, target_audience: str, unique_value_prop: str):
    """Read the landing-page-writer agent config."""
    config = await get_agent_config("landing-page-writer", user_id, {
        "idea": idea,
        "target_audience": target_audience,
        "unique_value_prop": unique_value_prop
    })

    if config:
        print(f"[landing-page-writer] Model: {(config.get('model') or {}).get('name')}")
        return config

    print("[landing-page-writer] Config not enabled")
    return None


async def recommend_tech_stack(user_id: str, expected_users: str, budget: str, team_expertise: str):
    """Read the tech-stack-advisor agent config."""
    config = await get_agent_config("tech-stack-advisor", user_id, {
        "expected_users": expected_users,
        "budget": budget,
        "team_expertise": team_expertise
    })

    if config:
        print(f"[tech-stack-advisor] Model: {(config.get('model') or {}).get('name')}")
        return config

    print("[tech-stack-advisor] Config not enabled")
    return None


def show_instructions(config):
    """Print the head of a config's instructions."""
    print(f"\nInstructions:\n{(config.get('instructions') or '')[:800]}...")


async def main():
    if not SDK_KEY:
        raise Exception("LAUNCHDARKLY_SDK_KEY is not set")

    # The key is passed explicitly so this keeps using LAUNCHDARKLY_SDK_KEY; the
    # SDK would otherwise look for LD_SDK_KEY.
    await init_client({"sdkKey": SDK_KEY})

    user_id = "user-123"
    idea = "AI-powered recipe app that suggests meals from fridge photos"
    target_audience = "busy parents who hate meal planning"
    problem_statement = "no time to plan meals, food goes to waste"

    print("=" * 60)
    print("SIDE PROJECT LAUNCHER")
    print("=" * 60)

    print("\n1. VALIDATING IDEA...")
    idea_config = await validate_idea(user_id, idea, target_audience, problem_statement)
    if idea_config:
        show_instructions(idea_config)

    print("\n" + "=" * 60)
    print("\n2. WRITING LANDING PAGE...")
    landing_config = await write_landing_page(
        user_id, idea, target_audience,
        "See what's in your fridge, get tonight's dinner in seconds"
    )
    if landing_config:
        show_instructions(landing_config)

    print("\n" + "=" * 60)
    print("\n3. RECOMMENDING TECH STACK...")
    stack_config = await recommend_tech_stack(
        user_id,
        expected_users="10,000 monthly active users",
        budget="$500/month",
        team_expertise="Python, React, some AWS experience"
    )
    if stack_config:
        show_instructions(stack_config)

    # Flush pending LaunchDarkly events before exiting.
    await shutdown()

    print("\n" + "=" * 60)
    print("Done! Use these configs with your preferred AI framework.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
