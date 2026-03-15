# Design Spec: Taiwan SVG City Picker

**Date:** 2026-03-15
**Status:** Approved

## Overview

Replace the `<select>` dropdown in the header bar with a button that opens a popover containing an inline SVG map of Taiwan. Users click a county/city shape to switch the main map's city. The current city is highlighted with a distinct fill colour.

---

## Architecture

A new component `TaiwanCityPicker.vue` is added. It encapsulates all SVG data, hover/select state, and popover open/close logic. `FilterBar.vue` imports it and renders it in place of the existing `<select>` element. No changes are needed to `App.vue` or `useAnimals.js`.

```
FilterBar.vue
  └── TaiwanCityPicker.vue   (new)
        ├── SVG path data    (inline, keyed by city name)
        ├── popover open/close logic
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

**Trigger button** — shows the current city name (or 🌏 全台灣). Clicking opens the popover. Clicking outside or pressing Escape closes it.

**Popover** — appears below the trigger button, z-index above the map (≥ 1001). Contains:
1. The SVG map of Taiwan mainland counties/cities
2. A small row of buttons below the SVG for the three offshore islands: 澎湖縣, 金門縣, 連江縣 (they are too small to click reliably on the SVG)
3. A "🌏 全台灣" button at the bottom

**SVG map**
- ViewBox tuned to Taiwan mainland bounds
- Each `<path>` has a `data-city` attribute with the Chinese city name
- States:
  - Default: `fill: #e5e7eb` (gray-200), `stroke: #fff`, `stroke-width: 0.5`
  - Hover: `fill: #93c5fd` (blue-300)
  - Selected: `fill: #2563eb` (blue-600), label text turns white
- City label (abbreviated, ≤3 chars) rendered as `<text>` centred on each path's bounding box
- Clicking a path emits `update:currentCity` and closes the popover

**Offshore islands row** — three pill buttons with the same hover/selected colour logic as the SVG paths.

**全台灣 button** — at bottom of popover, full-width, same pill style.

### SVG Data Source

Use the publicly available Taiwan county SVG path data from the `twgeojson` project (MIT licence). Paths are simplified to ~2% tolerance for small-size rendering. Data is embedded directly in the component as a JS constant — no runtime fetch required.

---

## Visual Design

- Popover: `bg-white rounded-2xl shadow-xl border border-gray-100 p-3`, min-width 180px
- SVG size: 160×300px (width×height), scales with `viewBox`
- Transition: fade + slight translateY (reuse existing `.panel-enter/leave` pattern)
- Mobile: same behaviour — popover opens downward, user can scroll if needed

---

## What Changes

| File | Change |
|------|--------|
| `src/components/TaiwanCityPicker.vue` | **New** — full SVG picker component |
| `src/components/FilterBar.vue` | Replace `<select>` block with `<TaiwanCityPicker>` |

No other files change.

---

## Out of Scope

- Colour coding paths by animal count (future enhancement)
- Search/filter within the picker
- Animated path transitions on city load
