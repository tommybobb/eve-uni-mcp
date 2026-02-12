from starlette.testclient import TestClient

import eve_wiki_mcp_server_docker as server


def test_health_endpoint_returns_service_and_version():
    app = server.create_sse_starlette_app()
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "eve-university-wiki-mcp"
    assert payload["version"] == "1.2.0"


def test_auth_required_when_token_is_set(monkeypatch):
    monkeypatch.setattr(server, "MCP_ENFORCE_HTTP_GUARDS", True)
    monkeypatch.setattr(server, "AUTH_TOKEN", "secret-token")
    app = server.create_sse_starlette_app()
    client = TestClient(app)

    unauthorized = client.get("/sse")
    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"] == "Unauthorized"

    # Health is explicitly exempt from auth.
    health = client.get("/health")
    assert health.status_code == 200


def test_rate_limit_returns_429(monkeypatch):
    monkeypatch.setattr(server, "MCP_ENFORCE_HTTP_GUARDS", True)
    monkeypatch.setattr(server, "AUTH_TOKEN", "")
    monkeypatch.setattr(server, "RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr(server, "RATE_LIMIT_WINDOW", 60)
    server.rate_limit_store.clear()

    app = server.create_sse_starlette_app()
    client = TestClient(app)

    first = client.post("/messages/")
    # Invalid POST shape is expected here (typically 400) but still consumes
    # one request in the rate-limit window.
    assert first.status_code in (400, 422)

    second = client.post("/messages/")
    assert second.status_code == 429
    assert second.json()["error"] == "Rate limit exceeded. Please try again later."


def test_health_endpoint_bypasses_rate_limit(monkeypatch):
    monkeypatch.setattr(server, "MCP_ENFORCE_HTTP_GUARDS", True)
    monkeypatch.setattr(server, "AUTH_TOKEN", "")
    monkeypatch.setattr(server, "RATE_LIMIT_REQUESTS", 0)
    monkeypatch.setattr(server, "RATE_LIMIT_WINDOW", 60)
    server.rate_limit_store.clear()

    app = server.create_sse_starlette_app()
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200


def test_messages_rejects_non_initialize_before_session_init():
    app = server.create_sse_starlette_app()
    client = TestClient(app)

    response = client.post(
        "/messages/?session_id=test-session",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        },
    )

    assert response.status_code == 409
    assert "not initialized" in response.json()["error"]


def test_messages_allows_initialize_request_before_session_init():
    app = server.create_sse_starlette_app()
    client = TestClient(app)

    response = client.post(
        "/messages/?session_id=test-session",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        },
    )

    # Shape may be invalid for MCP, but initialize must not be blocked by our pre-init gate.
    assert response.status_code != 409
