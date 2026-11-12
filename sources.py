"""Fetch the data the aurora app needs from NOAA, Open-Meteo and the Icelandic Met Office."""

from datetime import datetime
from math import asin, cos, radians, sin, sqrt

import httpx

# ---------------- URLs ----------------
KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
STATIONS_URL = "https://api.vedur.is/weather/stations"
OBSERVATIONS_URL = "https://api.vedur.is/weather/observations/aws/10min/latest"


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

        # Clouds: Open-Meteo forecast for the current hour
        weather = get_weather(lat, lon)
        hour = datetime.now().hour  # the index in the hourly lists is the hour
        cloud_now = weather["hourly"]["cloud_cover"][hour]

        # Temperature and wind: nearest station that actually reports
        stations = get_stations()
        observations = get_latest_observations()
        reporting = filter_reporting_stations(stations, observations)
        station, distance = find_nearest_station(lat, lon, reporting)
        obs = find_observation(station["station"], observations)

        print(f"Right now in {PLACE}:")
        print(f"  Cloud: {cloud_now}%")
        if obs is None:
            print("  No station measurements right now")
        else:
            print(f"  Temperature: {obs['t']}°C")
            print(f"  Wind: {obs['f']} m/s ({obs['d_txt']})")
            print(f"  Measured at {station['name']}, {distance:.1f} km away")
