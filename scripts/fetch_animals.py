# scripts/fetch_animals.py
"""
從農業部動物認領養 Open Data API 抓取全台待領養動物資料。
"""

import base64
import re
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from config import (
    MOA_API_URL,
    MOA_UNIT_ID,
    MOA_PAGE_SIZE,
    KNOWN_LOCATIONS,
    ALL_CITIES,
)


def _extract_city(record: dict) -> str:
    """從農業部 API 記錄中提取縣市名稱（回傳 ALL_CITIES 中的標準名稱）。"""
    fields = [
        record.get("animal_place", ""),
        record.get("shelter_name", ""),
        record.get("shelter_address", ""),
    ]
    for field in fields:
        normalized_field = field.replace("台", "臺")
        for city in ALL_CITIES:
            normalized_city = city.replace("台", "臺")
            if normalized_city in normalized_field:
                return city
    return ""


def _map_sex(raw: str) -> str:
    mapping = {"M": "M", "F": "F", "1": "M", "2": "F"}
    return mapping.get(str(raw).upper(), "N")


def _map_age(raw: str) -> str:
    raw = str(raw).upper()
    if raw in ("ADULT", "A"):
        return "adult"
    if raw in ("CHILD", "C", "YOUNG"):
        return "child"
    return "adult"


def _map_bodytype(raw: str) -> str:
    raw = str(raw).upper()
    if raw in ("SMALL", "S"):
        return "small"
    if raw in ("LARGE", "L"):
        return "large"
    return "medium"


def _map_bool(raw: str):
    """T → True, F → False, else None"""
    raw = str(raw).upper()
    if raw == "T":
        return True
    if raw == "F":
        return False
    return None


def _map_kind(raw: str) -> str:
    if "貓" in raw:
        return "cat"
    if "犬" in raw or "狗" in raw:
        return "dog"
    return "dog"


def parse_remark_location(remark: str, shelter_zone: str) -> dict | None:
    """
    依據「所在園區」欄位值與備註內容，解析地點資訊。

    回傳 dict（含 type / name / address / phone）或 None（表示使用預設收容所邏輯）。

    來源類型對照：
    - shelter_zone 為 '南屯園區' / '后里園區' → 回傳 None（由 KNOWN_LOCATIONS 處理）
    - shelter_zone 為 '中途動物醫院' → type='vet_transit'，解析店名與電話
    - shelter_zone 為 '益起認養吧'   → type='yiqi'，解析店名、電話、完整地址
    """
    SHELTER_ZONES = {"南屯園區", "后里園區"}
    if shelter_zone in SHELTER_ZONES or not remark:
        return None

    # 益起認養吧：備註末尾有完整地址
    # 格式：我在區域"店名"等待...電話：XXXX XX市XX區...
    if shelter_zone == "益起認養吧":
        phone_match = re.search(r"電話[：:]([\d\-]+)", remark)
        phone = phone_match.group(1).strip() if phone_match else ""
        name_match = re.search(r'["\u201c\u300c](.*?)["\u201d\u300d]', remark)
        name = name_match.group(1).strip() if name_match else ""
        # Match any city/county address (not just Taichung)
        addr_match = re.search(
            r"((?:[\u4e00-\u9fff]{2}市|[\u4e00-\u9fff]{2}縣)[^\s]+(?:路|街|道|巷|弄|號)[^\s]*)",
            remark
        )
        address = addr_match.group(1).strip() if addr_match else ""
        return {"type": "yiqi", "name": name, "address": address, "phone": phone}

    # 中途動物醫院：有店名但無完整地址
    # 格式：我在 " 區域 店名 " 等待...電話：XXXX
    if shelter_zone == "中途動物醫院":
        phone_match = re.search(r"電話[：:]([\d\-]+)", remark)
        phone = phone_match.group(1).strip() if phone_match else ""
        name_match = re.search(r'["\u201c\u300c]\s*(.*?)\s*["\u201d\u300d]', remark)
        if name_match:
            name_parts = name_match.group(1).strip().split()
            name = "".join(name_parts[1:]) if len(name_parts) > 1 else name_match.group(1).strip()
        else:
            name = ""
        return {"type": "vet_transit", "name": name, "address": "", "phone": phone}

    return None


def _build_source_url(rec: dict) -> str:
    """依據 animal_subid 產生 pet.gov.tw 的正確詳情頁 URL。"""
    subid = rec.get("animal_subid", "").strip()
    if not subid or len(subid) < 5:
        return ""
    ac_num = base64.b64encode(subid.encode()).decode()
    user_tag = base64.b64encode(subid[:5].encode()).decode()
    return (
        f"https://www.pet.gov.tw/AnimalApp/AnnounceSingle.aspx"
        f"?PageType=Adopt&AcNum={ac_num}&UT={user_tag}"
    )


def fetch_animals(city_filter: str | None = None) -> list[dict]:
    """
    分頁抓取農業部 API，回傳所有（或指定縣市）待領養動物的標準化 list。
    city_filter: 若為 None 則回傳全台；否則只回傳符合縣市的資料。
    """
    all_records = []
    skip = 0

    print("開始抓取農業部 API 資料...")
    while True:
        params = {
            "UnitId": MOA_UNIT_ID,
            "$top": MOA_PAGE_SIZE,
            "$skip": skip,
        }
        resp = requests.get(MOA_API_URL, params=params, timeout=30, verify=False)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        all_records.extend(batch)
        print(f"  已取得 {len(all_records)} 筆（本次 {len(batch)} 筆）")
        if len(batch) < MOA_PAGE_SIZE:
            break
        skip += MOA_PAGE_SIZE

    print(f"農業部 API 總計 {len(all_records)} 筆")

    animals = []
    for rec in all_records:
        city = _extract_city(rec)
        if city_filter and city != city_filter:
            continue

        animal_id = f"GOV-{rec.get('animal_id', '')}"
        shelter_name = rec.get("shelter_name", "").strip()
        shelter_address = rec.get("shelter_address", "").strip()
        remark = rec.get("animal_remark", "") or ""

        shelter_zone = rec.get("animal_place", "").strip()
        for zone_suffix in ("南屯園區", "后里園區", "中途動物醫院", "益起認養吧"):
            if shelter_zone.endswith(zone_suffix):
                shelter_zone = zone_suffix
                break

        parsed = parse_remark_location(remark, shelter_zone)

        if shelter_name in KNOWN_LOCATIONS:
            geo_address = shelter_name
            location_type = "shelter"
        elif parsed:
            location_type = parsed["type"]
            geo_address = parsed["address"] or parsed["name"] or shelter_address or shelter_name
        else:
            geo_address = shelter_address or shelter_name
            location_type = "shelter"

        animals.append({
            "id": animal_id,
            "source": "gov_shelter",
            "kind": _map_kind(rec.get("animal_kind", "")),
            "name": rec.get("animal_Variety", "") or "",
            "sex": _map_sex(rec.get("animal_sex", "")),
            "age": _map_age(rec.get("animal_age", "")),
            "bodytype": _map_bodytype(rec.get("animal_bodytype", "")),
            "colour": rec.get("animal_colour", "") or "",
            "sterilized": _map_bool(rec.get("animal_sterilization", "")),
            "vaccinated": _map_bool(rec.get("animal_bacterin", "")),
            "photo_url": rec.get("album_file", "") or "",
            "remark": remark,
            "open_date": _fmt_date(rec.get("animal_opendate", "")),
            "update_date": _fmt_date(rec.get("animal_update", "")),
            "city": city,
            "_shelter_name": (parsed["name"] if parsed and parsed["name"] else shelter_name),
            "_shelter_address": (parsed["address"] if parsed and parsed["address"] else shelter_address),
            "_shelter_phone": (parsed["phone"] if parsed and parsed["phone"] else rec.get("shelter_tel", "") or ""),
            "_geo_address": geo_address,
            "_location_type": location_type,
            "source_url": _build_source_url(rec),
        })

    print(f"符合條件動物 {len(animals)} 筆")
    return animals


def _fmt_date(raw: str) -> str:
    if not raw:
        return ""
    raw = raw.strip().split(" ")[0].split("T")[0]
    return raw.replace("/", "-")
