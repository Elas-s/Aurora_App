from fastapi import FastAPI, HTTPException

from sources import find_place

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
