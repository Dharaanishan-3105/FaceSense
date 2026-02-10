"""
Location utilities for campus verification - anti-fraud feature.
Uses Haversine formula for distance calculation.
"""
import math
from typing import Tuple, Optional


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two lat/lon points."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def is_within_campus(current_lat: float, current_lon: float,
                     campus_lat: float, campus_lon: float,
                     radius_meters: float = 500) -> bool:
    """Check if current location is within campus boundary."""
    dist = haversine_distance(current_lat, current_lon, campus_lat, campus_lon)
    return dist <= radius_meters


def is_near_registered_location(current_lat: float, current_lon: float,
                                 reg_lat: float, reg_lon: float,
                                 threshold_meters: float = 100) -> bool:
    """Check if current location is near the user's registered location (anti-fraud)."""
    dist = haversine_distance(current_lat, current_lon, reg_lat, reg_lon)
    return dist <= threshold_meters
