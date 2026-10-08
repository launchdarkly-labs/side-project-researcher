# Side Project Launcher

Multi-agent system powered by LaunchDarkly AgentControl configs that helps validate startup ideas, write landing pages, and recommend tech stacks.

Three agents run in sequence — `idea-validator`, `landing-page-writer`, `tech-stack-advisor` — and each one's instructions and model come from LaunchDarkly rather than from this code. Results are written as Markdown to `output/<idea>-<timestamp>/`.

## Requirements

Python 3.12 or later. This project uses the current LaunchDarkly AI SDK (`launchdarkly-ai-server`), which replaced the earlier `ldai` package; the exact versions are pinned in `requirements.txt` because the SDK is in open beta.

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

The script asks seven questions about your idea before it calls any model.

`side_project_launcher.py` is the same three agent calls without LangGraph, kept as the "before" version for the tutorial.

## Configuration

Copy `.env.example` to `.env` and add your Anthropic API key:
- `ANTHROPIC_API_KEY` - Anthropic API key (required for Claude models)

Your coding assistant retrieves the LaunchDarkly SDK key automatically when creating the project using your API key (`LD_API_KEY`).

The three AI Configs must exist in agent mode in your LaunchDarkly project under the keys listed above. If one is missing or turned off, that agent writes `Config not enabled` into its output file and the run continues.

## Troubleshooting

**`AsyncMessages.create() got an unexpected keyword argument 'maxTokens'`** — a config's model parameters use a camelCase name. The SDK passes model parameters straight through to the provider, so they have to match what the provider expects. Rename `maxTokens` to `max_tokens` in the AI Config in LaunchDarkly.
