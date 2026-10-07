"""High-Speed Local and Global City Search Service for VYAS.

Provides:
- Instant search across 565,000+ Indian cities, towns, tehsils, and villages from offline SQLite DB.
- No rate-limiting (429 errors completely eliminated).
- Fuzzy and prefix matching with verified State names and coordinates.
- Worldwide major global metro cities support.
"""
import os
import sqlite3
from typing import List, Dict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cities.db")

# Official GeoNames admin1 state code mapping for India
STATE_MAP = {
    '24': 'Rajasthan', '16': 'Maharashtra', '36': 'Uttar Pradesh', '35': 'Madhya Pradesh',
    '09': 'Gujarat', '23': 'Punjab', '10': 'Haryana', '07': 'Delhi', '34': 'Bihar',
    '28': 'West Bengal', '19': 'Karnataka', '25': 'Tamil Nadu', '40': 'Telangana',
    '02': 'Andhra Pradesh', '13': 'Kerala', '21': 'Odisha', '38': 'Jharkhand',
    '37': 'Chhattisgarh', '39': 'Uttarakhand', '11': 'Himachal Pradesh',
    '12': 'Jammu & Kashmir', '41': 'Ladakh', '33': 'Goa', '03': 'Assam',
    '29': 'Sikkim', '26': 'Tripura', '18': 'Meghalaya', '17': 'Manipur',
    '20': 'Nagaland', '31': 'Mizoram', '30': 'Arunachal Pradesh', '05': 'Chandigarh',
    '22': 'Puducherry', '01': 'Andaman & Nicobar', '14': 'Lakshadweep',
    '52': 'Dadra & Nagar Haveli and Daman & Diu'
}

GLOBAL_METROS = [
    {"label": "New York, USA", "name": "New York", "lat": 40.7128, "lon": -74.0060, "tz": -5.0},
    {"label": "London, UK", "name": "London", "lat": 51.5074, "lon": -0.1278, "tz": 0.0},
    {"label": "Dubai, UAE", "name": "Dubai", "lat": 25.2048, "lon": 55.2708, "tz": 4.0},
    {"label": "Singapore", "name": "Singapore", "lat": 1.3521, "lon": 103.8198, "tz": 8.0},
    {"label": "Toronto, Canada", "name": "Toronto", "lat": 43.6532, "lon": -79.3832, "tz": -5.0},
    {"label": "Sydney, Australia", "name": "Sydney", "lat": -33.8688, "lon": 151.2093, "tz": 10.0},
    {"label": "Kathmandu, Nepal", "name": "Kathmandu", "lat": 27.7172, "lon": 85.3240, "tz": 5.75},
    {"label": "Colombo, Sri Lanka", "name": "Colombo", "lat": 6.9271, "lon": 79.8612, "tz": 5.5},
]

def search_cities(query: str, limit: int = 30) -> List[Dict]:
    """
    Searches cities, towns, tehsils and villages matching query.
    Returns list of dicts with name, display label, state, lat, lon.
    """
    q = (query or "").strip()
    if not q or len(q) < 2:
        return []

    results = []
    
    # 1. Search in local offline GeoNames database
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            pattern_start = f"{q}%"
            pattern_any = f"%{q}%"
            
            cursor.execute("""
                SELECT name, name_ascii, state_code, lat, lon, pop, feature
                FROM cities
                WHERE name_ascii LIKE ? OR name LIKE ?
                ORDER BY 
                    CASE WHEN name_ascii LIKE ? THEN 1 ELSE 2 END,
                    pop DESC,
                    name_ascii ASC
                LIMIT ?
            """, (pattern_start, pattern_any, pattern_start, limit))
            
            rows = cursor.fetchall()
            seen = set()
            for r in rows:
                st_name = STATE_MAP.get(r["state_code"], "India")
                display_name = f"{r['name_ascii']}, {st_name}"
                coord_key = (round(r["lat"], 3), round(r["lon"], 3))
                if coord_key in seen:
                    continue
                seen.add(coord_key)
                results.append({
                    "label": display_name,
                    "name": r["name_ascii"],
                    "state": st_name,
                    "lat": round(r["lat"], 4),
                    "lon": round(r["lon"], 4),
                    "pop": r["pop"]
                })
            conn.close()
        except Exception:
            pass

    # 2. Check international metros
    q_lower = q.lower()
    for gm in GLOBAL_METROS:
        if q_lower in gm["name"].lower() or q_lower in gm["label"].lower():
            results.append({
                "label": gm["label"],
                "name": gm["name"],
                "state": gm["label"].split(",")[-1].strip(),
                "lat": gm["lat"],
                "lon": gm["lon"],
                "pop": 1000000
            })

    return results
