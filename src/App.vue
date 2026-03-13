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
      @update:filter-kind="val => filterKind = val"
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
