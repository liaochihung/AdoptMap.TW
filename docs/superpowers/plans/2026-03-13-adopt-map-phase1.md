# 領養地圖 Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working Vue 3 + Vite + Tailwind CSS + Leaflet map app showing mock adoptable pets in Taichung, deployable to GitHub Pages.

**Architecture:** Single-page app with a full-screen Leaflet map, a fixed FilterBar on top, and AnimalCard popups on marker click. Data is loaded from static JSON files in `public/data/`. Two composables (`useAnimals`, `useMap`) handle data/filtering logic and Leaflet lifecycle separately from UI components.

**Tech Stack:** Vue 3 (Composition API, `<script setup>`), Vite 5, Tailwind CSS 3 (PostCSS), Leaflet 1.9, leaflet.markercluster (CDN)

---

## Chunk 1: Project Scaffold & Configuration

### Task 1: Initialize Vite + Vue 3 project

**Files:**
- Create: `package.json` (via pnpm create vite)
- Create: `vite.config.js`
- Create: `index.html`

- [ ] **Step 1: Scaffold Vite project in the existing directory**

Run from `d:/Projects/AdoptMap`:
```bash
pnpm create vite@latest . -- --template vue
```
When prompted "Current directory is not empty, remove existing files and continue?" → answer **y** (only `adopt-map-spec.md` and `docs/` exist).
Accept all defaults.

- [ ] **Step 2: Install core dependencies**

```bash
pnpm install
pnpm add leaflet
pnpm add -D tailwindcss@3 postcss autoprefixer
```

- [ ] **Step 3: Initialize Tailwind**

```bash
pnpm dlx tailwindcss init -p
```
This creates `tailwind.config.js` and `postcss.config.js`.

- [ ] **Step 4: Verify scaffold**

```bash
pnpm run dev
```
Expected: Vite dev server starts on `http://localhost:5173`, browser shows default Vue template.
Stop server with Ctrl+C.

---

### Task 2: Configure vite.config.js

**Files:**
- Modify: `vite.config.js`

- [ ] **Step 1: Replace vite.config.js with correct base path**

```js
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/adopt-map/',
  build: {
    outDir: 'dist'
  }
})
```

---

### Task 3: Configure Tailwind CSS

**Files:**
- Modify: `tailwind.config.js`
- Modify: `src/assets/main.css` (replace content)

- [ ] **Step 1: Update tailwind.config.js to scan src files**

```js
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

- [ ] **Step 2: Replace src/assets/main.css with Tailwind directives**

Delete all existing content and replace with:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

### Task 4: Fix Leaflet icon issue in Vite & update main.js

**Files:**
- Modify: `src/main.js`

- [ ] **Step 1: Replace src/main.js**

```js
// src/main.js
import { createApp } from 'vue'
import './assets/main.css'
import 'leaflet/dist/leaflet.css'
import App from './App.vue'

import L from 'leaflet'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

createApp(App).mount('#app')
```

- [ ] **Step 2: Verify no import errors**

```bash
pnpm run dev
```
Expected: dev server starts without errors in terminal. Stop with Ctrl+C.

---

## Chunk 2: Mock Data

### Task 5: Create directory structure and mock JSON data

**Files:**
- Create: `public/data/animals.json`
- Create: `public/data/locations.json`
- Create: `src/components/.gitkeep` (placeholder)
- Create: `src/composables/.gitkeep`
- Create: `src/assets/markers/cat.svg`
- Create: `src/assets/markers/dog.svg`
- Create: `src/assets/markers/mixed.svg`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p public/data
mkdir -p src/components
mkdir -p src/composables
mkdir -p src/assets/markers
```

- [ ] **Step 2: Create public/data/locations.json**

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
      "counts": { "cat": 2, "dog": 2 }
    },
    {
      "id": "loc_houli",
      "name": "臺中市動物之家后里園區",
      "address": "臺中市后里區堤防路370號",
      "phone": "04-25588024",
      "lat": 24.3049,
      "lng": 120.7106,
      "type": "shelter",
      "counts": { "cat": 1, "dog": 1 }
    },
    {
      "id": "loc_vet_001",
      "name": "愛心動物醫院（中途收容）",
      "address": "臺中市西區民權路120號",
      "phone": "04-2222-3333",
      "lat": 24.1538,
      "lng": 120.6568,
      "type": "vet_transit",
      "counts": { "cat": 1, "dog": 1 }
    },
    {
      "id": "loc_bulletin_xitun",
      "name": "民眾送養 — 西屯區",
      "address": "臺中市西屯區",
      "phone": "",
      "lat": 24.1630,
      "lng": 120.6350,
      "type": "bulletin",
      "counts": { "cat": 0, "dog": 1 }
    },
    {
      "id": "loc_bulletin_beitun",
      "name": "民眾送養 — 北屯區",
      "address": "臺中市北屯區",
      "phone": "",
      "lat": 24.1820,
      "lng": 120.6890,
      "type": "bulletin",
      "counts": { "cat": 1, "dog": 0 }
    }
  ]
}
```

- [ ] **Step 3: Create public/data/animals.json**

```json
{
  "updated_at": "2026-03-13T06:00:00+08:00",
  "total": 10,
  "animals": [
    {
      "id": "GOV-10001",
      "source": "gov_shelter",
      "kind": "cat",
      "name": "",
      "sex": "F",
      "age": "adult",
      "bodytype": "small",
      "colour": "黑白色",
      "sterilized": true,
      "vaccinated": true,
      "photo_url": "",
      "remark": "個性溫順，適合家庭飼養",
      "open_date": "2026-02-01",
      "update_date": "2026-03-10",
      "location_id": "loc_nantun",
      "source_url": "https://www.pet.gov.tw/"
    },
    {
      "id": "GOV-10002",
      "source": "gov_shelter",
      "kind": "dog",
      "name": "",
      "sex": "M",
      "age": "adult",
      "bodytype": "medium",
      "colour": "黃色",
      "sterilized": true,
      "vaccinated": true,
      "photo_url": "",
      "remark": "活潑好動，喜歡戶外活動",
      "open_date": "2026-02-10",
      "update_date": "2026-03-11",
      "location_id": "loc_nantun",
      "source_url": "https://www.pet.gov.tw/"
    },
    {
      "id": "GOV-10003",
      "source": "gov_shelter",
      "kind": "cat",
      "name": "",
      "sex": "M",
      "age": "child",
      "bodytype": "small",
      "colour": "橘色",
      "sterilized": false,
      "vaccinated": true,
      "photo_url": "",
      "remark": "幼貓，需要耐心照顧",
      "open_date": "2026-03-01",
      "update_date": "2026-03-12",
      "location_id": "loc_nantun",
      "source_url": "https://www.pet.gov.tw/"
    },
    {
      "id": "GOV-10004",
      "source": "gov_shelter",
      "kind": "dog",
      "name": "",
      "sex": "F",
      "age": "adult",
      "bodytype": "large",
      "colour": "黑色",
      "sterilized": true,
      "vaccinated": true,
      "photo_url": "",
      "remark": "大型犬，需要寬敞空間",
      "open_date": "2026-01-20",
      "update_date": "2026-03-09",
      "location_id": "loc_nantun",
      "source_url": "https://www.pet.gov.tw/"
    },
    {
      "id": "GOV-20001",
      "source": "gov_shelter",
      "kind": "cat",
      "name": "",
      "sex": "F",
      "age": "adult",
      "bodytype": "small",
      "colour": "三花",
      "sterilized": true,
      "vaccinated": true,
      "photo_url": "",
      "remark": "安靜溫和，適合老人家",
      "open_date": "2026-02-15",
      "update_date": "2026-03-10",
      "location_id": "loc_houli",
      "source_url": "https://www.pet.gov.tw/"
    },
    {
      "id": "GOV-20002",
      "source": "gov_shelter",
      "kind": "dog",
      "name": "",
      "sex": "M",
      "age": "child",
      "bodytype": "small",
      "colour": "白色",
      "sterilized": false,
      "vaccinated": false,
      "photo_url": "",
      "remark": "幼犬，活潑可愛",
      "open_date": "2026-03-05",
      "update_date": "2026-03-12",
      "location_id": "loc_houli",
      "source_url": "https://www.pet.gov.tw/"
    },
    {
      "id": "VET-30001",
      "source": "gov_shelter",
      "kind": "cat",
      "name": "咪咪",
      "sex": "F",
      "age": "adult",
      "bodytype": "small",
      "colour": "灰色",
      "sterilized": true,
      "vaccinated": true,
      "photo_url": "",
      "remark": "中途貓，習慣室內生活",
      "open_date": "2026-02-20",
      "update_date": "2026-03-08",
      "location_id": "loc_vet_001",
      "source_url": "https://www.pet.gov.tw/"
    },
    {
      "id": "VET-30002",
      "source": "gov_shelter",
      "kind": "dog",
      "name": "小白",
      "sex": "M",
      "age": "adult",
      "bodytype": "medium",
      "colour": "白色",
      "sterilized": true,
      "vaccinated": true,
      "photo_url": "",
      "remark": "中途狗，已接受基本訓練",
      "open_date": "2026-03-01",
      "update_date": "2026-03-11",
      "location_id": "loc_vet_001",
      "source_url": "https://www.pet.gov.tw/"
    },
    {
      "id": "BUL-40001",
      "source": "bulletin",
      "kind": "dog",
      "name": "小黑",
      "sex": "M",
      "age": "adult",
      "bodytype": "medium",
      "colour": "黑色",
      "sterilized": null,
      "vaccinated": null,
      "photo_url": "",
      "remark": "個性溫馴，親人，需要有院子的家",
      "open_date": "2026-02-28",
      "update_date": "2026-03-10",
      "location_id": "loc_bulletin_xitun",
      "contact_name": "王先生",
      "contact_phone": "0912-345-678",
      "source_url": "https://www.animal.taichung.gov.tw/"
    },
    {
      "id": "BUL-50001",
      "source": "bulletin",
      "kind": "cat",
      "name": "花花",
      "sex": "F",
      "age": "child",
      "bodytype": "small",
      "colour": "虎斑",
      "sterilized": null,
      "vaccinated": null,
      "photo_url": "",
      "remark": "撿到的幼貓，需要愛心家庭",
      "open_date": "2026-03-05",
      "update_date": "2026-03-12",
      "location_id": "loc_bulletin_beitun",
      "contact_name": "李小姐",
      "contact_phone": "0987-654-321",
      "source_url": "https://www.animal.taichung.gov.tw/"
    }
  ]
}
```

- [ ] **Step 4: Create SVG marker icons**

Create `src/assets/markers/cat.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <circle cx="16" cy="16" r="14" fill="#f97316" stroke="white" stroke-width="2"/>
  <text x="16" y="22" text-anchor="middle" font-size="16">🐱</text>
</svg>
```

Create `src/assets/markers/dog.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <circle cx="16" cy="16" r="14" fill="#3b82f6" stroke="white" stroke-width="2"/>
  <text x="16" y="22" text-anchor="middle" font-size="16">🐶</text>
</svg>
```

Create `src/assets/markers/mixed.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <circle cx="16" cy="16" r="14" fill="#8b5cf6" stroke="white" stroke-width="2"/>
  <text x="16" y="22" text-anchor="middle" font-size="16">🐾</text>
</svg>
```

---

## Chunk 3: Composables

### Task 6: Implement useAnimals.js

**Files:**
- Create: `src/composables/useAnimals.js`

- [ ] **Step 1: Create src/composables/useAnimals.js**

```js
// src/composables/useAnimals.js
import { ref, computed } from 'vue'

export function useAnimals() {
  const animals = ref([])
  const locations = ref([])
  const loading = ref(true)
  const error = ref(null)
  const updatedAt = ref('')

  const filterKind = ref('all')  // 'all' | 'cat' | 'dog'
  const filterArea = ref('all')  // 'all' | location id

  const filteredAnimals = computed(() => {
    return animals.value.filter(a => {
      if (filterKind.value !== 'all' && a.kind !== filterKind.value) return false
      if (filterArea.value !== 'all' && a.location_id !== filterArea.value) return false
      return true
    })
  })

  // Recompute per-location counts based on filtered animals
  const filteredLocations = computed(() => {
    const countMap = {}
    filteredAnimals.value.forEach(a => {
      if (!countMap[a.location_id]) countMap[a.location_id] = { cat: 0, dog: 0 }
      if (a.kind === 'cat') countMap[a.location_id].cat++
      else if (a.kind === 'dog') countMap[a.location_id].dog++
    })

    return locations.value
      .map(loc => ({
        ...loc,
        counts: countMap[loc.id] || { cat: 0, dog: 0 }
      }))
      .filter(loc => {
        const c = loc.counts
        return c.cat + c.dog > 0
      })
  })

  async function loadData() {
    loading.value = true
    error.value = null
    try {
      const base = import.meta.env.BASE_URL
      const [animalsRes, locationsRes] = await Promise.all([
        fetch(`${base}data/animals.json`),
        fetch(`${base}data/locations.json`)
      ])
      if (!animalsRes.ok) throw new Error(`Failed to load animals: ${animalsRes.status}`)
      if (!locationsRes.ok) throw new Error(`Failed to load locations: ${locationsRes.status}`)

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
    filterKind,
    filterArea,
    filteredAnimals,
    filteredLocations,
    loadData,
  }
}
```

---

### Task 7: Implement useMap.js

**Files:**
- Create: `src/composables/useMap.js`

- [ ] **Step 1: Create src/composables/useMap.js**

```js
// src/composables/useMap.js
import L from 'leaflet'

// Color scheme per location type
const TYPE_COLORS = {
  shelter: '#3b82f6',      // blue
  vet_transit: '#22c55e',  // green
  bulletin: '#f97316',     // orange
}

export function useMap() {
  let map = null
  let markerLayer = null

  function initMap(containerId) {
    map = L.map(containerId).setView([24.15, 120.67], 12)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    }).addTo(map)
    markerLayer = L.layerGroup().addTo(map)
  }

  function createCustomIcon(location) {
    const color = TYPE_COLORS[location.type] || '#6b7280'
    const { cat, dog } = location.counts
    const total = cat + dog

    // Determine emoji
    let emoji = '🐾'
    if (cat > 0 && dog === 0) emoji = '🐱'
    else if (dog > 0 && cat === 0) emoji = '🐶'

    const html = `
      <div style="
        position: relative;
        width: 40px;
        height: 40px;
      ">
        <div style="
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: ${color};
          border: 3px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.35);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          line-height: 1;
        ">${emoji}</div>
        <div style="
          position: absolute;
          top: -6px;
          right: -6px;
          background: #ef4444;
          color: white;
          border-radius: 999px;
          min-width: 18px;
          height: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: bold;
          padding: 0 4px;
          border: 1.5px solid white;
          line-height: 1;
        ">${total}</div>
      </div>
    `

    return L.divIcon({
      html,
      className: '',
      iconSize: [40, 40],
      iconAnchor: [20, 20],
      popupAnchor: [0, -24],
    })
  }

  function updateMarkers(locations, onMarkerClick) {
    if (!markerLayer) return
    markerLayer.clearLayers()
    locations.forEach(loc => {
      const marker = L.marker([loc.lat, loc.lng], {
        icon: createCustomIcon(loc),
      })
      marker.on('click', () => onMarkerClick(loc))
      markerLayer.addLayer(marker)
    })
  }

  function flyTo(lat, lng, zoom = 15) {
    map?.flyTo([lat, lng], zoom)
  }

  function invalidateSize() {
    map?.invalidateSize()
  }

  return { initMap, updateMarkers, flyTo, invalidateSize }
}
```

---

## Chunk 4: Vue Components

### Task 8: Implement FilterBar.vue

**Files:**
- Create: `src/components/FilterBar.vue`

- [ ] **Step 1: Create src/components/FilterBar.vue**

```vue
<!-- src/components/FilterBar.vue -->
<script setup>
defineProps({
  filterKind: {
    type: String,
    default: 'all',
  },
  filteredCount: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['update:filterKind'])

const kindOptions = [
  { value: 'all', label: '全部' },
  { value: 'cat', label: '🐱 貓' },
  { value: 'dog', label: '🐶 狗' },
]
</script>

<template>
  <div class="fixed top-0 left-0 right-0 z-[1000] flex items-center gap-3 px-4 py-2 bg-white/90 backdrop-blur-sm shadow-md">
    <!-- Title -->
    <span class="font-bold text-gray-800 text-sm whitespace-nowrap">🗺 領養地圖</span>

    <!-- Kind filter buttons -->
    <div class="flex gap-1">
      <button
        v-for="opt in kindOptions"
        :key="opt.value"
        :class="[
          'px-3 py-1 rounded-full text-sm font-medium transition-colors',
          filterKind === opt.value
            ? 'bg-blue-600 text-white shadow-sm'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        ]"
        @click="emit('update:filterKind', opt.value)"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- Count display -->
    <span class="text-xs text-gray-500 ml-auto whitespace-nowrap">
      顯示 {{ filteredCount }} 隻
    </span>
  </div>
</template>
```

---

### Task 9: Implement AnimalCard.vue

**Files:**
- Create: `src/components/AnimalCard.vue`

- [ ] **Step 1: Create src/components/AnimalCard.vue**

```vue
<!-- src/components/AnimalCard.vue -->
<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  location: {
    type: Object,
    default: null,
  },
  animals: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['close'])

// Paginate through animals at this location
const currentIndex = ref(0)

const locationAnimals = computed(() =>
  props.animals.filter(a => a.location_id === props.location?.id)
)

const currentAnimal = computed(() => locationAnimals.value[currentIndex.value] || null)

function prev() {
  if (currentIndex.value > 0) currentIndex.value--
}
function next() {
  if (currentIndex.value < locationAnimals.value.length - 1) currentIndex.value++
}

// Reset page when location changes
watch(() => props.location?.id, () => { currentIndex.value = 0 })

const sexLabel = { M: '♂ 公', F: '♀ 母', N: '未知' }
const ageLabel = { adult: '成年', child: '幼年' }
const bodytypeLabel = { small: '小型', medium: '中型', large: '大型' }

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
</script>

<template>
  <div
    v-if="location"
    class="absolute bottom-6 right-4 z-[1000] w-72 bg-white rounded-xl shadow-2xl overflow-hidden"
  >
    <!-- Header: location info -->
    <div class="flex items-start justify-between px-4 pt-3 pb-2 bg-gray-50 border-b">
      <div class="flex-1 min-w-0">
        <div class="font-semibold text-gray-800 text-sm leading-tight truncate">{{ location.name }}</div>
        <div class="text-xs text-gray-500 mt-0.5 truncate">{{ location.address }}</div>
      </div>
      <button
        class="ml-2 text-gray-400 hover:text-gray-600 text-lg leading-none flex-shrink-0"
        @click="emit('close')"
      >✕</button>
    </div>

    <!-- Animal info -->
    <div v-if="currentAnimal" class="px-4 py-3">
      <!-- Photo placeholder -->
      <div class="w-full h-28 bg-gray-100 rounded-lg flex items-center justify-center mb-3 overflow-hidden">
        <img
          v-if="currentAnimal.photo_url"
          :src="currentAnimal.photo_url"
          :alt="currentAnimal.name || '待領養動物'"
          class="w-full h-full object-cover"
        />
        <span v-else class="text-5xl">{{ currentAnimal.kind === 'cat' ? '🐱' : '🐶' }}</span>
      </div>

      <!-- Name -->
      <div class="flex items-center gap-2 mb-2">
        <span class="font-semibold text-gray-800">
          {{ currentAnimal.name || (currentAnimal.kind === 'cat' ? '無名貓咪' : '無名狗狗') }}
        </span>
        <span :class="['text-xs px-2 py-0.5 rounded-full', typeColor[location.type] || 'bg-gray-100 text-gray-600']">
          {{ typeLabel[location.type] || location.type }}
        </span>
      </div>

      <!-- Tags -->
      <div class="flex flex-wrap gap-1 mb-2">
        <span class="tag">{{ sexLabel[currentAnimal.sex] || currentAnimal.sex }}</span>
        <span class="tag">{{ ageLabel[currentAnimal.age] || currentAnimal.age }}</span>
        <span class="tag">{{ bodytypeLabel[currentAnimal.bodytype] || currentAnimal.bodytype }}</span>
        <span v-if="currentAnimal.colour" class="tag">{{ currentAnimal.colour }}</span>
        <span v-if="currentAnimal.sterilized === true" class="tag bg-green-50 text-green-700">已絕育</span>
        <span v-if="currentAnimal.vaccinated === true" class="tag bg-blue-50 text-blue-700">已打疫苗</span>
      </div>

      <!-- Remark -->
      <p v-if="currentAnimal.remark" class="text-xs text-gray-600 mb-2 leading-relaxed line-clamp-2">
        {{ currentAnimal.remark }}
      </p>

      <!-- Contact (bulletin only) -->
      <div v-if="currentAnimal.contact_phone" class="text-xs text-gray-600 mb-2">
        📞 {{ currentAnimal.contact_name }} {{ currentAnimal.contact_phone }}
      </div>
      <div v-else-if="location.phone" class="text-xs text-gray-600 mb-2">
        📞 {{ location.phone }}
      </div>

      <!-- Source link -->
      <a
        v-if="currentAnimal.source_url"
        :href="currentAnimal.source_url"
        target="_blank"
        rel="noopener noreferrer"
        class="text-xs text-blue-600 hover:underline"
      >查看原始資料 →</a>
    </div>

    <!-- Empty state -->
    <div v-else class="px-4 py-6 text-center text-gray-400 text-sm">
      此地點目前無符合條件的動物
    </div>

    <!-- Pagination -->
    <div
      v-if="locationAnimals.length > 1"
      class="flex items-center justify-between px-4 py-2 border-t bg-gray-50 text-sm"
    >
      <button
        :disabled="currentIndex === 0"
        class="px-2 py-0.5 rounded disabled:opacity-30 hover:bg-gray-200"
        @click="prev"
      >← 上一隻</button>
      <span class="text-xs text-gray-500">{{ currentIndex + 1 }} / {{ locationAnimals.length }}</span>
      <button
        :disabled="currentIndex === locationAnimals.length - 1"
        class="px-2 py-0.5 rounded disabled:opacity-30 hover:bg-gray-200"
        @click="next"
      >下一隻 →</button>
    </div>
  </div>
</template>

<style scoped>
.tag {
  @apply text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full;
}
</style>
```

---

### Task 10: Implement MapView.vue

**Files:**
- Create: `src/components/MapView.vue`

- [ ] **Step 1: Create src/components/MapView.vue**

```vue
<!-- src/components/MapView.vue -->
<script setup>
import { onMounted, onUnmounted, watch } from 'vue'
import { useMap } from '../composables/useMap.js'

const props = defineProps({
  locations: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['locationClick'])
const { initMap, updateMarkers, invalidateSize } = useMap()

onMounted(() => {
  initMap('map-container')
  updateMarkers(props.locations, loc => emit('locationClick', loc))
})

watch(
  () => props.locations,
  newLocs => {
    updateMarkers(newLocs, loc => emit('locationClick', loc))
  },
  { deep: true }
)

onUnmounted(() => {
  // Leaflet cleans up automatically when the DOM element is removed
})
</script>

<template>
  <div id="map-container" class="w-full h-full" />
</template>
```

---

### Task 11: Implement App.vue

**Files:**
- Modify: `src/App.vue`

- [ ] **Step 1: Replace src/App.vue**

```vue
<!-- src/App.vue -->
<script setup>
import { onMounted, ref } from 'vue'
import FilterBar from './components/FilterBar.vue'
import MapView from './components/MapView.vue'
import AnimalCard from './components/AnimalCard.vue'
import { useAnimals } from './composables/useAnimals.js'

const {
  loading,
  error,
  updatedAt,
  filterKind,
  filteredAnimals,
  filteredLocations,
  loadData,
} = useAnimals()

const selectedLocation = ref(null)

onMounted(() => loadData())

function handleLocationClick(location) {
  selectedLocation.value = location
}

function closeCard() {
  selectedLocation.value = null
}

// Format display date
function formatDate(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="relative w-screen h-screen overflow-hidden">
    <!-- Filter bar -->
    <FilterBar
      :filter-kind="filterKind"
      :filtered-count="filteredAnimals.length"
      @update:filterKind="val => filterKind = val"
    />

    <!-- Loading overlay -->
    <div
      v-if="loading"
      class="absolute inset-0 z-[2000] flex items-center justify-center bg-white/80"
    >
      <div class="text-center text-gray-600">
        <div class="text-4xl mb-2">🗺</div>
        <div class="text-sm">載入中…</div>
      </div>
    </div>

    <!-- Error overlay -->
    <div
      v-if="error"
      class="absolute inset-0 z-[2000] flex items-center justify-center bg-white/90"
    >
      <div class="text-center text-red-600">
        <div class="text-4xl mb-2">⚠️</div>
        <div class="text-sm">{{ error }}</div>
      </div>
    </div>

    <!-- Map (full screen, below filter bar) -->
    <div class="absolute inset-0 top-[48px]">
      <MapView
        :locations="filteredLocations"
        @location-click="handleLocationClick"
      />
    </div>

    <!-- Animal card popup -->
    <AnimalCard
      :location="selectedLocation"
      :animals="filteredAnimals"
      @close="closeCard"
    />

    <!-- Footer: update time -->
    <div class="absolute bottom-4 left-4 z-[1000] text-xs text-gray-500 bg-white/80 px-2 py-1 rounded">
      資料更新：{{ formatDate(updatedAt) }}
      ｜資料來源：農業部動物認領養 Open Data
    </div>
  </div>
</template>
```

---

## Chunk 5: GitHub Actions & Verification

### Task 12: Create GitHub Actions deploy.yml

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Create .github/workflows/deploy.yml**

```bash
mkdir -p .github/workflows
```

```yaml
# .github/workflows/deploy.yml
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
  workflow_dispatch:

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

      - name: Setup pnpm
        uses: pnpm/action-setup@v4
        with:
          version: latest

      - run: pnpm install --frozen-lockfile
      - run: pnpm run build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: dist

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

### Task 13: Final verification

- [ ] **Step 1: Run pnpm run dev and verify the app works**

```bash
pnpm run dev
```

Expected:
- Dev server starts on `http://localhost:5173` (note: with `base: '/adopt-map/'`, the app is served at `http://localhost:5173/adopt-map/`)
- Browser shows: filter bar at top, Leaflet map of Taichung with 5 colored markers
- Clicking a marker shows the AnimalCard popup with pet info
- Clicking 貓/狗 buttons filters markers
- No console errors

- [ ] **Step 2: Run production build to verify it compiles clean**

```bash
pnpm run build
```

Expected: `dist/` directory created, no build errors.

- [ ] **Step 3: Clean up default Vite template files**

Remove unused template files:
```bash
rm -f src/components/HelloWorld.vue
rm -f src/assets/vue.svg
rm -f public/vite.svg
```
Also remove the `<style>` block from `src/App.vue` if the template added a default one (our replacement already has no global styles).

- [ ] **Step 4: Verify build still passes after cleanup**

```bash
pnpm run build
```

Expected: clean build, no errors.

---

## Notes

- Dev server URL with `base: '/adopt-map/'` is `http://localhost:5173/adopt-map/`
- The mock data has 10 animals across 5 locations; `filteredLocations` computed property hides locations with 0 matching animals when filtering
- Leaflet requires the map container div to have explicit dimensions; `h-full` on the inner div and explicit `inset-0 top-[48px]` on the wrapper provides this
- `leaflet.markercluster` is deferred to Phase 4; the current marker layer handles the 5 mock locations without clustering
