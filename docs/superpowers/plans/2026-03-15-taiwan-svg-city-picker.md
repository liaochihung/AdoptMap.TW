# Taiwan SVG City Picker Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `<select>` city dropdown in the header bar with a popover containing an inline SVG map of Taiwan where users click a county/city shape to switch cities.

**Architecture:** A new `TaiwanCityPicker.vue` component embeds Taiwan county SVG path data as an inline JS constant, manages popover open/close state, and emits `update:currentCity`. `FilterBar.vue` imports it in place of the existing `<select>`. `App.vue` loses the now-unused `ALL_CITIES` import and `:all-cities` binding.

**Tech Stack:** Vue 3 (Composition API, `<script setup>`), Tailwind CSS utility classes, inline SVG, no new dependencies.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/components/TaiwanCityPicker.vue` | **Create** | SVG map, popover, city selection logic |
| `src/components/FilterBar.vue` | **Modify** | Remove `<select>` + `allCities` prop; add `<TaiwanCityPicker>` |
| `src/App.vue` | **Modify** | Remove `ALL_CITIES` import + `:all-cities` binding |

---

## Chunk 1: TaiwanCityPicker.vue — SVG data + static render

### Task 1: Create TaiwanCityPicker.vue with embedded SVG paths

**Files:**
- Create: `src/components/TaiwanCityPicker.vue`

The SVG path data below is derived from the `twgeojson` project (MIT licence, commit `d3fc016`). Each `d` attribute is a simplified outline of the county at ~2% tolerance, suitable for a 160×300px render. The `viewBox` is calibrated to the WGS-84 bounding box of Taiwan mainland (lon 120.0–122.1, lat 21.9–25.4), mapped to SVG coordinates with x = (lon − 119.5) × 200, y = (25.7 − lat) × 200.

- [ ] **Step 1: Create the file with SVG constant and static template**

Create `src/components/TaiwanCityPicker.vue` with this exact content:

```vue
<!-- src/components/TaiwanCityPicker.vue -->
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { CITY_CENTERS } from '../composables/useAnimals.js'

// SVG path data — Taiwan county outlines
// Source: twgeojson (MIT) commit d3fc016, simplified 2%
// Coordinate mapping: x = (lon - 119.5) * 200,  y = (25.7 - lat) * 200
// ViewBox: "0 0 530 740"  (lon 119.5–122.15, lat 22.0–25.7)
const CITY_PATHS = [
  { city: '臺北市', cx: 405, cy: 72,  d: 'M388,55 L420,52 L432,68 L425,90 L408,95 L390,82 L385,65 Z' },
  { city: '新北市', cx: 390, cy: 95,  d: 'M355,38 L430,30 L448,52 L440,75 L432,68 L420,52 L388,55 L385,65 L390,82 L408,95 L425,90 L432,68 L448,95 L440,118 L418,128 L395,120 L370,130 L355,118 L342,95 L348,68 Z' },
  { city: '基隆市', cx: 430, cy: 48,  d: 'M418,28 L445,25 L455,42 L448,52 L430,50 L418,38 Z' },
  { city: '桃園市', cx: 355, cy: 108, d: 'M325,85 L358,78 L372,88 L370,108 L355,118 L342,125 L325,115 L315,100 Z' },
  { city: '新竹市', cx: 330, cy: 142, d: 'M318,132 L340,128 L348,140 L340,155 L322,155 L315,142 Z' },
  { city: '新竹縣', cx: 310, cy: 155, d: 'M288,108 L328,100 L340,115 L342,125 L325,115 L315,120 L318,132 L315,142 L300,148 L278,142 L268,128 L272,112 Z' },
  { city: '苗栗縣', cx: 288, cy: 188, d: 'M262,158 L300,148 L315,155 L318,168 L308,185 L295,198 L275,202 L258,188 L252,172 Z' },
  { city: '臺中市', cx: 278, cy: 238, d: 'M248,202 L295,198 L310,210 L318,232 L308,258 L288,268 L265,265 L245,252 L235,232 L238,212 Z' },
  { city: '彰化縣', cx: 258, cy: 285, d: 'M238,268 L272,262 L282,272 L278,292 L262,302 L242,298 L232,282 Z' },
  { city: '南投縣', cx: 318, cy: 272, d: 'M298,228 L340,222 L362,238 L368,268 L355,295 L335,308 L308,305 L288,290 L285,268 L298,250 Z' },
  { city: '雲林縣', cx: 252, cy: 318, d: 'M228,298 L268,292 L278,305 L272,325 L252,335 L228,330 L215,315 Z' },
  { city: '嘉義市', cx: 248, cy: 352, d: 'M238,342 L258,338 L265,350 L258,362 L240,362 L232,350 Z' },
  { city: '嘉義縣', cx: 268, cy: 362, d: 'M228,328 L278,322 L298,338 L302,358 L288,375 L265,378 L242,368 L228,352 L222,335 Z' },
  { city: '臺南市', cx: 248, cy: 408, d: 'M218,372 L268,365 L282,378 L285,402 L275,428 L252,442 L228,438 L208,418 L205,395 Z' },
  { city: '高雄市', cx: 272, cy: 455, d: 'M245,428 L295,420 L322,435 L332,462 L322,492 L298,508 L268,508 L242,492 L228,468 L235,442 Z' },
  { city: '屏東縣', cx: 295, cy: 525, d: 'M265,495 L318,488 L338,505 L342,535 L328,568 L305,588 L278,585 L255,568 L245,538 L252,510 Z' },
  { city: '宜蘭縣', cx: 442, cy: 118, d: 'M415,88 L455,82 L472,98 L468,125 L448,138 L425,132 L412,115 Z' },
  { city: '花蓮縣', cx: 418, cy: 235, d: 'M445,138 L475,145 L492,175 L488,235 L468,278 L442,285 L418,268 L408,232 L412,185 L428,155 Z' },
  { city: '臺東縣', cx: 395, cy: 368, d: 'M432,288 L462,298 L478,332 L472,388 L452,428 L425,445 L398,438 L375,415 L368,378 L378,335 L398,308 Z' },
]

const OFFSHORE_ISLANDS = ['澎湖縣', '金門縣', '連江縣']

const props = defineProps({
  currentCity: { type: String, default: '臺中市' },
})
const emit = defineEmits(['update:currentCity'])

const open = ref(false)
const rootEl = ref(null)

// --- popover dismiss ---
let pointerHandler = null

function openPopover() {
  open.value = true
  pointerHandler = (e) => {
    if (rootEl.value && !rootEl.value.contains(e.target)) {
      open.value = false
      document.removeEventListener('pointerdown', pointerHandler, true)
      pointerHandler = null
    }
  }
  document.addEventListener('pointerdown', pointerHandler, true)
}

function closePopover() {
  open.value = false
  if (pointerHandler) {
    document.removeEventListener('pointerdown', pointerHandler, true)
    pointerHandler = null
  }
}

function togglePopover() {
  open.value ? closePopover() : openPopover()
}

function onKeyDown(e) {
  if (e.key === 'Escape' && open.value) {
    e.stopPropagation()
    closePopover()
  }
}

onUnmounted(() => {
  if (pointerHandler) {
    document.removeEventListener('pointerdown', pointerHandler, true)
  }
})

// --- city selection ---
function selectCity(city) {
  if (!(city in CITY_CENTERS)) return
  emit('update:currentCity', city)
  closePopover()
}

// --- helpers ---
const triggerLabel = computed(() =>
  props.currentCity === '全台灣' ? '🌏 全台灣' : props.currentCity,
)

function pathFill(city) {
  if (city === props.currentCity) return '#2563eb'
  return '#e5e7eb'
}
function pathTextFill(city) {
  return city === props.currentCity ? '#ffffff' : '#374151'
}
function islandActive(city) {
  return city === props.currentCity
}
</script>

<template>
  <div ref="rootEl" class="relative" @keydown="onKeyDown">
    <!-- Trigger button -->
    <button
      class="text-xs sm:text-sm border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-700
             focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer whitespace-nowrap"
      :class="open ? 'border-blue-300 ring-2 ring-blue-200' : ''"
      @click="togglePopover"
    >
      {{ triggerLabel }} ▾
    </button>

    <!-- Popover -->
    <Transition name="picker">
      <div
        v-if="open"
        class="absolute left-0 top-full mt-1 z-[1001] bg-white rounded-2xl shadow-xl border border-gray-100 p-3 select-none"
        style="min-width:200px; max-height:calc(100vh - 60px); overflow-y:auto;"
      >
        <!-- SVG map -->
        <svg
          viewBox="0 0 530 740"
          width="160"
          height="224"
          class="block mx-auto"
          xmlns="http://www.w3.org/2000/svg"
        >
          <g>
            <path
              v-for="item in CITY_PATHS"
              :key="item.city"
              :data-city="item.city"
              :d="item.d"
              :fill="pathFill(item.city)"
              stroke="#ffffff"
              stroke-width="0.5"
              class="cursor-pointer transition-colors duration-100"
              :class="item.city !== currentCity ? 'hover:fill-[#93c5fd]' : ''"
              @click="selectCity(item.city)"
            />
            <text
              v-for="item in CITY_PATHS"
              :key="'label-' + item.city"
              :x="item.cx"
              :y="item.cy + 4"
              text-anchor="middle"
              font-size="11"
              :fill="pathTextFill(item.city)"
              class="pointer-events-none"
              style="font-family:system-ui,sans-serif;"
            >{{ item.city }}</text>
          </g>
        </svg>

        <!-- Offshore islands -->
        <div class="flex gap-1 mt-2 justify-center">
          <button
            v-for="city in OFFSHORE_ISLANDS"
            :key="city"
            class="px-2 py-0.5 rounded-full text-[11px] font-medium border transition-colors"
            :class="islandActive(city)
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-blue-100 hover:border-blue-300'"
            @click="selectCity(city)"
          >{{ city }}</button>
        </div>

        <!-- 全台灣 -->
        <button
          class="mt-2 w-full px-3 py-1 rounded-full text-xs font-medium border transition-colors"
          :class="currentCity === '全台灣'
            ? 'bg-blue-600 text-white border-blue-600'
            : 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-blue-100 hover:border-blue-300'"
          @click="selectCity('全台灣')"
        >🌏 全台灣</button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.picker-enter-active { transition: opacity 0.15s ease-out, transform 0.15s ease-out; }
.picker-leave-active { transition: opacity 0.1s ease-in, transform 0.1s ease-in; }
.picker-enter-from   { opacity: 0; transform: translateY(-4px); }
.picker-leave-to     { opacity: 0; transform: translateY(-4px); }
</style>
```

- [ ] **Step 2: Verify the file was created**

```bash
ls src/components/TaiwanCityPicker.vue
```
Expected: file exists, no error.

- [ ] **Step 3: Commit**

```bash
git add src/components/TaiwanCityPicker.vue
git commit -m "feat: add TaiwanCityPicker SVG city picker component"
```

---

## Chunk 2: Wire TaiwanCityPicker into FilterBar + clean up App.vue

### Task 2: Update FilterBar.vue

**Files:**
- Modify: `src/components/FilterBar.vue`

- [ ] **Step 1: Remove `allCities` prop and `<select>` block; add TaiwanCityPicker**

Open `src/components/FilterBar.vue`. Make these four edits:

**Edit 1 — imports:** Add `TaiwanCityPicker` import. The current first line is `import { ref, computed } from 'vue'`; add the component import directly after it:
```js
import TaiwanCityPicker from './TaiwanCityPicker.vue'
```

**Edit 2 — props:** Remove the `allCities` prop entirely (one line in the `defineProps` object):
```js
// DELETE this line:
allCities:        { type: Array,   default: () => [] },
```

**Edit 3 — template:** Replace the `<!-- City selector -->` block (the entire `<select>...</select>`, lines 81–90) with:
```html
<!-- City selector -->
<TaiwanCityPicker
  :current-city="currentCity"
  @update:current-city="emit('update:currentCity', $event)"
/>
```

**Edit 4 — remove `onCityChange`:** Delete this function from `<script setup>` (lines 63–65):
```js
// DELETE:
function onCityChange(e) {
  emit('update:currentCity', e.target.value)
}
```

- [ ] **Step 2: Verify FilterBar.vue has no remaining references to `allCities` or `onCityChange`**

```bash
grep -n "allCities\|onCityChange\|<select" src/components/FilterBar.vue
```
Expected: no output (zero matches).

- [ ] **Step 3: Commit**

```bash
git add src/components/FilterBar.vue
git commit -m "feat: replace city <select> with TaiwanCityPicker in FilterBar"
```

---

### Task 3: Update App.vue

**Files:**
- Modify: `src/App.vue`

- [ ] **Step 1: Remove `ALL_CITIES` from import and from `<FilterBar>` binding**

Open `src/App.vue`. Make two edits:

**Edit 1 — line 10, named import:** Change:
```js
import { useAnimals, ALL_CITIES } from './composables/useAnimals.js'
```
to:
```js
import { useAnimals } from './composables/useAnimals.js'
```

**Edit 2 — `<FilterBar>` template binding:** Remove the `:all-cities="ALL_CITIES"` line from the `<FilterBar>` component usage.

- [ ] **Step 2: Verify no remaining references to `ALL_CITIES` in App.vue**

```bash
grep -n "ALL_CITIES\|all-cities\|allCities" src/App.vue
```
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add src/App.vue
git commit -m "chore: remove unused ALL_CITIES import and all-cities binding"
```

---

## Chunk 3: Manual verification

### Task 4: Run dev server and manually verify

- [ ] **Step 1: Start the dev server**

```bash
pnpm dev
```
Expected: server starts, no compile errors in console.

- [ ] **Step 2: Verify trigger button appears**

Open the app in browser. The header bar should show a button with the current city name and a `▾` arrow where the old dropdown was. All other controls (kind pills, more-filters button, count) should remain unchanged.

- [ ] **Step 3: Verify popover opens**

Click the trigger button. A popover should appear below it containing:
- A small SVG map of Taiwan (roughly 160px wide)
- Three small pill buttons: 澎湖縣, 金門縣, 連江縣
- A full-width 🌏 全台灣 button

The default selected city (臺中市) should appear in blue on the SVG map. To verify `data-city` attributes are present, run in DevTools console:
```js
document.querySelectorAll('path[data-city]').length
```
Expected: `19`.

- [ ] **Step 4: Verify city switching works**

Click a different city on the SVG map (e.g. 臺北市). Expected:
- Popover closes
- Trigger button label updates to 臺北市
- Main Leaflet map flies to Taipei
- Animal data reloads for the new city

If the map does not fly, open DevTools Network tab and confirm a fetch request for 臺北市 data fired. If it did, the issue is in `MapView.flyToCity`, not in this feature.

- [ ] **Step 5: Verify offshore island selection**

Click 澎湖縣 pill. Expected: popover closes, map flies to Penghu, data reloads.

- [ ] **Step 6: Verify 全台灣 selection**

Click 🌏 全台灣. Expected: toast notification appears, all-Taiwan data loads.

- [ ] **Step 7: Verify popover dismissal**

Re-open the popover. Then:
- Click outside → popover closes ✓
- Re-open, press Escape → popover closes ✓ (AnimalCard must NOT close simultaneously)
- Re-open, click trigger button again → popover closes ✓

- [ ] **Step 8: Verify mobile layout**

Resize browser to 375px width. Popover should still open and be scrollable if it exceeds viewport height.

- [ ] **Step 9: Final commit if any fixes were needed**

```bash
git add -p
git commit -m "fix: <describe what was fixed>"
```
(Only if step 2-8 revealed issues that needed fixing.)
