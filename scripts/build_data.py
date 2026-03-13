# scripts/build_data.py
"""
主控腳本：呼叫 fetch_animals、geocode，產出 animals.json 與 locations.json。
由 GitHub Actions 每日執行。
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


def main():
    now = _now_iso()

    # 1. 抓取農業部 API 資料
    animals = fetch_animals()
    if not animals:
        print("❌ 未取得任何動物資料，中止。")
        sys.exit(1)

    # 2. 收集所有需要 geocoding 的地址
    addresses = list({a["_geo_address"] for a in animals if a["_geo_address"]})
    print(f"\n需要 geocoding 的地址共 {len(addresses)} 個")

    # 3. 執行 geocoding（含快取）
    coords = geocode_addresses(addresses)

    # 4. 組合地點資料
    locations = build_locations(animals, coords)
    print(f"\n地點共 {len(locations)} 個")

    # 5. 為每隻動物指定 location_id（並移除暫存欄位）
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
