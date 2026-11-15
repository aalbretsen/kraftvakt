"""The state held in memory is turned into JSON for the diagnostics."""

import pytest

from custom_components.kraftvakt.json_values import plain


def test_a_value_the_diagnostics_cannot_show_is_an_error() -> None:
    with pytest.raises(TypeError, match="object cannot be shown"):
        plain({"key": object()})
