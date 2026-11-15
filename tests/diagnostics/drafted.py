"""Drafted files loaded as modules of the package they are drafted for, so their relative imports work wherever they are written."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

PROFILES_PACKAGE = "custom_components.kraftvakt.charger_profiles.profiles"
PROFILE_TESTS_PACKAGE = "tests.charger_profiles.profiles"


def load(path: Path, package: str) -> ModuleType:
    spec = spec_from_file_location(f"{package}.{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
