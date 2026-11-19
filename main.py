from fastapi import FastAPI, HTTPException

from sources import (find_best_hour, find_best_spot, find_place, get_conditions,
                     get_kp_forecast, get_moon_phase, get_tips, get_tonight, moon_is_bright)
from spots import DARK_SPOTS

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Aurora API is alive"}


@app.get("/place")
def get_place(name: str):
    coordinates = find_place(name)
    if coordinates is None:
        raise HTTPException(
            status_code=404,
            detail=f"Couldn't find {name} in Iceland. Please try a place in Iceland, like Reykjavik or Akureyri."
        )
    lat, lon = coordinates
    return {"name": name, "lat": lat, "lon": lon}


@app.get("/conditions")
def conditions(place: str):
    coordinates = find_place(place)
    if coordinates is None:
        raise HTTPException(status_code=404, detail=f"Couldn't find {place} in Iceland.")
    lat, lon = coordinates
    return get_conditions(lat, lon)


@app.get("/tonight")
def tonight(place: str):
    coordinates = find_place(place)
    if coordinates is None:
        raise HTTPException(status_code=404, detail=f"Couldn't find {place} in Iceland.")
    lat, lon = coordinates
    forecast = get_kp_forecast()
    hours = get_tonight(lat, lon, forecast)
    spot, spot_hour = find_best_spot(lat, lon, DARK_SPOTS, forecast)
    bright_moon = moon_is_bright(get_moon_phase())

    if spot_hour is None:
        tips = []  # summer, or no dark spot nearby: nothing to advise
    else:
        tips = get_tips(spot_hour, bright_moon)

    return {
        "hours": hours,
        "best": find_best_hour(hours),
        "best_spot": {"spot": spot, "hour": spot_hour},
        "tips": tips,
    }