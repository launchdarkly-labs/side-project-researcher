# AGENTS.md

Side Project Launcher: a three-agent LangGraph pipeline (idea validator → landing-page writer → tech-stack advisor) where each agent is a LaunchDarkly AI Config in agent mode, so its instructions and model come from LaunchDarkly rather than the code. Outputs are written as Markdown to `output/<idea>-<timestamp>/`. Upstream is `launchdarkly-labs/side-project-researcher`.

## Setup and commands

- Python 3.12 or later.
- `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`, then `cp .env.example .env`.
- `ANTHROPIC_API_KEY` is required. `LAUNCHDARKLY_SDK_KEY` is left blank in `.env.example` on purpose: the tutorial has the reader's coding assistant create the LaunchDarkly project and fill it in.
- Run `python3 side_project_launcher_langgraph.py`. It asks seven questions on stdin first. `side_project_launcher.py` is the "before" version for the tutorial.
- No tests. Verify by running the graph end to end and confirming three files land in `output/`.

## Config keys are the contract

The three AI Config keys, `idea-validator`, `landing-page-writer` and `tech-stack-advisor`, must exist in agent mode in the LaunchDarkly project. A missing or disabled config doesn't crash: the node writes `"Config not enabled"` and the graph continues. The fix for that is in LaunchDarkly, not the code.

A new `{{variable}}` in a config's instructions needs a matching key in the variables dict passed to `run_agent()`.

## Tools need handlers

A tool attached to a config in LaunchDarkly needs an entry with the same name in `TOOL_HANDLERS` in `tools.py`, or the agent fails on its first call to it.

## Model parameters

The SDK forwards a config's model parameters to Anthropic. Use the provider's names (`max_tokens`), and don't set `temperature`: current Claude models reject it.
