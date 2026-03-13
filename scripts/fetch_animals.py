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


def _extract_vet_transit_info(remark: str):
    """
    嘗試從 animal_remark 中解析中途動物醫院名稱。
    回傳 (name, address) 或 (None, None)。
    """
    # 常見格式：「XX動物醫院」或「XX動物診所」
    patterns = [
        r"([\w\s]+(?:動物醫院|動物診所|獸醫院))[，,、\s]*(臺中[^\s，,、]+)?",
    ]
    for pat in patterns:
        m = re.search(pat, remark)
        if m:
            name = m.group(1).strip()
            address = (m.group(2) or "").strip()
            return name, address
    return None, None


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

        # 嘗試辨識中途動物醫院
        vet_name, vet_address = _extract_vet_transit_info(remark)

        # 決定地址欄位（供 geocoding 使用）
        if shelter_name in KNOWN_LOCATIONS:
            geo_address = shelter_name  # 用名稱當 key，直接對應固定座標
            location_type = "shelter"
        elif vet_name:
            geo_address = vet_address or vet_name
            location_type = "vet_transit"
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
            "_shelter_name": shelter_name,
            "_shelter_address": shelter_address,
            "_shelter_phone": rec.get("shelter_tel", "") or "",
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
