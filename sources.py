"""Fetch the data the aurora app needs from NOAA, Open-Meteo and the Icelandic Met Office."""

from datetime import date, datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt

import httpx
from astral import Observer
from astral.moon import phase
from astral.sun import dawn, dusk, elevation

# ---------------- URLs ----------------
KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
STATIONS_URL = "https://api.vedur.is/weather/stations"
OBSERVATIONS_URL = "https://api.vedur.is/weather/observations/aws/10min/latest"
OVATION_URL = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"


# ---------------- Helpers ----------------
def distance_km(lat1, lon1, lat2, lon2):
    """Distance in km between two points on Earth (haversine formula)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


# ---------------- Aurora (Kp) ----------------
def get_kp():
    """Fetch the last 7.5 days of Kp readings from NOAA."""
    response = httpx.get(KP_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def get_latest_kp(readings):
    """Return (time, Kp) of the newest reading."""
    latest = readings[-1]
    return latest["time_tag"], latest["Kp"]


# ---------------- Aurora map (OVATION) ----------------
def get_ovation():
    """Fetch NOAA's latest aurora chance grid for the whole planet."""
    response = httpx.get(OVATION_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def find_aurora_chance(lat, lon, ovation):
    """Return the aurora chance (0-100) at the grid point nearest (lat, lon)."""
    grid_lon = round(lon) % 360  # NOAA longitudes go 0-359, not -180 to 180
    grid_lat = round(lat)
    for point in ovation["coordinates"]:  # each point is [lon, lat, chance]
        if point[0] == grid_lon and point[1] == grid_lat:
            return point[2]
    return None


# ---------------- Darkness (Sun & Moon) ----------------
def get_sun_elevation(lat, lon):
    """Return how many degrees the sun is above (+) or below (-) the horizon now."""
    observer = Observer(latitude=lat, longitude=lon)
    now = datetime.now(timezone.utc)
    return elevation(observer, now)


def is_dark(sun_elevation):
    """Return True if the sun is low enough (below -12°) for aurora."""
    return sun_elevation < -12


def get_dark_window(lat, lon):
    """Return (start, end) of tonight's dark window in UTC, or None in summer."""
    observer = Observer(latitude=lat, longitude=lon)
    today = date.today()
    tomorrow = today + timedelta(days=1)
    try:
        start = dusk(observer, today, depression=12)
        end = dawn(observer, tomorrow, depression=12)
    except ValueError:
        return None  # summer: the sun never gets 12° below the horizon
    return start, end


def get_moon_phase():
    """Return today's moon phase: 0 = new moon, 14 = full moon, 28 = new again."""
    return phase(date.today())


def moon_is_bright(moon_phase):
    """Return True around full moon (phase 10-18), when moonlight hides faint aurora."""
    return 10 <= moon_phase <= 18


# ---------------- Place -> coordinates ----------------
def find_place(name):
    """Turn a place name in Iceland into (lat, lon), or None if not found."""
    settings = {"name": name, "count": 1, "countryCode": "IS"}
    response = httpx.get(GEO_URL, params=settings, timeout=10)
    response.raise_for_status()
    data = response.json()
    if "results" not in data:
        return None
    place = data["results"][0]
    return place["latitude"], place["longitude"]


# ---------------- Weather forecast ----------------
def get_weather(lat, lon):
    """Fetch today's hourly forecast for one location."""
    settings = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "cloud_cover,precipitation,snowfall,wind_gusts_10m",
        "timezone": "Atlantic/Reykjavik",
        "forecast_days": 1,
    }
    response = httpx.get(WEATHER_URL, params=settings, timeout=10)
    response.raise_for_status()
    return response.json()


# ---------------- Weather stations ----------------
def get_stations():
    """Fetch all active automatic weather stations in Iceland."""
    settings = {"active": "true", "station_type": "sj"}
    response = httpx.get(STATIONS_URL, params=settings, timeout=10)
    response.raise_for_status()
    return response.json()


def get_latest_observations():
    """Fetch the latest 10-minute observation from every station."""
    response = httpx.get(OBSERVATIONS_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def filter_reporting_stations(stations, observations):
    """Keep only the stations that sent an observation."""
    reporting_ids = []
    for obs in observations:
        reporting_ids.append(obs["station"])

    reporting_stations = []
    for station in stations:
        if station["station"] in reporting_ids:
            reporting_stations.append(station)
    return reporting_stations


def find_nearest_station(lat, lon, stations):
    """Return (station, distance_km) of the station closest to (lat, lon)."""
    nearest = None
    best = float("inf")  # "infinity": any real distance beats it
    for station in stations:
        d = distance_km(lat, lon, station["lat"], station["lon"])
        if d < best:
            best = d
            nearest = station
    return nearest, best


def find_observation(station_id, observations):
    """Return the observation for one station, or None if it has none."""
    for obs in observations:
        if obs["station"] == station_id:
            return obs
    return None


# ---------------- Everything at once ----------------
def get_conditions(lat, lon):
    """Return all aurora conditions for one place as a dict."""
    # Clouds: Open-Meteo forecast for the current hour
    weather = get_weather(lat, lon)
    hour = datetime.now(timezone.utc).hour  # Iceland time = UTC all year
    cloud_now = weather["hourly"]["cloud_cover"][hour]

    # Aurora: NOAA OVATION chance at our grid point
    ovation = get_ovation()
    chance = find_aurora_chance(lat, lon, ovation)

    # Darkness: where the sun is now, and tonight's dark window
    sun = get_sun_elevation(lat, lon)
    dark = is_dark(sun)
    window = get_dark_window(lat, lon)

    # Moon: a bright moon washes out faint aurora
    moon = get_moon_phase()
    bright_moon = moon_is_bright(moon)

    # Temperature and wind: nearest station that actually reports
    stations = get_stations()
    observations = get_latest_observations()
    reporting = filter_reporting_stations(stations, observations)
    station, distance = find_nearest_station(lat, lon, reporting)

    if station is None:
        obs = None
    else:
        obs = find_observation(station["station"], observations)

    if obs is None:
        station_info = None
    else:
        station_info = {
            "name": station["name"],
            "distance_km": round(distance, 1),
            "temperature": obs["t"],
            "wind": obs["f"],
            "wind_direction": obs["d_txt"],
        }

    return {
        "aurora_chance": chance,
        "cloud_cover": cloud_now,
        "sun_elevation": round(sun, 1),
        "is_dark": dark,
        "dark_window": window,
        "moon_phase": round(moon, 1),
        "bright_moon": bright_moon,
        "station": station_info,
    }


# ---------------- Try it out ----------------
if __name__ == "__main__":
    PLACE = "Reykjanesbaer"

    time, kp_value = get_latest_kp(get_kp())
    print(f"Latest Kp: {kp_value} at {time}")

    place = find_place(PLACE)
    if place is None:
        print("Try another place in Iceland")
    else:
        lat, lon = place
        conditions = get_conditions(lat, lon)

        print(f"Right now in {PLACE}:")
        print(f"  Aurora chance: {conditions['aurora_chance']}%")
        print(f"  Cloud: {conditions['cloud_cover']}%")
        print(f"  Dark enough: {conditions['is_dark']}")
        station = conditions["station"]
        if station is None:
            print("  No station measurements right now")
        else:
            print(f"  Temperature: {station['temperature']}°C at {station['name']}")
            print(f"  Wind: {station['wind']} m/s ({station['wind_direction']})")


