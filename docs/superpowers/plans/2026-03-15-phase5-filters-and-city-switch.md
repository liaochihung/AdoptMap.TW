# Phase 5 Filters & City Switch Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add county/city switching (per-city JSON files), source-type filtering (shelter/vet_transit/yiqi), sex filtering, and colour filtering to the AdoptMap frontend and data pipeline.

**Architecture:** The Python pipeline is extended to output one `animals_{city}.json` + `locations_{city}.json` per city, plus a combined `animals_全台.json` + `locations_全台.json`. `useAnimals.js` is extended with new filter refs and a city-aware `loadData(city)` function. `FilterBar.vue` is rebuilt to implement the "main row + expandable panel" layout (Option C from design), with a city dropdown, kind pills, and a "更多篩選" button revealing source/sex/colour controls.

**Tech Stack:** Vue 3 Composition API, Python 3.11, Leaflet, Tailwind CSS 3, GitHub Actions

---

## File Map

### Python (backend pipeline)

| File | Change |
|------|--------|
| `scripts/config.py` | Add `CITY_CENTERS` dict (city → lat/lng/zoom), `ALL_CITIES` list, update `OUTPUT_DIR` notes |
| `scripts/fetch_animals.py` | Full file replacement: remove `_is_taichung`, `_extract_shelter_key`; add `_extract_city`; `fetch_animals()` gains optional `city_filter` param and adds `city` field to every animal |
| `scripts/build_data.py` | Add `build_for_city(city, animals)` helper; loop over all cities + 全台 |

### Frontend (Vue)

| File | Change |
|------|--------|
| `src/composables/useAnimals.js` | Add `currentCity`, `filterSource`, `filterSex`, `filterColour`, `availableSources`, `availableColours`; update `loadData(city)`, `filteredAnimals` |
| `src/components/FilterBar.vue` | Full rewrite: city dropdown, kind pills, 更多篩選 panel (source/sex/colour) |
| `src/components/ToastNotification.vue` | New: yellow toast for 全台 warning |
| `src/App.vue` | Wire new filter props/events; handle city change + map flyTo; show Toast |
| `src/composables/useMap.js` | Add `flyToCity(city)` using `CITY_CENTERS` constant |

---

## Chunk 1: Python — Multi-City Data Pipeline

### Task 1: Extend `config.py` with city metadata

**Files:**
- Modify: `scripts/config.py`

- [ ] **Step 1: Add city list and map centers to config.py**

Add after the existing `LOCATION_TYPES` block:

```python
# 支援的縣市清單（依農業部 API animal_place 欄位）
ALL_CITIES = [
    "臺北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣",
    "苗栗縣", "臺中市", "彰化縣", "南投縣", "雲林縣", "嘉義市",
    "嘉義縣", "臺南市", "高雄市", "屏東縣", "宜蘭縣", "花蓮縣",
    "臺東縣", "澎湖縣", "金門縣", "連江縣",
]

# 各縣市地圖中心座標（lat, lng）與預設 zoom
CITY_CENTERS = {
    "臺北市":  {"lat": 25.0478, "lng": 121.5319, "zoom": 12},
    "新北市":  {"lat": 25.0120, "lng": 121.4653, "zoom": 11},
    "基隆市":  {"lat": 25.1283, "lng": 121.7419, "zoom": 13},
    "桃園市":  {"lat": 24.9937, "lng": 121.3009, "zoom": 11},
    "新竹市":  {"lat": 24.8138, "lng": 120.9675, "zoom": 13},
    "新竹縣":  {"lat": 24.7036, "lng": 121.1542, "zoom": 11},
    "苗栗縣":  {"lat": 24.5602, "lng": 120.8214, "zoom": 11},
    "臺中市":  {"lat": 24.1477, "lng": 120.6736, "zoom": 12},
    "彰化縣":  {"lat": 23.9921, "lng": 120.5161, "zoom": 11},
    "南投縣":  {"lat": 23.9610, "lng": 120.9718, "zoom": 11},
    "雲林縣":  {"lat": 23.7092, "lng": 120.4313, "zoom": 11},
    "嘉義市":  {"lat": 23.4801, "lng": 120.4491, "zoom": 13},
    "嘉義縣":  {"lat": 23.4518, "lng": 120.2555, "zoom": 11},
    "臺南市":  {"lat": 22.9999, "lng": 120.2270, "zoom": 11},
    "高雄市":  {"lat": 22.6273, "lng": 120.3014, "zoom": 11},
    "屏東縣":  {"lat": 22.5519, "lng": 120.5487, "zoom": 11},
    "宜蘭縣":  {"lat": 24.7021, "lng": 121.7378, "zoom": 11},
    "花蓮縣":  {"lat": 23.9871, "lng": 121.6015, "zoom": 10},
    "臺東縣":  {"lat": 22.7972, "lng": 121.0713, "zoom": 10},
    "澎湖縣":  {"lat": 23.5654, "lng": 119.5793, "zoom": 12},
    "金門縣":  {"lat": 24.4493, "lng": 118.3765, "zoom": 12},
    "連江縣":  {"lat": 26.1605, "lng": 119.9497, "zoom": 13},
    "全台灣":  {"lat": 23.9739, "lng": 120.9820, "zoom": 8},
}

# 全台灣特殊值（用於前端判斷）
ALL_TAIWAN = "全台灣"
```

- [ ] **Step 2: Verify config loads without errors**

```bash
cd d:/Projects/AdoptMap && python scripts/config.py 2>&1 | head -3; python -c "
import sys; sys.path.insert(0,'scripts')
from config import ALL_CITIES, CITY_CENTERS, ALL_TAIWAN
print(len(ALL_CITIES), 'cities, centers ok:', ALL_TAIWAN in CITY_CENTERS)
"
```

Expected output: `22 cities, centers ok: True`

- [ ] **Step 3: Commit**

```bash
git add scripts/config.py
git commit -m "feat: add ALL_CITIES, CITY_CENTERS, ALL_TAIWAN to config"
```

---

### Task 2: Extend `fetch_animals.py` to support all cities

**Files:**
- Modify: `scripts/fetch_animals.py`

- [ ] **Step 1: Write failing test for city extraction**

Create `scripts/tests/test_fetch_cities.py`:

```python
import sys
sys.path.insert(0, 'scripts')
from fetch_animals import _extract_city

def test_extract_city_taichung():
    rec = {"animal_place": "臺中市動物之家南屯園區", "shelter_name": "", "shelter_address": ""}
    assert _extract_city(rec) == "臺中市"

def test_extract_city_taipei():
    rec = {"animal_place": "臺北市動物之家", "shelter_name": "", "shelter_address": "臺北市中山區"}
    assert _extract_city(rec) == "臺北市"

def test_extract_city_unknown():
    rec = {"animal_place": "", "shelter_name": "", "shelter_address": ""}
    assert _extract_city(rec) == ""

def test_extract_city_from_address():
    rec = {"animal_place": "", "shelter_name": "", "shelter_address": "高雄市某收容所路1號"}
    assert _extract_city(rec) == "高雄市"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd d:/Projects/AdoptMap && python -m pytest scripts/tests/test_fetch_cities.py -v
```

Expected: FAIL with `ImportError: cannot import name '_extract_city'`

- [ ] **Step 3: Rewrite `fetch_animals.py` with all-city support**

Replace the **entire file** `scripts/fetch_animals.py` with the following. Key changes vs. the original:
- `_is_taichung` **deleted**; replaced by `_extract_city`
- `_extract_shelter_key` **deleted** (was unused dead code)
- `TAICHUNG_KEYWORDS` removed from imports; `ALL_CITIES` added
- `parse_remark_location` address regex generalised: `台中市|臺中市` → `(?:[\u4e00-\u9fff]{2}市|[\u4e00-\u9fff]{2}縣)` to match any city/county
- `fetch_animals()` gains optional `city_filter` param and adds `city` field to every animal dict
- `_fmt_date` remains unchanged at bottom of file

Full replacement file:

```python
# scripts/fetch_animals.py
"""
從農業部動物認領養 Open Data API 抓取全台待領養動物資料。
"""

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
            "source_url": f"https://www.pet.gov.tw/Web/L315.aspx?no={rec.get('animal_id', '')}",
        })

    print(f"符合條件動物 {len(animals)} 筆")
    return animals


def _fmt_date(raw: str) -> str:
    if not raw:
        return ""
    raw = raw.strip().split(" ")[0].split("T")[0]
    return raw.replace("/", "-")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd d:/Projects/AdoptMap && python -m pytest scripts/tests/test_fetch_cities.py -v
```

Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_animals.py scripts/tests/test_fetch_cities.py
git commit -m "feat: extend fetch_animals to support all cities with city field"
```

---

### Task 3: Extend `build_data.py` to output per-city JSON files

**Files:**
- Modify: `scripts/build_data.py`

- [ ] **Step 1: Write a failing test for per-city file output**

Create `scripts/tests/test_build_city.py`:

```python
import sys, os, json, tempfile
sys.path.insert(0, 'scripts')

# Patch OUTPUT_DIR before importing build_data
import config as _cfg
_orig_output_dir = _cfg.OUTPUT_DIR

def test_build_for_city_outputs_correct_filenames(tmp_path, monkeypatch):
    import config
    monkeypatch.setattr(config, 'OUTPUT_DIR', str(tmp_path))
    # Re-import build_data so it picks up patched OUTPUT_DIR
    import importlib, build_data
    importlib.reload(build_data)

    fake_animals = [
        {
            "id": "GOV-1", "source": "gov_shelter", "kind": "dog", "name": "",
            "sex": "M", "age": "adult", "bodytype": "medium", "colour": "黑色",
            "sterilized": None, "vaccinated": None, "photo_url": "", "remark": "",
            "open_date": "2026-01-01", "update_date": "2026-01-01", "city": "臺北市",
            "_shelter_name": "臺北市動物之家", "_shelter_address": "臺北市中山區",
            "_shelter_phone": "", "_geo_address": "臺北市動物之家", "_location_type": "shelter",
            "source_url": "",
        }
    ]

    # Should produce animals_臺北市.json and locations_臺北市.json
    build_data.build_for_city("臺北市", fake_animals, "2026-01-01T00:00:00+08:00")

    assert (tmp_path / "animals_臺北市.json").exists(), "animals_臺北市.json not created"
    assert (tmp_path / "locations_臺北市.json").exists(), "locations_臺北市.json not created"

def test_build_for_city_taiwan_uses_全台_suffix(tmp_path, monkeypatch):
    """Verify ALL_TAIWAN uses '全台' filename suffix, not '全台灣'."""
    import config
    monkeypatch.setattr(config, 'OUTPUT_DIR', str(tmp_path))
    import importlib, build_data
    importlib.reload(build_data)

    fake_animals = [
        {
            "id": "GOV-2", "source": "gov_shelter", "kind": "cat", "name": "",
            "sex": "F", "age": "adult", "bodytype": "small", "colour": "白色",
            "sterilized": None, "vaccinated": None, "photo_url": "", "remark": "",
            "open_date": "2026-01-01", "update_date": "2026-01-01", "city": "臺北市",
            "_shelter_name": "臺北市動物之家", "_shelter_address": "臺北市中山區",
            "_shelter_phone": "", "_geo_address": "臺北市動物之家", "_location_type": "shelter",
            "source_url": "",
        }
    ]

    build_data.build_for_city("全台灣", fake_animals, "2026-01-01T00:00:00+08:00")
    # Must use '全台' suffix, not '全台灣'
    assert (tmp_path / "animals_全台.json").exists(), "Should create animals_全台.json"
    assert not (tmp_path / "animals_全台灣.json").exists(), "Should NOT create animals_全台灣.json"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd d:/Projects/AdoptMap && python -m pytest scripts/tests/test_build_city.py -v
```

Expected: FAIL with `ImportError: cannot import name 'build_for_city'`

- [ ] **Step 3: Add `build_for_city` helper and update `main()`**

Keep existing functions `_now_iso`, `_slugify_name`, `build_locations`, `assign_location_ids`, `write_json` unchanged. Only:
1. Update the `from config import ...` line (leave the other import lines for `fetch_animals`, `scrape_animals`, `geocode_addresses` intact)
2. Add new `build_for_city()` function before `main()`
3. Replace `main()` entirely

**Sub-step A — Update only the config import line** (find `from config import KNOWN_LOCATIONS, OUTPUT_DIR` and replace with):

```python
from config import KNOWN_LOCATIONS, OUTPUT_DIR, ALL_CITIES, ALL_TAIWAN
```

**Sub-step B — Add `build_for_city()` function** (insert before `main()`, after `_merge_animals`):

```python
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
```

**Sub-step C — Clean up dead code in `build_data.py`**: delete the `_merge_animals` function — it is no longer called.

**Sub-step D — Clean up dead constants in `config.py`**: delete `TAICHUNG_KEYWORDS` and `TAICHUNG_VIEWBOX` — they are no longer imported anywhere after Task 2.

**Sub-step E — Replace `main()`**: find the existing `def main():` block and replace it entirely with the `main()` shown above. `sys` is already imported at the top of the file — do not change that import.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd d:/Projects/AdoptMap && python -m pytest scripts/tests/test_build_city.py -v
```

Expected: 2 tests PASS

- [ ] **Step 5: Verify syntax and importability**

```bash
cd d:/Projects/AdoptMap && python -m py_compile scripts/build_data.py && echo "syntax ok"
```

Expected: `syntax ok`

- [ ] **Step 6: Commit**

```bash
git add scripts/build_data.py scripts/tests/test_build_city.py scripts/config.py
git commit -m "feat: build_data outputs per-city and 全台 JSON files"
```

---

## Chunk 2: Frontend — useAnimals & city switching

### Task 4: Extend `useAnimals.js` with new filters and city-aware loading

**Files:**
- Modify: `src/composables/useAnimals.js`

- [ ] **Step 1: Replace useAnimals.js with extended version**

```javascript
// src/composables/useAnimals.js
import { ref, computed } from 'vue'

// City centers for map flyTo (mirrors config.py CITY_CENTERS)
export const CITY_CENTERS = {
  '臺北市':  { lat: 25.0478, lng: 121.5319, zoom: 12 },
  '新北市':  { lat: 25.0120, lng: 121.4653, zoom: 11 },
  '基隆市':  { lat: 25.1283, lng: 121.7419, zoom: 13 },
  '桃園市':  { lat: 24.9937, lng: 121.3009, zoom: 11 },
  '新竹市':  { lat: 24.8138, lng: 120.9675, zoom: 13 },
  '新竹縣':  { lat: 24.7036, lng: 121.1542, zoom: 11 },
  '苗栗縣':  { lat: 24.5602, lng: 120.8214, zoom: 11 },
  '臺中市':  { lat: 24.1477, lng: 120.6736, zoom: 12 },
  '彰化縣':  { lat: 23.9921, lng: 120.5161, zoom: 11 },
  '南投縣':  { lat: 23.9610, lng: 120.9718, zoom: 11 },
  '雲林縣':  { lat: 23.7092, lng: 120.4313, zoom: 11 },
  '嘉義市':  { lat: 23.4801, lng: 120.4491, zoom: 13 },
  '嘉義縣':  { lat: 23.4518, lng: 120.2555, zoom: 11 },
  '臺南市':  { lat: 22.9999, lng: 120.2270, zoom: 11 },
  '高雄市':  { lat: 22.6273, lng: 120.3014, zoom: 11 },
  '屏東縣':  { lat: 22.5519, lng: 120.5487, zoom: 11 },
  '宜蘭縣':  { lat: 24.7021, lng: 121.7378, zoom: 11 },
  '花蓮縣':  { lat: 23.9871, lng: 121.6015, zoom: 10 },
  '臺東縣':  { lat: 22.7972, lng: 121.0713, zoom: 10 },
  '澎湖縣':  { lat: 23.5654, lng: 119.5793, zoom: 12 },
  '金門縣':  { lat: 24.4493, lng: 118.3765, zoom: 12 },
  '連江縣':  { lat: 26.1605, lng: 119.9497, zoom: 13 },
  '全台灣':  { lat: 23.9739, lng: 120.9820, zoom:  8 },
}

export const ALL_CITIES = Object.keys(CITY_CENTERS)

export function useAnimals() {
  const animals = ref([])
  const locations = ref([])
  const loading = ref(true)
  const error = ref(null)
  const updatedAt = ref('')

  // Primary filters
  const currentCity = ref('臺中市')
  const filterKind = ref('all')       // 'all' | 'cat' | 'dog'

  // Secondary filters (shown in expandable panel)
  const filterSource = ref('all')     // 'all' | 'shelter' | 'vet_transit' | 'yiqi'
  const filterSex = ref('all')        // 'all' | 'M' | 'F'
  const filterColour = ref('all')     // 'all' | colour string

  // Derived: which source types exist in current city data
  const availableSources = computed(() => {
    const types = new Set(locations.value.map(l => l.type).filter(Boolean))
    return [...types]
  })

  // Derived: which colours exist in current city data
  const availableColours = computed(() => {
    const colours = new Set(animals.value.map(a => a.colour).filter(Boolean))
    return [...colours].sort()
  })

  // Build a location_id → location.type lookup
  const locationTypeMap = computed(() => {
    const map = {}
    locations.value.forEach(l => { map[l.id] = l.type })
    return map
  })

  const filteredAnimals = computed(() => {
    return animals.value.filter(a => {
      if (filterKind.value !== 'all' && a.kind !== filterKind.value) return false
      if (filterSource.value !== 'all') {
        const locType = locationTypeMap.value[a.location_id]
        if (locType !== filterSource.value) return false
      }
      if (filterSex.value !== 'all' && a.sex !== filterSex.value) return false
      if (filterColour.value !== 'all' && a.colour !== filterColour.value) return false
      return true
    })
  })

  const filteredLocations = computed(() => {
    const countMap = {}
    filteredAnimals.value.forEach(a => {
      if (!countMap[a.location_id]) countMap[a.location_id] = { cat: 0, dog: 0 }
      if (a.kind === 'cat') countMap[a.location_id].cat++
      else if (a.kind === 'dog') countMap[a.location_id].dog++
    })
    return locations.value
      .map(loc => ({ ...loc, counts: countMap[loc.id] || { cat: 0, dog: 0 } }))
      .filter(loc => loc.counts.cat + loc.counts.dog > 0)
  })

  function resetSecondaryFilters() {
    filterSource.value = 'all'
    filterSex.value = 'all'
    filterColour.value = 'all'
  }

  async function loadData(city = '臺中市') {
    loading.value = true
    error.value = null
    currentCity.value = city
    resetSecondaryFilters()

    try {
      const base = import.meta.env.BASE_URL
      const suffix = city === '全台灣' ? '全台' : city
      const [animalsRes, locationsRes] = await Promise.all([
        fetch(`${base}data/animals_${suffix}.json`),
        fetch(`${base}data/locations_${suffix}.json`),
      ])
      if (!animalsRes.ok) throw new Error(`無法載入動物資料：${animalsRes.status}`)
      if (!locationsRes.ok) throw new Error(`無法載入地點資料：${locationsRes.status}`)

      const animalsData = await animalsRes.json()
      const locationsData = await locationsRes.json()

      animals.value = animalsData.animals
      locations.value = locationsData.locations
      updatedAt.value = animalsData.updated_at
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return {
    animals,
    locations,
    loading,
    error,
    updatedAt,
    currentCity,
    filterKind,
    filterSource,
    filterSex,
    filterColour,
    availableSources,
    availableColours,
    filteredAnimals,
    filteredLocations,
    loadData,
    resetSecondaryFilters,
    CITY_CENTERS,
    ALL_CITIES,
  }
}
```

- [ ] **Step 2: Verify Vue dev server still starts**

```bash
cd d:/Projects/AdoptMap && pnpm dev
```

Expected: dev server starts, no console errors (data load will 404 until JSON files are renamed — that's OK for now, continue)

- [ ] **Step 3: Create per-city copies of existing data files**

The old `animals.json` / `locations.json` are kept in place (backward compat); we create new copies with the city-suffixed names:

```bash
cd d:/Projects/AdoptMap && cp public/data/animals.json public/data/animals_臺中市.json && cp public/data/locations.json public/data/locations_臺中市.json
```

Note: `filterArea` from the old `useAnimals.js` is dropped in the replacement. Verify no other component imports `filterArea` from `useAnimals`:

```bash
grep -r "filterArea" src/
```

Expected: zero results (the old ref was never wired to any UI component).

- [ ] **Step 4: Verify data loads correctly in browser**

Open http://localhost:5173/adopt-map/ — map should show 149 animals as before.

- [ ] **Step 5: Commit**

```bash
git add src/composables/useAnimals.js public/data/animals_臺中市.json public/data/locations_臺中市.json
git commit -m "feat: extend useAnimals with city switching and source/sex/colour filters"
```

---

### Task 5: Add `flyToCity` to `useMap.js`

**Files:**
- Modify: `src/composables/useMap.js`

- [ ] **Step 1: Add `flyToCity` to `useMap.js`**

Two changes:

**A — Add import at top of file** (alongside the existing `import L from 'leaflet'` line):

```javascript
import { CITY_CENTERS } from './useAnimals.js'
```

**B — Add `flyToCity` function inside `useMap()`, after the existing `flyTo` function**:

```javascript
function flyToCity(city) {
  const center = CITY_CENTERS[city]
  if (center && map) {
    map.flyTo([center.lat, center.lng], center.zoom, { duration: 1.2 })
  }
}
```

**C — Update the return object** (replace existing return line):

```javascript
return { initMap, updateMarkers, flyTo, flyToCity, invalidateSize, locateUser }
```

- [ ] **Step 2: Verify no import errors**

```bash
cd d:/Projects/AdoptMap && pnpm build 2>&1 | head -20
```

Expected: build succeeds (or only shows non-import errors)

- [ ] **Step 3: Commit**

```bash
git add src/composables/useMap.js
git commit -m "feat: add flyToCity to useMap"
```

---

## Chunk 3: Frontend — FilterBar & Toast

### Task 6: Create `ToastNotification.vue`

**Files:**
- Create: `src/components/ToastNotification.vue`

- [ ] **Step 1: Write `ToastNotification.vue`**

```vue
<!-- src/components/ToastNotification.vue -->
<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  message: { type: String, default: '' },
  duration: { type: Number, default: 3500 },
})

const visible = ref(false)
let timer = null

watch(() => props.message, (msg) => {
  if (!msg) return
  visible.value = true
  clearTimeout(timer)
  timer = setTimeout(() => { visible.value = false }, props.duration)
})
</script>

<template>
  <Transition name="toast">
    <div
      v-if="visible"
      class="fixed top-14 left-1/2 -translate-x-1/2 z-[2000] flex items-center gap-2
             bg-amber-400 text-gray-900 text-sm font-medium px-4 py-2.5 rounded-xl shadow-lg
             whitespace-nowrap pointer-events-none"
    >
      <span>⚠️</span>
      <span>{{ message }}</span>
    </div>
  </Transition>
</template>

<style scoped>
.toast-enter-active { transition: all 0.25s ease-out; }
.toast-leave-active { transition: all 0.3s ease-in; }
.toast-enter-from  { opacity: 0; transform: translate(-50%, -8px); }
.toast-leave-to    { opacity: 0; transform: translate(-50%, -8px); }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add src/components/ToastNotification.vue
git commit -m "feat: add ToastNotification component"
```

---

### Task 7: Rewrite `FilterBar.vue`

**Files:**
- Modify: `src/components/FilterBar.vue`

- [ ] **Step 1: Rewrite FilterBar.vue**

```vue
<!-- src/components/FilterBar.vue -->
<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  currentCity:      { type: String,  default: '臺中市' },
  allCities:        { type: Array,   default: () => [] },
  filterKind:       { type: String,  default: 'all' },
  filterSource:     { type: String,  default: 'all' },
  filterSex:        { type: String,  default: 'all' },
  filterColour:     { type: String,  default: 'all' },
  availableSources: { type: Array,   default: () => [] },
  availableColours: { type: Array,   default: () => [] },
  filteredCount:    { type: Number,  default: 0 },
})

const emit = defineEmits([
  'update:currentCity',
  'update:filterKind',
  'update:filterSource',
  'update:filterSex',
  'update:filterColour',
])

const panelOpen = ref(false)

const kindOptions = [
  { value: 'all', label: '全部', emoji: null },
  { value: 'cat', label: '貓',   emoji: '🐱' },
  { value: 'dog', label: '狗',   emoji: '🐶' },
]

const sexOptions = [
  { value: 'all', label: '全部' },
  { value: 'M',   label: '♂ 公' },
  { value: 'F',   label: '♀ 母' },
]

const SOURCE_LABELS = {
  all:         '全部',
  shelter:     '🏛️ 收容所',
  vet_transit: '🏥 中途醫院',
  yiqi:        '🟣 益起認養吧',
}

const sourceOptions = computed(() => {
  const opts = [{ value: 'all', label: '全部' }]
  for (const src of props.availableSources) {
    if (SOURCE_LABELS[src]) opts.push({ value: src, label: SOURCE_LABELS[src] })
  }
  return opts
})

// Count active secondary filters
const activeSecondaryCount = computed(() => {
  let n = 0
  if (props.filterSource !== 'all') n++
  if (props.filterSex !== 'all') n++
  if (props.filterColour !== 'all') n++
  return n
})

function onCityChange(e) {
  emit('update:currentCity', e.target.value)
}
</script>

<template>
  <div
    class="fixed top-0 left-0 right-0 z-[1000] bg-white/92 backdrop-blur-md border-b border-gray-100/80"
    style="box-shadow: 0 1px 12px rgba(0,0,0,0.08);"
  >
    <!-- Main row -->
    <div class="flex items-center gap-2 px-3 sm:px-4 py-2">
      <!-- Logo -->
      <span class="font-bold text-gray-800 text-sm whitespace-nowrap leading-none select-none">
        🗺&nbsp;<span class="hidden sm:inline">領養地圖</span>
      </span>

      <!-- City selector -->
      <select
        :value="currentCity"
        class="text-xs sm:text-sm border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-700
               focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer"
        @change="onCityChange"
      >
        <option v-for="city in allCities" :key="city" :value="city">
          {{ city === '全台灣' ? '🌏 ' + city : city }}
        </option>
      </select>

      <!-- Kind pills -->
      <div class="flex gap-1">
        <button
          v-for="opt in kindOptions"
          :key="opt.value"
          :class="[
            'px-2.5 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium transition-all',
            filterKind === opt.value
              ? 'bg-blue-600 text-white shadow-sm scale-105'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200 active:scale-95',
          ]"
          @click="emit('update:filterKind', opt.value)"
        >
          <span v-if="opt.emoji">{{ opt.emoji }}&nbsp;</span>{{ opt.label }}
        </button>
      </div>

      <!-- More filters button -->
      <button
        :class="[
          'ml-auto flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all',
          panelOpen
            ? 'bg-blue-50 text-blue-700 border border-blue-200'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        ]"
        @click="panelOpen = !panelOpen"
      >
        <span>⚙️ 更多篩選</span>
        <span
          v-if="activeSecondaryCount > 0"
          class="bg-amber-400 text-gray-900 rounded-full px-1.5 py-0 text-[10px] font-bold leading-4"
        >{{ activeSecondaryCount }}</span>
      </button>

      <!-- Count badge -->
      <span class="text-xs text-gray-400 whitespace-nowrap tabular-nums">
        <span class="font-semibold text-gray-600">{{ filteredCount }}</span> 隻
      </span>
    </div>

    <!-- Expandable secondary panel -->
    <Transition name="panel">
      <div
        v-if="panelOpen"
        class="flex flex-wrap items-center gap-x-4 gap-y-2 px-3 sm:px-4 py-2 border-t border-gray-100 bg-gray-50/80"
      >
        <!-- Source filter -->
        <div v-if="sourceOptions.length > 1" class="flex items-center gap-1.5">
          <span class="text-[11px] text-gray-400 font-medium">來源</span>
          <div class="flex gap-1">
            <button
              v-for="opt in sourceOptions"
              :key="opt.value"
              :class="[
                'px-2 py-0.5 rounded-full text-[11px] font-medium transition-all',
                filterSource === opt.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-100',
              ]"
              @click="emit('update:filterSource', opt.value)"
            >{{ opt.label }}</button>
          </div>
        </div>

        <!-- Sex filter -->
        <div class="flex items-center gap-1.5">
          <span class="text-[11px] text-gray-400 font-medium">性別</span>
          <div class="flex gap-1">
            <button
              v-for="opt in sexOptions"
              :key="opt.value"
              :class="[
                'px-2 py-0.5 rounded-full text-[11px] font-medium transition-all',
                filterSex === opt.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-100',
              ]"
              @click="emit('update:filterSex', opt.value)"
            >{{ opt.label }}</button>
          </div>
        </div>

        <!-- Colour filter -->
        <div v-if="availableColours.length > 0" class="flex items-center gap-1.5">
          <span class="text-[11px] text-gray-400 font-medium">毛色</span>
          <select
            :value="filterColour"
            class="text-[11px] border border-gray-200 rounded-lg px-2 py-0.5 bg-white text-gray-700
                   focus:outline-none focus:ring-1 focus:ring-blue-400 cursor-pointer"
            @change="emit('update:filterColour', $event.target.value)"
          >
            <option value="all">全部</option>
            <option v-for="colour in availableColours" :key="colour" :value="colour">
              {{ colour }}
            </option>
          </select>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.panel-enter-active { transition: all 0.2s ease-out; }
.panel-leave-active { transition: all 0.15s ease-in; }
.panel-enter-from   { opacity: 0; transform: translateY(-4px); }
.panel-leave-to     { opacity: 0; transform: translateY(-4px); }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add src/components/FilterBar.vue
git commit -m "feat: rewrite FilterBar with city dropdown and expandable filter panel"
```

---

### Task 8: Wire everything together in `App.vue`

**Files:**
- Modify: `src/App.vue`

- [ ] **Step 1: Update App.vue**

Key changes:
1. Destructure new refs from `useAnimals()`
2. Destructure `flyToCity` from `useMap()` (via `MapView` ref)
3. Add `toastMessage` ref
4. Add `handleCityChange` function
5. Pass new props to `FilterBar`
6. Add `ToastNotification` component

Replace the `<script setup>` section:

```javascript
import { onMounted, onUnmounted, ref, nextTick } from 'vue'
import FilterBar from './components/FilterBar.vue'
import MapView from './components/MapView.vue'
import AnimalCard from './components/AnimalCard.vue'
import LegendPanel from './components/LegendPanel.vue'
import HoverPreview from './components/HoverPreview.vue'
import ToastNotification from './components/ToastNotification.vue'
import { useAnimals, ALL_CITIES } from './composables/useAnimals.js'

const {
  loading,
  error,
  updatedAt,
  currentCity,
  filterKind,
  filterSource,
  filterSex,
  filterColour,
  availableSources,
  availableColours,
  filteredAnimals,
  filteredLocations,
  loadData,
} = useAnimals()

const mapRef = ref(null)
const selectedLocation = ref(null)
const selectedAnimalIndex = ref(0)
const hoveredLocation = ref(null)
const hoveredPosition = ref(null)
const toastMessage = ref('')

const isMobile = ref(window.innerWidth < 640)
function onResize() { isMobile.value = window.innerWidth < 640 }

let hoverLeaveTimer = null

function onKeyDown(e) {
  if (e.key === 'Escape') closeCard()
}

onMounted(() => {
  loadData('臺中市')
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('resize', onResize)
})

async function handleCityChange(city) {
  if (city === '全台灣') {
    // Reset to '' first so the watch in ToastNotification fires even if message is unchanged
    toastMessage.value = ''
    await nextTick()
    toastMessage.value = '🌏 全台資料約 3000+ 筆，載入中…'
  }
  selectedLocation.value = null
  await loadData(city)
  // Fly map to new city center
  if (mapRef.value?.flyToCity) {
    mapRef.value.flyToCity(city)
  }
}

function handleLocationClick(payload) {
  if (payload && typeof payload === 'object' && 'location' in payload) {
    selectedLocation.value = payload.location
    selectedAnimalIndex.value = payload.animalIndex ?? 0
  } else {
    selectedLocation.value = payload
    selectedAnimalIndex.value = 0
  }
  hoveredLocation.value = null
  hoveredPosition.value = null
}

function closeCard() { selectedLocation.value = null }

function handleLocationHover(location, position) {
  clearTimeout(hoverLeaveTimer)
  if (location) {
    hoveredLocation.value = location
    hoveredPosition.value = position
  } else {
    hoverLeaveTimer = setTimeout(() => {
      hoveredLocation.value = null
      hoveredPosition.value = null
    }, 200)
  }
}

function onPreviewMouseEnter() { clearTimeout(hoverLeaveTimer) }
function onPreviewMouseLeave() {
  hoverLeaveTimer = setTimeout(() => {
    hoveredLocation.value = null
    hoveredPosition.value = null
  }, 150)
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleString('zh-TW', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}
```

Update `<template>` — add `ToastNotification` and new `FilterBar` props:

```html
<template>
  <div class="relative w-screen h-screen overflow-hidden">
    <!-- Toast -->
    <ToastNotification :message="toastMessage" />

    <!-- Filter bar -->
    <FilterBar
      :current-city="currentCity"
      :all-cities="ALL_CITIES"
      :filter-kind="filterKind"
      :filter-source="filterSource"
      :filter-sex="filterSex"
      :filter-colour="filterColour"
      :available-sources="availableSources"
      :available-colours="availableColours"
      :filtered-count="filteredAnimals.length"
      @update:current-city="handleCityChange"
      @update:filter-kind="val => filterKind = val"
      @update:filter-source="val => filterSource = val"
      @update:filter-sex="val => filterSex = val"
      @update:filter-colour="val => filterColour = val"
    />

    <!-- Legend panel (desktop only) -->
    <LegendPanel class="hidden sm:block" />

    <!-- Loading overlay -->
    <div v-if="loading" class="absolute inset-0 z-[2000] flex items-center justify-center bg-white/80">
      <div class="text-center text-gray-600">
        <div class="text-4xl mb-2">🗺</div>
        <div class="text-sm">載入中…</div>
      </div>
    </div>

    <!-- Error overlay -->
    <div v-if="error" class="absolute inset-0 z-[2000] flex items-center justify-center bg-white/90">
      <div class="text-center text-red-600">
        <div class="text-4xl mb-2">⚠️</div>
        <div class="text-sm">{{ error }}</div>
      </div>
    </div>

    <!-- Map: top offset increases when panel is open, but we keep it simple at 44px base -->
    <div class="absolute inset-0 top-[44px]">
      <MapView
        ref="mapRef"
        :locations="filteredLocations"
        @location-click="handleLocationClick"
        @location-hover="handleLocationHover"
      />
    </div>

    <!-- Hover preview (desktop only) -->
    <HoverPreview
      v-if="!isMobile"
      :location="hoveredLocation"
      :animals="filteredAnimals"
      :position="hoveredPosition"
      :map-top-offset="44"
      @mouseenter="onPreviewMouseEnter"
      @mouseleave="onPreviewMouseLeave"
      @select="handleLocationClick"
    />

    <!-- Desktop: slide-in panel -->
    <template v-if="!isMobile">
      <AnimalCard
        :location="selectedLocation"
        :animals="filteredAnimals"
        :initial-index="selectedAnimalIndex"
        @close="closeCard"
      />
    </template>

    <!-- Mobile: bottom sheet -->
    <template v-else>
      <Transition name="sheet-up">
        <div v-if="selectedLocation" class="absolute inset-x-0 bottom-0 z-[1001]" style="max-height:88vh;">
          <div class="fixed inset-0 bg-black/20 backdrop-blur-[1px]" @click="closeCard" />
          <div class="relative rounded-t-3xl overflow-hidden" style="background:rgba(255,255,255,0.99);box-shadow:0 -8px 40px rgba(0,0,0,0.18);">
            <div class="flex justify-center pt-3 pb-1">
              <div class="w-10 h-1.5 rounded-full bg-gray-300" />
            </div>
            <AnimalCard
              :location="selectedLocation"
              :animals="filteredAnimals"
              :initial-index="selectedAnimalIndex"
              mobile
              @close="closeCard"
            />
          </div>
        </div>
      </Transition>
    </template>

    <!-- Footer -->
    <div class="absolute bottom-4 left-4 z-[1000] text-xs text-gray-500 bg-white/80 backdrop-blur-sm px-2.5 py-1.5 rounded-lg hidden sm:block"
      style="box-shadow:0 1px 6px rgba(0,0,0,0.08);">
      資料更新：{{ formatDate(updatedAt) }}
      ｜資料來源：農業部動物認領養 Open Data
    </div>
  </div>
</template>
```

Keep the existing `<style>` block (sheet-up animation) unchanged.

- [ ] **Step 2: Expose `flyToCity` from `MapView.vue`**

Open `src/components/MapView.vue`. Make two changes:

**A — Update the `useMap` destructure line** (find the existing `const { initMap, updateMarkers, locateUser } = useMap()` line and replace with):

```javascript
const { initMap, updateMarkers, flyToCity, locateUser } = useMap()
```

(`flyTo` and `invalidateSize` are only used internally in `useMap.js` so they don't need to be destructured here.)

**B — Add `defineExpose`** (add at the end of `<script setup>`, before `</script>`):

```javascript
defineExpose({ flyToCity })
```

- [ ] **Step 3: Verify in browser**

Start dev server and verify:
- Map loads with 台中市 data
- City dropdown switches city and flies map
- 全台灣 shows toast
- 更多篩選 opens panel with source/sex/colour
- Filtering works correctly

```bash
cd d:/Projects/AdoptMap && pnpm dev
```

- [ ] **Step 4: Commit**

```bash
git add src/App.vue src/components/MapView.vue
git commit -m "feat: wire city switching, source/sex/colour filters in App.vue"
```

---

## Chunk 4: Data files & CI

### Task 9: Ensure old `animals.json` / `locations.json` still exist as fallback

**Files:**
- `public/data/animals.json` (keep, but it will be superseded)

- [ ] **Step 1: Keep old files as symlink or copy for deploy compatibility**

The old filenames (`animals.json`, `locations.json`) are no longer loaded by the frontend. They can remain for backward compatibility but are not required. No action needed.

- [ ] **Step 2: Update GitHub Actions `update-data.yml` to commit new per-city files**

In `.github/workflows/update-data.yml`, update the commit step:

```yaml
      - name: Commit and push data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add public/data/ scripts/.cache/
          git diff --cached --quiet || git commit -m "chore: update animal data $(date +%Y-%m-%d)"
          git push
```

No change needed — `git add public/data/` already picks up all new per-city files.

- [ ] **Step 3: Confirm no workflow changes needed**

The existing `git add public/data/` in `update-data.yml` already picks up all new per-city files — no changes required. Skip this step if there are no other workflow modifications.

---

### Task 10: Add `.gitignore` entry for brainstorm files

**Files:**
- `.gitignore`

- [ ] **Step 1: Add `.superpowers/` to `.gitignore`**

```bash
cd d:/Projects/AdoptMap && echo '.superpowers/' >> .gitignore
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore .superpowers/ brainstorm files"
```

---

### Task 11: Final integration test

- [ ] **Step 1: Run full build to ensure no TypeScript/Vite errors**

```bash
cd d:/Projects/AdoptMap && pnpm build
```

Expected: build completes without errors. `dist/` contains the built app.

- [ ] **Step 2: Smoke test in browser**

```bash
cd d:/Projects/AdoptMap && pnpm preview
```

Open the preview URL and verify:
1. Default city is 臺中市, map centers on Taichung
2. 全部 / 貓 / 狗 pills filter markers
3. 更多篩選 panel opens; source options match actual data (shelter, vet_transit, yiqi for 台中市)
4. Sex filter (公/母) reduces animal count
5. Colour dropdown shows actual colours from data
6. City dropdown — switching to any other city shows empty or loads data
7. Selecting 全台灣 shows amber toast
8. FilterBar secondary filters reset when city changes

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: Phase 5 complete — city switching, source/sex/colour filters"
```
