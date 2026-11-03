# Side Project Launcher

Multi-agent system powered by LaunchDarkly AgentControl configs that helps validate startup ideas, write landing pages, and recommend tech stacks.

## Requirements

Python 3.12 or later.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Anthropic API key
```

## Run

```bash
source .venv/bin/activate
python3 side_project_launcher_langgraph.py
```

The script asks seven questions about your idea, then writes the three agents' results to `output/`.

## Configuration

Copy `.env.example` to `.env` and add your Anthropic API key:
- `ANTHROPIC_API_KEY` - Anthropic API key (required for Claude models)

Your coding assistant retrieves the LaunchDarkly SDK key automatically when creating the project using your API key (`LD_API_KEY`).

The tools each config attaches in LaunchDarkly are implemented in `tools.py`. If you attach a new tool, add a handler with the same name to `TOOL_HANDLERS`.
