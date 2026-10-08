"""Tool implementations for the Side Project Launcher agents.

Each AI Config attaches tool schemas in LaunchDarkly, but a schema only tells
the model that a tool exists. The running application has to supply the code
behind it, which is what this module is: a name-to-callable mapping passed to
the SDK as `tool_handlers`. A tool the model calls with no handler registered
raises `No handler registered for tool "<name>"`.

The SDK calls a handler with a single dict of the arguments the model chose,
not as keyword arguments, so every function here takes one `args` mapping. The
keys inside it come from the tool's schema in LaunchDarkly.
"""

from __future__ import annotations

from typing import Any

from ddgs import DDGS

# Keep agent turns cheap; the model gets a readable digest, not raw HTML.
MAX_SEARCH_RESULTS = 10


def _search(query: str, num_results: int) -> list[dict[str, str]]:
    count = max(1, min(int(num_results), MAX_SEARCH_RESULTS))
    hits = DDGS().text(query, max_results=count)
    return [
        {
            "title": hit.get("title", ""),
            "url": hit.get("href", ""),
            "snippet": hit.get("body", ""),
        }
        for hit in hits
    ]


def web_search(args: dict[str, Any]) -> dict[str, Any]:
    """Search the web for competitor and market information."""
    query = str(args.get("query") or "").strip()
    if not query:
        return {"error": "web_search requires a non-empty 'query'."}

    try:
        results = _search(query, args.get("num_results", MAX_SEARCH_RESULTS))
    except Exception as exc:
        return {"query": query, "error": f"Search failed: {exc}", "results": []}
    return {"query": query, "results": results}


_ANALYSIS_ANGLES = {
    "pricing": ["pricing", "cost per month"],
    "features": ["features", "product overview"],
    "positioning": ["vs alternatives", "who is it for"],
}


def competitor_analysis(args: dict[str, Any]) -> dict[str, Any]:
    """Analyze a competitor product and positioning."""
    name = str(args.get("competitor_name") or "").strip()
    if not name:
        return {"error": "competitor_analysis requires 'competitor_name'."}

    website = args.get("website_url")
    analysis_type = args.get("analysis_type", "full")

    if analysis_type == "full":
        terms = [term for group in _ANALYSIS_ANGLES.values() for term in group]
    else:
        terms = _ANALYSIS_ANGLES.get(analysis_type, ["overview"])

    findings = {}
    for term in terms:
        query = f"{name} {term}"
        if website:
            query = f"{query} {website}"
        findings[term] = web_search({"query": query, "num_results": 3}).get("results", [])

    return {
        "competitor": name,
        "website": website,
        "analysis_type": analysis_type,
        "findings": findings,
    }


# Copy scaffolding. These are structural approaches for the model to fill in,
# not finished marketing copy: the agent has the product context and this
# module does not, so inventing specifics here would put words in the
# product's mouth.
_COPY_PATTERNS = {
    "headline": [
        "Outcome-first: lead with the result the user gets",
        "Problem-first: name the pain, then the relief",
        "Contrast: the old way versus the new way",
    ],
    "subheadline": [
        "Expand the headline with the mechanism",
        "Name the audience explicitly",
        "Quantify the benefit",
    ],
    "value_prop": [
        "Single sentence, one differentiator, no hedging",
        "Comparison against the status quo",
        "Time or effort saved",
    ],
    "cta": [
        "Action verb plus outcome",
        "Low-commitment framing",
        "Urgency without a fake deadline",
    ],
    "faq": [
        "Objection the skeptic raises first",
        "Question about price or commitment",
        "Question about effort to get started",
    ],
}

_TONE_GUIDANCE = {
    "professional": "measured, concrete, no exclamation marks",
    "casual": "conversational, contractions, short sentences",
    "urgent": "direct, present tense, emphasis on the cost of waiting",
    "friendly": "warm, second person, reassuring",
}


def generate_copy(args: dict[str, Any]) -> dict[str, Any]:
    """Generate copy variations for a specific landing page section."""
    section = str(args.get("section") or "")
    patterns = _COPY_PATTERNS.get(section)
    if patterns is None:
        return {
            "error": f"Unknown section {section!r}",
            "known_sections": sorted(_COPY_PATTERNS),
        }

    tone = str(args.get("tone") or "professional")
    count = max(1, min(int(args.get("num_variations", 3)), len(patterns)))

    return {
        "section": section,
        "tone": tone,
        "tone_guidance": _TONE_GUIDANCE.get(tone, "neutral"),
        "variations": [
            {"approach": pattern, "write_in_tone": tone} for pattern in patterns[:count]
        ],
    }


_AB_METRICS = {
    "conversions": "completed signups divided by unique visitors",
    "signups": "account creations divided by unique visitors",
    "clicks": "clicks on the element divided by impressions",
    "engagement": "median time on page and scroll depth",
}


def suggest_ab_tests(args: dict[str, Any]) -> dict[str, Any]:
    """Suggest A/B test variations for headlines and CTAs."""
    element = str(args.get("element") or "headline")
    goal = str(args.get("goal") or "conversions")
    patterns = _COPY_PATTERNS.get(element, _COPY_PATTERNS["headline"])

    return {
        "element": element,
        "control": args.get("current_copy", ""),
        "goal": goal,
        "primary_metric": _AB_METRICS.get(goal, goal),
        "variants": [
            {"name": f"variant_{index}", "approach": pattern}
            for index, pattern in enumerate(patterns, start=1)
        ],
        "guidance": (
            "Change one thing per variant so the result is attributable. Run "
            "until the primary metric reaches significance rather than "
            "stopping at the first favorable reading."
        ),
    }


# Stack recommendations indexed by category and scale. Costs are
# order-of-magnitude monthly figures for the listed tier, meant for budgeting
# rather than quoting.
_STACK = {
    "frontend": {
        "mvp": [("Next.js on Vercel Hobby", "$0")],
        "startup": [("Next.js on Vercel Pro", "$20 per user")],
        "growth": [("Next.js on Vercel Enterprise, or self-hosted on ECS", "$500+")],
        "enterprise": [("Self-hosted Next.js behind a CDN", "$1,000+")],
    },
    "backend": {
        "mvp": [("FastAPI on Fly.io shared CPU", "$5")],
        "startup": [("FastAPI on Fly.io or Railway, two instances", "$50")],
        "growth": [("FastAPI on ECS Fargate with autoscaling", "$300")],
        "enterprise": [("FastAPI on EKS, multi-AZ", "$2,000+")],
    },
    "database": {
        "mvp": [("Postgres on Supabase free tier", "$0")],
        "startup": [("Postgres on Supabase Pro or Neon Scale", "$25")],
        "growth": [("RDS Postgres with a read replica", "$300")],
        "enterprise": [("Aurora Postgres, multi-AZ", "$1,500+")],
    },
    "hosting": {
        "mvp": [("Vercel plus Fly.io", "$5")],
        "startup": [("Vercel plus Fly.io with a staging environment", "$75")],
        "growth": [("AWS: CloudFront, ECS, RDS", "$800")],
        "enterprise": [("AWS multi-region", "$5,000+")],
    },
    "auth": {
        "mvp": [("Supabase Auth", "$0")],
        "startup": [("Clerk or Auth0 developer tier", "$25")],
        "growth": [("Auth0 or WorkOS with SSO", "$250")],
        "enterprise": [("WorkOS or Okta with SCIM", "$1,000+")],
    },
    "payments": {
        "mvp": [("Stripe Checkout", "2.9% plus 30 cents")],
        "startup": [("Stripe Billing", "2.9% plus 30 cents, plus 0.5%")],
        "growth": [("Stripe Billing with revenue recognition", "usage-based")],
        "enterprise": [("Stripe Invoicing plus a tax provider", "negotiated")],
    },
}

_SCALES = ("mvp", "startup", "growth", "enterprise")


def recommend_stack(args: dict[str, Any]) -> dict[str, Any]:
    """Get detailed tech stack recommendations with cost estimates."""
    scale = str(args.get("scale") or "")
    if scale not in _SCALES:
        return {"error": f"Unknown scale {scale!r}", "known_scales": list(_SCALES)}

    category = str(args.get("category") or "full")
    categories = sorted(_STACK) if category == "full" else [category]
    unknown = [name for name in categories if name not in _STACK]
    if unknown:
        return {
            "error": f"Unknown category {unknown[0]!r}",
            "known_categories": sorted(_STACK),
        }

    return {
        "category": category,
        "scale": scale,
        "preferences": args.get("preferences") or [],
        "recommendations": {
            name: [
                {"option": option, "estimated_monthly_cost": cost}
                for option, cost in _STACK[name][scale]
            ]
            for name in categories
        },
        "note": (
            "Costs are order-of-magnitude monthly estimates for the listed "
            "tier and exclude egress and support plans. Weigh them against "
            "the team's stated expertise before recommending a switch."
        ),
    }


# The keys must match the tool names in the LaunchDarkly configs.
TOOL_HANDLERS = {
    "web_search": web_search,
    "competitor_analysis": competitor_analysis,
    "generate_copy": generate_copy,
    "suggest_ab_tests": suggest_ab_tests,
    "recommend_stack": recommend_stack,
}
