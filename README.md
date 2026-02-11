# Side Project Launcher

Multi-agent system powered by LaunchDarkly AI Configs that helps validate startup ideas, write landing pages, and recommend tech stacks.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
```

## Run

```bash
source .venv/bin/activate
python3 side_project_launcher_langgraph.py
```

## Configuration

Copy `.env.example` to `.env` and add your keys:
- `LAUNCHDARKLY_SDK_KEY` - LaunchDarkly SDK key (from project settings)
- `ANTHROPIC_API_KEY` - Anthropic API key
