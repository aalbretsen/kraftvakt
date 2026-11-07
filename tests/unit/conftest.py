"""Fixtures for unit tests, which run without Home Assistant unless they ask for it."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations():
    """Override the package fixture so unit tests do not start Home Assistant."""
    return
