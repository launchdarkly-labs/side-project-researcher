# AGENTS.md

Side Project Launcher: a three-agent LangGraph pipeline (idea validator → landing-page writer → tech-stack advisor) where each agent is a LaunchDarkly AI Config in agent mode, so its instructions and model come from LaunchDarkly rather than the code. Outputs are written as Markdown to `output/<idea>-<timestamp>/`. Upstream is `launchdarkly-labs/side-project-researcher`.

## Setup and commands

- Python 3.12 or later; `launchdarkly-ai-server` will not install below that.
- `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`, then `cp .env.example .env`.
- `ANTHROPIC_API_KEY` is required. `LAUNCHDARKLY_SDK_KEY` is read from the environment and is left blank in `.env.example` on purpose: the tutorial flow has the reader's coding assistant create the LaunchDarkly project through the API (`LD_API_KEY`) and fill the SDK key in.
- Run `python3 side_project_launcher_langgraph.py`. `side_project_launcher.py` is the same three calls without LangGraph, kept as the "before" version for the tutorial.
- Both scripts prompt for seven answers on stdin before any model call, so a non-interactive run needs them piped in.
- No tests. Verify by running the graph end to end and confirming three files land in `output/`: `01-idea-validation.md` and its siblings. `output/` is gitignored.

## The SDK surface is async

`init_client`, `inspect_config`, and `shutdown` are all coroutines, which is why both scripts are built around `asyncio.run(main())` rather than running straight through. `init_client({"sdkKey": SDK_KEY})` passes the key explicitly because the SDK otherwise looks for `LD_SDK_KEY`, not `LAUNCHDARKLY_SDK_KEY`.

Agents run through `langchain_agents(config_key, user_input, context, variables=...)` from `launchdarkly-ai-langchain-agents`. That handler builds the chat model from the config's own `provider` and `model` fields, so neither file constructs `ChatAnthropic` directly any more. Adding a `ChatAnthropic(...)` call back into a node is a regression, not a fix.

## Config keys are the contract

The three AI Config keys, `idea-validator`, `landing-page-writer`, `tech-stack-advisor`, appear in both Python files and must exist in agent mode in the LaunchDarkly project. Both files read them with `inspect_config()`, which never raises and never calls a provider, so a missing or disabled config does not crash: the helper returns `None`, the node writes the literal string `"Config not enabled"` into the state, and the graph continues. When output looks like that, the fix is in LaunchDarkly, not the code.

Prompt variables are passed per call, as the third argument to `run_agent()`; a new `{{variable}}` in a LaunchDarkly instruction needs a matching key in that dict in both files. Note that `inspect_config()` only reads — it does not interpolate. The variables matter at the point you actually run the agent through `langchain_agents()`.

## Model parameters are passed through verbatim

The LangChain agents handler takes whatever sits in a config's `model.parameters` and hands it to the chat model constructor unchanged, which in turn forwards unrecognized keys to the provider API. So the parameter names in LaunchDarkly have to be the ones the provider expects: `max_tokens`, not `maxTokens`. A camelCase name reaches Anthropic as-is and the run dies with `AsyncMessages.create() got an unexpected keyword argument 'maxTokens'` at the first agent node.

`model.custom` is not a workaround. The handler never reads it, so anything parked there is silently dropped.

## Branches

`sdk-roll-forward` carries the migration from the legacy `ldai` package to `launchdarkly-ai-server`. Work from it rather than reapplying the old API.
