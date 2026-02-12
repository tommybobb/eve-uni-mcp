#!/usr/bin/env python3
"""
EVE University Wiki MCP Server
Provides access to EVE Online game information from wiki.eveuniversity.org

Supports both stdio (local) and SSE (containerized/remote) transports
"""

import os
import sys
from collections import defaultdict
from typing import Any
from urllib.parse import quote
import asyncio
import logging
import time

import html2text
import httpx
from mcp.server import Server
from mcp.types import TextContent, Tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Server("eve-university-wiki")

WIKI_API = "https://wiki.eveuniversity.org/api.php"
TIMEOUT = 30.0

# Security configuration
MAX_QUERY_LENGTH = 500
MAX_TITLE_LENGTH = 500
MAX_CATEGORY_LENGTH = 200
AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))  # requests per window
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
rate_limit_store = defaultdict(list)

# Initialize html2text converter
h = html2text.HTML2Text()
h.ignore_links = False
h.ignore_images = False
h.ignore_emphasis = False
h.body_width = 0  # Don't wrap text


def validate_string_input(value: Any, max_length: int, field_name: str) -> tuple[bool, str]:
    """Validate string input for security"""
    if not isinstance(value, str):
        return False, f"{field_name} must be a string"
    
    if len(value) == 0:
        return False, f"{field_name} cannot be empty"
    
    if len(value) > max_length:
        return False, f"{field_name} exceeds maximum length of {max_length}"
    
    # Check for null bytes
    if '\x00' in value:
        return False, f"{field_name} contains invalid characters"
    
    return True, ""


def check_rate_limit(client_id: str) -> bool:
    """Simple in-memory rate limiting"""
    now = time.time()
    
    # Clean old entries
    rate_limit_store[client_id] = [
        timestamp for timestamp in rate_limit_store[client_id]
        if now - timestamp < RATE_LIMIT_WINDOW
    ]
    
    # Check limit
    if len(rate_limit_store[client_id]) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    rate_limit_store[client_id].append(now)
    return True


async def fetch_wiki(params: dict) -> dict:
    """Make an API request to the EVE University Wiki"""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(WIKI_API, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.warning("Wiki API timeout for params: %s", params)
            return {"error": {"info": "Request timed out. Wiki may be slow."}}
        except httpx.HTTPStatusError as e:
            logger.error("Wiki API HTTP error: %s", e)
            return {"error": {"info": "Wiki API returned an error. Please try again."}}
        except Exception as e:
            logger.exception("Wiki API request failed")
            return {"error": {"info": "Request failed. Please try again later."}}


MINING_PLAN_MAX_FREEFORM_LENGTH = 1200
MINING_SEED_QUERIES = [
    "EVE University mining guide",
    "Venture",
    "Mining frigates",
    "Career Agents mining",
    "Highsec mining safety",
    "Ore and mining mechanics",
    "Fitting ships for mining",
]
MINING_RELEVANCE_KEYWORDS = {
    "mining": 8,
    "venture": 8,
    "ore": 5,
    "asteroid": 4,
    "highsec": 4,
    "safety": 4,
    "career": 3,
    "agent": 3,
    "fit": 3,
    "fitting": 3,
    "barge": 2,
    "alpha": 2,
}
MINING_PLAN_SECTION_ORDER = [
    "Profile + Assumptions",
    "Day 1 Plan",
    "Week 1 Plan",
    "Shopping List",
    "Skill Priorities (Alpha-safe)",
    "Safety and Loss Prevention",
    "If Things Go Wrong",
    "Next Session Check-in Questions",
    "Sources",
]
SECTION_KEYWORDS = {
    "Profile + Assumptions": ["mining", "career", "venture"],
    "Day 1 Plan": ["career", "venture", "mining"],
    "Week 1 Plan": ["mining", "ore", "venture"],
    "Shopping List": ["venture", "fitting", "mining"],
    "Skill Priorities (Alpha-safe)": ["skills", "mining", "alpha"],
    "Safety and Loss Prevention": ["safety", "highsec", "gank"],
    "If Things Go Wrong": ["safety", "venture", "mining"],
    "Next Session Check-in Questions": ["mining", "career"],
}


def validate_numeric_input(
    value: Any,
    min_value: float,
    max_value: float,
    field_name: str,
    integer_only: bool = False,
) -> tuple[bool, str]:
    """Validate numeric fields for planner input."""
    if integer_only:
        if not isinstance(value, int) or isinstance(value, bool):
            return False, f"{field_name} must be an integer between {int(min_value)} and {int(max_value)}"
    else:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False, f"{field_name} must be a number between {min_value} and {max_value}"

    if value < min_value or value > max_value:
        if integer_only:
            return False, f"{field_name} must be between {int(min_value)} and {int(max_value)}"
        return False, f"{field_name} must be between {min_value} and {max_value}"
    return True, ""


def validate_enum_input(value: Any, allowed_values: list[str], field_name: str) -> tuple[bool, str]:
    """Validate enum values with a clear allowed list."""
    if not isinstance(value, str):
        return False, f"{field_name} must be one of: {', '.join(allowed_values)}"
    if value not in allowed_values:
        return False, f"{field_name} must be one of: {', '.join(allowed_values)}"
    return True, ""


def validate_optional_text_input(value: Any, max_length: int, field_name: str) -> tuple[bool, str]:
    """Validate optional freeform text fields."""
    if not isinstance(value, str):
        return False, f"{field_name} must be a string"
    if len(value) > max_length:
        return False, f"{field_name} exceeds maximum length of {max_length}"
    if "\x00" in value:
        return False, f"{field_name} contains invalid characters"
    return True, ""


def build_wiki_url(title: str) -> str:
    """Build a safe wiki URL from a page title."""
    return f"https://wiki.eveuniversity.org/wiki/{quote(title.replace(' ', '_'), safe='')}"


def score_mining_candidate(title: str, description: str, query: str) -> int:
    """Score page relevance for newbro mining planning."""
    text = f"{title} {description}".lower()
    score = 0
    for keyword, weight in MINING_RELEVANCE_KEYWORDS.items():
        if keyword in text:
            score += weight

    for token in query.lower().split():
        if token in text:
            score += 1
    return score


def normalize_mining_plan_inputs(arguments: Any) -> tuple[dict[str, Any] | None, str]:
    """Apply defaults and validate inputs for mining planner tool."""
    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict):
        return None, "arguments must be an object"

    defaults = {
        "hours_per_session": 1.5,
        "sessions_per_week": 4,
        "starting_isk": 0,
        "experience_level": "brand_new",
        "risk_preference": "conservative",
        "current_assets": "",
        "recent_outcome": "",
        "questions": "",
    }
    normalized = defaults.copy()
    normalized.update(arguments)

    valid, error_msg = validate_numeric_input(
        normalized["hours_per_session"], 0.5, 8.0, "hours_per_session"
    )
    if not valid:
        return None, error_msg

    valid, error_msg = validate_numeric_input(
        normalized["sessions_per_week"], 1, 14, "sessions_per_week", integer_only=True
    )
    if not valid:
        return None, error_msg

    valid, error_msg = validate_numeric_input(
        normalized["starting_isk"], 0, 10_000_000_000, "starting_isk", integer_only=True
    )
    if not valid:
        return None, error_msg

    valid, error_msg = validate_enum_input(
        normalized["experience_level"], ["brand_new"], "experience_level"
    )
    if not valid:
        return None, error_msg

    valid, error_msg = validate_enum_input(
        normalized["risk_preference"], ["conservative"], "risk_preference"
    )
    if not valid:
        return None, error_msg

    for field in ["current_assets", "recent_outcome", "questions"]:
        valid, error_msg = validate_optional_text_input(
            normalized[field], MINING_PLAN_MAX_FREEFORM_LENGTH, field
        )
        if not valid:
            return None, error_msg

    return normalized, ""


def _extract_summary_from_query_response(data: dict, fallback_title: str) -> str:
    """Extract plain summary text from MediaWiki query response."""
    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return ""
    page = next(iter(pages.values()))
    if "missing" in page:
        return ""
    extract = page.get("extract", "")
    if not extract:
        return ""
    return extract.strip()


async def gather_mining_wiki_context() -> dict[str, Any]:
    """Retrieve, rank, and summarize mining-focused wiki context."""
    candidates: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    for query in MINING_SEED_QUERIES:
        data = await fetch_wiki(
            {
                "action": "opensearch",
                "search": query,
                "limit": 8,
                "format": "json",
                "namespace": "0",
            }
        )

        if "error" in data:
            errors.append(f"search:{query}")
            continue

        titles = data[1] if len(data) > 1 else []
        descriptions = data[2] if len(data) > 2 else []
        urls = data[3] if len(data) > 3 else []

        for idx, title in enumerate(titles):
            desc = descriptions[idx] if idx < len(descriptions) else ""
            url = urls[idx] if idx < len(urls) and urls[idx] else build_wiki_url(title)
            score = score_mining_candidate(title, desc, query)
            key = title.lower()

            if key not in candidates:
                candidates[key] = {
                    "title": title,
                    "description": desc,
                    "url": url,
                    "score": score,
                }
            elif score > candidates[key]["score"]:
                candidates[key]["score"] = score
                candidates[key]["description"] = desc
                candidates[key]["url"] = url

    ranked_candidates = sorted(
        candidates.values(),
        key=lambda item: (item["score"], item["title"].lower()),
        reverse=True,
    )

    if not ranked_candidates:
        ranked_candidates = [
            {
                "title": "Mining",
                "description": "General mining overview",
                "url": build_wiki_url("Mining"),
                "score": 1,
            }
        ]

    summaries: dict[str, str] = {}
    page_snippets: dict[str, str] = {}

    for candidate in ranked_candidates[:8]:
        title = candidate["title"]
        summary_data = await fetch_wiki(
            {
                "action": "query",
                "prop": "extracts",
                "exintro": "true",
                "explaintext": "true",
                "titles": title,
                "format": "json",
            }
        )

        if "error" in summary_data:
            errors.append(f"summary:{title}")
            continue

        summary_text = _extract_summary_from_query_response(summary_data, title)
        if summary_text:
            summaries[title] = summary_text

    for candidate in ranked_candidates[:3]:
        title = candidate["title"]
        if len(summaries.get(title, "")) >= 180:
            continue

        page_data = await fetch_wiki(
            {
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "disabletoc": "true",
            }
        )

        if "error" in page_data:
            errors.append(f"page:{title}")
            continue

        try:
            markdown_content = h.handle(page_data["parse"]["text"]["*"])
            page_snippets[title] = markdown_content.strip()[:600]
        except Exception:
            errors.append(f"page-parse:{title}")

    fallback_url = ranked_candidates[0]["url"]
    section_citations: dict[str, str] = {}
    for section_name in SECTION_KEYWORDS:
        section_url = ""
        keywords = SECTION_KEYWORDS[section_name]
        for candidate in ranked_candidates:
            haystack = f"{candidate['title']} {candidate['description']}".lower()
            if any(keyword in haystack for keyword in keywords):
                section_url = candidate["url"]
                break
        section_citations[section_name] = section_url or fallback_url

    return {
        "ranked_candidates": ranked_candidates,
        "summaries": summaries,
        "page_snippets": page_snippets,
        "errors": errors,
        "partial": len(errors) > 0,
        "section_citations": section_citations,
    }


def _format_source(section_name: str, context: dict[str, Any]) -> str:
    """Format a source line for a section."""
    url = context.get("section_citations", {}).get(section_name, "")
    if not url:
        url = build_wiki_url("Mining")
    return f"Source: {url}"


def build_mining_plan_markdown(profile: dict[str, Any], context: dict[str, Any]) -> str:
    """Build deterministic mining onboarding plan with citations."""
    hours_per_session = float(profile["hours_per_session"])
    sessions_per_week = int(profile["sessions_per_week"])
    starting_isk = int(profile["starting_isk"])
    recent_outcome = profile["recent_outcome"].lower()
    player_questions = profile["questions"].strip()
    assets = profile["current_assets"].strip() or "No assets provided"

    if hours_per_session <= 1.0:
        day1_tasks = 3
    elif hours_per_session <= 2.5:
        day1_tasks = 4
    else:
        day1_tasks = 5

    week_target_sessions = min(sessions_per_week, 7)
    low_capital_mode = starting_isk <= 0
    recovery_mode = any(token in recent_outcome for token in ["lost", "killed", "ganked", "destroyed", "death"])
    low_isk_recovery = any(token in recent_outcome for token in ["broke", "low isk", "no isk", "can't afford"])
    confusion_mode = any(token in recent_outcome for token in ["stuck", "confused", "overwhelmed", "not sure", "dont know", "don't know"])

    confidence_line = "Normal confidence: Wiki retrieval completed for core mining pages."
    if context.get("partial"):
        confidence_line = (
            "Reduced confidence: some wiki pages timed out or failed; plan uses partial context and conservative defaults."
        )

    shopping_header = "Start with low-capital purchases only." if low_capital_mode else "Use your starting ISK to front-load survivability."
    if starting_isk >= 2_000_000:
        shopping_header = "Prioritize a complete Venture fitting and spare replacements."

    if recovery_mode:
        fallback_intro = "You reported a ship loss. Switch to a safer high-sec loop for the next 2 sessions."
    elif low_isk_recovery:
        fallback_intro = "You reported low ISK pressure. Run a low-capital recovery loop before upgrades."
    elif confusion_mode:
        fallback_intro = "You reported confusion/stall. Use a simplified 3-task session to regain momentum."
    else:
        fallback_intro = "If progress stalls, fall back to a short high-sec routine and reassess after one session."

    day1_items = [
        "Complete the mining-focused Career Agent steps and accept all tutorial rewards.",
        "Acquire or verify access to a Venture hull and fit basic mining modules.",
        "Run a short high-sec mining session and record ISK earned, cargo cycles, and travel time.",
        "Create one bookmark for station tether/dock and one for your preferred belt entry.",
        "Set overview and d-scan habits before undocking again.",
    ][:day1_tasks]

    week1_items = [
        f"Run {week_target_sessions} mining sessions in high-sec with a short pre-undock safety check.",
        "After each session, review: ISK/hour, number of interruptions, and risk events.",
        "Upgrade fitting only when you can afford replacement of your current ship and modules.",
        "Practice route discipline: avoid predictable belts when local activity spikes.",
        "At end of week, choose one improvement goal: cycle uptime, hauling efficiency, or survival habits.",
    ]

    if confusion_mode:
        week1_items[1] = "Keep each session to three goals: undock safely, fill hold once, dock safely."

    lines = [
        "# Newbro Mining Copilot Plan",
        "",
        "## Profile + Assumptions",
        f"- Experience level: {profile['experience_level']}",
        f"- Risk preference: {profile['risk_preference']}",
        f"- Time budget: {hours_per_session:.1f}h/session, {sessions_per_week} sessions/week",
        f"- Starting ISK: {starting_isk:,}",
        f"- Current assets: {assets}",
        f"- Confidence: {confidence_line}",
        _format_source("Profile + Assumptions", context),
        "",
        "## Day 1 Plan",
    ]
    lines.extend([f"{idx + 1}. {item}" for idx, item in enumerate(day1_items)])
    lines.extend(
        [
            "Completion criteria: one safe undock-to-dock mining run with notes captured.",
            _format_source("Day 1 Plan", context),
            "",
            "## Week 1 Plan",
        ]
    )
    lines.extend([f"{idx + 1}. {item}" for idx, item in enumerate(week1_items)])
    lines.extend(
        [
            "Completion criteria: at least 3 logged sessions and one deliberate fitting/behavior improvement.",
            _format_source("Week 1 Plan", context),
            "",
            "## Shopping List",
            f"- {shopping_header}",
            "- Venture hull (or replacement hull if already owned).",
            "- Basic mining lasers and low-cost tank modules before yield upgrades.",
            "- Mobile reserve: keep enough ISK for one full replacement before risky upgrades.",
            _format_source("Shopping List", context),
            "",
            "## Skill Priorities (Alpha-safe)",
            "1. Core fitting/powergrid/capacitor support to stabilize your fit.",
            "2. Mining throughput and mining frigate support skills.",
            "3. Basic navigation and survivability skills before yield-only specialization.",
            "4. Queue short skills first for immediate quality-of-life gains.",
            _format_source("Skill Priorities (Alpha-safe)", context),
            "",
            "## Safety and Loss Prevention",
            "1. Mine in high-sec systems with manageable local traffic and clear docking options.",
            "2. Treat every undock as disposable: never fly what you cannot replace.",
            "3. Pre-align and monitor local/d-scan; dock immediately on suspicious spikes.",
            "4. Avoid autopilot hauling of ore value you cannot lose.",
            _format_source("Safety and Loss Prevention", context),
            "",
            "## If Things Go Wrong",
            f"- {fallback_intro}",
            "- Recovery loop: one short safe run, sell ore, refill replacement fund, reassess fit.",
            "- If two losses happen in a row, downgrade risk and focus on safety drills only.",
            _format_source("If Things Go Wrong", context),
            "",
            "## Next Session Check-in Questions",
            "1. Did you complete a safe undock -> mine -> dock cycle?",
            "2. What blocked you most: travel, fitting, safety pressure, or income?",
            "3. Do you currently have replacement ISK for your active ship?",
            "4. Which single change should the next plan optimize first?",
        ]
    )
    if player_questions:
        lines.append(f"5. Player focus question to address next: {player_questions}")
    lines.extend(
        [
            _format_source("Next Session Check-in Questions", context),
            "",
            "## Sources",
        ]
    )

    source_urls = []
    for candidate in context.get("ranked_candidates", [])[:10]:
        url = candidate.get("url", "")
        title = candidate.get("title", "")
        if not url or url in source_urls:
            continue
        source_urls.append(url)
        lines.append(f"- {title}: {url}")

    if not source_urls:
        lines.append(f"- Mining: {build_wiki_url('Mining')}")

    if context.get("errors"):
        lines.extend(
            [
                "",
                "Note: Some wiki requests failed during planning. Retry for fresher/complete citations.",
            ]
        )

    return "\n".join(lines)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools for the EVE University Wiki"""
    return [
        Tool(
            name="search_eve_wiki",
            description="Search the EVE University Wiki for articles about ships, mechanics, guides, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (e.g., 'Drake', 'exploration guide', 'wormhole mechanics')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return (1-50, default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_eve_wiki_page",
            description="Get the full content of a specific EVE University Wiki page in markdown format",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Exact page title (e.g., 'Drake', 'Mining', 'Wormholes')"
                    }
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="get_eve_wiki_summary",
            description="Get a brief summary/introduction of a wiki page without full content",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Page title to get summary for"
                    }
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="browse_eve_wiki_category",
            description="Browse pages in a specific category (e.g., Ships, Modules, Skills, Guides)",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category name (e.g., 'Ships', 'Mining', 'PvP', 'Exploration')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of pages to return (1-500, default: 50)",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 500
                    }
                },
                "required": ["category"]
            }
        ),
        Tool(
            name="get_related_pages",
            description="Find pages that link to a specific wiki page",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Page title to find related pages for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results (1-500, default: 20)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 500
                    }
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="generate_newbro_mining_plan",
            description="Generate a conservative mining-only onboarding strategy for a brand-new Alpha player with wiki citations",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours_per_session": {
                        "type": "number",
                        "minimum": 0.5,
                        "maximum": 8,
                        "default": 1.5
                    },
                    "sessions_per_week": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 14,
                        "default": 4
                    },
                    "starting_isk": {
                        "type": "integer",
                        "minimum": 0,
                        "default": 0
                    },
                    "experience_level": {
                        "type": "string",
                        "enum": ["brand_new"],
                        "default": "brand_new"
                    },
                    "risk_preference": {
                        "type": "string",
                        "enum": ["conservative"],
                        "default": "conservative"
                    },
                    "current_assets": {
                        "type": "string",
                        "default": ""
                    },
                    "recent_outcome": {
                        "type": "string",
                        "description": "What happened last session; used for replanning",
                        "default": ""
                    },
                    "questions": {
                        "type": "string",
                        "default": ""
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    
    if name == "search_eve_wiki":
        query = arguments.get("query", "")
        
        # Validate input
        valid, error_msg = validate_string_input(query, MAX_QUERY_LENGTH, "query")
        if not valid:
            return [TextContent(type="text", text=f"❌ {error_msg}")]
        
        limit = min(arguments.get("limit", 10), 50)
        
        params = {
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "format": "json",
            "namespace": "0"  # Main namespace only
        }
        
        data = await fetch_wiki(params)
        
        if "error" in data:
            return [TextContent(
                type="text",
                text=f"❌ Error: {data['error']['info']}"
            )]
        
        # OpenSearch returns: [query, [titles], [descriptions], [urls]]
        titles = data[1] if len(data) > 1 else []
        descriptions = data[2] if len(data) > 2 else []
        urls = data[3] if len(data) > 3 else []
        
        if not titles:
            return [TextContent(
                type="text",
                text=f"No results found for '{query}'. Try different search terms or check spelling."
            )]
        
        results = []
        for i in range(len(titles)):
            title = titles[i]
            desc = descriptions[i] if i < len(descriptions) else ""
            url = urls[i] if i < len(urls) else ""
            results.append(f"**{title}**\n{desc}\n🔗 {url}\n")
        
        return [TextContent(
            type="text",
            text=f"# Search Results for '{query}'\n\nFound {len(titles)} results:\n\n" + "\n".join(results)
        )]
    
    elif name == "get_eve_wiki_page":
        title = arguments.get("title", "")
        
        # Validate input
        valid, error_msg = validate_string_input(title, MAX_TITLE_LENGTH, "title")
        if not valid:
            return [TextContent(type="text", text=f"❌ {error_msg}")]
        
        params = {
            "action": "parse",
            "page": title,
            "prop": "text|displaytitle|categories",
            "format": "json",
            "disabletoc": "true"
        }
        
        data = await fetch_wiki(params)
        
        if "error" in data:
            return [TextContent(
                type="text",
                text=f"❌ Error: {data['error']['info']}\n\nThe page '{title}' might not exist. Try searching first."
            )]
        
        try:
            html_content = data["parse"]["text"]["*"]
            display_title = data["parse"]["displaytitle"]
            categories = [cat["*"] for cat in data["parse"].get("categories", [])]
            
            # Convert HTML to Markdown
            markdown_content = h.handle(html_content)
            
            # Clean up some MediaWiki artifacts
            markdown_content = markdown_content.replace("[ edit ]", "")
            
            # Build response with properly encoded URL
            url_safe_title = quote(title.replace(' ', '_'), safe='')
            result = f"# {display_title}\n\n"
            result += f"🔗 https://wiki.eveuniversity.org/wiki/{url_safe_title}\n\n"
            
            if categories:
                result += f"**Categories:** {', '.join(categories[:5])}\n\n"
            
            result += "---\n\n"
            result += markdown_content
            
            return [TextContent(type="text", text=result)]
            
        except KeyError as e:
            logger.error("Missing expected key in wiki response: %s", e)
            return [TextContent(
                type="text",
                text="❌ Error parsing page content. The page format may be unexpected."
            )]
        except Exception as e:
            logger.exception("Error parsing wiki page: %s", title)
            return [TextContent(
                type="text",
                text="❌ Error parsing page content. Please try again."
            )]
    
    elif name == "get_eve_wiki_summary":
        title = arguments.get("title", "")
        
        # Validate input
        valid, error_msg = validate_string_input(title, MAX_TITLE_LENGTH, "title")
        if not valid:
            return [TextContent(type="text", text=f"❌ {error_msg}")]
        
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": "true",
            "explaintext": "true",
            "titles": title,
            "format": "json"
        }
        
        data = await fetch_wiki(params)
        
        if "error" in data:
            return [TextContent(
                type="text",
                text=f"❌ Error: {data['error']['info']}"
            )]
        
        try:
            pages = data["query"]["pages"]
            page = next(iter(pages.values()))
            
            if "missing" in page:
                return [TextContent(
                    type="text",
                    text=f"❌ Page '{title}' does not exist."
                )]
            
            extract = page.get("extract", "No summary available.")
            page_title = page.get("title", title)
            
            # Build response with properly encoded URL
            url_safe_title = quote(title.replace(' ', '_'), safe='')
            result = f"# {page_title}\n\n"
            result += f"🔗 https://wiki.eveuniversity.org/wiki/{url_safe_title}\n\n"
            result += extract
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.exception("Error getting summary for: %s", title)
            return [TextContent(
                type="text",
                text="❌ Error getting summary. Please try again."
            )]
    
    elif name == "browse_eve_wiki_category":
        category = arguments.get("category", "")
        
        # Validate input
        valid, error_msg = validate_string_input(category, MAX_CATEGORY_LENGTH, "category")
        if not valid:
            return [TextContent(type="text", text=f"❌ {error_msg}")]
        
        limit = min(arguments.get("limit", 50), 500)
        
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": limit,
            "format": "json",
            "cmnamespace": "0"  # Main namespace only
        }
        
        data = await fetch_wiki(params)
        
        if "error" in data:
            return [TextContent(
                type="text",
                text=f"❌ Error: {data['error']['info']}"
            )]
        
        try:
            members = data["query"]["categorymembers"]
            
            if not members:
                return [TextContent(
                    type="text",
                    text=f"No pages found in Category:{category}. The category might not exist or be empty."
                )]
            
            results = [f"- {member['title']}" for member in members]
            
            result = f"# Category: {category}\n\n"
            result += f"Found {len(members)} pages:\n\n"
            result += "\n".join(results)
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.exception("Error browsing category: %s", category)
            return [TextContent(
                type="text",
                text="❌ Error browsing category. Please try again."
            )]
    
    elif name == "get_related_pages":
        title = arguments.get("title", "")
        
        # Validate input
        valid, error_msg = validate_string_input(title, MAX_TITLE_LENGTH, "title")
        if not valid:
            return [TextContent(type="text", text=f"❌ {error_msg}")]
        
        limit = min(arguments.get("limit", 20), 500)
        
        params = {
            "action": "query",
            "list": "backlinks",
            "bltitle": title,
            "bllimit": limit,
            "blnamespace": "0",
            "format": "json"
        }
        
        data = await fetch_wiki(params)
        
        if "error" in data:
            return [TextContent(
                type="text",
                text=f"❌ Error: {data['error']['info']}"
            )]
        
        try:
            backlinks = data["query"]["backlinks"]
            
            if not backlinks:
                return [TextContent(
                    type="text",
                    text=f"No pages link to '{title}'."
                )]
            
            results = [f"- {bl['title']}" for bl in backlinks]
            
            result = f"# Pages linking to '{title}'\n\n"
            result += f"Found {len(backlinks)} pages:\n\n"
            result += "\n".join(results)
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.exception("Error finding related pages for: %s", title)
            return [TextContent(
                type="text",
                text="❌ Error finding related pages. Please try again."
            )]

    elif name == "generate_newbro_mining_plan":
        normalized, error_msg = normalize_mining_plan_inputs(arguments)
        if not normalized:
            return [TextContent(type="text", text=f"❌ {error_msg}")]

        context = await gather_mining_wiki_context()
        plan_markdown = build_mining_plan_markdown(normalized, context)
        return [TextContent(type="text", text=plan_markdown)]

    return [TextContent(
        type="text",
        text=f"❌ Unknown tool: {name}"
    )]


async def run_stdio():
    """Run with stdio transport (for local use)"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


async def _noop_asgi_response(scope, receive, send):
    """No-op ASGI response for SSE endpoints where the response was already sent."""
    pass


def create_sse_starlette_app():
    """Create Starlette app for SSE transport with auth/rate-limit middleware."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

    # CORS configuration - restrictive by default
    cors_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []

    # Create SSE endpoint handler
    sse = SseServerTransport("/messages/")

    async def authorize_request(request: Request):
        """Return JSONResponse on auth failure, else None."""
        if AUTH_TOKEN:
            # Skip auth for health endpoint
            if request.url.path == "/health":
                return None

            auth_header = request.headers.get("Authorization", "")
            token = auth_header.replace("Bearer ", "").strip()

            if token != AUTH_TOKEN:
                logger.warning(
                    "Unauthorized access attempt from %s",
                    request.client.host if request.client else "unknown"
                )
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return None

    async def enforce_rate_limit(request: Request):
        """Return JSONResponse on rate-limit failure, else None."""
        # Skip rate limiting for health endpoint
        if request.url.path == "/health":
            return None

        client_id = request.client.host if request.client else "unknown"
        if not check_rate_limit(client_id):
            logger.warning("Rate limit exceeded for client: %s", client_id)
            return JSONResponse(
                {"error": "Rate limit exceeded. Please try again later."},
                status_code=429
            )
        return None

    async def handle_sse(request: Request):
        auth_error = await authorize_request(request)
        if auth_error:
            return auth_error

        rate_error = await enforce_rate_limit(request)
        if rate_error:
            return rate_error

        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        # SSE response was already sent via the raw ASGI send callable.
        # Return a no-op ASGI response to prevent Starlette from raising
        # TypeError when it tries to call the return value as a Response.
        return _noop_asgi_response

    async def handle_messages(request: Request):
        auth_error = await authorize_request(request)
        if auth_error:
            return auth_error

        rate_error = await enforce_rate_limit(request)
        if rate_error:
            return rate_error

        await sse.handle_post_message(request.scope, request.receive, request._send)
        # POST response was already sent by sse.handle_post_message.
        return _noop_asgi_response

    # Health check endpoint
    async def health(request):
        return JSONResponse({
            "status": "healthy",
            "service": "eve-university-wiki-mcp",
            "version": "1.2.0"
        })

    # Build middleware stack
    middleware = []

    if cors_origins:
        middleware.append(
            Middleware(
                CORSMiddleware,
                allow_origins=cors_origins,
                allow_credentials=True,
                allow_methods=["GET", "POST"],
                allow_headers=["*"],
            )
        )

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages/", endpoint=handle_messages, methods=["POST"]),
            Route("/health", endpoint=health, methods=["GET"]),
        ],
        middleware=middleware
    )


async def run_sse():
    """Run with SSE transport (for containerized/remote use)"""
    import uvicorn
    starlette_app = create_sse_starlette_app()

    # Get configuration from environment
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    logger.info("🚀 Starting EVE University Wiki MCP Server on %s:%s", host, port)
    logger.info("📡 SSE endpoint: http://%s:%s/sse", host, port)
    logger.info("❤️  Health check: http://%s:%s/health", host, port)
    
    if AUTH_TOKEN:
        logger.info("🔒 Authentication enabled")
    else:
        logger.warning("⚠️  Authentication disabled - server is open to all clients")
    
    logger.info("⏱️  Rate limit: %d requests per %d seconds", RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)

    config = uvicorn.Config(
        starlette_app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Main entry point - decides between stdio and SSE based on environment"""
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    
    if transport == "sse":
        await run_sse()
    else:
        await run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
