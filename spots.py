"""Well-known dark places to watch the aurora in Iceland.

Picked from places that several travel guides recommend (Visit Reykjanes,
Guide to Iceland, Perlan, Aurora Reykjavik, Golden Circle Day Tours).
Coordinates are checked on Wikipedia or a travel guide, unless the comment says "~ approx".
"""

DARK_SPOTS = [
    # ---- Reykjanes peninsula (near Keflavík airport) ----
    {"name": "Garðskagi lighthouse", "region": "Reykjanes", "lat": 64.082, "lon": -22.690},
    {"name": "Reykjanes lighthouse", "region": "Reykjanes", "lat": 63.816, "lon": -22.704},
    {"name": "Bridge Between Continents", "region": "Reykjanes", "lat": 63.868, "lon": -22.676},  # ~ approx
    {"name": "Krýsuvík", "region": "Reykjanes", "lat": 63.895, "lon": -22.056},
    {"name": "Kleifarvatn", "region": "Reykjanes", "lat": 63.925, "lon": -21.980},

    # ---- Capital area ----
    {"name": "Grótta lighthouse", "region": "Capital area", "lat": 64.164, "lon": -22.022},  # ~ approx
    {"name": "Hvalfjörður", "region": "Capital area", "lat": 64.383, "lon": -21.667},

    # ---- Golden Circle ----
    {"name": "Þingvellir", "region": "Golden Circle", "lat": 64.254, "lon": -21.037},
    {"name": "Laugarvatn", "region": "Golden Circle", "lat": 64.211, "lon": -20.711},
    {"name": "Geysir", "region": "Golden Circle", "lat": 64.314, "lon": -20.300},
    {"name": "Gullfoss", "region": "Golden Circle", "lat": 64.326, "lon": -20.121},

    # ---- South coast ----
    {"name": "Seljalandsfoss", "region": "South", "lat": 63.616, "lon": -19.993},
    {"name": "Skógafoss", "region": "South", "lat": 63.532, "lon": -19.511},
    {"name": "Reynisfjara beach", "region": "South", "lat": 63.404, "lon": -19.045},  # ~ approx
    {"name": "Vík", "region": "South", "lat": 63.417, "lon": -19.000},

    # ---- South-east ----
    {"name": "Jökulsárlón glacier lagoon", "region": "South-east", "lat": 64.070, "lon": -16.212},
    {"name": "Vestrahorn (Stokksnes)", "region": "South-east", "lat": 64.248, "lon": -14.995},  # ~ approx

    # ---- West (Snæfellsnes) ----
    {"name": "Kirkjufell", "region": "Snæfellsnes", "lat": 64.941, "lon": -23.306},
    {"name": "Búðir black church", "region": "Snæfellsnes", "lat": 64.833, "lon": -23.550},

    # ---- North-west ----
    {"name": "Hvítserkur", "region": "North-west", "lat": 65.606, "lon": -20.636},

    # ---- Westfjords ----
    {"name": "Dynjandi", "region": "Westfjords", "lat": 65.733, "lon": -23.199},

    # ---- North ----
    {"name": "Goðafoss", "region": "North", "lat": 65.683, "lon": -17.550},  # ~ approx
    {"name": "Mývatn", "region": "North", "lat": 65.600, "lon": -17.000},
    {"name": "Dettifoss", "region": "North-east", "lat": 65.815, "lon": -16.384},
    {"name": "Arctic Henge (Raufarhöfn)", "region": "North-east", "lat": 66.459, "lon": -15.947},  # ~ approx

    # ---- East ----
    {"name": "Seyðisfjörður", "region": "East", "lat": 65.263, "lon": -14.009},
]
