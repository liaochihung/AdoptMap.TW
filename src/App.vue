<!-- src/App.vue -->
<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import FilterBar from './components/FilterBar.vue'
import MapView from './components/MapView.vue'
import AnimalCard from './components/AnimalCard.vue'
import LegendPanel from './components/LegendPanel.vue'
import HoverPreview from './components/HoverPreview.vue'
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
const selectedAnimalIndex = ref(0)
const hoveredLocation = ref(null)
const hoveredPosition = ref(null)

// Timer for hover delay (allows mouse to move from marker to preview panel)
let hoverLeaveTimer = null

function onKeyDown(e) {
  if (e.key === 'Escape') closeCard()
}

onMounted(() => {
  loadData()
  window.addEventListener('keydown', onKeyDown)
})
onUnmounted(() => window.removeEventListener('keydown', onKeyDown))

// Accept either a plain location object (from map click) or { location, animalIndex } (from hover preview)
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

function closeCard() {
  selectedLocation.value = null
}

function handleLocationHover(location, position) {
  clearTimeout(hoverLeaveTimer)
  if (location) {
    hoveredLocation.value = location
    hoveredPosition.value = position
  } else {
    // Delay hiding so mouse can move to the preview panel
    hoverLeaveTimer = setTimeout(() => {
      hoveredLocation.value = null
      hoveredPosition.value = null
    }, 200)
  }
}

function onPreviewMouseEnter() {
  clearTimeout(hoverLeaveTimer)
}

function onPreviewMouseLeave() {
  hoverLeaveTimer = setTimeout(() => {
    hoveredLocation.value = null
    hoveredPosition.value = null
  }, 150)
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
      @update:filter-kind="val => filterKind = val"
    />

    <!-- Legend panel -->
    <LegendPanel />

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
        @location-hover="handleLocationHover"
      />
    </div>

    <!-- Hover preview panel -->
    <HoverPreview
      :location="hoveredLocation"
      :animals="filteredAnimals"
      :position="hoveredPosition"
      :map-top-offset="48"
      @mouseenter="onPreviewMouseEnter"
      @mouseleave="onPreviewMouseLeave"
      @select="handleLocationClick"
    />

    <!-- Animal card popup -->
    <AnimalCard
      :location="selectedLocation"
      :animals="filteredAnimals"
      :initial-index="selectedAnimalIndex"
      @close="closeCard"
    />

    <!-- Footer: update time -->
    <div class="absolute bottom-4 left-4 z-[1000] text-xs text-gray-500 bg-white/80 px-2 py-1 rounded">
      資料更新：{{ formatDate(updatedAt) }}
      ｜資料來源：農業部動物認領養 Open Data
    </div>
  </div>
</template>
