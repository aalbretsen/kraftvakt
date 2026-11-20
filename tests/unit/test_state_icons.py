import pytest

from custom_components.kraftvakt.sensor import StateIcon


@pytest.mark.parametrize(("color", "badge_color"), [("grey", "dark-grey"), ("amber", "orange"), ("red", "red")])
def test_badge_is_darker_where_white_on_the_colour_is_hard_to_read(color: str, badge_color: str) -> None:
    assert StateIcon("mdi:timer-sand", color).badge_color == badge_color
