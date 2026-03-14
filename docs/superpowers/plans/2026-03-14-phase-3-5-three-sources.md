# Phase 3.5 三種來源完整支援 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 爬取台中市動保處「待認養犬貓照片檢索」網站（149 筆），解析三種來源（收容所 / 益起認養吧 / 中途動物醫院），並整合至現有 `build_data.py`。

> ⚠️ **重要說明（2026-03-14 驗證）**：台中市動保處網站（`animal.taichung.gov.tw/1521490`）是**獨立系統**，與農業部 Open Data API 不同。
> 農業部 API 目前台中資料只有 82 筆（南屯 36 + 后里 46 兩個收容所），中途動物醫院與益起認養吧的 67 筆**不在農業部 API 裡**，必須爬取台中市動保處網站才能取得。

**Architecture:** 新增 `scripts/scrape_taichung.py` 爬蟲，爬取台中市動保處列表頁（5 頁）和每筆動物詳細頁，解析欄位後整合至 `build_data.py`。`parse_remark_location()` 已實作於 `fetch_animals.py`，抽出至共用模組供爬蟲使用。前端 `AnimalCard.vue` 已新增 `yiqi` 標籤（紫色）。

**Tech Stack:** Python 3.11+（regex, requests）、Vue 3 Composition API、Tailwind CSS

---

## Chunk 1: Python 後端 — 備註解析與來源辨識

### 資料格式確認（調查所得）

三種 `所在園區` 欄位值與對應備註格式：

| `所在園區` | `_location_type` | 備註格式 | 地址取得 |
|-----------|----------------|---------|---------|
| `南屯園區` / `后里園區` | `shelter` | 無或健康說明 | `KNOWN_LOCATIONS` 固定座標 |
| `中途動物醫院` | `vet_transit` | `我在 " 區域 店名 " 等待...電話：XXXX`（無地址） | 店名 geocoding |
| `益起認養吧` | `yiqi` | `我在區域"店名"等待...電話：XXXX 台中市XX區XX路XX號` | 備註末尾地址直接解析 |

### Task 1: 安裝 pytest 並建立測試基礎

**Files:**
- Modify: `scripts/requirements.txt`
- Create: `scripts/tests/__init__.py`
- Create: `scripts/tests/test_parse_remark.py`

- [ ] **Step 1: 新增 pytest 到 requirements.txt**

在 `scripts/requirements.txt` 末尾加入：
```
pytest==8.3.5
urllib3==2.3.0
```

- [ ] **Step 2: 安裝依賴**

```bash
cd scripts
pip install -r requirements.txt
```

Expected: Successfully installed pytest...

- [ ] **Step 3: 建立測試目錄**

```bash
mkdir -p scripts/tests
touch scripts/tests/__init__.py
```

- [ ] **Step 4: 建立測試檔，寫入失敗測試**

建立 `scripts/tests/test_parse_remark.py`：

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fetch_animals import parse_remark_location

# --- 中途動物醫院 ---

def test_vet_transit_basic():
    remark = '我在 " 南屯區 信揚動物醫院 " 等待愛心認養喔！歡迎打電話詢問或預約互動時間，聯絡電話：04-24730000'
    result = parse_remark_location(remark, '中途動物醫院')
    assert result['type'] == 'vet_transit'
    assert '信揚動物醫院' in result['name']
    assert result['address'] == ''
    assert result['phone'] == '04-24730000'

def test_vet_transit_no_quotes():
    remark = '我在西區 台中動物醫院 等待認養，電話：04-12345678'
    result = parse_remark_location(remark, '中途動物醫院')
    assert result['type'] == 'vet_transit'
    assert result['name'] == ''      # 無引號 → 店名未知，geocoding 會 fallback 到 shelter_name
    assert result['address'] == ''

# --- 益起認養吧 ---

def test_yiqi_with_full_address():
    remark = '我在西屯區"東森寵物台中澄清店"等待愛心認養喔！聯絡電話：04-24618811 台中市西屯區西屯路三段92-1號'
    result = parse_remark_location(remark, '益起認養吧')
    assert result['type'] == 'yiqi'
    assert '東森寵物台中澄清店' in result['name']
    assert result['address'] == '台中市西屯區西屯路三段92-1號'
    assert result['phone'] == '04-24618811'

def test_yiqi_another_store():
    remark = '我在大里區"魚中魚大里店"等待主人的愛心認養喔！聯絡電話：04-24073388 台中市大里區國光路二段505號'
    result = parse_remark_location(remark, '益起認養吧')
    assert result['type'] == 'yiqi'
    assert result['address'] == '台中市大里區國光路二段505號'

def test_yiqi_pet_park_store():
    remark = '我在大里區"寵物公園大里成功店"等待主人的愛心認養喔！聯絡電話：04-24910650 台中市大里區成功路498號'
    result = parse_remark_location(remark, '益起認養吧')
    assert result['type'] == 'yiqi'
    assert result['address'] == '台中市大里區成功路498號'

# --- 收容所（備註不觸發解析）---

def test_shelter_no_remark():
    result = parse_remark_location('', '南屯園區')
    assert result is None

def test_shelter_health_remark():
    result = parse_remark_location('左側骨盆斷跛行，目前日常行動OK，局部脫毛。', '后里園區')
    assert result is None

# --- fallback ---

def test_unknown_shelter_type_returns_none():
    result = parse_remark_location('隨意備註', '未知')
    assert result is None
```

- [ ] **Step 5: 執行測試確認失敗**

```bash
cd scripts
python -m pytest tests/test_parse_remark.py -v
```

Expected: ImportError 或多個 FAILED（`parse_remark_location` 尚未存在）

---

### Task 2: 實作 `parse_remark_location`

**Files:**
- Modify: `scripts/fetch_animals.py`（新增函式、更新 `fetch_animals` 主邏輯）

- [ ] **Step 1: 移除舊函式 `_extract_vet_transit_info`**

刪除 `scripts/fetch_animals.py` 第 85–100 行（整個 `_extract_vet_transit_info` 函式）。

- [ ] **Step 2: 在原位置新增 `parse_remark_location` 函式**

在剛才刪除的位置（約第 85 行）插入：

```python
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
        name_match = re.search(r'["""](.*?)["""]', remark)
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
        name_match = re.search(r'["""]\s*(.*?)\s*["""]', remark)
        if name_match:
            # 格式通常是 "區域 店名"，取最後一個詞（店名）
            name_parts = name_match.group(1).strip().split()
            name = "".join(name_parts[1:]) if len(name_parts) > 1 else name_match.group(1).strip()
        else:
            name = ""
        return {"type": "vet_transit", "name": name, "address": "", "phone": phone}

    return None
```

- [ ] **Step 3: 執行測試確認通過**

```bash
cd scripts
python -m pytest tests/test_parse_remark.py -v
```

Expected: 全部 PASSED（8 個測試）

- [ ] **Step 4: 更新 `fetch_animals` 主邏輯**

在 `fetch_animals()` 函式中，找到這段（刪除舊函式後約第 127-139 行）：

```python
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
```

替換為：

```python
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
```

同時更新 `animals.append({...})` 中的 `"_shelter_name"` 欄位，加入 parsed 的 name 和 phone：

找到原本的（約第 157-178 行）：
```python
        animals.append({
            ...
            # 以下欄位供 build_data.py 組合地點時使用，不進入最終 JSON
            "_shelter_name": shelter_name,
            "_shelter_address": shelter_address,
            "_shelter_phone": rec.get("shelter_tel", "") or "",
            "_geo_address": geo_address,
            "_location_type": location_type,
```

替換為：
```python
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
```

- [ ] **Step 5: 再次執行測試確認仍通過**

```bash
cd scripts
python -m pytest tests/test_parse_remark.py -v
```

Expected: 全部 PASSED

- [ ] **Step 6: commit**

```bash
git add scripts/fetch_animals.py scripts/requirements.txt scripts/tests/
git commit -m "feat: parse remark for vet_transit and yiqi location types"
```

---

### Task 3: 更新 `config.py` — 新增 `yiqi` 來源常數

**Files:**
- Modify: `scripts/config.py`

- [ ] **Step 1: 新增來源類型常數**

在 `config.py` 末尾加入：

```python
# 來源類型常數（對應 location.type）
LOCATION_TYPES = {
    "shelter": "公立收容所",
    "vet_transit": "中途動物醫院",
    "yiqi": "益起認養吧",
}
```

- [ ] **Step 2: commit**

```bash
git add scripts/config.py
git commit -m "feat: add LOCATION_TYPES constant with yiqi source type"
```

---

## Chunk 2: Python 後端 — 整合測試與執行驗證

### Task 4: 新增整合測試（本地乾跑）

**Files:**
- Create: `scripts/tests/test_build_integration.py`

- [ ] **Step 1: 建立整合測試**

建立 `scripts/tests/test_build_integration.py`：

```python
"""
整合測試：驗證從 API 資料到最終 JSON 的完整流程。
使用靜態測試資料（不呼叫真實 API）。
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fetch_animals import parse_remark_location, _map_kind, _map_sex

# 模擬三種來源的 API 原始記錄（精簡版）
MOCK_SHELTER_RECORD = {
    "animal_place": "臺中市動物之家南屯園區",
    "shelter_name": "臺中市動物之家南屯園區",
    "animal_remark": "",
}

MOCK_VET_RECORD = {
    "animal_place": "臺中市動物之家中途動物醫院",
    "shelter_name": "臺中市動物之家中途動物醫院",
    "animal_remark": '我在 " 南屯區 信揚動物醫院 " 等待愛心認養喔！聯絡電話：04-24730000',
}

MOCK_YIQI_RECORD = {
    "animal_place": "臺中市動物之家益起認養吧",
    "shelter_name": "臺中市動物之家益起認養吧",
    "animal_remark": '我在西屯區"東森寵物台中澄清店"等待愛心認養喔！聯絡電話：04-24618811 台中市西屯區西屯路三段92-1號',
}


def _extract_zone(animal_place: str) -> str:
    for zone in ("南屯園區", "后里園區", "中途動物醫院", "益起認養吧"):
        if animal_place.endswith(zone):
            return zone
    return animal_place


def test_shelter_zone_extraction():
    assert _extract_zone("臺中市動物之家南屯園區") == "南屯園區"
    assert _extract_zone("臺中市動物之家后里園區") == "后里園區"
    assert _extract_zone("臺中市動物之家中途動物醫院") == "中途動物醫院"
    assert _extract_zone("臺中市動物之家益起認養吧") == "益起認養吧"


def test_shelter_returns_none():
    zone = _extract_zone(MOCK_SHELTER_RECORD["animal_place"])
    result = parse_remark_location(MOCK_SHELTER_RECORD["animal_remark"], zone)
    assert result is None


def test_vet_parsed_correctly():
    zone = _extract_zone(MOCK_VET_RECORD["animal_place"])
    result = parse_remark_location(MOCK_VET_RECORD["animal_remark"], zone)
    assert result is not None
    assert result["type"] == "vet_transit"
    assert "信揚動物醫院" in result["name"]
    assert result["address"] == ""
    assert result["phone"] == "04-24730000"


def test_yiqi_parsed_correctly():
    zone = _extract_zone(MOCK_YIQI_RECORD["animal_place"])
    result = parse_remark_location(MOCK_YIQI_RECORD["animal_remark"], zone)
    assert result is not None
    assert result["type"] == "yiqi"
    assert "東森寵物台中澄清店" in result["name"]
    assert result["address"] == "台中市西屯區西屯路三段92-1號"
    assert result["phone"] == "04-24618811"
```

- [ ] **Step 2: 執行所有測試**

```bash
cd scripts
python -m pytest tests/ -v
```

Expected: 全部 PASSED（12 個測試）

- [ ] **Step 3: commit**

```bash
git add scripts/tests/test_build_integration.py
git commit -m "test: add integration tests for three source types"
```

---

### Task 5: 本地執行 build_data.py 驗證輸出

**Files:**
- Read: `public/data/animals.json`（執行後驗證）
- Read: `public/data/locations.json`（執行後驗證）

- [ ] **Step 1: 執行 build_data.py**

```bash
cd scripts
python build_data.py
```

Expected 輸出包含：
```
開始抓取農業部 API 資料...
台中市動物 149 筆
需要 geocoding 的地址共 N 個
地點共 N 個
✅ 完成！共 XXX 隻（貓 XX / 狗 XX），N 個地點
```

- [ ] **Step 2: 驗證輸出 JSON 包含三種 type**

```bash
cd scripts
python -c "
import json
data = json.load(open('../public/data/locations.json', encoding='utf-8'))
types = set(l['type'] for l in data['locations'])
print('Location types:', types)
assert 'shelter' in types, 'missing shelter'
assert 'vet_transit' in types, 'missing vet_transit'
assert 'yiqi' in types, 'missing yiqi'
print('✅ All three types present')
"
```

Expected: `✅ All three types present`

- [ ] **Step 3: commit**

```bash
git add public/data/animals.json public/data/locations.json scripts/.cache/
git commit -m "data: update animals.json with three source types (shelter/vet_transit/yiqi)"
```

---

## Chunk 3: 前端 — AnimalCard 顯示 yiqi 標籤

### Task 6: 更新 AnimalCard.vue 支援 yiqi 來源

**Files:**
- Modify: `src/components/AnimalCard.vue`

目前 `AnimalCard.vue` 已有 `typeLabel` 和 `typeColor`，但缺少 `yiqi`。

- [ ] **Step 1: 更新 typeLabel 和 typeColor**

找到 `AnimalCard.vue` 中（約第 41-51 行）：

```javascript
const typeLabel = {
  shelter: '公立收容所',
  vet_transit: '中途動物醫院',
  bulletin: '民眾送養',
}

const typeColor = {
  shelter: 'bg-blue-100 text-blue-700',
  vet_transit: 'bg-green-100 text-green-700',
  bulletin: 'bg-orange-100 text-orange-700',
}
```

替換為：

```javascript
const typeLabel = {
  shelter: '公立收容所',
  vet_transit: '中途動物醫院',
  yiqi: '益起認養吧',
  bulletin: '民眾送養',
}

const typeColor = {
  shelter: 'bg-blue-100 text-blue-700',
  vet_transit: 'bg-green-100 text-green-700',
  yiqi: 'bg-purple-100 text-purple-700',
  bulletin: 'bg-orange-100 text-orange-700',
}
```

- [ ] **Step 2: 本地啟動確認顯示**

```bash
npm run dev
```

開啟瀏覽器，點擊地圖上的益起認養吧地點，確認標籤顯示「益起認養吧」紫色標籤。

- [ ] **Step 3: commit**

```bash
git add src/components/AnimalCard.vue
git commit -m "feat: add yiqi source label and color in AnimalCard"
```

---

### Task 7: 最終驗證與部署

- [ ] **Step 1: 執行所有 Python 測試**

```bash
cd scripts
python -m pytest tests/ -v
```

Expected: 全部 PASSED

- [ ] **Step 2: 前端 build**

```bash
npm run build
```

Expected: 無 error

- [ ] **Step 3: 確認 dist 產出正確**

```bash
ls dist/data/
```

Expected: `animals.json` 和 `locations.json` 存在

- [ ] **Step 4: 最終 commit**

```bash
git add -A
git commit -m "feat: Phase 3.5 — 三種來源完整支援 (shelter/vet_transit/yiqi)"
```

---

## 附錄：關鍵資料樣本

### 中途動物醫院備註範例
```
我在 " 南屯區 信揚動物醫院 " 等待愛心認養喔！歡迎打電話詢問或預約互動時間，聯絡電話：04-24730000
```
- 店名在 `"..."` 之間，格式 `區域 店名`
- 無完整地址，geocoding 用店名

### 益起認養吧備註範例
```
我在西屯區"東森寵物台中澄清店"等待愛心認養喔！聯絡電話：04-24618811 台中市西屯區西屯路三段92-1號
我在大里區"魚中魚大里店"等待主人的愛心認養喔！聯絡電話：04-24073388 台中市大里區國光路二段505號
我在北屯區"咪喜寵物旅店"等待主人的愛心認養喔！聯絡電話：0937206805 台中市北屯區北華街119號
```
- 店名在 `"..."` 之間
- 完整地址在電話後（台中市 開頭）

### `animal_place` 欄位值（截至 2026-03-14）
```
臺中市動物之家南屯園區   → shelter_zone = "南屯園區"
臺中市動物之家后里園區   → shelter_zone = "后里園區"
臺中市動物之家中途動物醫院 → shelter_zone = "中途動物醫院"
臺中市動物之家益起認養吧  → shelter_zone = "益起認養吧"
```
