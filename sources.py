import httpx

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