import asyncio

import eve_wiki_mcp_server_docker as server


def _call_tool(name: str, arguments: dict) -> str:
    response = asyncio.run(server.call_tool(name, arguments))
    return response[0].text


def test_search_eve_wiki_happy_path(monkeypatch):
    async def fake_fetch(params: dict) -> dict:
        return [
            params.get("search", ""),
            ["Mining", "Venture"],
            ["Mining basics", "Starter mining frigate"],
            [server.build_wiki_url("Mining"), server.build_wiki_url("Venture")],
        ]

    monkeypatch.setattr(server, "fetch_wiki", fake_fetch)
    text = _call_tool("search_eve_wiki", {"query": "mining"})
    assert "Search Results for 'mining'" in text
    assert "**Mining**" in text


def test_search_eve_wiki_empty_results(monkeypatch):
    async def fake_fetch(params: dict) -> dict:
        return [params.get("search", ""), [], [], []]

    monkeypatch.setattr(server, "fetch_wiki", fake_fetch)
    text = _call_tool("search_eve_wiki", {"query": "zzzz"})
    assert "No results found for 'zzzz'" in text


def test_search_eve_wiki_api_error(monkeypatch):
    async def fake_fetch(params: dict) -> dict:
        return {"error": {"info": "Wiki API returned an error. Please try again."}}

    monkeypatch.setattr(server, "fetch_wiki", fake_fetch)
    text = _call_tool("search_eve_wiki", {"query": "mining"})
    assert "Error: Wiki API returned an error. Please try again." in text


def test_get_eve_wiki_page_happy_path(monkeypatch):
    async def fake_fetch(params: dict) -> dict:
        return {
            "parse": {
                "text": {"*": "<p>Mining page content</p>"},
                "displaytitle": "Mining",
                "categories": [{"*": "Mining"}],
            }
        }

    monkeypatch.setattr(server, "fetch_wiki", fake_fetch)
    text = _call_tool("get_eve_wiki_page", {"title": "Mining"})
    assert "# Mining" in text
    assert "https://wiki.eveuniversity.org/wiki/Mining" in text


def test_get_eve_wiki_summary_happy_path(monkeypatch):
    async def fake_fetch(params: dict) -> dict:
        return {
            "query": {
                "pages": {
                    "123": {
                        "title": "Mining",
                        "extract": "Mining summary.",
                    }
                }
            }
        }

    monkeypatch.setattr(server, "fetch_wiki", fake_fetch)
    text = _call_tool("get_eve_wiki_summary", {"title": "Mining"})
    assert "# Mining" in text
    assert "Mining summary." in text


def test_browse_category_happy_path(monkeypatch):
    async def fake_fetch(params: dict) -> dict:
        return {"query": {"categorymembers": [{"title": "Mining"}, {"title": "Venture"}]}}

    monkeypatch.setattr(server, "fetch_wiki", fake_fetch)
    text = _call_tool("browse_eve_wiki_category", {"category": "Mining"})
    assert "# Category: Mining" in text
    assert "- Venture" in text


def test_related_pages_happy_path(monkeypatch):
    async def fake_fetch(params: dict) -> dict:
        return {"query": {"backlinks": [{"title": "Mining"}, {"title": "Ore"}]}}

    monkeypatch.setattr(server, "fetch_wiki", fake_fetch)
    text = _call_tool("get_related_pages", {"title": "Venture"})
    assert "Pages linking to 'Venture'" in text
    assert "- Ore" in text


def test_existing_input_validation_boundaries():
    long_query = "a" * (server.MAX_QUERY_LENGTH + 1)
    text = _call_tool("search_eve_wiki", {"query": long_query})
    assert "query exceeds maximum length" in text

    text = _call_tool("get_eve_wiki_page", {"title": "bad\x00title"})
    assert "title contains invalid characters" in text

    text = _call_tool("browse_eve_wiki_category", {"category": ""})
    assert "category cannot be empty" in text
