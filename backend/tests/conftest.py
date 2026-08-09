import pytest
from app.core.rate_limiter import (
    feed_config_limiter,
    persona_update_limiter,
    workflow_run_limiter,
)


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Autouse fixture to reset in-memory process-local rate limiters before and after every test."""
    workflow_run_limiter.reset()
    persona_update_limiter.reset()
    feed_config_limiter.reset()
    yield
    workflow_run_limiter.reset()
    persona_update_limiter.reset()
    feed_config_limiter.reset()
