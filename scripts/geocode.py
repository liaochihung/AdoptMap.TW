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
    GEOCODE_OVERRIDES_FILE,
)


def _load_cache() -> dict:
    if os.path.exists(GEOCODE_CACHE_FILE):
        with open(GEOCODE_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _load_overrides() -> dict:
    if os.path.exists(GEOCODE_OVERRIDES_FILE):
        with open(GEOCODE_OVERRIDES_FILE, encoding="utf-8") as f:
            return json.load(f)
    print(f"  ⚠ 找不到 geocode overrides 檔案：{GEOCODE_OVERRIDES_FILE}（手動覆寫功能停用）")
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
    import re as _re
    headers = {"User-Agent": NOMINATIM_USER_AGENT}

    def _query(q: str) -> tuple[float, float] | None:
        params = {
            "q": q,
            "format": "json",
            "limit": 1,
            "countrycodes": "tw",
            "viewbox": TAICHUNG_VIEWBOX,
            "bounded": 0,
        }
        try:
            resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            results = resp.json()
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
        except Exception as e:
            print(f"  Nominatim 請求失敗：{q}  ({e})")
        return None

    # 嘗試原始地址
    result = _query(address)
    if result:
        return result

    # 若含逗號分隔多門牌（如 78,80號），先取第一個號碼再試
    # 例：台中市南屯區五權西路二段78,80號 → 台中市南屯區五權西路二段78號
    single_no = _re.sub(r"(\d+)[,，]\d+號", r"\1號", address)
    if single_no != address:
        time.sleep(NOMINATIM_DELAY)
        result = _query(single_no)
        if result:
            return result

    # 若含「號」，移除號碼後再試（Nominatim 對中文門牌號支援差）
    # 例：台中市西屯區西屯路三段92-1號 → 台中市西屯區西屯路三段
    stripped = _re.sub(r"\d[\d\-,，]*號.*$", "", address).strip()
    if stripped and stripped != address:
        time.sleep(NOMINATIM_DELAY)
        result = _query(stripped)
        if result:
            return result

    # 移除「台中市XX區」前綴，只留路段（部分路名 Nominatim 需省略縣市才能找到）
    # 例：台中市南屯區五權西路二段 → 五權西路二段 南屯 台中
    no_prefix = _re.sub(r"^(?:台中市|臺中市)(\w+區)", r"\1", stripped or address)
    if no_prefix != (stripped or address):
        # 轉為「路段 區名 台中」格式
        district_m = _re.match(r"(\w+區)(.*)", no_prefix)
        if district_m:
            query_alt = district_m.group(2).strip() + " " + district_m.group(1) + " 台中"
            time.sleep(NOMINATIM_DELAY)
            result = _query(query_alt)
            if result:
                return result

    return None


def geocode_addresses(addresses: list[str]) -> dict[str, dict]:
    """
    對 addresses 清單進行 geocoding，回傳 {地址: {lat, lng}}。
    - KNOWN_LOCATIONS 中的地址直接使用固定座標，不查詢 API。
    - 已快取的地址直接使用快取。
    - 新地址查詢 Nominatim，間隔 NOMINATIM_DELAY 秒。
    """
    cache = _load_cache()
    overrides = _load_overrides()
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

        # 手動覆寫座標（優先於快取與 Nominatim）
        if address in overrides:
            loc = overrides[address]
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
