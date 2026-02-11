#!/usr/bin/env python3
"""
EVE University Wiki MCP Server
Provides access to EVE Online game information from wiki.eveuniversity.org

Supports both stdio (local) and SSE (containerized/remote) transports
"""

import os
import sys
from mcp.server import Server
from mcp.types import Tool, TextContent
import httpx
import html2text
from typing import Any
import asyncio
import logging
from urllib.parse import quote
import time
from collections import defaultdict

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


async def run_sse():
    """Run with SSE transport (for containerized/remote use)"""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    from starlette.requests import Request
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    import uvicorn

    # CORS configuration - restrictive by default
    cors_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
    
    # Authentication middleware
    async def auth_middleware(request: Request, call_next):
        """Optional token-based authentication"""
        if AUTH_TOKEN:
            # Skip auth for health endpoint
            if request.url.path == "/health":
                return await call_next(request)
            
            auth_header = request.headers.get("Authorization", "")
            token = auth_header.replace("Bearer ", "").strip()
            
            if token != AUTH_TOKEN:
                logger.warning("Unauthorized access attempt from %s", request.client.host if request.client else "unknown")
                return JSONResponse(
                    {"error": "Unauthorized"},
                    status_code=401
                )
        
        return await call_next(request)
    
    # Rate limiting middleware
    async def rate_limit_middleware(request: Request, call_next):
        """Simple rate limiting based on client IP"""
        # Skip rate limiting for health endpoint
        if request.url.path == "/health":
            return await call_next(request)
        
        client_id = request.client.host if request.client else "unknown"
        
        if not check_rate_limit(client_id):
            logger.warning("Rate limit exceeded for client: %s", client_id)
            return JSONResponse(
                {"error": "Rate limit exceeded. Please try again later."},
                status_code=429
            )
        
        return await call_next(request)

    # Health check endpoint
    async def health(request):
        return JSONResponse({
            "status": "healthy",
            "service": "eve-university-wiki-mcp",
            "version": "1.1.0"
        })

    # Create SSE endpoint handler
    sse = SseServerTransport("/messages")

    async def handle_sse(request: Request):
        return await sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        )

    async def handle_messages(request: Request):
        return await sse.handle_post_message(request.scope, request.receive, request._send)

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

    starlette_app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
            Route("/health", endpoint=health, methods=["GET"]),
        ],
        middleware=middleware
    )
    
    # Add custom middleware
    starlette_app.middleware("http")(rate_limit_middleware)
    starlette_app.middleware("http")(auth_middleware)

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
