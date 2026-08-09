from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import init_db
from app.core.rate_limiter import (
    feed_config_limiter,
    persona_update_limiter,
    workflow_run_limiter,
)
from app.repositories import (
    SQLiteAgentRepository,
    SQLitePersonaRepository,
    SQLitePostRepository,
    SQLiteTopicRepository,
    SQLiteWorkflowRepository,
    get_agent_repository,
    get_persona_repository,
    get_post_repository,
    get_workflow_repository,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated temporary SQLite database path and initializing schema."""
    db_file = tmp_path / "test_hardening.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def setup_hardening_agent(temp_db):
    """Fixture setting up agent, repositories, and TestClient for hardening tests."""
    agent_repo = SQLiteAgentRepository(temp_db)
    topic_repo = SQLiteTopicRepository(temp_db)
    wf_repo = SQLiteWorkflowRepository(temp_db)
    post_repo = SQLitePostRepository(temp_db)
    persona_repo = SQLitePersonaRepository(temp_db)

    agent = agent_repo.save_agent("agent-harden-001", "NOVA Strategist", "AI & Quantum")

    app.dependency_overrides[get_agent_repository] = lambda: agent_repo
    app.dependency_overrides[get_workflow_repository] = lambda: wf_repo
    app.dependency_overrides[get_post_repository] = lambda: post_repo
    app.dependency_overrides[get_persona_repository] = lambda: persona_repo

    workflow_run_limiter.reset()
    persona_update_limiter.reset()
    feed_config_limiter.reset()

    client = TestClient(app)
    yield agent, client, temp_db, agent_repo, topic_repo, wf_repo, post_repo
    app.dependency_overrides.clear()
    workflow_run_limiter.reset()
    persona_update_limiter.reset()
    feed_config_limiter.reset()


def test_malformed_path_and_query_identifiers(setup_hardening_agent):
    """Verify path traversal, empty IDs, oversized IDs, and credential strings are rejected."""
    agent, client, _, _, _, _, _ = setup_hardening_agent

    # Empty agent_id
    res = client.get("/api/agent/   /persona")
    assert res.status_code in (400, 404, 422)

    # Oversized agent_id (> 100 chars)
    long_id = "a" * 105
    res = client.get(f"/api/agent/{long_id}/persona")
    assert res.status_code == 400
    assert "exceeds maximum" in res.json()["detail"]

    # Path traversal characters in agent_id
    res = client.get("/api/agent/..%2F..%2Fetc/persona")
    assert res.status_code in (400, 404)

    # Credential keyword in agent_id
    res = client.get("/api/agent/agent-password=secret/persona")
    assert res.status_code == 400
    assert "forbidden credential" in res.json()["detail"]


def test_invalid_pagination_parameters(setup_hardening_agent):
    """Verify invalid limit and offset values return HTTP 422 or 400."""
    agent, client, _, _, _, _, _ = setup_hardening_agent

    # Excessive limit (> 100)
    res = client.get(f"/api/agent/{agent.agent_id}/workflows?limit=150")
    assert res.status_code == 422

    # Negative limit
    res = client.get(f"/api/agent/{agent.agent_id}/workflows?limit=0")
    assert res.status_code == 422

    # Negative offset
    res = client.get(f"/api/agent/{agent.agent_id}/workflows?offset=-5")
    assert res.status_code == 422

    # Excessive offset (> 10000)
    res = client.get(f"/api/agent/{agent.agent_id}/workflows?offset=20000")
    assert res.status_code == 422


def test_oversized_payload_and_list_limits(setup_hardening_agent):
    """Verify oversized strings and lists are rejected in Persona and FeedConfig update requests."""
    agent, client, _, _, _, _, _ = setup_hardening_agent

    # Oversized persona name (> 100 chars)
    res = client.put(
        f"/api/agent/{agent.agent_id}/persona",
        json={
            "persona_name": "x" * 105,
            "primary_domain": "Tech",
        }
    )
    assert res.status_code == 422

    # Oversized list (> 50 items)
    oversized_list = [f"item-{i}" for i in range(60)]
    res = client.put(
        f"/api/agent/{agent.agent_id}/persona",
        json={
            "persona_name": "Valid Name",
            "primary_domain": "Tech",
            "preferred_categories": oversized_list,
        }
    )
    assert res.status_code == 422

    # Oversized list item (> 100 chars)
    res = client.put(
        f"/api/agent/{agent.agent_id}/persona",
        json={
            "persona_name": "Valid Name",
            "primary_domain": "Tech",
            "preferred_categories": ["a" * 105],
        }
    )
    assert res.status_code == 422


def test_deterministic_rate_limiting_and_retry_after(setup_hardening_agent):
    """Verify process-local rate limiter triggers HTTP 429, returns Retry-After, and resets deterministically."""
    agent, client, _, _, _, _, _ = setup_hardening_agent

    fake_clock = 1000.0

    def mock_time():
        return fake_clock

    workflow_run_limiter.set_time_func(mock_time)
    persona_update_limiter.set_time_func(mock_time)

    # First 5 workflow runs should succeed
    for _ in range(5):
        with patch("app.services.workflow.orchestrator.discover_topics", return_value=[]):
            res = client.post(
                f"/api/agent/{agent.agent_id}/workflow/run",
                json={"max_topics": 2}
            )
            assert res.status_code == 200

    # 6th request should fail with HTTP 429 and Retry-After header
    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[]):
        res_blocked = client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={"max_topics": 2}
        )
        assert res_blocked.status_code == 429
        assert "Retry-After" in res_blocked.headers
        assert res_blocked.headers["Retry-After"] == "60"
        assert "Rate limit exceeded" in res_blocked.json()["detail"]

    # Advance clock by 61 seconds -> Rate limit window resets deterministically without sleep
    fake_clock += 61.0

    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[]):
        res_after_reset = client.post(
            f"/api/agent/{agent.agent_id}/workflow/run",
            json={"max_topics": 2}
        )
        assert res_after_reset.status_code == 200

    # Restore default time functions
    workflow_run_limiter.set_time_func(None)
    persona_update_limiter.set_time_func(None)


def test_rate_limit_identity_isolation(setup_hardening_agent):
    """Verify rate limits are isolated per agent_id."""
    agent, client, _, agent_repo, _, _, _ = setup_hardening_agent
    agent2 = agent_repo.save_agent("agent-harden-002", "NOVA 2", "Robotics")

    fake_clock = 2000.0
    workflow_run_limiter.set_time_func(lambda: fake_clock)

    # Exhaust agent 1 limit (5 requests)
    for _ in range(5):
        with patch("app.services.workflow.orchestrator.discover_topics", return_value=[]):
            client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={"max_topics": 1})

    # Agent 1 is rate limited
    res1 = client.post(f"/api/agent/{agent.agent_id}/workflow/run", json={"max_topics": 1})
    assert res1.status_code == 429

    # Agent 2 is NOT rate limited
    with patch("app.services.workflow.orchestrator.discover_topics", return_value=[]):
        res2 = client.post(f"/api/agent/{agent2.agent_id}/workflow/run", json={"max_topics": 1})
        assert res2.status_code == 200

    workflow_run_limiter.set_time_func(None)


def test_error_sanitization_for_unhandled_exceptions(setup_hardening_agent):
    """Verify unhandled exceptions return sanitized HTTP 500 without leaking stack traces or internal paths."""
    agent, client, _, _, _, _, _ = setup_hardening_agent

    def mock_exploding_workflow(*args, **kwargs):
        raise RuntimeError("C:\\SecretData\\DB\\internal.sqlite connection error: SELECT * FROM secrets")

    with patch("app.api.agent.run_agent_workflow", side_effect=mock_exploding_workflow):
        res = client.post(f"/api/agent/{agent.agent_id}/workflow/run")
        assert res.status_code == 500
        data = res.json()
        assert "SecretData" not in str(data)
        assert "SELECT" not in str(data)
        assert "sqlite" not in str(data).lower()
        assert data["detail"] == "Internal workflow execution error."


def test_valid_request_backward_compatibility(setup_hardening_agent):
    """Verify legitimate, valid requests succeed without regression."""
    agent, client, _, _, _, _, _ = setup_hardening_agent

    # PUT Persona
    res_persona = client.put(
        f"/api/agent/{agent.agent_id}/persona",
        json={
            "persona_name": "Updated NOVA",
            "primary_domain": "Tech Strategy",
            "preferred_categories": ["AI", "Cloud"],
            "min_relevance_threshold": 0.7,
        }
    )
    assert res_persona.status_code == 200
    assert res_persona.json()["persona_name"] == "Updated NOVA"

    # GET Feed Config
    res_cfg = client.get(f"/api/agent/{agent.agent_id}/feed/config")
    assert res_cfg.status_code == 200
    assert res_cfg.json()["min_relevance_score"] == 0.7

    # GET Feed
    res_feed = client.get(f"/api/agent/feed?agentId={agent.agent_id}")
    assert res_feed.status_code == 200
    assert res_feed.json()["status"] == "ok"
