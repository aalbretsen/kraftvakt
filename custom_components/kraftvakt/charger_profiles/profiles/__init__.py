"""Every charger profile. A new profile is a module here with a `PROFILE`, added to `PROFILES`."""

from __future__ import annotations

from typing import Final

from . import amina_s_zigbee2mqtt, easee

PROFILES: Final = (
    amina_s_zigbee2mqtt.PROFILE,
    easee.PROFILE,
)
