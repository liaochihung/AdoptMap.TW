# 領養地圖 (adopt-map) — 專案規格書

> 本文件用於指導 Claude Code CLI 建立完整專案。
> 請在空目錄中執行 `claude` 並提供此文件作為上下文。

---

## 1. 專案概述

### 1.1 目標

建立一個以地圖為核心的台中市待領養犬貓資訊平台。使用者可以在地圖上一眼看到哪些位置有待領養的寵物，透過篩選找到想要的貓或狗，點擊地圖標記即可查看寵物詳細資訊。

### 1.2 要解決的問題

- 台中市動保處官網無法依貓/狗篩選，也無法在列表頁看到寵物所在位置
- 寵物可能分散在動物之家（南屯/后里）、中途動物醫院、民間送養等不同地點
- 現有第三方網站（如「我愛毛小孩」）只有列表檢視，缺乏地圖視覺化

### 1.3 核心功能

- 地圖全版顯示，以台中市為中心
- 地圖上標記各地點，依該地點有貓/狗數量顯示聚合圖示
- 點擊標記彈出寵物卡片（照片、品種、性別、體型、來源連結）
- 頂部篩選列：全部 / 貓 / 狗，可額外篩選地區
- 資料來源標示與最後更新時間

### 1.4 命名

- **網站名稱**：領養地圖
- **GitHub Repo**：`adopt-map`
- **GitHub Pages URL**：`{username}.github.io/adopt-map`
- **Meta Description**：台中市待領養犬貓地圖 — 一眼找到離你最近的毛孩

---

## 2. 技術棧

| 層級 | 技術 | 說明 |
|------|------|------|
| 前端框架 | Vue 3 (Composition API) | 使用 `<script setup>` 語法 |
| 建構工具 | Vite | Vue 官方推薦，輸出靜態檔案 |
| 地圖 | Leaflet 1.9+ | 原生使用，不用 vue-leaflet 封裝 |
| 地圖圖磚 | OpenStreetMap | 完全免費，不需 API Key |
| CSS | Tailwind CSS 3 | 透過 PostCSS 整合至 Vite |
| 資料排程 | GitHub Actions (cron) | 每日自動更新資料 |
| 排程腳本 | Python 3.11+ | 抓取 API、爬蟲、geocoding |
| 部署 | GitHub Pages | 靜態託管，完全免費 |

### 2.1 為什麼不用 vue-leaflet

vue-leaflet 的 Vue 3 版本 (`@vue-leaflet/vue-leaflet`) 維護狀態不穩定，且原生 Leaflet API 非常直觀。直接使用原生 leaflet 搭配 Vue 的 `onMounted` / `watch` 即可，減少一層抽象，也更好 debug。

### 2.2 費用

**$0** — 所有服務均為免費方案：
- GitHub Pages：免費靜態託管
- GitHub Actions：公開 repo 免費（每月 2000 分鐘）
- 農業部 Open Data API：免費公開資料
- OpenStreetMap + Leaflet：完全免費開源
- Nominatim geocoding：免費（限每秒 1 次請求）

---

## 3. 資料來源

### 3.1 農業部動物認領養 Open Data API

- **端點**：`https://data.moa.gov.tw/Service/OpenData/TransService.aspx?UnitId=QcbUEzN6E6DL`
- **格式**：JSON
- **更新頻率**：每日
- **授權**：政府資料開放授權條款第 1 版（免費）
- **篩選方式**：支援 `$top`、`$skip`、`$filter` 參數
  - 範例：`$filter=animal_kind+like+貓`
  - 組合：`$filter=animal_kind+like+貓+and+animal_colour+like+黑色`
- **主要欄位**：

| 欄位名 | 說明 | 範例 |
|--------|------|------|
| `animal_id` | 動物編號 | 12345 |
| `animal_kind` | 種類 | 貓/犬 |
| `animal_sex` | 性別 | M/F |
| `animal_bodytype` | 體型 | SMALL/MEDIUM/LARGE |
| `animal_colour` | 毛色 | 黑色 |
| `animal_age` | 年齡 | ADULT/CHILD |
| `animal_sterilization` | 是否絕育 | T/F/N（是/否/未輸入） |
| `animal_bacterin` | 是否注射疫苗 | T/F/N |
| `animal_place` | 收容場所 | 臺中市動物之家南屯園區 |
| `shelter_name` | 收容所名稱 | 臺中市動物之家南屯園區 |
| `shelter_address` | 收容所地址 | 臺中市南屯區中台路601號 |
| `shelter_tel` | 聯絡電話 | 04-23850949 |
| `album_file` | 照片 URL | https://... |
| `album_update` | 資料更新時間 | 2026/03/13 |
| `animal_remark` | 備註 | 可能包含中途醫院資訊 |
| `animal_opendate` | 開放認養日期 | 2026/03/01 |
| `animal_update` | 異動時間 | 2026/03/13 |
| `cDate` | 建立時間 | 2026/01/15 |

- **篩選台中市資料**：使用 `$filter=animal_place+like+臺中` 或在本地端過濾 `shelter_name` 或 `shelter_address` 包含「臺中」
- **特別注意**：
  - 已被領養的動物會自動從 API 下架
  - `animal_remark` 欄位可能包含中途動物醫院名稱與地址

### 3.2 台中市動保處 — 民眾寵物送養佈告欄

- **網址**：`https://www.animal.taichung.gov.tw/1521448/1521481/1521495/1521497/1521500`
- **格式**：HTML（需爬蟲）
- **目前筆數**：約 292 筆
- **取得方式**：Python 爬蟲（requests + BeautifulSoup）
- **需取得欄位**：寵物名稱、種類、聯絡人、聯絡電話、地點描述、照片
- **特別注意**：
  - 這是 ASP.NET 後端，分頁可能需要處理 ViewState
  - 地址資訊不一定結構化，可能需要從描述文字中解析
  - 刊登時間為 3 個月，過期自動下架

### 3.3 Geocoding（地址轉經緯度）

- **服務**：OpenStreetMap Nominatim
- **端點**：`https://nominatim.openstreetmap.org/search`
- **限制**：每秒 1 次請求（在 GitHub Actions 裡跑即可）
- **策略**：
  - 收容所地址（南屯、后里等）為固定地點，座標直接寫死在設定檔中
  - 中途動物醫院地址較少變動，geocode 後快取結果，僅新地址需查詢
  - 送養佈告欄的地址可能模糊，需做 fallback 處理（如無法解析則歸類到「未知地點」）
- **快取設計**：`geocode_cache.json` 記錄已查詢過的地址與座標，避免重複請求

---

## 4. 專案目錄結構

```
adopt-map/
├── public/
│   └── data/                    # 靜態資料（GitHub Actions 每日更新）
│       ├── animals.json         # 所有待領養動物（含座標）
│       └── locations.json       # 地點彙整（地點名 + 座標 + 動物數量）
│
├── src/
│   ├── components/
│   │   ├── MapView.vue          # Leaflet 地圖容器
│   │   ├── FilterBar.vue        # 頂部篩選列（貓/狗/全部 + 地區）
│   │   ├── AnimalCard.vue       # 寵物資訊彈窗卡片
│   │   └── AnimalList.vue       # 側邊/底部清單（選用，MVP 可先不做）
│   │
│   ├── composables/
│   │   ├── useAnimals.js        # 載入 JSON、篩選邏輯、computed
│   │   └── useMap.js            # Leaflet 初始化、marker 管理、事件
│   │
│   ├── assets/
│   │   ├── main.css             # Tailwind 進入點
│   │   └── markers/             # 自訂地圖標記圖示
│   │       ├── cat.svg
│   │       ├── dog.svg
│   │       └── mixed.svg
│   │
│   ├── App.vue                  # 主佈局
│   └── main.js                  # 進入點
│
├── scripts/                     # Python 排程腳本
│   ├── fetch_animals.py         # 呼叫農業部 API，篩選台中市資料
│   ├── scrape_bulletin.py       # 爬台中市動保處送養佈告欄
│   ├── geocode.py               # 地址轉經緯度（含快取）
│   ├── build_data.py            # 主控腳本：呼叫上述三支，產出最終 JSON
│   ├── requirements.txt         # Python 依賴（requests, beautifulsoup4）
│   └── config.py                # 固定座標設定、API 端點等常數
│
├── .github/
│   └── workflows/
│       ├── update-data.yml      # 每日資料更新排程
│       └── deploy.yml           # 前端 build + 部署到 GitHub Pages
│
├── index.html                   # Vite 進入 HTML
├── vite.config.js               # Vite 設定（含 base path）
├── tailwind.config.js           # Tailwind 設定
├── postcss.config.js            # PostCSS 設定
├── package.json
└── README.md
```

---

## 5. 資料結構設計

### 5.1 animals.json

這是主要的資料檔案，包含所有待領養動物的資訊。

```json
{
  "updated_at": "2026-03-13T06:00:00+08:00",
  "total": 168,
  "animals": [
    {
      "id": "GOV-12345",
      "source": "gov_shelter",
      "kind": "cat",
      "name": "",
      "sex": "F",
      "age": "adult",
      "bodytype": "small",
      "colour": "黑色",
      "sterilized": true,
      "vaccinated": true,
      "photo_url": "https://asms.coa.gov.tw/...",
      "remark": "",
      "open_date": "2026-03-01",
      "update_date": "2026-03-13",
      "location_id": "loc_nantun",
      "source_url": "https://www.pet.gov.tw/..."
    },
    {
      "id": "BUL-00123",
      "source": "bulletin",
      "kind": "dog",
      "name": "小黑",
      "sex": "M",
      "age": "adult",
      "bodytype": "medium",
      "colour": "黑色",
      "sterilized": null,
      "vaccinated": null,
      "photo_url": "https://www.animal.taichung.gov.tw/media/...",
      "remark": "個性溫馴，親人",
      "open_date": "2026-02-15",
      "update_date": "2026-03-10",
      "location_id": "loc_custom_001",
      "contact_name": "王先生",
      "contact_phone": "0912-345-678",
      "source_url": "https://www.animal.taichung.gov.tw/..."
    }
  ]
}
```

#### 欄位說明

| 欄位 | 型別 | 說明 |
|------|------|------|
| `id` | string | 唯一識別碼。政府資料前綴 `GOV-`，佈告欄前綴 `BUL-` |
| `source` | string | `"gov_shelter"` 或 `"bulletin"` |
| `kind` | string | `"cat"` 或 `"dog"` |
| `name` | string | 動物名字（官方資料通常無名字，佈告欄可能有） |
| `sex` | string | `"M"` / `"F"` / `"N"`（未知） |
| `age` | string | `"adult"` / `"child"`（幼年） |
| `bodytype` | string | `"small"` / `"medium"` / `"large"` |
| `colour` | string | 毛色（原始中文） |
| `sterilized` | bool/null | 是否絕育 |
| `vaccinated` | bool/null | 是否注射疫苗 |
| `photo_url` | string | 照片網址 |
| `remark` | string | 備註 |
| `open_date` | string | 開放認養日期 (YYYY-MM-DD) |
| `update_date` | string | 資料更新日期 (YYYY-MM-DD) |
| `location_id` | string | 對應 locations.json 的地點 ID |
| `source_url` | string | 原始資料來源網址 |
| `contact_name` | string | （僅佈告欄）聯絡人 |
| `contact_phone` | string | （僅佈告欄）聯絡電話 |

### 5.2 locations.json

地點的彙整資料，包含座標，避免前端重複計算。

```json
{
  "updated_at": "2026-03-13T06:00:00+08:00",
  "locations": [
    {
      "id": "loc_nantun",
      "name": "臺中市動物之家南屯園區",
      "address": "臺中市南屯區中台路601號",
      "phone": "04-23850949",
      "lat": 24.1366,
      "lng": 120.6175,
      "type": "shelter",
      "counts": { "cat": 42, "dog": 65 }
    },
    {
      "id": "loc_houli",
      "name": "臺中市動物之家后里園區",
      "address": "臺中市后里區堤防路370號",
      "phone": "04-25588024",
      "lat": 24.3049,
      "lng": 120.7106,
      "type": "shelter",
      "counts": { "cat": 18, "dog": 30 }
    },
    {
      "id": "loc_vet_001",
      "name": "OO動物醫院（中途收容）",
      "address": "臺中市西區...",
      "phone": "04-2222-3333",
      "lat": 24.1500,
      "lng": 120.6600,
      "type": "vet_transit",
      "counts": { "cat": 3, "dog": 1 }
    },
    {
      "id": "loc_custom_001",
      "name": "民眾送養 — 北屯區",
      "address": "臺中市北屯區...",
      "phone": "",
      "lat": 24.1820,
      "lng": 120.6890,
      "type": "bulletin",
      "counts": { "cat": 0, "dog": 1 }
    }
  ]
}
```

#### 地點類型 (type)

| type | 說明 | 地圖標記顏色建議 |
|------|------|----------------|
| `shelter` | 公立收容所 | 藍色 |
| `vet_transit` | 中途動物醫院 | 綠色 |
| `bulletin` | 民眾送養佈告欄 | 橘色 |

---

## 6. 前端元件規格

### 6.1 App.vue — 主佈局

```
┌──────────────────────────────────────┐
│  FilterBar（固定於頂部，z-index 高）    │
├──────────────────────────────────────┤
│                                      │
│           MapView（地圖全版）           │
│                                      │
│     [marker] [marker]                │
│              [marker]                │
│                    [marker]          │
│                                      │
│  ┌────────────────┐                  │
│  │  AnimalCard    │  ← 點擊彈出      │
│  │  (popup/panel) │                  │
│  └────────────────┘                  │
│                                      │
│  ┌─────────────────────────┐         │
│  │  更新時間 │ 資料來源聲明   │         │
│  └─────────────────────────┘         │
└──────────────────────────────────────┘
```

### 6.2 FilterBar.vue

- 固定於畫面頂部 (`fixed top-0`)，半透明背景
- 三個按鈕：全部 / 貓 / 狗（toggle 切換，active 有明顯視覺反饋）
- 可選：地區下拉選單（依 locations.json 的地點動態生成）
- 可選：搜尋框（搜尋動物編號或備註文字）
- 篩選結果數量顯示（如「顯示 42 隻貓」）
- 響應式：手機版可折疊為漢堡選單或底部工具列

### 6.3 MapView.vue

- 使用 `onMounted` 初始化 Leaflet 地圖
- 初始視角：台中市中心 `[24.15, 120.67]`，zoom 12
- 圖磚：OpenStreetMap 預設圖層
- 使用 `watch` 監聽篩選條件變化，動態更新 markers
- Marker 樣式：
  - 自訂 SVG icon（貓用貓爪圖示、狗用狗爪圖示、混合用愛心）
  - Marker 上顯示該地點的動物數量（作為 badge）
  - 不同 `type` 用不同顏色圈圈區分
- 點擊 marker 顯示 AnimalCard（Leaflet popup 或自訂 panel）
- 使用 Leaflet 的 `MarkerClusterGroup` 外掛處理標記過多時的聚合
  - CDN: `https://unpkg.com/leaflet.markercluster/dist/...`

### 6.4 AnimalCard.vue

- 作為 Leaflet popup 的自訂內容，或作為右下角浮動面板
- 顯示內容：
  - 寵物照片（有則顯示，無則顯示預設圖）
  - 種類 + 性別 + 體型 + 毛色（tag 呈現）
  - 是否絕育 / 已打疫苗（icon badge）
  - 所在地點名稱與地址
  - 聯絡電話
  - 備註
  - 「查看原始資料」連結（連到官網或佈告欄原始頁面）
  - 資料更新日期
- 如果該地點有多隻動物，卡片內可左右翻頁瀏覽

### 6.5 useAnimals.js (composable)

```js
// 核心 API
export function useAnimals() {
  const animals = ref([])          // 所有動物原始資料
  const locations = ref([])        // 所有地點資料
  const loading = ref(true)
  const error = ref(null)
  const updatedAt = ref('')

  // 篩選狀態
  const filterKind = ref('all')    // 'all' | 'cat' | 'dog'
  const filterArea = ref('all')    // 'all' | 特定地區

  // 計算屬性
  const filteredAnimals = computed(() => { /* 依篩選條件過濾 */ })
  const filteredLocations = computed(() => { /* 依篩選結果重算各地點數量 */ })

  // 載入資料
  async function loadData() { /* fetch animals.json + locations.json */ }

  return {
    animals, locations, loading, error, updatedAt,
    filterKind, filterArea,
    filteredAnimals, filteredLocations,
    loadData
  }
}
```

### 6.6 useMap.js (composable)

```js
// 核心 API
export function useMap() {
  let map = null
  let markerLayer = null

  function initMap(containerId) {
    map = L.map(containerId).setView([24.15, 120.67], 12)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18
    }).addTo(map)
    markerLayer = L.layerGroup().addTo(map)
  }

  function updateMarkers(locations, onMarkerClick) {
    markerLayer.clearLayers()
    locations.forEach(loc => {
      const marker = L.marker([loc.lat, loc.lng], {
        icon: createCustomIcon(loc)
      })
      marker.on('click', () => onMarkerClick(loc))
      markerLayer.addLayer(marker)
    })
  }

  function createCustomIcon(location) {
    // 依據 location.type 和 counts 建立自訂 DivIcon
  }

  function flyTo(lat, lng, zoom = 15) {
    map?.flyTo([lat, lng], zoom)
  }

  return { initMap, updateMarkers, flyTo }
}
```

---

## 7. Python 排程腳本規格

### 7.1 scripts/config.py

```python
# API 端點
MOA_API_URL = "https://data.moa.gov.tw/Service/OpenData/TransService.aspx"
MOA_UNIT_ID = "QcbUEzN6E6DL"

# 台中市動保處送養佈告欄
BULLETIN_URL = "https://www.animal.taichung.gov.tw/1521448/1521481/1521495/1521497/1521500"

# Nominatim geocoding
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = "adopt-map/1.0 (https://github.com/{username}/adopt-map)"

# 固定座標（收容所不需要 geocoding）
KNOWN_LOCATIONS = {
    "臺中市動物之家南屯園區": {
        "id": "loc_nantun",
        "lat": 24.1366,
        "lng": 120.6175,
        "address": "臺中市南屯區中台路601號",
        "phone": "04-23850949",
        "type": "shelter"
    },
    "臺中市動物之家后里園區": {
        "id": "loc_houli",
        "lat": 24.3049,
        "lng": 120.7106,
        "address": "臺中市后里區堤防路370號",
        "phone": "04-25588024",
        "type": "shelter"
    }
}

# 輸出路徑
OUTPUT_DIR = "public/data"
CACHE_DIR = "scripts/.cache"
```

### 7.2 scripts/fetch_animals.py

- 呼叫農業部 API，使用 `$top=1000&$skip=0` 分頁取得所有資料
- 過濾 `shelter_address` 或 `animal_place` 包含「臺中」的動物
- 將 API 欄位映射為 animals.json 的格式
- 解析 `animal_remark` 欄位，嘗試提取中途動物醫院名稱
- 輸出：回傳 list of animal dict

### 7.3 scripts/scrape_bulletin.py

- 使用 requests + BeautifulSoup 爬取送養佈告欄
- 處理分頁（ASP.NET ViewState / PostBack）
- 每筆取得：標題、寵物種類、聯絡資訊、圖片、地址描述
- 解析地址文字，盡可能提取結構化的地址
- 輸出：回傳 list of animal dict

### 7.4 scripts/geocode.py

- 讀取 `scripts/.cache/geocode_cache.json`
- 對於新的地址，呼叫 Nominatim API 查詢座標
- 每次請求間隔 1.5 秒（遵守 Nominatim 使用政策）
- 查詢時加入 `countrycodes=tw` 和 `viewbox=120.4,24.0,121.0,24.5`（台中市範圍偏好）
- 結果寫回快取
- 無法解析的地址記錄到 `geocode_failures.log`
- 輸出：回傳 dict (地址 → {lat, lng})

### 7.5 scripts/build_data.py — 主控腳本

這是 GitHub Actions 呼叫的進入點。

```python
def main():
    # 1. 取得農業部 API 資料
    gov_animals = fetch_animals()

    # 2. 爬取送養佈告欄
    bulletin_animals = scrape_bulletin()

    # 3. 彙整所有動物
    all_animals = gov_animals + bulletin_animals

    # 4. 收集所有需要 geocoding 的地址
    addresses = extract_unique_addresses(all_animals)

    # 5. 執行 geocoding（含快取）
    coordinates = geocode_addresses(addresses)

    # 6. 組合地點資料
    locations = build_locations(all_animals, coordinates)

    # 7. 為每隻動物指定 location_id
    assign_location_ids(all_animals, locations)

    # 8. 輸出 JSON
    write_json("public/data/animals.json", animals_payload)
    write_json("public/data/locations.json", locations_payload)

    # 9. 輸出統計報告
    print(f"總計 {len(all_animals)} 隻動物，{len(locations)} 個地點")
```

---

## 8. GitHub Actions 工作流程

### 8.1 update-data.yml（每日資料更新）

```yaml
name: Update Animal Data

on:
  schedule:
    - cron: '0 22 * * *'  # UTC 22:00 = 台灣時間 06:00
  workflow_dispatch:        # 允許手動觸發

jobs:
  update:
    runs-on: ubuntu-latest
    permissions:
      contents: write       # 需要 push 權限

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r scripts/requirements.txt

      - name: Run data pipeline
        run: python scripts/build_data.py

      - name: Commit and push data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add public/data/ scripts/.cache/
          git diff --cached --quiet || git commit -m "chore: update animal data $(date +%Y-%m-%d)"
          git push
```

### 8.2 deploy.yml（前端部署）

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'public/**'
      - 'index.html'
      - 'package.json'
      - 'vite.config.js'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write

    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npm run build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: dist

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## 9. Vite 設定要點

### 9.1 vite.config.js

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/adopt-map/',  // GitHub Pages 子路徑
  build: {
    outDir: 'dist'
  }
})
```

### 9.2 注意事項

- `base` 必須設為 `'/adopt-map/'`，否則 GitHub Pages 上的資源路徑會錯
- 前端 fetch 資料時路徑要用 `import.meta.env.BASE_URL + 'data/animals.json'`
- Leaflet 的 CSS 需要在 main.js 中 import：`import 'leaflet/dist/leaflet.css'`
- Leaflet 的 default marker icon 在 Vite 打包後會壞掉，需要手動修正：

```js
// main.js 中加入
import L from 'leaflet'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow
})
```

---

## 10. 開發階段規劃

### Phase 1：MVP（預計 1-2 天）

- [x] 初始化 Vue 3 + Vite + Tailwind 專案
- [x] 建立模擬資料 (mock JSON)
- [x] 實作 MapView 元件（Leaflet 地圖 + markers）
- [x] 實作 FilterBar 元件（貓/狗切換）
- [x] 點擊 marker 顯示基本 popup
- [x] 部署到 GitHub Pages

### Phase 2：資料串接（預計 2-3 天）

- [x] 撰寫 fetch_animals.py（農業部 API）
- [x] 撰寫 geocode.py（含快取）
- [x] 撰寫 build_data.py（主控腳本）
- [x] 設定 GitHub Actions 排程
- [x] 前端改為讀取真實資料

### Phase 3：送養佈告欄（略過）

> 台中市動保處「民眾送養佈告欄」（https://www.animal.taichung.gov.tw/1521448/1521481/1521495/1521497/1521500）
> 為民眾自行刊登的送養廣告，目前略過不爬取。

### Phase 3.5：台中市動保處「待認養犬貓照片檢索」爬蟲（目前實作目標）

**背景**：台中市動保處在 https://www.animal.taichung.gov.tw/1521490/Lpsimplelist 維護一份獨立的待認養列表，共 149 筆（截至 2026-03-14），**與農業部 Open Data API 是不同系統**。農業部 API 目前只含收容所資料（82 筆：南屯 36 + 后里 46）。

三種來源分佈（截至 2026-03-14）：

| 來源類型 | 筆數 | 所在地點 | 地址取得方式 |
|---------|------|---------|------------|
| 政府收容所 | 127 | 南屯園區 / 后里園區 | 固定座標（`KNOWN_LOCATIONS`） |
| 益起認養吧 | 15 | 合作寵物店，備註含完整地址 | 從備註解析地址後 geocoding |
| 中途動物醫院 | 7 | 委託動物醫院，備註含店名但無完整地址 | 店名 geocoding |

**備註欄格式**（從台中市動保處各頁面個別爬取）：
- 益起認養吧：`我在區域"店名"等待...電話：XXXX 台中市XX區XX路XX號`
- 中途動物醫院：`我在 " 區域 店名 " 等待...電話：XXXX`（無地址）

**完成（2026-03-14）**：

- [x] 撰寫 `scripts/scrape_taichung.py`：爬取 `animal.taichung.gov.tw/1521490` 全部 5 頁列表，取得每筆的 nodeId
- [x] 每筆動物頁面（`/1521490/animalCp?nodeId=XXXX`）解析：編號、所在園區、年齡、性別、體型、毛色、備註、照片
- [x] 依「所在園區」欄位分類：`南屯園區`/`后里園區` → `shelter`；`益起認養吧` → `yiqi`；`中途動物醫院` → `vet_transit`
- [x] 備註欄地址解析（`parse_remark_location` 已實作於 `fetch_animals.py`，共用）
- [x] 整合至 `build_data.py`（台中市爬蟲為主，農業部 API 為備援）
- [x] 前端 `AnimalCard.vue`：已新增 `yiqi` 標籤（紫色）✅
- [x] geocode 改進：支援多門牌格式（78,80號）與省略縣市前綴 fallback
- [x] 結果：149/149 筆全部成功，14 個地點

### Phase 4：UI 優化（預計 1-2 天）

- [x] 自訂 marker 圖示（貓/狗/混合 emoji + 數量 badge + 地點類型顏色圈）
- [x] AnimalCard 美化（照片 contain 不裁切、模糊背景、標籤、翻頁箭頭、dots 指示器、滑鼠拖曳/滾輪翻頁、備註可展開）
- [x] 手機版響應式調整（AnimalCard 底部 sheet 滑出、FilterBar 精簡、HoverPreview/Legend 手機隱藏）
- [x] 增加 marker cluster 聚合（leaflet.markercluster，zoom ≥ 15 自動展開）
- [x] 新增「定位我的位置」按鈕（右下角，含 spinner、錯誤提示、使用者位置 marker）

### Phase 5：進階功能（未來可選）

- [x] 地區篩選下拉選單（城市切換 + 來源/性別/毛色篩選面板）
- [ ] 搜尋功能
- [ ] 收藏功能（localStorage）
- [ ] PWA 支援
- [x] 擴展至其他縣市（全台 22 縣市 + 全台灣合併模式）

---

## 11. Claude Code CLI 使用指引

將此文件放在專案根目錄，在終端機中執行：

```bash
mkdir adopt-map && cd adopt-map
claude
```

然後提供以下指令：

> 請閱讀 `adopt-map-spec.md` 這份專案規格書，依據 Phase 1 的內容建立完整的 Vue 3 + Vite + Tailwind CSS + Leaflet 專案。包含：
> 1. 初始化專案（npm create vite, 安裝依賴）
> 2. 設定 Tailwind CSS
> 3. 建立目錄結構（如 spec 第 4 節）
> 4. 建立模擬資料 JSON（各 5 筆模擬資料，涵蓋不同地點和種類）
> 5. 實作所有 Vue 元件和 composables（如 spec 第 6 節）
> 6. 確保 `npm run dev` 可以正常啟動並看到地圖
> 7. 設定 vite.config.js 的 base path
> 8. 建立 GitHub Actions deploy.yml
>
> 請一步一步執行，每一步完成後確認沒有錯誤再繼續。

---

## 12. 參考連結

- 農業部動物認領養 Open Data：https://data.gov.tw/dataset/85903
- 農業部 API 文件：https://data.moa.gov.tw/open_detail.aspx?id=QcbUEzN6E6DL
- 台中市動保處官網：https://www.animal.taichung.gov.tw/
- 台中市動保處送養佈告欄：https://www.animal.taichung.gov.tw/1521448/1521481/1521495/1521497/1521500
- Leaflet 官方文件：https://leafletjs.com/reference.html
- OpenStreetMap：https://www.openstreetmap.org/
- Nominatim API：https://nominatim.org/release-docs/develop/api/Search/
- Vue 3 文件：https://vuejs.org/guide/introduction.html
- Vite 文件：https://vitejs.dev/guide/
- Tailwind CSS：https://tailwindcss.com/docs
- Leaflet.markercluster：https://github.com/Leaflet/Leaflet.markercluster
- 全國動物收容管理系統：https://www.pet.gov.tw/AnimalApp/AnnounceMent.aspx?PageType=Adopt