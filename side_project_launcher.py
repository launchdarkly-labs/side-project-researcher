"""
Side Project Launcher - Multi-agent system powered by LaunchDarkly AI Configs

This glue code connects your LaunchDarkly AI Configs to your application.
Based on the tutorial: LLM Product Development with LaunchDarkly Agent Skills
"""

import os
from dotenv import load_dotenv

load_dotenv()

import ldclient
from ldclient import Context
from ldclient.config import Config
from ldai.client import LDAIClient, AIAgentConfigDefault

# Initialize LaunchDarkly SDK
SDK_KEY = os.environ.get('LAUNCHDARKLY_SDK_KEY')
ldclient.set_config(Config(SDK_KEY))
ld_client = ldclient.get()
ai_client = LDAIClient(ld_client)

if not ld_client.is_initialized():
    raise Exception("LaunchDarkly client failed to initialize")


def build_context(user_id: str, **attributes):
    """Build LaunchDarkly context for targeting."""
    builder = Context.builder(user_id)
    for key, value in attributes.items():
        builder.set(key, value)
    return builder.build()


def get_agent_config(config_key: str, user_id: str, variables: dict = None):
    """Get agent-mode AI Config from LaunchDarkly."""
    context = build_context(user_id)
    fallback = AIAgentConfigDefault(enabled=False)
    return ai_client.agent_config(config_key, context, fallback, variables or {})


def validate_idea(user_id: str, idea: str, target_audience: str, problem_statement: str):
    """Validate a startup idea using the idea-validator agent."""
    config = get_agent_config("idea-validator", user_id, {
        "idea": idea,
        "target_audience": target_audience,
        "problem_statement": problem_statement
    })

    if config.enabled:
        print(f"[idea-validator] Model: {config.model.name}")
        return config
    else:
        print("[idea-validator] Config not enabled")
        return None


def write_landing_page(user_id: str, idea: str, target_audience: str, unique_value_prop: str):
    """Generate landing page copy using the landing-page-writer agent."""
    config = get_agent_config("landing-page-writer", user_id, {
        "idea": idea,
        "target_audience": target_audience,
        "unique_value_prop": unique_value_prop
    })

    if config.enabled:
        print(f"[landing-page-writer] Model: {config.model.name}")
        return config
    else:
        print("[landing-page-writer] Config not enabled")
        return None


def recommend_tech_stack(user_id: str, expected_users: str, budget: str, team_expertise: str):
    """Get tech stack recommendations using the tech-stack-advisor agent."""
    config = get_agent_config("tech-stack-advisor", user_id, {
        "expected_users": expected_users,
        "budget": budget,
        "team_expertise": team_expertise
    })

    if config.enabled:
        print(f"[tech-stack-advisor] Model: {config.model.name}")
        return config
    else:
        print("[tech-stack-advisor] Config not enabled")
        return None


if __name__ == "__main__":
    user_id = "user-123"
    idea = "AI-powered recipe app that suggests meals from fridge photos"
    target_audience = "busy parents who hate meal planning"
    problem_statement = "no time to plan meals, food goes to waste"

    print("=" * 60)
    print("SIDE PROJECT LAUNCHER")
    print("=" * 60)

    print("\n1. VALIDATING IDEA...")
    idea_config = validate_idea(user_id, idea, target_audience, problem_statement)
    if idea_config:
        print(f"\nInstructions:\n{idea_config.instructions[:800]}...")

    print("\n" + "=" * 60)
    print("\n2. WRITING LANDING PAGE...")
    landing_config = write_landing_page(
        user_id, idea, target_audience,
        "See what's in your fridge, get tonight's dinner in seconds"
    )
    if landing_config:
        print(f"\nInstructions:\n{landing_config.instructions[:800]}...")

    print("\n" + "=" * 60)
    print("\n3. RECOMMENDING TECH STACK...")
    stack_config = recommend_tech_stack(
        user_id,
        expected_users="10,000 monthly active users",
        budget="$500/month",
        team_expertise="Python, React, some AWS experience"
    )
    if stack_config:
        print(f"\nInstructions:\n{stack_config.instructions[:800]}...")

    # Flush events before exiting
    ld_client.flush()

    print("\n" + "=" * 60)
    print("Done! Use these configs with your preferred AI framework.")
    print("=" * 60)
