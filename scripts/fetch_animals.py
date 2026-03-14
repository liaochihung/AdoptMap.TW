# scripts/fetch_animals.py
"""
從農業部動物認領養 Open Data API 抓取台中市待領養動物資料。
"""

import re
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from config import (
    MOA_API_URL,
    MOA_UNIT_ID,
    MOA_PAGE_SIZE,
    TAICHUNG_KEYWORDS,
    KNOWN_LOCATIONS,
)


def _is_taichung(record: dict) -> bool:
    """判斷此動物是否屬於台中市。"""
    fields = [
        record.get("animal_place", ""),
        record.get("shelter_name", ""),
        record.get("shelter_address", ""),
    ]
    return any(
        kw in field
        for field in fields
        for kw in TAICHUNG_KEYWORDS
    )


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


def _extract_shelter_key(record: dict) -> str:
    """
    回傳對應 KNOWN_LOCATIONS 的 key（收容所名稱），
    或從 shelter_name 組出地址字串供 geocoding 使用。
    """
    shelter_name = record.get("shelter_name", "").strip()
    if shelter_name in KNOWN_LOCATIONS:
        return shelter_name
    return shelter_name


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
    # 格式：我在區域"店名"等待...電話：XXXX 台中市XX區...
    if shelter_zone == "益起認養吧":
        phone_match = re.search(r"電話[：:]([\d\-]+)", remark)
        phone = phone_match.group(1).strip() if phone_match else ""
        # 店名在引號內
        name_match = re.search(r'["\u201c\u300c](.*?)["\u201d\u300d]', remark)
        name = name_match.group(1).strip() if name_match else ""
        # 完整地址在電話後，格式為 台中市...
        addr_match = re.search(r"((?:台中市|臺中市)[^\s]+(?:路|街|道|巷|弄|號)[^\s]*)", remark)
        address = addr_match.group(1).strip() if addr_match else ""
        return {"type": "yiqi", "name": name, "address": address, "phone": phone}

    # 中途動物醫院：有店名但無完整地址
    # 格式：我在 " 區域 店名 " 等待...電話：XXXX
    if shelter_zone == "中途動物醫院":
        phone_match = re.search(r"電話[：:]([\d\-]+)", remark)
        phone = phone_match.group(1).strip() if phone_match else ""
        # 店名在引號內（含前後空白）
        name_match = re.search(r'["\u201c\u300c]\s*(.*?)\s*["\u201d\u300d]', remark)
        if name_match:
            # 格式通常是 "區域 店名"，取最後一個詞（店名）
            name_parts = name_match.group(1).strip().split()
            name = "".join(name_parts[1:]) if len(name_parts) > 1 else name_match.group(1).strip()
        else:
            name = ""
        return {"type": "vet_transit", "name": name, "address": "", "phone": phone}

    return None


def fetch_animals() -> list[dict]:
    """
    分頁抓取農業部 API，回傳台中市動物的標準化 list。
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

    print(f"農業部 API 總計 {len(all_records)} 筆，篩選台中市中...")

    animals = []
    for rec in all_records:
        if not _is_taichung(rec):
            continue

        animal_id = f"GOV-{rec.get('animal_id', '')}"
        shelter_name = rec.get("shelter_name", "").strip()
        shelter_address = rec.get("shelter_address", "").strip()
        remark = rec.get("animal_remark", "") or ""

        # 依據所在園區與備註解析來源類型
        shelter_zone = rec.get("animal_place", "").strip()
        # animal_place 格式為「臺中市動物之家南屯園區」，取最後部分
        for zone_suffix in ("南屯園區", "后里園區", "中途動物醫院", "益起認養吧"):
            if shelter_zone.endswith(zone_suffix):
                shelter_zone = zone_suffix
                break

        parsed = parse_remark_location(remark, shelter_zone)

        # 決定地址欄位（供 geocoding 使用）
        # 注意：shelter_zone 來自 animal_place（用於辨識來源類型）
        #        shelter_name 來自 shelter_name 欄位（用於查詢 KNOWN_LOCATIONS，包含完整名稱如「臺中市動物之家南屯園區」）
        if shelter_name in KNOWN_LOCATIONS:
            geo_address = shelter_name
            location_type = "shelter"
        elif parsed:
            location_type = parsed["type"]
            if parsed["address"]:
                geo_address = parsed["address"]
            elif parsed["name"]:
                geo_address = parsed["name"]
            else:
                geo_address = shelter_address or shelter_name
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
            # 以下欄位供 build_data.py 組合地點時使用，不進入最終 JSON
            "_shelter_name": (parsed["name"] if parsed and parsed["name"] else shelter_name),
            "_shelter_address": (parsed["address"] if parsed and parsed["address"] else shelter_address),
            "_shelter_phone": (parsed["phone"] if parsed and parsed["phone"] else rec.get("shelter_tel", "") or ""),
            "_geo_address": geo_address,
            "_location_type": location_type,
            "source_url": f"https://www.pet.gov.tw/Web/L315.aspx?no={rec.get('animal_id', '')}",
        })

    print(f"台中市動物 {len(animals)} 筆")
    return animals


def _fmt_date(raw: str) -> str:
    """
    把 '2026/03/13' 或 '2026-03-13' 格式統一為 'YYYY-MM-DD'，
    無法解析則回傳空字串。
    """
    if not raw:
        return ""
    raw = raw.strip().split(" ")[0].split("T")[0]
    return raw.replace("/", "-")
