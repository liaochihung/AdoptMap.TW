# Design Spec: Taiwan SVG City Picker

**Date:** 2026-03-15
**Status:** Approved

## Overview

Replace the `<select>` dropdown in the header bar with a button that opens a popover containing an inline SVG map of Taiwan. Users click a county/city shape to switch the main map's city. The current city is highlighted with a distinct fill colour.

---

## Architecture

A new component `TaiwanCityPicker.vue` is added. It encapsulates all SVG data, hover/select state, and popover open/close logic. `FilterBar.vue` imports it and renders it in place of the existing `<select>` element.

City names come from `CITY_CENTERS` in `useAnimals.js` — `TaiwanCityPicker` imports this directly, so the `allCities` prop is **removed** from `FilterBar.vue` and the corresponding `:all-cities` binding is removed from `App.vue`.

```
FilterBar.vue
  └── TaiwanCityPicker.vue   (new)
        ├── SVG path data    (inline JS constant, sourced from twgeojson)
        ├── imports CITY_CENTERS from useAnimals.js
        ├── popover open/close logic (pure, no @vueuse/core)
        └── emits 'update:currentCity'
```

---

## Component: TaiwanCityPicker.vue

### Props
| Prop | Type | Description |
|------|------|-------------|
| `currentCity` | String | Currently selected city name |

### Emits
| Event | Payload | Description |
|-------|---------|-------------|
| `update:currentCity` | String | City name user clicked |

### Behaviour

**Trigger button** — shows the current city name (or 🌏 全台灣). Clicking toggles the popover open/closed.

**Popover dismiss:**
- Click the trigger button again
- Click anywhere outside the popover (implemented via `document.addEventListener('pointerdown', handler, true)` in capture phase, registered on open and removed on close / `onUnmounted`)
- Press Escape — `TaiwanCityPicker` registers a `keydown` listener on its own root element (not `window`), so it fires before `App.vue`'s `window`-level Escape handler in the bubble chain; call `event.stopPropagation()` to prevent the event reaching `window` and accidentally closing `AnimalCard`

**Popover** — appears below the trigger button, `position: fixed`, `z-index: 1001` (above FilterBar's `z-[1000]`). Contains:
1. The SVG map of Taiwan mainland counties/cities (19 paths)
2. A small row of buttons below the SVG for three offshore islands: 澎湖縣, 金門縣, 連江縣
3. A "🌏 全台灣" button at the bottom

Total cities: 22 縣市 + 全台灣 = 23 items (matching `Object.keys(CITY_CENTERS)`).

**SVG map**
- ViewBox tuned to Taiwan mainland geographic bounds
- Each `<path>` has a `data-city` attribute with the Chinese city name
- City label: full 3-character name (e.g. `臺北市`, `新竹縣`) rendered as `<text>` centred on the path's approximate centroid — no abbreviation mapping needed
- States:
  - Default: `fill: #e5e7eb` (gray-200), `stroke: #fff`, `stroke-width: 0.5`
  - Hover: `fill: #93c5fd` (blue-300)
  - Selected (matches `currentCity`): `fill: #2563eb` (blue-600), label colour `#fff`
- Each path's `data-city` value must exactly match a key in `CITY_CENTERS`; clicking an unmatched path (if any) is a no-op
- Clicking a matched path emits `update:currentCity` and closes the popover

**Offshore islands row** — three pill buttons with the same hover/selected colour logic as the SVG paths.

**全台灣 button** — full-width pill at bottom of popover.

### SVG Data Source

Taiwan county outline SVG path data taken from the `twgeojson` open-source project (MIT licence). Paths are embedded directly in the component as a JS constant — no runtime fetch. A source comment at the top of the constant records the origin commit for traceability.

---

## Visual Design

- Trigger button: matches the style of other FilterBar controls — `border border-gray-200 rounded-lg px-2 py-1 text-xs sm:text-sm bg-white text-gray-700`
- Popover: `bg-white rounded-2xl shadow-xl border border-gray-100 p-3`, min-width 200px
- SVG size: 160×300px (width×height) via `viewBox`
- Mobile safety: popover sets `max-height: calc(100vh - 60px); overflow-y: auto` to prevent overflow on small/landscape screens
- Transition: fade + slight translateY, reusing the same `.panel-enter/leave` pattern already in `FilterBar.vue`

---

## What Changes

| File | Change |
|------|--------|
| `src/components/TaiwanCityPicker.vue` | **New** — SVG picker component |
| `src/components/FilterBar.vue` | Replace `<select>` with `<TaiwanCityPicker>`; remove `allCities` prop |
| `src/App.vue` | Remove `:all-cities="ALL_CITIES"` binding from `<FilterBar>`; remove `ALL_CITIES` from the named import on line 10 |

`useAnimals.js` and all other files are unchanged.

---

## Out of Scope

- Colour coding paths by animal count (future enhancement)
- Search/filter within the picker
- Animated path transitions on city load
- `@vueuse/core` or any new dependency
