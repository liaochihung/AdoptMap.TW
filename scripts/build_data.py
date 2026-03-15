# scripts/build_data.py
"""
主控腳本：呼叫 fetch_animals、scrape_taichung、geocode，產出 animals.json 與 locations.json。
由 GitHub Actions 每日執行。
資料來源：
  1. 農業部 Open Data API（台中市收容所）
  2. 台中市動保處網站爬蟲（中途動物醫院、益起認養吧）
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 切換工作目錄到專案根目錄（scripts/ 的上一層）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

from fetch_animals import fetch_animals
from scrape_taichung import scrape_animals
from geocode import geocode_addresses
from config import KNOWN_LOCATIONS, OUTPUT_DIR, ALL_CITIES, ALL_TAIWAN

TZ_TAIPEI = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(TZ_TAIPEI).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def _slugify_name(name: str) -> str:
    """把地址/名稱轉成合法的 location id 字串。"""
    import re
    name = re.sub(r"[^\w\u4e00-\u9fff]", "_", name)
    return name.strip("_")[:40]


def build_locations(animals: list[dict], coords: dict) -> list[dict]:
    """
    依動物的 _geo_address 分組，組出 locations 清單。
    """
    loc_map: dict[str, dict] = {}

    for animal in animals:
        geo_addr = animal["_geo_address"]
        if not geo_addr:
            geo_addr = "__unknown__"

        if geo_addr not in loc_map:
            # 固定座標收容所
            if geo_addr in KNOWN_LOCATIONS:
                known = KNOWN_LOCATIONS[geo_addr]
                loc_map[geo_addr] = {
                    "id": known["id"],
                    "name": geo_addr,
                    "address": known["address"],
                    "phone": known["phone"],
                    "lat": known["lat"],
                    "lng": known["lng"],
                    "type": known["type"],
                    "counts": {"cat": 0, "dog": 0},
                }
            else:
                coord = coords.get(geo_addr)
                if coord is None:
                    # geocoding 失敗，跳過此動物
                    continue
                loc_id = f"loc_{_slugify_name(geo_addr)}"
                loc_map[geo_addr] = {
                    "id": loc_id,
                    "name": animal["_shelter_name"] or geo_addr,
                    "address": animal["_shelter_address"] or geo_addr,
                    "phone": animal["_shelter_phone"],
                    "lat": coord["lat"],
                    "lng": coord["lng"],
                    "type": animal["_location_type"],
                    "counts": {"cat": 0, "dog": 0},
                }

        # 累加數量
        kind = animal["kind"]
        if kind in ("cat", "dog"):
            loc_map[geo_addr]["counts"][kind] += 1

    return list(loc_map.values())


def assign_location_ids(animals: list[dict], locations: list[dict]) -> None:
    """為每隻動物設定 location_id，並移除內部暫存欄位。"""
    addr_to_id = {}
    for loc in locations:
        # 找到對應的 geo_address
        for key, known in KNOWN_LOCATIONS.items():
            if known["id"] == loc["id"]:
                addr_to_id[key] = loc["id"]
                break
        else:
            # 非固定收容所：用 name 或 address 反查
            addr_to_id[loc["address"]] = loc["id"]
            addr_to_id[loc["name"]] = loc["id"]

    for animal in animals:
        geo_addr = animal.pop("_geo_address", "")
        animal.pop("_shelter_name", None)
        animal.pop("_shelter_address", None)
        animal.pop("_shelter_phone", None)
        animal.pop("_location_type", None)

        # 嘗試找 location_id
        loc_id = addr_to_id.get(geo_addr)
        if loc_id is None and geo_addr in KNOWN_LOCATIONS:
            loc_id = KNOWN_LOCATIONS[geo_addr]["id"]
        animal["location_id"] = loc_id or ""


def write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已寫入 {path}（{os.path.getsize(path):,} bytes）")


def build_for_city(city: str, animals: list[dict], now: str) -> None:
    """
    從全台動物清單中篩選出指定縣市，執行 geocoding 並輸出 JSON。
    city == ALL_TAIWAN 時使用全部動物。
    """
    if city == ALL_TAIWAN:
        city_animals = [dict(a) for a in animals]
        suffix = "全台"
    else:
        city_animals = [dict(a) for a in animals if a.get("city") == city]
        # Normalize 台/臺
        if not city_animals:
            city_norm = city.replace("台", "臺")
            city_animals = [dict(a) for a in animals if a.get("city", "").replace("台", "臺") == city_norm]
        suffix = city

    if not city_animals:
        print(f"  ⚠ {city}：無資料，跳過")
        return

    addresses = list({a["_geo_address"] for a in city_animals if a["_geo_address"]})
    coords = geocode_addresses(addresses)
    locations = build_locations(city_animals, coords)
    assign_location_ids(city_animals, locations)

    valid_animals = [a for a in city_animals if a["location_id"]]
    skipped = len(city_animals) - len(valid_animals)
    if skipped:
        print(f"  ⚠ {city}：略過 {skipped} 隻無法解析地址的動物")

    animals_payload = {
        "updated_at": now,
        "total": len(valid_animals),
        "city": city,
        "animals": valid_animals,
    }
    locations_payload = {
        "updated_at": now,
        "city": city,
        "locations": locations,
    }

    write_json(f"{OUTPUT_DIR}/animals_{suffix}.json", animals_payload)
    write_json(f"{OUTPUT_DIR}/locations_{suffix}.json", locations_payload)

    cat_count = sum(1 for a in valid_animals if a["kind"] == "cat")
    dog_count = sum(1 for a in valid_animals if a["kind"] == "dog")
    print(f"  ✅ {city}：{len(valid_animals)} 隻（貓 {cat_count} / 狗 {dog_count}），{len(locations)} 個地點")


def main():
    now = _now_iso()

    # 1. 台中市：爬蟲優先，農業部 API 備援
    print("=== 台中市（爬蟲）===")
    tc_animals = scrape_animals()
    if not tc_animals:
        print("⚠ 台中市動保處爬蟲未取得資料，fallback 至農業部 API...")

    # 2. 全台農業部 API（一次抓完，避免重複請求）
    print("\n=== 農業部 API（全台）===")
    gov_animals = fetch_animals()  # no city_filter → all cities

    if not gov_animals and not tc_animals:
        print("❌ 未取得任何動物資料，中止。")
        sys.exit(1)

    # 3. 用台中市爬蟲替換農業部中的台中市資料
    gov_non_tc = [a for a in gov_animals if a.get("city") not in ("臺中市", "台中市")]
    if tc_animals:
        all_animals = tc_animals + gov_non_tc
        print(f"\n合併：台中市爬蟲 {len(tc_animals)} 筆 + 其他縣市農業部 {len(gov_non_tc)} 筆 = {len(all_animals)} 筆")
    else:
        all_animals = gov_animals
        print(f"\n使用農業部 API 全台資料共 {len(all_animals)} 筆")

    # 4. 為台中市爬蟲資料補上 city 欄位（若尚未設定）
    for a in all_animals:
        if "city" not in a:
            a["city"] = "臺中市"

    # 5. 逐縣市輸出
    print("\n=== 逐縣市輸出 ===")
    cities_with_data = set(a.get("city", "") for a in all_animals if a.get("city"))
    for city in ALL_CITIES:
        if city in cities_with_data or city.replace("台", "臺") in cities_with_data:
            print(f"\n--- {city} ---")
            build_for_city(city, all_animals, now)

    # 6. 全台合併輸出
    print("\n--- 全台灣 ---")
    build_for_city(ALL_TAIWAN, all_animals, now)

    print("\n✅ 全部完成！")


if __name__ == "__main__":
    main()
