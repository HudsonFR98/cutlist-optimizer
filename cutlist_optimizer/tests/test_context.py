"""Context names do not need a database."""

import os

NO_DB = True


def test_deployed_context_names():
    from cutlist_optimizer.lib.const import (
        CONTEXTS,
        CONTEXT_DEV,
        CONTEXT_INTEGRATION,
        CONTEXT_PROD,
        CONTEXT_VALIDATION,
        DEPLOYED_CONTEXTS,
        TEST_UI_CONTEXTS,
    )

    assert CONTEXTS == (CONTEXT_DEV, CONTEXT_INTEGRATION, CONTEXT_VALIDATION, CONTEXT_PROD)
    assert "test" not in CONTEXTS
    assert "demo" not in CONTEXTS
    assert CONTEXT_DEV not in DEPLOYED_CONTEXTS
    assert CONTEXT_INTEGRATION in TEST_UI_CONTEXTS
    assert CONTEXT_VALIDATION not in TEST_UI_CONTEXTS


def test_loaded_config_matches_environment():
    from cutlist_optimizer.lib import config
    from cutlist_optimizer.lib.const import CONTEXTS

    expected = os.environ["CUTLIST_OPTIMIZER_CONTEXT"]
    assert expected in CONTEXTS
    assert config.CONTEXT == expected
    if expected == "integration":
        assert config.TESTING is True
    if expected == "validation":
        assert config.CONTEXT == "validation"
        assert getattr(config, "TESTING", False) is False
