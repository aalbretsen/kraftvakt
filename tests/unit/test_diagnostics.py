"""The diagnostics turn the state held in memory into JSON."""

import pytest

from custom_components.kraftvakt.diagnostics import plain


def test_a_value_the_diagnostics_cannot_show_is_an_error() -> None:
    with pytest.raises(TypeError, match="object cannot be shown"):
        plain({"key": object()})
