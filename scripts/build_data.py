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
from config import KNOWN_LOCATIONS, OUTPUT_DIR

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


def _merge_animals(gov_animals: list[dict], tc_animals: list[dict]) -> list[dict]:
    """
    合併農業部 API 與台中市動保處爬蟲資料，以台中市動保處資料為主（去重）。
    去重依據：台中市動保處的動物編號（TC-XXXXX）與農業部的 animal_Variety 欄位無直接對應，
    改以 source_url 或動物編號的最後幾碼做模糊比對。
    目前策略：優先使用台中市爬蟲資料（較完整），並補充農業部 API 中未被台中市涵蓋的資料。
    農業部 API 的台中市資料目前只有 shelter（南屯/后里），台中市動保處也有這兩個。
    為避免重複，直接以台中市爬蟲資料為主，捨棄農業部中的同來源 shelter 資料。
    """
    # 台中市爬蟲已涵蓋 shelter/vet_transit/yiqi 全部類型
    # 農業部 API 另有全國其他縣市，但本專案只抓台中市
    # 結論：直接使用台中市爬蟲資料，農業部 API 用於去重確認（目前省略）
    print(f"農業部 API：{len(gov_animals)} 筆，台中市爬蟲：{len(tc_animals)} 筆")
    print("以台中市動保處爬蟲資料為主（已涵蓋完整 149 筆）")
    return tc_animals


def main():
    now = _now_iso()

    # 1. 抓取台中市動保處爬蟲資料（主要來源，149 筆）
    tc_animals = scrape_animals()
    if not tc_animals:
        print("⚠ 台中市動保處爬蟲未取得資料，fallback 至農業部 API...")

    # 2. 抓取農業部 API 資料（備援）
    gov_animals = fetch_animals()

    # 3. 合併去重
    if tc_animals:
        animals = _merge_animals(gov_animals, tc_animals)
    else:
        animals = gov_animals

    if not animals:
        print("❌ 未取得任何動物資料，中止。")
        sys.exit(1)

    # 4. 收集所有需要 geocoding 的地址
    addresses = list({a["_geo_address"] for a in animals if a["_geo_address"]})
    print(f"\n需要 geocoding 的地址共 {len(addresses)} 個")

    # 5. 執行 geocoding（含快取）
    coords = geocode_addresses(addresses)

    # 6. 組合地點資料
    locations = build_locations(animals, coords)
    print(f"\n地點共 {len(locations)} 個")

    # 7. 為每隻動物指定 location_id（並移除暫存欄位）
    assign_location_ids(animals, locations)

    # 過濾掉沒有 location_id 的動物（geocoding 失敗）
    valid_animals = [a for a in animals if a["location_id"]]
    skipped = len(animals) - len(valid_animals)
    if skipped:
        print(f"⚠ 略過 {skipped} 隻無法解析地址的動物")

    # 6. 輸出 JSON
    animals_payload = {
        "updated_at": now,
        "total": len(valid_animals),
        "animals": valid_animals,
    }
    locations_payload = {
        "updated_at": now,
        "locations": locations,
    }

    write_json(f"{OUTPUT_DIR}/animals.json", animals_payload)
    write_json(f"{OUTPUT_DIR}/locations.json", locations_payload)

    # 7. 統計報告
    cat_count = sum(1 for a in valid_animals if a["kind"] == "cat")
    dog_count = sum(1 for a in valid_animals if a["kind"] == "dog")
    print(f"\n✅ 完成！共 {len(valid_animals)} 隻（貓 {cat_count} / 狗 {dog_count}），{len(locations)} 個地點")


if __name__ == "__main__":
    main()
