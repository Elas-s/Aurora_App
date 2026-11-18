"""Fetch the data the aurora app needs from NOAA, Open-Meteo and the Icelandic Met Office."""

from datetime import date, datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt

import httpx
from astral import Observer
from astral.moon import phase
from astral.sun import dawn, dusk, elevation

from spots import DARK_SPOTS

# ---------------- URLs ----------------
KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
KP_FORECAST_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
STATIONS_URL = "https://api.vedur.is/weather/stations"
OBSERVATIONS_URL = "https://api.vedur.is/weather/observations/aws/10min/latest"
OVATION_URL = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"

# ---------------- Settings ----------------
BRIGHT_MOON_FACTOR = 0.7  # moonlight hides faint aurora, not strong ones
GREAT_KP = 5  # in Iceland, Kp 5+ is already a great night
MAX_SPOT_KM = 50  # don't send people on a long night drive


# ---------------- Helpers ----------------
def distance_km(lat1, lon1, lat2, lon2):
    """Distance in km between two points on Earth (haversine formula)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


# ---------------- Aurora (Kp) ----------------
def get_kp():
    """Fetch the last 7 days of Kp readings from NOAA."""
    response = httpx.get(KP_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def get_kp_forecast():
    """Fetch NOAA's Kp readings and forecast for the next 3 days."""
    response = httpx.get(KP_FORECAST_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def get_latest_kp(readings):
    """Return (time, Kp) of the newest reading."""
    latest = readings[-1]
    return latest["time_tag"], latest["Kp"]


def find_kp(hour, forecast):
    """Return the forecast Kp for the 3-hour slot that contains this hour."""
    slot = hour.replace(hour=hour.hour // 3 * 3)  # 22:00 -> 21:00
    label = slot.strftime("%Y-%m-%dT%H:00:00")  # same shape as NOAA's time_tag
    for reading in forecast:
        if reading["time_tag"] == label:
            return reading["kp"]  # lowercase k in the forecast data!
    return None


def kp_to_factor(kp):
    """Turn Kp (0-9) into a 0-1 aurora factor for Iceland."""
    return min(kp / GREAT_KP, 1)


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


def get_dark_hours(window):
    """Return every whole hour inside tonight's dark window."""
    start, end = window
    hour = start.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    hours = []
    while hour <= end:
        hours.append(hour)
        hour = hour + timedelta(hours=1)
    return hours


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
    """Fetch the hourly forecast for today and tomorrow for one location."""
    settings = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "cloud_cover,precipitation,snowfall,wind_gusts_10m",
        "timezone": "Atlantic/Reykjavik",
        "forecast_days": 2,  # the night goes past midnight
    }
    response = httpx.get(WEATHER_URL, params=settings, timeout=10)
    response.raise_for_status()
    return response.json()


def find_cloud(hour, weather):
    """Return the forecast cloud cover (%) for one hour."""
    label = hour.strftime("%Y-%m-%dT%H:00")  # same shape as Open-Meteo's times
    times = weather["hourly"]["time"]
    i = times.index(label)
    return weather["hourly"]["cloud_cover"][i]


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


# ---------------- Chance score ----------------
def calculate_score(aurora_chance, cloud_cover, is_dark, bright_moon):
    """Return a 0-100 chance of actually seeing the aurora."""
    aurora = aurora_chance / 100
    clear_sky = (100 - cloud_cover) / 100
    dark = 1 if is_dark else 0
    moon = BRIGHT_MOON_FACTOR if bright_moon else 1
    return round(aurora * clear_sky * dark * moon * 100)


def get_tonight(lat, lon, forecast=None):
    """Return tonight's hour-by-hour scores, or [] when it never gets dark.

    Pass in a Kp forecast you already fetched to avoid fetching it again.
    """
    window = get_dark_window(lat, lon)
    if window is None:
        return []
    weather = get_weather(lat, lon)
    if forecast is None:
        forecast = get_kp_forecast()
    bright_moon = moon_is_bright(get_moon_phase())

    hours = []
    for hour in get_dark_hours(window):
        cloud = find_cloud(hour, weather)
        kp = find_kp(hour, forecast)
        score = calculate_score(kp_to_factor(kp) * 100, cloud, True, bright_moon)
        hours.append({"time": hour.strftime("%H:%M"), "cloud": cloud, "kp": kp, "score": score})
    return hours


def find_best_hour(hours):
    """Return the hour with the highest score, or None if there are no hours."""
    best = None
    for hour in hours:
        if best is None or hour["score"] > best["score"]:
            best = hour
    return best


# ---------------- Nearby dark spots ----------------
def find_nearby_spots(lat, lon, spots):
    """Return the spots within MAX_SPOT_KM of (lat, lon)."""
    nearby = []
    for spot in spots:
        if distance_km(lat, lon, spot["lat"], spot["lon"]) <= MAX_SPOT_KM:
            nearby.append(spot)
    return nearby

def find_best_spot(lat, lon, spots):
    """Return (spot, best_hour) for the best nearby spot tonight, or (None, None)."""
    forecast = get_kp_forecast()          # 📨 fetch Kp ONCE
    best_spot = None
    best_hour = None
    for spot in find_nearby_spots(lat, lon, spots):
        hours = get_tonight(spot["lat"], spot["lon"], forecast)   # ♻️ reuse it
        hour = find_best_hour(hours)
        if hour is not None and (best_hour is None or hour["score"] > best_hour["score"]):
            best_spot = spot
            best_hour = hour
    return best_spot, best_hour


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
        "score": calculate_score(chance, cloud_now, dark, bright_moon),
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

        # Right now
        conditions = get_conditions(lat, lon)
        print(f"Right now in {PLACE}:")
        print(f"  Aurora chance: {conditions['aurora_chance']}%")
        print(f"  Cloud: {conditions['cloud_cover']}%")
        print(f"  Dark enough: {conditions['is_dark']}")
        print(f"  Chance right now: {conditions['score']}%")
        station = conditions["station"]
        if station is None:
            print("  No station measurements right now")
        else:
            print(f"  Temperature: {station['temperature']}°C at {station['name']}")
            print(f"  Wind: {station['wind']} m/s ({station['wind_direction']})")

        # Tonight
        tonight = get_tonight(lat, lon)
        print(f"Tonight in {PLACE}:")
        for h in tonight:
            print(f"  {h['time']}  cloud {h['cloud']}%  Kp {h['kp']}  score {h['score']}%")
        best = find_best_hour(tonight)
        if best is None:
            print("  It doesn't get dark enough tonight")
        else:
            print(f"  Best time: {best['time']} ({best['score']}%)")

        # Best nearby spot
        spot, hour = find_best_spot(lat, lon, DARK_SPOTS)
        if spot is None:
            print("No good spot nearby tonight")
        else:
            print(f"It is advised to see the aurora at {spot['name']} around {hour['time']}.")
            print(f"The clouds there are {hour['cloud']}% and your chance is {hour['score']}%.")