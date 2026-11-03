"""Code behind the tools attached to the configs in LaunchDarkly.

The SDK calls each handler with one dict of the arguments the model chose.
"""

from ddgs import DDGS
from ddgs.exceptions import DDGSException


def web_search(args: dict) -> list[dict]:
    try:
        hits = DDGS().text(args["query"], max_results=min(int(args.get("num_results", 5)), 10))
    except DDGSException as e:
        return [{"error": str(e)}]
    return [{"title": h["title"], "url": h["href"], "snippet": h["body"]} for h in hits]


def competitor_analysis(args: dict) -> list[dict]:
    focus = args.get("analysis_type", "full")
    query = f"{args['competitor_name']} {'' if focus == 'full' else focus} {args.get('website_url', '')}"
    return web_search({"query": query.strip()})


def echo(args: dict) -> dict:
    """The model writes copy, A/B tests and stack advice itself; these tools just confirm the request."""
    return args


# The keys must match the tool names in LaunchDarkly.
TOOL_HANDLERS = {
    "web_search": web_search,
    "competitor_analysis": competitor_analysis,
    "generate_copy": echo,
    "suggest_ab_tests": echo,
    "recommend_stack": echo,
}
