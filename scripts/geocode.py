# scripts/geocode.py
"""
地址轉經緯度（Nominatim），含本地快取。
"""

import json
import os
import time
import requests
from config import (
    NOMINATIM_URL,
    NOMINATIM_USER_AGENT,
    NOMINATIM_DELAY,
    TAICHUNG_VIEWBOX,
    GEOCODE_CACHE_FILE,
    GEOCODE_FAILURES_LOG,
    KNOWN_LOCATIONS,
)


def _load_cache() -> dict:
    if os.path.exists(GEOCODE_CACHE_FILE):
        with open(GEOCODE_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(GEOCODE_CACHE_FILE), exist_ok=True)
    with open(GEOCODE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _log_failure(address: str, reason: str) -> None:
    os.makedirs(os.path.dirname(GEOCODE_FAILURES_LOG), exist_ok=True)
    with open(GEOCODE_FAILURES_LOG, "a", encoding="utf-8") as f:
        f.write(f"{address}\t{reason}\n")


def _query_nominatim(address: str) -> tuple[float, float] | None:
    """向 Nominatim 查詢一個地址，回傳 (lat, lng) 或 None。"""
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "tw",
        "viewbox": TAICHUNG_VIEWBOX,
        "bounded": 0,  # 0 = 超出 viewbox 也可回傳，但優先 viewbox 內
    }
    headers = {"User-Agent": NOMINATIM_USER_AGENT}
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        results = resp.json()
        if results:
            lat = float(results[0]["lat"])
            lng = float(results[0]["lon"])
            return lat, lng
    except Exception as e:
        print(f"  Nominatim 請求失敗：{address}  ({e})")
    return None


def geocode_addresses(addresses: list[str]) -> dict[str, dict]:
    """
    對 addresses 清單進行 geocoding，回傳 {地址: {lat, lng}}。
    - KNOWN_LOCATIONS 中的地址直接使用固定座標，不查詢 API。
    - 已快取的地址直接使用快取。
    - 新地址查詢 Nominatim，間隔 NOMINATIM_DELAY 秒。
    """
    cache = _load_cache()
    result = {}

    new_queries = 0
    for address in addresses:
        if not address:
            continue

        # 已知固定座標（收容所）
        if address in KNOWN_LOCATIONS:
            loc = KNOWN_LOCATIONS[address]
            result[address] = {"lat": loc["lat"], "lng": loc["lng"]}
            continue

        # 快取命中
        if address in cache:
            result[address] = cache[address]
            continue

        # 需要查詢
        print(f"  Geocoding: {address}")
        coords = _query_nominatim(address)
        if coords:
            lat, lng = coords
            entry = {"lat": lat, "lng": lng}
            cache[address] = entry
            result[address] = entry
            new_queries += 1
        else:
            print(f"  ⚠ 無法解析地址：{address}")
            _log_failure(address, "nominatim returned no results")
            # 仍放入 cache 避免重複查詢（用 None 標記失敗）
            cache[address] = None

        time.sleep(NOMINATIM_DELAY)

    if new_queries > 0:
        _save_cache(cache)
        print(f"  Geocoding 完成，新查詢 {new_queries} 筆，已更新快取")

    return result
