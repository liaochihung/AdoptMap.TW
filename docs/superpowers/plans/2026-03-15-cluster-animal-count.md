# Cluster Animal Count Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在地圖縮放較遠、標記集中成 cluster 時，cluster 圓圈顯示「動物總數」而非「地點數」。

**Architecture:** 在 `L.marker` 建立時將動物數存入 `marker.options.animalCount`，`iconCreateFunction` 遍歷所有子 marker 加總後渲染。不需要新增檔案，只改 `useMap.js`。

**Tech Stack:** leaflet.markercluster（`cluster.getAllChildMarkers()`）、Leaflet divIcon

---

## Chunk 1: 修改 useMap.js

### Task 1: 把動物數附加到每個 marker

**Files:**
- Modify: `src/composables/useMap.js:104-121`

- [x] **Step 1: 在 `updateMarkers` 的 marker 建立處加入 `animalCount`**

找到 [useMap.js:105](src/composables/useMap.js#L105)，目前程式碼：

```js
const marker = L.marker([loc.lat, loc.lng], {
  icon: createCustomIcon(loc),
})
```

改為：

```js
const animalCount = (loc.counts?.cat ?? 0) + (loc.counts?.dog ?? 0)
const marker = L.marker([loc.lat, loc.lng], {
  icon: createCustomIcon(loc),
  animalCount,
})
```

- [x] **Step 2: 確認 marker.options 可存自訂屬性**

Leaflet 的 `L.marker(latlng, options)` 會將所有 options 屬性存入 `marker.options`，`getAllChildMarkers()` 回傳的每個 marker 都可以透過 `marker.options.animalCount` 取得。無需額外驗證，繼續下一步。

---

### Task 2: 修改 `iconCreateFunction` 顯示動物總數

**Files:**
- Modify: `src/composables/useMap.js:30-48`

- [x] **Step 3: 修改 `iconCreateFunction`**

找到 [useMap.js:30](src/composables/useMap.js#L30)，目前程式碼：

```js
iconCreateFunction(cluster) {
  const count = cluster.getChildCount()
  const size = count < 10 ? 36 : count < 50 ? 44 : 52
  return L.divIcon({
    html: `<div style="
      width:${size}px;height:${size}px;
      border-radius:50%;
      background:rgba(29,78,216,0.85);
      border:3px solid white;
      box-shadow:0 3px 10px rgba(0,0,0,0.35);
      display:flex;align-items:center;justify-content:center;
      font-size:${count < 10 ? 13 : 12}px;font-weight:700;
      color:white;
      backdrop-filter:blur(4px);
    ">${count}</div>`,
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
},
```

改為：

```js
iconCreateFunction(cluster) {
  const animalTotal = cluster.getAllChildMarkers()
    .reduce((sum, m) => sum + (m.options.animalCount ?? 0), 0)
  const size = animalTotal < 10 ? 36 : animalTotal < 50 ? 44 : 52
  return L.divIcon({
    html: `<div style="
      width:${size}px;height:${size}px;
      border-radius:50%;
      background:rgba(29,78,216,0.85);
      border:3px solid white;
      box-shadow:0 3px 10px rgba(0,0,0,0.35);
      display:flex;align-items:center;justify-content:center;
      font-size:${animalTotal < 10 ? 13 : 12}px;font-weight:700;
      color:white;
      backdrop-filter:blur(4px);
    ">${animalTotal}</div>`,
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
},
```

**差異重點：**
- `cluster.getChildCount()` → `cluster.getAllChildMarkers().reduce(...)` 加總 `animalCount`
- `count` 全部改為 `animalTotal`

- [x] **Step 4: 手動驗證（瀏覽器）**

啟動開發伺服器（`pnpm dev`），縮放到台灣全圖或縣市層級，確認：
1. cluster 圓圈顯示的數字 = 圓圈內各地點動物數的加總
2. 放大到 zoom 15 以上（`disableClusteringAtZoom: 15`）後，個別 marker 的紅色角標數字合計 = 之前 cluster 顯示的數字
3. 套用篩選條件後，cluster 數字隨之變動（因為 `filteredLocations` 重建 marker 時 `animalCount` 會重新計算）

- [x] **Step 5: Commit**

```bash
git add src/composables/useMap.js
git commit -m "feat: show total animal count on cluster icons instead of location count"
```
