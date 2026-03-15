# Geocode Override Mechanism Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 geocoding 流程中加入 override JSON 機制，讓特定地址可手動指定正確座標，解決 Nominatim 定位錯誤的問題。

**Architecture:** 新增 `scripts/geocode_overrides.json` 作為手動維護的座標覆寫檔；在 `config.py` 加入路徑常數；在 `geocode.py` 的查詢流程中，KNOWN_LOCATIONS 之後、快取之前插入 override 查詢。

**Tech Stack:** Python 3.11+, pytest, JSON

---

## Chunk 1: 設定與資料檔

### Task 1: 加入 config 路徑常數與建立 override JSON

**Files:**
- Modify: `scripts/config.py`
- Create: `scripts/geocode_overrides.json`

- [ ] **Step 1: 在 config.py 加入 GEOCODE_OVERRIDES_FILE 常數**

在 `config.py` 的 `GEOCODE_CACHE_FILE` 那行下方加入：

```python
GEOCODE_OVERRIDES_FILE = "scripts/geocode_overrides.json"
```

- [ ] **Step 2: 從 Google Maps 確認信揚動物醫院的正確座標**

開啟 `https://www.google.com/maps?cid=5479832452740978733`，在地圖上確認該地點的正確座標（lat/lng）後，再進行下一步。

- [ ] **Step 3: 建立 geocode_overrides.json**

建立 `scripts/geocode_overrides.json`，填入上一步確認的正確座標：

```json
{
  "南屯區 信揚動物醫院": {
    "lat": <從 Google Maps 確認的緯度>,
    "lng": <從 Google Maps 確認的經度>,
    "note": "Nominatim 誤判到桃園，手動修正。來源：https://www.google.com/maps?cid=5479832452740978733"
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add scripts/config.py scripts/geocode_overrides.json
git commit -m "feat: add geocode overrides config and initial override for 信揚動物醫院"
```

---

## Chunk 2: geocode.py 邏輯修改

### Task 2: 在 geocode.py 加入 override 讀取與查詢邏輯

**Files:**
- Modify: `scripts/geocode.py`

- [ ] **Step 1: 在 geocode.py 的 import 區塊加入 GEOCODE_OVERRIDES_FILE**

在 `geocode.py` 頂部的 `from config import (...)` 區塊中加入：

```python
from config import (
    NOMINATIM_URL,
    NOMINATIM_USER_AGENT,
    NOMINATIM_DELAY,
    TAICHUNG_VIEWBOX,
    GEOCODE_CACHE_FILE,
    GEOCODE_FAILURES_LOG,
    KNOWN_LOCATIONS,
    GEOCODE_OVERRIDES_FILE,  # 新增
)
```

- [ ] **Step 2: 在 geocode.py 加入 _load_overrides() 函式**

在 `_load_cache()` 函式下方加入：

```python
def _load_overrides() -> dict:
    if os.path.exists(GEOCODE_OVERRIDES_FILE):
        with open(GEOCODE_OVERRIDES_FILE, encoding="utf-8") as f:
            return json.load(f)
    print(f"  ⚠ 找不到 geocode overrides 檔案：{GEOCODE_OVERRIDES_FILE}（手動覆寫功能停用）")
    return {}
```

- [ ] **Step 3: 在 geocode_addresses() 中插入 override 查詢**

在 `geocode_addresses()` 函式中，`cache = _load_cache()` 之後加入 `overrides = _load_overrides()`，並在 `KNOWN_LOCATIONS` 檢查之後、快取檢查之前插入 override 查詢：

將原本的：
```python
    cache = _load_cache()
    result = {}

    new_queries = 0
    for address in addresses:
        if not address:
            continue

        # 已知固定座標（收容所）
        if address in KNOWN_LOCATIONS:
            loc = KNOWN_LOCATIONS[address]
            result[address] = {"lat": loc["lat"], "lng": loc["lng"]}
            continue

        # 快取命中
        if address in cache:
```

改為：
```python
    cache = _load_cache()
    overrides = _load_overrides()
    result = {}

    new_queries = 0
    for address in addresses:
        if not address:
            continue

        # 已知固定座標（收容所）
        if address in KNOWN_LOCATIONS:
            loc = KNOWN_LOCATIONS[address]
            result[address] = {"lat": loc["lat"], "lng": loc["lng"]}
            continue

        # 手動覆寫座標（優先於快取與 Nominatim）
        if address in overrides:
            loc = overrides[address]
            result[address] = {"lat": loc["lat"], "lng": loc["lng"]}
            continue

        # 快取命中
        if address in cache:
```

- [ ] **Step 4: Commit**

```bash
git add scripts/geocode.py
git commit -m "feat: apply geocode_overrides before cache lookup in geocode_addresses()"
```

---

## Chunk 3: 測試

### Task 3: 撰寫 geocode override 的單元測試

**Files:**
- Create: `scripts/tests/test_geocode_override.py`

- [ ] **Step 1: 建立測試檔**

建立 `scripts/tests/test_geocode_override.py`：

```python
import sys, os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import geocode


def test_override_takes_priority_over_nominatim(monkeypatch, tmp_path):
    """override JSON 中的地址應直接回傳指定座標，不呼叫 Nominatim。"""
    override_data = {
        "南屯區 信揚動物醫院": {"lat": 24.1372, "lng": 120.6468, "note": "test"}
    }
    override_file = tmp_path / "overrides.json"
    override_file.write_text(json.dumps(override_data, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr('geocode.GEOCODE_OVERRIDES_FILE', str(override_file))
    monkeypatch.setattr('geocode.GEOCODE_CACHE_FILE', str(tmp_path / "cache.json"))

    # 確保 Nominatim 不被呼叫
    called = []
    monkeypatch.setattr('geocode._query_nominatim', lambda addr: called.append(addr) or None)

    result = geocode.geocode_addresses(["南屯區 信揚動物醫院"])

    assert "南屯區 信揚動物醫院" in result
    assert result["南屯區 信揚動物醫院"]["lat"] == 24.1372
    assert result["南屯區 信揚動物醫院"]["lng"] == 120.6468
    assert called == [], "Nominatim 不應被呼叫"


def test_override_takes_priority_over_stale_cache(monkeypatch, tmp_path):
    """override 應優先於舊快取，確保手動修正能覆蓋錯誤的快取座標。"""
    override_data = {
        "南屯區 信揚動物醫院": {"lat": 24.1372, "lng": 120.6468, "note": "test"}
    }
    # 舊快取存有錯誤座標（桃園的經緯度）
    stale_cache = {
        "南屯區 信揚動物醫院": {"lat": 25.0, "lng": 121.3}
    }
    override_file = tmp_path / "overrides.json"
    cache_file = tmp_path / "cache.json"
    override_file.write_text(json.dumps(override_data, ensure_ascii=False), encoding="utf-8")
    cache_file.write_text(json.dumps(stale_cache, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr('geocode.GEOCODE_OVERRIDES_FILE', str(override_file))
    monkeypatch.setattr('geocode.GEOCODE_CACHE_FILE', str(cache_file))

    result = geocode.geocode_addresses(["南屯區 信揚動物醫院"])

    # 應使用 override 座標，不是快取的錯誤座標
    assert result["南屯區 信揚動物醫院"]["lat"] == 24.1372
    assert result["南屯區 信揚動物醫院"]["lng"] == 120.6468


def test_non_override_address_falls_through_to_nominatim(monkeypatch, tmp_path):
    """不在 override 中的地址應繼續走 Nominatim 流程，並回傳正確座標。"""
    override_file = tmp_path / "overrides.json"
    override_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr('geocode.GEOCODE_OVERRIDES_FILE', str(override_file))
    monkeypatch.setattr('geocode.GEOCODE_CACHE_FILE', str(tmp_path / "cache.json"))

    called = []
    def mock_nominatim(addr):
        called.append(addr)
        return (24.0, 120.5)

    monkeypatch.setattr('geocode._query_nominatim', mock_nominatim)

    result = geocode.geocode_addresses(["台中市某個地址"])

    assert called == ["台中市某個地址"], "Nominatim 應被呼叫"
    assert result["台中市某個地址"]["lat"] == 24.0
    assert result["台中市某個地址"]["lng"] == 120.5
```

- [ ] **Step 2: 執行測試，確認全部 PASS**

```bash
cd d:/Projects/AdoptMap/scripts
python -m pytest tests/test_geocode_override.py -v
```

預期輸出：
```
tests/test_geocode_override.py::test_override_takes_priority_over_nominatim PASSED
tests/test_geocode_override.py::test_override_takes_priority_over_stale_cache PASSED
tests/test_geocode_override.py::test_non_override_address_falls_through_to_nominatim PASSED
```

- [ ] **Step 3: Commit**

```bash
git add scripts/tests/test_geocode_override.py
git commit -m "test: add unit tests for geocode override mechanism"
```

---

## 使用說明（給維護者）

當發現某個地址被 Nominatim 定位錯誤時：

1. 開啟 Google Maps 確認正確座標（lat/lng）
2. 開啟 `scripts/geocode_overrides.json`，新增一筆：
   ```json
   "地址或地點名稱（與 _geo_address 欄位一致）": {
     "lat": 正確緯度,
     "lng": 正確經度,
     "note": "說明來源或原因"
   }
   ```
3. **不需要**手動刪除舊快取——override 優先於快取，舊快取會被自動略過
4. 重新執行 `python scripts/build_data.py`
