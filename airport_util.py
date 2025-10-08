import math
from data import AirportDto
from enum import Enum

class CompassDirection(Enum):
    N = 'N'
    NE = 'NE'
    E = 'E'
    SE = 'SE'
    S = 'S'
    SW = 'SW'
    W = 'W'
    NW = 'NW'

def calculate_distance_km(a: AirportDto, b: AirportDto) -> float:
    lat1, lon1 = math.radians(float(a.latitude)), math.radians(float(a.longitude))
    lat2, lon2 = math.radians(float(b.latitude)), math.radians(float(b.longitude))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))

    # Earth's radius in kilometers
    r = 6371

    return r * c

def calculate_bearing(from_airport: AirportDto, to_airport: AirportDto) -> float:
    lat1, lon1 = math.radians(float(from_airport.latitude)), math.radians(float(from_airport.longitude))
    lat2, lon2 = math.radians(float(to_airport.latitude)), math.radians(float(to_airport.longitude))

    dlon = lon2 - lon1

    x = math.sin(dlon) * math.cos(lat2)
    y = (math.cos(lat1) * math.sin(lat2) -
         math.sin(lat1) * math.cos(lat2) * math.cos(dlon))

    initial_bearing = math.atan2(x, y)

    # Convert from radians to degrees and normalize to 0-360
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

def bearing_to_compass_direction(bearing: float) -> CompassDirection:
    directions = [
        (0, CompassDirection.N),
        (45, CompassDirection.NE),
        (90, CompassDirection.E),
        (135, CompassDirection.SE),
        (180, CompassDirection.S),
        (225, CompassDirection.SW),
        (270, CompassDirection.W),
        (315, CompassDirection.NW),
        (360, CompassDirection.N)
    ]

    for angle, direction in directions:
        if bearing < angle + 22.5:
            return direction

    return CompassDirection.N  # Fallback, should not reach here

def get_direction(from_airport: AirportDto, to_airport: AirportDto) -> CompassDirection:
    bearing = calculate_bearing(from_airport, to_airport)
    return bearing_to_compass_direction(bearing)