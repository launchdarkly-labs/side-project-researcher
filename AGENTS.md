# AGENTS.md

Side Project Launcher: a three-agent LangGraph pipeline (idea validator → landing-page writer → tech-stack advisor) where each agent is a LaunchDarkly AI Config in agent mode, so its instructions and model come from LaunchDarkly rather than the code. Outputs are written as Markdown to `output/<idea>-<timestamp>/`. Upstream is `launchdarkly-labs/side-project-researcher`.

## Setup and commands

- `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`, then `cp .env.example .env`.
- `ANTHROPIC_API_KEY` is required. `LAUNCHDARKLY_SDK_KEY` is read from the environment and is left blank in `.env.example` on purpose: the tutorial flow has the reader's coding assistant create the LaunchDarkly project through the API (`LD_API_KEY`) and fill the SDK key in.
- Run `python3 side_project_launcher_langgraph.py`. `side_project_launcher.py` is the same three calls without LangGraph, kept as the "before" version for the tutorial.
- No tests. Verify by running the graph end to end and confirming three files land in `output/`: `01-idea-validation.md` and its siblings. `output/` is gitignored.

## Config keys are the contract

The three AI Config keys, `idea-validator`, `landing-page-writer`, `tech-stack-advisor`, appear in both Python files and must exist in agent mode in the LaunchDarkly project. Both files read them with `inspect_config()`, which never raises and never calls a provider, so a missing or disabled config does not crash: the helper returns `None`, the node writes the literal string `"Config not enabled"` into the state, and the graph continues. When output looks like that, the fix is in LaunchDarkly, not the code.

Prompt variables are passed per call (`get_agent_config(key, context, {...})`); a new `{{variable}}` in a LaunchDarkly instruction needs a matching key in that dict in both files. Note that `inspect_config()` only reads — it does not interpolate. The variables matter at the point you actually run the agent through `config().invoke()`.

## Branches

`origin/fix/modernize-ai-sdk-0.20` updates the code to the AI SDK 0.20+ API; check whether it has landed before touching SDK calls, and match its idioms if it has.
