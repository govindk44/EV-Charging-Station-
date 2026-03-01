import math
from decimal import Decimal

EARTH_RADIUS_KM = 6371
OVERSTAY_FINE_PER_MINUTE = Decimal("5.00")
DC_FAST_SURCHARGE_PER_KWH = Decimal("2.00")

PEAK_START_HOUR = 18
PEAK_END_HOUR = 22
NIGHT_START_HOUR = 23
NIGHT_END_HOUR = 6

PEAK_MULTIPLIER = Decimal("1.20")
NIGHT_MULTIPLIER = Decimal("0.90")
NORMAL_MULTIPLIER = Decimal("1.00")


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points using Haversine formula."""
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    return EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


def get_pricing_multiplier(hour: int) -> Decimal:
    """Return dynamic pricing multiplier based on hour of day (0-23)."""
    if PEAK_START_HOUR <= hour < PEAK_END_HOUR:
        return PEAK_MULTIPLIER
    if hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR:
        return NIGHT_MULTIPLIER
    return NORMAL_MULTIPLIER


def get_pricing_label(hour: int) -> str:
    """Return human-readable pricing tier label."""
    if PEAK_START_HOUR <= hour < PEAK_END_HOUR:
        return "peak"
    if hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR:
        return "off-peak"
    return "normal"


