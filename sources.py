import httpx

KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"

def get_kp():
    response = httpx.get(KP_URL, timeout = 10)
    response.raise_for_status()
    return response.json()

def get_latest_kp(readings):
    latest_kp = readings[-1]
    return latest_kp['time_tag'],latest_kp['Kp']

if __name__ == "__main__":
    kp = get_kp()
    time, kp_value = get_latest_kp(kp)

    print(type(kp),len(kp))
    print(kp[:3])

    print(f"Latest Kp: {kp_value} at {time}")




