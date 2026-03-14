# scripts/scrape_taichung.py
"""
爬取台中市動保處「待認養犬貓照片檢索」網站，取得農業部 API 未收錄的動物資料
（中途動物醫院、益起認養吧，以及所有台中市動保處列管動物）。

來源：https://www.animal.taichung.gov.tw/1521490/Lpsimplelist
"""

import re
import time
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from fetch_animals import parse_remark_location, _map_kind, _map_sex, _map_age, _map_bodytype, _map_bool

BASE_URL = "https://www.animal.taichung.gov.tw"
LIST_URL = f"{BASE_URL}/1521490/Lpsimplelist"
DETAIL_URL = f"{BASE_URL}/1521490/animalCp"
PAGE_SIZE = 30
REQUEST_DELAY = 1.0  # 秒，避免對伺服器造成負擔

HEADERS = {
    "User-Agent": "adopt-map/1.0 (https://github.com/liaochihung/AdoptMap.TW)",
}


def _get_soup(url: str, params: dict = None) -> BeautifulSoup:
    resp = requests.get(url, params=params, headers=HEADERS, timeout=30, verify=False)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, "html.parser")


def _parse_age(raw: str) -> str:
    """幼犬/幼貓 → child，成犬/成貓 → adult"""
    if "幼" in raw:
        return "child"
    return "adult"


def _parse_sex(raw: str) -> str:
    if raw == "公":
        return "M"
    if raw == "母":
        return "F"
    return "N"


def _parse_bodytype(raw: str) -> str:
    """小型(3-13公斤) → small，中型 → medium，大型 → large"""
    if "小型" in raw:
        return "small"
    if "大型" in raw:
        return "large"
    return "medium"


def _parse_kind_from_age(raw: str) -> str:
    """從年齡欄位判斷貓/狗（幼犬/成犬 → dog，幼貓/成貓 → cat）"""
    if "貓" in raw:
        return "cat"
    if "犬" in raw:
        return "dog"
    return "dog"


def _get_total_pages(soup: BeautifulSoup) -> int:
    """從分頁區塊解析總頁數，例如 '1/5' → 5。"""
    page_section = soup.find("section", class_="page")
    if not page_section:
        return 1
    abbr = page_section.find("abbr")
    if abbr:
        m = re.search(r"\d+/(\d+)", abbr.get_text())
        if m:
            return int(m.group(1))
    return 1


def fetch_node_ids() -> list[int]:
    """爬取所有列表頁，回傳全部 nodeId 清單。"""
    node_ids = []

    print("開始爬取台中市動保處列表頁...")
    # 先抓第 1 頁，取得總頁數
    soup = _get_soup(LIST_URL, params={"Page": 1, "PageSize": PAGE_SIZE, "type": ""})
    total_pages = _get_total_pages(soup)
    print(f"  共 {total_pages} 頁")

    for page in range(1, total_pages + 1):
        if page > 1:
            time.sleep(REQUEST_DELAY)
            soup = _get_soup(LIST_URL, params={"Page": page, "PageSize": PAGE_SIZE, "type": ""})

        section = soup.find("section", class_="animalPhotos")
        if not section:
            break
        ul = section.find("ul")
        if not ul:
            break
        lis = ul.find_all("li", recursive=False)

        for li in lis:
            a = li.find("a")
            if not a:
                continue
            href = a.get("href", "")
            m = re.search(r"nodeId=(\d+)", href)
            if m:
                node_ids.append(int(m.group(1)))

        print(f"  第 {page}/{total_pages} 頁：{len(lis)} 筆，累計 {len(node_ids)} 筆")

    print(f"列表頁共取得 {len(node_ids)} 個 nodeId")
    return node_ids


def parse_detail_page(node_id: int) -> dict | None:
    """
    爬取單一動物詳細頁，回傳標準化動物資料 dict。
    Table 0 的 td 欄位順序（固定）：
      [0]=編號  [1]=所在園區  [2]=年齡  [3]=性別  [4]=體型
      [5]=毛色  [6]=驅蟲紀錄  [7]=預防注射  [8]=絕育
      [9]=訓犬狀態  [10]=性情  [11]=備註  [12]=被認養日期
    """
    url = DETAIL_URL
    soup = _get_soup(url, params={"nodeId": node_id})

    tables = soup.find_all("table")
    if not tables:
        return None

    tds = tables[0].find_all("td")
    if len(tds) < 9:
        return None

    animal_no = tds[0].get_text(strip=True)   # 編號，如 11501210004
    shelter_zone = tds[1].get_text(strip=True) # 所在園區
    age_raw = tds[2].get_text(strip=True)      # 幼犬/成貓 等
    sex_raw = tds[3].get_text(strip=True)
    bodytype_raw = tds[4].get_text(strip=True)
    colour = tds[5].get_text(strip=True)
    sterilized_raw = tds[8].get_text(strip=True) if len(tds) > 8 else ""
    remark = tds[11].get_text(strip=True) if len(tds) > 11 else ""

    # 照片：找 /media/ 開頭且非 logo 的第一張
    photo_url = ""
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if "/media/" in src and "logo" not in src.lower():
            # 移除 query string（?height=300）
            photo_url = BASE_URL + src.split("?")[0]
            break

    # 依所在園區決定 location_type 與 _geo_address
    from config import KNOWN_LOCATIONS

    shelter_zone_key = shelter_zone  # 台中市動保處直接給簡短名稱

    # 收容所：對應 KNOWN_LOCATIONS（用完整名稱查詢）
    full_shelter_name_map = {
        "南屯園區": "臺中市動物之家南屯園區",
        "后里園區": "臺中市動物之家后里園區",
    }

    parsed_remark = parse_remark_location(remark, shelter_zone_key)

    if shelter_zone_key in full_shelter_name_map:
        full_name = full_shelter_name_map[shelter_zone_key]
        geo_address = full_name
        location_type = "shelter"
        shelter_name = full_name
        shelter_address = KNOWN_LOCATIONS[full_name]["address"]
        shelter_phone = KNOWN_LOCATIONS[full_name]["phone"]
    elif parsed_remark:
        location_type = parsed_remark["type"]
        shelter_name = parsed_remark["name"]
        shelter_address = parsed_remark["address"]
        shelter_phone = parsed_remark["phone"]
        geo_address = parsed_remark["address"] or parsed_remark["name"] or shelter_zone_key
    else:
        # fallback
        location_type = "shelter"
        shelter_name = shelter_zone_key
        shelter_address = ""
        shelter_phone = ""
        geo_address = shelter_zone_key

    return {
        "id": f"TC-{animal_no}",
        "source": "taichung_shelter",
        "kind": _parse_kind_from_age(age_raw),
        "name": "",  # 台中市動保處無品種欄位
        "sex": _parse_sex(sex_raw),
        "age": _parse_age(age_raw),
        "bodytype": _parse_bodytype(bodytype_raw),
        "colour": colour,
        "sterilized": True if "已絕育" in sterilized_raw else (False if "未絕育" in sterilized_raw else None),
        "vaccinated": None,
        "photo_url": photo_url,
        "remark": remark,
        "open_date": "",
        "update_date": "",
        "_shelter_name": shelter_name,
        "_shelter_address": shelter_address,
        "_shelter_phone": shelter_phone,
        "_geo_address": geo_address,
        "_location_type": location_type,
        "source_url": f"{BASE_URL}/1521490/animalCp?nodeId={node_id}",
    }


def scrape_animals() -> list[dict]:
    """
    爬取台中市動保處全部待認養動物，回傳標準化清單。
    """
    node_ids = fetch_node_ids()
    animals = []
    failed = 0

    print(f"\n開始爬取 {len(node_ids)} 筆動物詳細頁...")
    for i, node_id in enumerate(node_ids, 1):
        try:
            animal = parse_detail_page(node_id)
            if animal:
                animals.append(animal)
        except Exception as e:
            print(f"  ⚠ nodeId={node_id} 失敗：{e}")
            failed += 1
        if i % 10 == 0:
            print(f"  已處理 {i}/{len(node_ids)} 筆（{failed} 失敗）")
        time.sleep(REQUEST_DELAY)

    print(f"台中市動保處共爬取 {len(animals)} 筆（失敗 {failed} 筆）")
    return animals
