#!/usr/bin/env python3
"""
amazfit_fetch_decode.py
Pull one day from Huami/Zepp cloud and *decode* its base64 payloads.
"""

import argparse, base64, csv, datetime as dt, json, struct, requests
from pathlib import Path

BASE   = "https://api-mifit.huami.com"
HEAD   = {"appPlatform":"web",
          "appname":"com.xiaomi.hm.health",
          "User-Agent":"ZeppPython/1.7"}     # ≈ Zepp 6.10

# ---------- helpers ---------------------------------------------------------
def b64json(s: str) -> dict:
    """decode base64-encoded JSON → dict"""
    return json.loads(base64.b64decode(s + "==").decode())

def decode_hr_blob(b64: str):
    raw = base64.b64decode(b64)
    hr_values = []
    
    # Try different decoding approaches
    for off in range(0, len(raw), 2):
        if off + 1 < len(raw):
            value = struct.unpack_from("<H", raw, off)[0]
            
            # Filter out invalid values (65535 is often used as "no data")
            if value < 65535:
                # Some devices might store HR in different ranges
                if value > 300:  # If it's in the 300+ range, might need scaling
                    value = value // 10  # Scale down to get realistic BPM
                hr_values.append(value)
            else:
                hr_values.append(0)  # No data
        else:
            hr_values.append(0)
    
    return hr_values

def save(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2))

# ---------- fetchers --------------------------------------------------------
def band(token:str, uid:str, day:str):
    qs  = {"query_type":"detail", "userid":uid, "device_type":"android_phone",
           "from_date":day, "to_date":day}
    r = requests.get(f"{BASE}/v1/data/band_data.json",
                     headers=HEAD|{"apptoken":token}, params=qs, timeout=20)
    r.raise_for_status()
    return r.json()

def workouts(token:str):
    r = requests.get(f"{BASE}/v1/sport/run/history.json",
                     headers=HEAD|{"apptoken":token},
                     params={"source":"run.mifit.huami.com"}, timeout=20)
    r.raise_for_status();  return r.json()

def events(token:str, uid:str, ms_from:int, ms_to:int):
    r = requests.get(f"{BASE}/users/{uid}/events",
                     headers=HEAD|{"apptoken":token},
                     params={"eventType":"all","from":ms_from,"to":ms_to,"limit":1000},
                     timeout=20)
    r.raise_for_status();  return r.json().get("events",[])

# ---------- main ------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--uid",   required=True)
    ap.add_argument("--date",  help="YYYY-MM-DD (default=today)")
    ap.add_argument("--out",   default="amazfit_dump")
    args = ap.parse_args()

    day = args.date or dt.date.today().isoformat()
    out = Path(args.out); out.mkdir(exist_ok=True)

    # --- band detail --------------------------------------------------------
    bd = band(args.token, args.uid, day)
    save(out/f"band_{day}.raw.json", bd)          # raw dump for reference

    # summary is base64-JSON
    summary = b64json(bd["data"][0]["summary"])
    save(out/f"summary_{day}.json", summary)      # decoded summary for debugging
    
    # Extract step data
    steps = summary.get("stp", {}).get("ttl", 0)
    kcals = summary.get("stp", {}).get("cal", 0)
    
    # Calculate sleep duration from start/end times
    sleep_s = 0
    if "slp" in summary:
        slp = summary["slp"]
        if "st" in slp and "ed" in slp:
            # Calculate sleep duration in seconds
            sleep_s = slp["ed"] - slp["st"]
            print(f"Sleep: {slp['st']} → {slp['ed']} = {sleep_s}s ({sleep_s//60} min)")
        else:
            print(f"Available sleep fields: {list(slp.keys())}")
            # Fallback: try to find any numeric field that might be total sleep time
            for key, value in slp.items():
                if isinstance(value, (int, float)) and value > 0 and key not in ['st', 'ed']:
                    print(f"Using {key}={value} as sleep time")
                    sleep_s = value
                    break

    # decode HR blob
    hr_blob = decode_hr_blob(bd["data"][0]["data_hr"])
    
    # Debug: show some sample values
    non_zero = [v for v in hr_blob if v > 0]
    if non_zero:
        print(f"Heart rate sample values: {non_zero[:10]}...")
    else:
        print("No heart rate data found")
    
    with (out/f"heart_{day}.csv").open("w", newline="") as fp:
        w = csv.writer(fp); w.writerow(["minute","bpm"])
        w.writerows([(i,bpm) for i,bpm in enumerate(hr_blob)])

    # --- workouts -----------------------------------------------------------
    wk = workouts(args.token)
    runs_today = [r for r in wk.get("trackInfo",[])
                  if r.get("startTime","").startswith(day)]
    save(out/f"workouts_{day}.json", runs_today)

    # --- events -------------------------------------------------------------
    d   = dt.datetime.fromisoformat(day)
    ev  = events(args.token, args.uid,
                 int(d.timestamp()*1000),
                 int((d+dt.timedelta(days=1,seconds=-1)).timestamp()*1000))
    save(out/f"events_{day}.json", ev)

    # --- summary ------------------------------------------------------------
    print(f"[✓] {day}: steps {steps:,}  kcals {kcals:,}  "
          f"sleep {sleep_s//60} min  HR-samples {len(hr_blob)}  "
          f"runs {len(runs_today)}  events {len(ev)}")

if __name__ == "__main__":
    main() 