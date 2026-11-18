"""
fetch_live_ogd.py
Fetch real-time CPCB CAAQMS sensor telemetry from Open Government Data (data.gov.in)
Resource ID: 3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69
Uses http.client to prevent URL percent-encoding of square brackets.
"""
import os
import json
import http.client
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env with override=True so user's fresh key overrides any stale system env var
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path, override=True)

API_KEY = os.getenv("OGD_API_KEY")
if not API_KEY:
    raise ValueError("Missing OGD_API_KEY! Please set it in your .env file or as a GitHub Actions Secret.")
RESOURCE_ID = "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"

TARGET_CITIES = ["Delhi", "Bengaluru", "Mumbai", "Chennai", "Hyderabad", "Kolkata", "Ahmedabad"]

def fetch_city_pm25(city):
    conn = http.client.HTTPSConnection("api.data.gov.in", timeout=25)
    path = f"/resource/{RESOURCE_ID}?api-key={API_KEY}&format=json&filters[city]={city}&filters[pollutant_id]=PM2.5&limit=100"
    headers = {
        "User-Agent": "curl/7.88.1"
    }
    try:
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        if res.status == 200:
            payload = res.read().decode('utf-8')
            data = json.loads(payload)
            return data.get("records", [])
        else:
            print(f"[WARN] HTTP {res.status} for {city}")
            return []
    except Exception as e:
        print(f"[WARN] Exception for {city}: {e}")
        return []
    finally:
        conn.close()

def run():
    print(f"[INFO] Connecting to data.gov.in CPCB CAAQMS Live Gateway...")
    all_records = []
    city_summaries = {}

    for city in TARGET_CITIES:
        print(f"  -> Polling {city} stations...", end="", flush=True)
        recs = fetch_city_pm25(city)
        print(f" found {len(recs)} active PM2.5 records.")
        all_records.extend(recs)
        
        # Calculate city statistics
        vals = []
        for r in recs:
            try:
                val = float(r.get("avg_value"))
                vals.append(val)
            except (ValueError, TypeError):
                pass
                
        city_summaries[city] = {
            "station_count": len(recs),
            "mean_pm25": round(sum(vals) / len(vals), 1) if vals else None,
            "min_pm25": min(vals) if vals else None,
            "max_pm25": max(vals) if vals else None,
            "latest_update": recs[0].get("last_update") if recs else None
        }

    # Format structured output for BharatAIR Web
    output = {
        "source": "Open Government Data (data.gov.in) - CPCB CAAQMS Live Telemetry",
        "resource_id": RESOURCE_ID,
        "polled_at": datetime.now().isoformat(),
        "cities": city_summaries,
        "stations": [
            {
                "city": r.get("city"),
                "state": r.get("state"),
                "station": r.get("station"),
                "latitude": float(r.get("latitude")) if r.get("latitude") else None,
                "longitude": float(r.get("longitude")) if r.get("longitude") else None,
                "pm25": float(r.get("avg_value")) if r.get("avg_value") not in (None, "", "NA") else None,
                "pm25_min": float(r.get("min_value")) if r.get("min_value") not in (None, "", "NA") else None,
                "pm25_max": float(r.get("max_value")) if r.get("max_value") not in (None, "", "NA") else None,
                "last_update": r.get("last_update")
            }
            for r in all_records
        ]
    }

    repo_root = Path(__file__).resolve().parent.parent
    targets = [
        repo_root / "web" / "public" / "data" / "live_cpcb_telemetry.json",
        repo_root / "web" / "src" / "data" / "live_cpcb_telemetry.json",
        repo_root / "web" / "dist" / "data" / "live_cpcb_telemetry.json",
        repo_root.parent / "BharatAIR_Web" / "public" / "data" / "live_cpcb_telemetry.json",
        repo_root.parent / "BharatAIR_Web" / "src" / "data" / "live_cpcb_telemetry.json",
        repo_root.parent / "BharatAIR_Web" / "dist" / "data" / "live_cpcb_telemetry.json",
    ]

    written_count = 0
    for out_file in targets:
        if out_file.parent.parent.exists():
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2)
            written_count += 1
            print(f"[SUCCESS] Exported live telemetry to {out_file}")

    print(f"\n[SUCCESS] Successfully written {len(output['stations'])} live stations across {written_count} target paths!")
    print("\n--- LIVE CPCB AIR QUALITY SNAPSHOT (TODAY) ---")
    for city, stats in city_summaries.items():
        if stats["mean_pm25"] is not None:
            print(f"  • {city:12s}: Mean PM2.5 = {stats['mean_pm25']:5.1f} ug/m3  (Range: {stats['min_pm25']} - {stats['max_pm25']}) | Stations: {stats['station_count']} | Updated: {stats['latest_update']}")

if __name__ == "__main__":
    run()
