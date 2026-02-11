"""
Side Project Launcher - LangGraph Integration

Wire LaunchDarkly AI Configs to LangGraph for multi-agent orchestration.
Based on the tutorial: LLM Product Development with LaunchDarkly Agent Skills
"""

import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import ldclient
from ldclient import Context
from ldclient.config import Config
from ldai.client import LDAIClient, AIAgentConfigDefault

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict

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


def get_agent_config(config_key: str, context: Context, variables: dict = None):
    """Get agent-mode AI Config from LaunchDarkly."""
    fallback = AIAgentConfigDefault(enabled=False)
    return ai_client.agent_config(config_key, context, fallback, variables or {})


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


def idea_validator_node(state: SideProjectState) -> SideProjectState:
    print("\n[idea-validator] Analyzing your idea...")
    context = build_context(state["user_id"])
    config = get_agent_config("idea-validator", context, {
        "idea": state["idea"],
        "target_audience": state["target_audience"],
        "problem_statement": state["problem_statement"]
    })

    if config.enabled:
        llm = ChatAnthropic(model=config.model.name)
        messages = [
            SystemMessage(content=config.instructions),
            HumanMessage(content="Please validate this idea and provide your analysis.")
        ]
        response = llm.invoke(messages)
        state["idea_validation"] = response.content
        config.tracker.track_success()
    else:
        state["idea_validation"] = "Config not enabled"

    return state


def landing_page_writer_node(state: SideProjectState) -> SideProjectState:
    print("[landing-page-writer] Writing landing page copy...")
    context = build_context(state["user_id"])
    config = get_agent_config("landing-page-writer", context, {
        "idea": state["idea"],
        "target_audience": state["target_audience"],
        "unique_value_prop": state["unique_value_prop"]
    })

    if config.enabled:
        llm = ChatAnthropic(model=config.model.name)
        messages = [
            SystemMessage(content=config.instructions),
            HumanMessage(content="Please write the landing page copy.")
        ]
        response = llm.invoke(messages)
        state["landing_page_copy"] = response.content
        config.tracker.track_success()
    else:
        state["landing_page_copy"] = "Config not enabled"

    return state


def tech_stack_advisor_node(state: SideProjectState) -> SideProjectState:
    print("[tech-stack-advisor] Recommending tech stack...")
    context = build_context(state["user_id"])
    config = get_agent_config("tech-stack-advisor", context, {
        "expected_users": state["expected_users"],
        "budget": state["budget"],
        "team_expertise": state["team_expertise"]
    })

    if config.enabled:
        llm = ChatAnthropic(model=config.model.name)
        messages = [
            SystemMessage(content=config.instructions),
            HumanMessage(content="Please recommend a tech stack.")
        ]
        response = llm.invoke(messages)
        state["tech_stack"] = response.content
        config.tracker.track_success()
    else:
        state["tech_stack"] = "Config not enabled"

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

    print(f"\n[done] Output saved to: {output_dir}/")

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


if __name__ == "__main__":
    initial_state = get_user_input()

    print("\n" + "=" * 60)
    print("Launching agents...")
    print("=" * 60)

    app = build_side_project_graph()
    result = app.invoke(initial_state)

    # Flush events before exiting
    ld_client.flush()

    print("\n" + "=" * 60)
    print(f"Done! Check your output in: {result['output_dir']}/")
    print("=" * 60)
