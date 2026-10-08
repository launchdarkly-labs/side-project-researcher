"""
Side Project Launcher - LangGraph Integration

Wire LaunchDarkly AgentControl configs to LangGraph for multi-agent orchestration.
Based on the tutorial: LLM Product Development with LaunchDarkly Agent Skills
"""

import asyncio
import os
import warnings
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from launchdarkly_ai_langchain_agents import langchain_agents
from launchdarkly_ai_server import init_client, inspect_config, shutdown

from tools import TOOL_HANDLERS

# A config's tools arrive twice: at the top level, where the SDK binds them,
# and as a backwards-compatibility copy inside model.parameters. Versions
# through 0.2.4 forward that copy to the model constructor, so LangChain warns
# once per agent call. Fixed upstream; delete this when the pin moves past
# 0.2.4.
warnings.filterwarnings("ignore", message=".*tools is not default parameter.*")

from langgraph.graph import StateGraph, END
from typing import TypedDict

SDK_KEY = os.environ.get('LAUNCHDARKLY_SDK_KEY')


def build_context(user_id: str, **attributes):
    """Build a LaunchDarkly context for targeting."""
    return {"kind": "user", "key": user_id, **attributes}


async def run_agent(config_key: str, context: dict, variables: dict, user_input: str) -> str:
    """Run one agent-mode config, or report that it is not enabled.

    inspect_config never raises and never calls a provider, so it is a cheap way
    to keep this graph's "Config not enabled" branch. The invoke that follows is
    what records duration, tokens, and success/error to LaunchDarkly.
    """
    inspected = await inspect_config(config_key, context)
    if not inspected["enabled"] or not inspected["config"]:
        return "Config not enabled"

    # The LangChain handler builds the chat model from the config's provider and
    # model name, so this file no longer constructs ChatAnthropic itself. The
    # tools attached in LaunchDarkly are schemas only, so the callables behind
    # them have to be supplied here or the agent fails the moment it calls one.
    result = await langchain_agents(
        config_key,
        user_input,
        context,
        variables=variables,
        tool_handlers=TOOL_HANDLERS,
    )
    return str(result.response)


class SideProjectState(TypedDict):
    user_id: str
    idea: str
    target_audience: str
    problem_statement: str
    unique_value_prop: str
    expected_users: str
    budget: str
    team_expertise: str
    idea_validation: str
    landing_page_copy: str
    tech_stack: str
    output_dir: str


async def idea_validator_node(state: SideProjectState) -> SideProjectState:
    print("\n[idea-validator] Analyzing your idea...")
    state["idea_validation"] = await run_agent(
        "idea-validator",
        build_context(state["user_id"]),
        {
            "idea": state["idea"],
            "target_audience": state["target_audience"],
            "problem_statement": state["problem_statement"],
        },
        "Please validate this idea and provide your analysis.",
    )
    return state


async def landing_page_writer_node(state: SideProjectState) -> SideProjectState:
    print("[landing-page-writer] Writing landing page copy...")
    state["landing_page_copy"] = await run_agent(
        "landing-page-writer",
        build_context(state["user_id"]),
        {
            "idea": state["idea"],
            "target_audience": state["target_audience"],
            "unique_value_prop": state["unique_value_prop"],
        },
        "Please write the landing page copy.",
    )
    return state


async def tech_stack_advisor_node(state: SideProjectState) -> SideProjectState:
    print("[tech-stack-advisor] Recommending tech stack...")
    state["tech_stack"] = await run_agent(
        "tech-stack-advisor",
        build_context(state["user_id"]),
        {
            "expected_users": state["expected_users"],
            "budget": state["budget"],
            "team_expertise": state["team_expertise"],
        },
        "Please recommend a tech stack.",
    )
    return state


def save_outputs_node(state: SideProjectState) -> SideProjectState:
    print("[saving] Writing output files...")

    output_dir = Path(state["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "01-idea-validation.md").write_text(
        f"# Idea Validation\n\n{state['idea_validation']}"
    )

    (output_dir / "02-landing-page.md").write_text(
        f"# Landing Page Copy\n\n{state['landing_page_copy']}"
    )

    (output_dir / "03-tech-stack.md").write_text(
        f"# Tech Stack Recommendation\n\n{state['tech_stack']}"
    )

    summary = f"""# Side Project Summary

## Idea
{state['idea']}

## Target Audience
{state['target_audience']}

## Problem Statement
{state['problem_statement']}

## Unique Value Proposition
{state['unique_value_prop']}

## Technical Requirements
- Expected Users: {state['expected_users']}
- Budget: {state['budget']}
- Team Expertise: {state['team_expertise']}

---
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    (output_dir / "00-summary.md").write_text(summary)

    return state


def build_side_project_graph():
    workflow = StateGraph(SideProjectState)

    workflow.add_node("validate_idea", idea_validator_node)
    workflow.add_node("write_landing_page", landing_page_writer_node)
    workflow.add_node("recommend_stack", tech_stack_advisor_node)
    workflow.add_node("save_outputs", save_outputs_node)

    workflow.set_entry_point("validate_idea")
    workflow.add_edge("validate_idea", "write_landing_page")
    workflow.add_edge("write_landing_page", "recommend_stack")
    workflow.add_edge("recommend_stack", "save_outputs")
    workflow.add_edge("save_outputs", END)

    return workflow.compile()


def get_user_input():
    print("=" * 60)
    print("SIDE PROJECT LAUNCHER")
    print("=" * 60)
    print("\nAnswer a few questions about your side project idea:\n")

    idea = input("What's your idea? (e.g., AI-powered recipe app)\n> ").strip()

    target_audience = input("\nWho is your target audience? (e.g., busy parents)\n> ").strip()

    problem_statement = input("\nWhat problem does it solve? (e.g., no time to plan meals)\n> ").strip()

    unique_value_prop = input("\nWhat's your unique value proposition? (e.g., snap a photo, get dinner)\n> ").strip()

    expected_users = input("\nExpected users? (e.g., 10,000 monthly active users)\n> ").strip()

    budget = input("\nMonthly budget for infrastructure? (e.g., $500/month)\n> ").strip()

    team_expertise = input("\nTeam's tech expertise? (e.g., Python, React, AWS)\n> ").strip()

    # Create output folder name from idea
    folder_name = idea.lower()[:30].replace(" ", "-").replace("/", "-")
    folder_name = "".join(c for c in folder_name if c.isalnum() or c == "-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    output_dir = f"output/{folder_name}-{timestamp}"

    return {
        "user_id": f"user-{timestamp}",
        "idea": idea,
        "target_audience": target_audience,
        "problem_statement": problem_statement,
        "unique_value_prop": unique_value_prop,
        "expected_users": expected_users,
        "budget": budget,
        "team_expertise": team_expertise,
        "idea_validation": "",
        "landing_page_copy": "",
        "tech_stack": "",
        "output_dir": output_dir
    }


async def main():
    if not SDK_KEY:
        raise Exception("LAUNCHDARKLY_SDK_KEY is not set")

    initial_state = get_user_input()

    print("\n" + "=" * 60)
    print("Launching agents...")
    print("=" * 60)

    # The key is passed explicitly so this keeps using LAUNCHDARKLY_SDK_KEY; the
    # SDK would otherwise look for LD_SDK_KEY.
    await init_client({"sdkKey": SDK_KEY})

    app = build_side_project_graph()
    result = await app.ainvoke(initial_state)

    # Flush pending LaunchDarkly events and spans before exiting.
    await shutdown()

    output_dir = Path(result["output_dir"]).resolve()
    files = sorted(output_dir.glob("*.md"))

    print("\n" + "=" * 60)
    print("Done. Your side project brief is ready.")
    print("=" * 60 + "\n")

    for path in files:
        lines = len(path.read_text().splitlines())
        print(f"  {path.name:<24} {lines:>4} lines")

    # Most terminals turn a file:// URL into something you can click.
    print(f"\n  {output_dir.as_uri()}\n")


if __name__ == "__main__":
    asyncio.run(main())
