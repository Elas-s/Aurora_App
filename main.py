from fastapi import FastAPI, HTTPException

from sources import find_place, get_conditions, find_best_hour, get_tonight,

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
            detail = f"Couldn't find {name} in Iceland. Please try a place in Iceland, like Reykjavik or Akureyri."
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
    hours = get_tonight(lat, lon)
    return {"hours": hours, "best": find_best_hour(hours)}