"""The list of charger profiles stays whole as profiles are added."""

from importlib import import_module
from itertools import combinations
from pathlib import Path
from pkgutil import iter_modules

from custom_components.kraftvakt.charger_profiles import profiles
from custom_components.kraftvakt.charger_profiles.profile import DeviceMatch
from custom_components.kraftvakt.charger_profiles.profiles import PROFILES

MODULES = [module.name for module in iter_modules(profiles.__path__)]


def test_every_profile_module_is_listed_and_tested() -> None:
    listed = [import_module(f"{profiles.__name__}.{name}").PROFILE for name in MODULES]
    assert len(listed) == len(PROFILES)
    assert all(profile in PROFILES for profile in listed)
    tests = Path(__file__).parent / "profiles"
    assert [name for name in MODULES if not (tests / f"test_{name}.py").exists()] == []


def test_profiles_have_their_own_names_and_devices() -> None:
    """The first profile that fits a device is used, so two profiles must not fit the same device."""
    assert len({profile.name for profile in PROFILES}) == len(PROFILES)
    assert [(first.name, second.name) for first, second in combinations(PROFILES, 2) if _overlap(first.device, second.device)] == []


def _overlap(first: DeviceMatch, second: DeviceMatch) -> bool:
    return first.integration == second.integration and all(
        None in (one, other) or one == other for one, other in [(first.manufacturer, second.manufacturer), (first.model_id, second.model_id)]
    )


def test_profiles_that_fit_the_same_device_overlap() -> None:
    assert _overlap(DeviceMatch("mqtt", "Amina Distribution AS"), DeviceMatch("mqtt", "Amina Distribution AS", "amina S"))
    assert not _overlap(DeviceMatch("mqtt", "Amina Distribution AS"), DeviceMatch("mqtt", "Zaptec"))
    assert not _overlap(DeviceMatch("mqtt"), DeviceMatch("easee"))
