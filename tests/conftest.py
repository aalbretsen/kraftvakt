"""Felles fixtures for Kraftvakt-testene."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Tillat lasting av custom_components i alle tester."""
    return
