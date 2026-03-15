<!-- src/App.vue -->
<script setup>
import { onMounted, onUnmounted, ref, nextTick } from 'vue'
import FilterBar from './components/FilterBar.vue'
import MapView from './components/MapView.vue'
import AnimalCard from './components/AnimalCard.vue'
import LegendPanel from './components/LegendPanel.vue'
import HoverPreview from './components/HoverPreview.vue'
import ToastNotification from './components/ToastNotification.vue'
import { useAnimals, ALL_CITIES } from './composables/useAnimals.js'

const {
  loading,
  error,
  noData,
  updatedAt,
  currentCity,
  filterKind,
  filterSource,
  filterSex,
  filterColour,
  availableSources,
  availableColours,
  filteredAnimals,
  filteredLocations,
  loadData,
} = useAnimals()

const mapRef = ref(null)
const selectedLocation = ref(null)
const selectedAnimalIndex = ref(0)
const hoveredLocation = ref(null)
const hoveredPosition = ref(null)
const toastMessage = ref('')

const isMobile = ref(window.innerWidth < 640)
function onResize() { isMobile.value = window.innerWidth < 640 }

let hoverLeaveTimer = null

function onKeyDown(e) {
  if (e.key === 'Escape') closeCard()
}

onMounted(() => {
  loadData('臺中市')
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('resize', onResize)
})

async function handleCityChange(city) {
  if (city === '全台灣') {
    // Reset to '' first so the watch in ToastNotification fires even if message is unchanged
    toastMessage.value = ''
    await nextTick()
    toastMessage.value = '🌏 全台資料約 3000+ 筆，載入中…'
  }
  selectedLocation.value = null
  await loadData(city)
  // Fly map to new city center
  if (mapRef.value?.flyToCity) {
    mapRef.value.flyToCity(city)
  }
}

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

function closeCard() { selectedLocation.value = null }

function handleLocationHover(location, position) {
  clearTimeout(hoverLeaveTimer)
  if (location) {
    hoveredLocation.value = location
    hoveredPosition.value = position
  } else {
    hoverLeaveTimer = setTimeout(() => {
      hoveredLocation.value = null
      hoveredPosition.value = null
    }, 200)
  }
}

function onPreviewMouseEnter() { clearTimeout(hoverLeaveTimer) }
function onPreviewMouseLeave() {
  hoverLeaveTimer = setTimeout(() => {
    hoveredLocation.value = null
    hoveredPosition.value = null
  }, 150)
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleString('zh-TW', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <div class="relative w-screen h-screen overflow-hidden">
    <!-- Toast -->
    <ToastNotification :message="toastMessage" />

    <!-- Filter bar -->
    <FilterBar
      :current-city="currentCity"
      :all-cities="ALL_CITIES"
      :filter-kind="filterKind"
      :filter-source="filterSource"
      :filter-sex="filterSex"
      :filter-colour="filterColour"
      :available-sources="availableSources"
      :available-colours="availableColours"
      :filtered-count="filteredAnimals.length"
      @update:current-city="handleCityChange"
      @update:filter-kind="val => filterKind = val"
      @update:filter-source="val => filterSource = val"
      @update:filter-sex="val => filterSex = val"
      @update:filter-colour="val => filterColour = val"
    />

    <!-- Legend panel (desktop only) -->
    <LegendPanel class="hidden sm:block" />

    <!-- Loading overlay -->
    <div v-if="loading" class="absolute inset-0 z-[2000] flex items-center justify-center bg-white/80">
      <div class="text-center text-gray-600">
        <div class="text-4xl mb-2">🗺</div>
        <div class="text-sm">載入中…</div>
      </div>
    </div>

    <!-- Error overlay -->
    <div v-if="error" class="absolute inset-0 z-[2000] flex items-center justify-center bg-white/90">
      <div class="text-center text-red-600">
        <div class="text-4xl mb-2">⚠️</div>
        <div class="text-sm">{{ error }}</div>
      </div>
    </div>

    <!-- No data overlay (shows map underneath) -->
    <div v-if="noData && !loading" class="absolute top-[44px] inset-x-0 z-[999] flex justify-center pointer-events-none">
      <div class="mt-6 flex items-center gap-2 bg-white/90 backdrop-blur-sm text-gray-500 text-sm px-4 py-2.5 rounded-xl shadow-md">
        <span>😔</span>
        <span>{{ currentCity }} 目前尚無領養資料</span>
      </div>
    </div>

    <!-- Map: top offset increases when panel is open, but we keep it simple at 44px base -->
    <div class="absolute inset-0 top-[44px]">
      <MapView
        ref="mapRef"
        :locations="filteredLocations"
        @location-click="handleLocationClick"
        @location-hover="handleLocationHover"
      />
    </div>

    <!-- Hover preview (desktop only) -->
    <HoverPreview
      v-if="!isMobile"
      :location="hoveredLocation"
      :animals="filteredAnimals"
      :position="hoveredPosition"
      :map-top-offset="44"
      @mouseenter="onPreviewMouseEnter"
      @mouseleave="onPreviewMouseLeave"
      @select="handleLocationClick"
    />

    <!-- Desktop: slide-in panel -->
    <template v-if="!isMobile">
      <AnimalCard
        :location="selectedLocation"
        :animals="filteredAnimals"
        :initial-index="selectedAnimalIndex"
        @close="closeCard"
      />
    </template>

    <!-- Mobile: bottom sheet -->
    <template v-else>
      <Transition name="sheet-up">
        <div v-if="selectedLocation" class="absolute inset-x-0 bottom-0 z-[1001]" style="max-height:88vh;">
          <div class="fixed inset-0 bg-black/20 backdrop-blur-[1px]" @click="closeCard" />
          <div class="relative rounded-t-3xl overflow-hidden" style="background:rgba(255,255,255,0.99);box-shadow:0 -8px 40px rgba(0,0,0,0.18);">
            <div class="flex justify-center pt-3 pb-1">
              <div class="w-10 h-1.5 rounded-full bg-gray-300" />
            </div>
            <AnimalCard
              :location="selectedLocation"
              :animals="filteredAnimals"
              :initial-index="selectedAnimalIndex"
              mobile
              @close="closeCard"
            />
          </div>
        </div>
      </Transition>
    </template>

    <!-- Footer -->
    <div class="absolute bottom-4 left-4 z-[1000] text-xs text-gray-500 bg-white/80 backdrop-blur-sm px-2.5 py-1.5 rounded-lg hidden sm:block"
      style="box-shadow:0 1px 6px rgba(0,0,0,0.08);">
      資料更新：{{ formatDate(updatedAt) }}
      ｜資料來源：農業部動物認領養 Open Data
    </div>
  </div>
</template>

<style>
/* Mobile bottom sheet animation */
.sheet-up-enter-active { transition: transform 0.32s cubic-bezier(0.16,1,0.3,1); }
.sheet-up-leave-active { transition: transform 0.22s ease-in; }
.sheet-up-enter-from  { transform: translateY(100%); }
.sheet-up-leave-to    { transform: translateY(100%); }
</style>
