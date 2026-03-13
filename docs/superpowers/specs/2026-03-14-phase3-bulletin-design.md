# Phase 3：送養佈告欄 — 設計文件

**日期：** 2026-03-14
**專案：** 領養地圖 (AdoptMap.TW)
**範圍：** 台中市動保處民眾寵物送養佈告欄爬蟲整合

---

## 1. 目標

將台中市動保處「民眾寵物送養佈告欄」的資料整合進領養地圖，讓民眾送養的寵物也能出現在地圖上。有地址的項目顯示為橘色 marker；無地址的項目透過 header 通知圖示提醒使用者。

---

## 2. 網頁結構研究

- **URL：** `https://www.animal.taichung.gov.tw/1521448/1521481/1521495/1521497/1521500`
- **分頁機制：** 純 GET 參數，`?Page={n}&PageSize=30`，無 ViewState，無需 Selenium
- **每頁筆數：** 30 筆，目前約 10 頁（~292 筆）
- **項目結構：** 每筆為 `<li>` 內含 `<table class="meta4col">`
- **可取欄位：** 編號（caption）、登錄日期、年齡、寵物名字、寵物種類、性別、毛色、品種、要送養人、聯絡地址、備註、照片（`<img src="media/...">`）
- **隱私處理：** 不儲存電話/email，前端改用「查看原始資料」連結

---

## 3. 架構設計（方案 A：最小整合）

兩個資料來源各自獨立運作，`build_data.py` 負責合併。

```
scrape_bulletin.py  ──┐
                      ├──▶  build_data.py --source all  ──▶  animals.json
fetch_animals.py    ──┘                                       locations.json
                                                              bulletin_no_address.json
```

### 3.1 新增：`scripts/scrape_bulletin.py`

- 逐頁 GET 佈告欄，每頁間隔 2 秒
- 停止條件：取回筆數 < 30
- 解析 `<table class="meta4col">` 取出各欄位
- 回傳標準化 `list[dict]`，含暫存欄位：
  - `_geo_address`：來自「聯絡地址」，空白時為 `""`
  - `_location_type`：固定為 `"bulletin"`
- `source_url`：連到佈告欄列表頁（不含個人聯絡資訊）
- 新增欄位 `breed`（品種）

### 3.2 修改：`scripts/build_data.py`

新增 `--source` 參數：

| 值 | 行為 |
|----|------|
| `gov` | 只跑農業部流程（現有邏輯） |
| `bulletin` | 只跑佈告欄爬蟲 + geocode，輸出 `bulletin_no_address.json` |
| `all` | 合併兩來源，輸出 `animals.json` / `locations.json` |

`--source all` 從快取讀取兩來源最近一次的結果合併，不重新抓取。

### 3.3 新增：`public/data/bulletin_no_address.json`

存放「聯絡地址為空」的送養項目，供前端通知圖示使用：

```json
{
  "updated_at": "2026-03-14T06:00:00+08:00",
  "total": 45,
  "animals": [
    {
      "id": "BUL-22396",
      "source": "bulletin",
      "kind": "cat",
      "name": "迪迪",
      "sex": "M",
      "age": "adult",
      "bodytype": "unknown",
      "colour": "白色",
      "breed": "布偶",
      "photo_url": "https://www.animal.taichung.gov.tw/media/...",
      "remark": "",
      "open_date": "2026-03-11",
      "source_url": "https://www.animal.taichung.gov.tw/1521448/1521481/1521495/1521497/1521500"
    }
  ]
}
```

### 3.4 修改：`public/data/animals.json`

佈告欄有地址的項目合併進來，`source` 為 `"bulletin"`，新增 `breed` 欄位。

---

## 4. GitHub Actions Workflows

### 修改：`.github/workflows/update-data.yml`（農業部，每日）

```yaml
- run: python scripts/build_data.py --source gov
- run: python scripts/build_data.py --source all
- # git commit & push public/data/
```

### 新增：`.github/workflows/update-bulletin.yml`（佈告欄，每 3 天）

```yaml
on:
  schedule:
    - cron: '0 6 */3 * *'  # 每 3 天 UTC 06:00（台北時間 14:00）
  workflow_dispatch:

jobs:
  update-bulletin:
    steps:
      - run: python scripts/build_data.py --source bulletin
      - run: python scripts/build_data.py --source all
      - # git commit & push public/data/
```

---

## 5. 前端改動

### 5.1 `useAnimals.js`

- `loadData()` 額外 fetch `bulletin_no_address.json`
- 新增：`noAddressAnimals` ref、`noAddressCount` computed

### 5.2 `FilterBar.vue`

新增通知圖示於篩選列右側：

```
[ 全部 | 貓 | 狗 ]                    🔔 45
```

- 橘色鈴鐺圖示 + 數字 badge（`noAddressCount`）
- 點擊展開浮動清單面板，顯示：照片、名字、種類、備註
- 每筆底部有「查看原始資料」連結（連到佈告欄列表頁）
- 數量為 0 時隱藏圖示

### 5.3 `MapView.vue` / `useMap.js`

- `bulletin` 類型地點 marker 顏色改為**橘色**
- 現有顏色對應：`shelter` → 藍色、`vet_transit` → 綠色、`bulletin` → 橘色

### 5.4 `AnimalCard.vue`

- `source === "bulletin"` 時，不顯示電話/email
- 改顯示「查看原始資料」按鈕（連到佈告欄列表頁）

### 5.5 Footer

- 資料來源新增「台中市動保處送養佈告欄」連結
- 顯示佈告欄最後更新時間（來自 `bulletin_no_address.json` 的 `updated_at`）

---

## 6. 資料欄位對照

| 佈告欄欄位 | 對應 animals.json 欄位 | 備註 |
|-----------|----------------------|------|
| 編號 | `id` = `BUL-{編號}` | |
| 登錄日期 | `open_date` | |
| 年齡 | `age` | 成貓/幼貓 → adult/child |
| 寵物名字 | `name` | |
| 寵物種類 | `kind` | 貓→cat、狗→dog |
| 性別 | `sex` | 公→M、母→F |
| 毛色 | `colour` | |
| 品種 | `breed` | 新欄位，僅佈告欄有 |
| 聯絡地址 | `_geo_address`（暫存）| 空白則排除地圖 |
| 備註 | `remark` | |
| 照片 | `photo_url` | |
| — | `source` = `"bulletin"` | |
| — | `source_url` | 佈告欄列表頁 URL |

---

## 7. 地址解析策略

- 有地址 → 交給現有 `geocode.py`（含快取）解析
- 地址解析失敗 → 移至 `bulletin_no_address.json`
- 地址為空 → 直接移至 `bulletin_no_address.json`，不嘗試 geocoding

---

## 8. 不在範圍內

- 電話、email 欄位不儲存、不顯示
- 不做個別詳情頁（無資料支撐）
- 不做「要送養人」姓名顯示
