import httpx
from math import radians, sin , cos, asin, sqrt

#------------haversine formula-----------
def distance_km(lat1, lon1, lat2, lon2):
    """Distance in km between two points on Earth (haversine formula)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))
# ---------------- URLs ----------------
KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
STATIONS_URL = "https://api.vedur.is/weather/stations"

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
    """Turn a place name in Iceland into (lat, lon)."""
    settings = {"name": name, "count": 1, "countryCode": "IS"}
    response = httpx.get(GEO_URL, params=settings, timeout=10)
    response.raise_for_status()
    data = response.json()
    if "results" not in data:
        return None
    place = data["results"][0]
    return place["latitude"], place["longitude"]


# ---------------- Weather ----------------
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

#-----------------Stations------------------
def get_stations():
    """Fetch all active automatic weather stations in Iceland."""
    settings ={
        "active": "true",
        "station_type": "sj",
    }
    response = httpx.get(STATIONS_URL, params=settings, timeout=10)
    response.raise_for_status()
    return response.json()
#------------Nearest_station---------------------
def find_nearest_station(lat,long,stations):
    """Return (station, distance_km) of the station closest to (lat, lon)."""
    nearest = None
    best = float("inf")  # "infinity": any real distance beats it
    for station in stations:
        d = distance_km(lat,long,station["lat"],station["lon"])
        if d < best:
            best = d
            nearest = station
    return nearest, best




#--------------------------------------------



if __name__ == "__main__":
    time, kp_value = get_latest_kp(get_kp())
    print(f"Latest Kp: {kp_value} at {time}")

    place= find_place("Reykjanesbaer")
    if place is None:
        print(f"Try another place in iceland")
    else:
        lat, lon = place
        weather = get_weather(lat, lon)
        print("Cloud at 20:00:", weather["hourly"]["cloud_cover"][20])

        stations = get_stations()
        print(len(stations), stations[0]["name"])

        closest_station, closest_distance = find_nearest_station(lat,lon,stations)
        print(f"Nearest Station: {closest_station['name']},"
              f" Distance: {closest_distance:.1f}km")