"""The public service keys are stable and independent of module filenames."""
from .contracts import ServiceModule
from .modules.baby_names import BabyNamesService
from .modules.compatibility import CompatibilityService
from .modules.forecast import ForecastService
from .modules.gemstone import GemstoneService
from .modules.horoscope import HoroscopeService
from .modules.numerology import NumerologyService
from .modules.vastu import VastuService

SERVICES: dict[str, ServiceModule] = {
    "horoscope": HoroscopeService(),
    "numerology": NumerologyService(),
    "compatibility": CompatibilityService(),
    "vastu": VastuService(),
    "gemstone": GemstoneService(),
    "baby-names": BabyNamesService(),
    "forecast": ForecastService(),
}


def get_service(key: str) -> ServiceModule:
    """Return the registered service, raising KeyError for unknown keys."""
    return SERVICES[key]