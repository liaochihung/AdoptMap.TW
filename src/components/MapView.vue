<!-- src/components/MapView.vue -->
<script setup>
import { onMounted, ref, watch } from 'vue'
import { useMap } from '../composables/useMap.js'

const props = defineProps({
  locations: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['locationClick', 'locationHover'])
const { initMap, updateMarkers, flyToCity, locateUser } = useMap()

// Locate button state
const locating = ref(false)
const locateError = ref(null)
let errorTimer = null

function registerMarkers(locs) {
  updateMarkers(
    locs,
    loc => emit('locationClick', loc),
    (loc, pos) => emit('locationHover', loc, pos),
  )
}

onMounted(() => {
  initMap('map-container')
  registerMarkers(props.locations)
})

watch(
  () => props.locations,
  newLocs => registerMarkers(newLocs),
  { deep: true }
)

function handleLocate() {
  if (locating.value) return
  locating.value = true
  locateError.value = null
  clearTimeout(errorTimer)

  locateUser(
    () => { locating.value = false },
    msg => {
      locating.value = false
      locateError.value = msg
      errorTimer = setTimeout(() => { locateError.value = null }, 3000)
    }
  )
}

defineExpose({ flyToCity })
</script>

<template>
  <div class="relative w-full h-full">
    <div id="map-container" class="w-full h-full" />

    <!-- Locate me button -->
    <div class="absolute bottom-12 right-4 z-[1000] flex flex-col items-end gap-2">
      <!-- Error tooltip -->
      <Transition name="err-fade">
        <div
          v-if="locateError"
          class="bg-gray-900 text-white text-xs px-3 py-1.5 rounded-lg shadow-lg whitespace-nowrap"
        >{{ locateError }}</div>
      </Transition>

      <button
        :disabled="locating"
        class="w-10 h-10 rounded-full bg-white shadow-lg flex items-center justify-center text-gray-600 hover:text-blue-600 hover:shadow-xl transition-all active:scale-95 disabled:opacity-60"
        style="box-shadow:0 3px 12px rgba(0,0,0,0.18);"
        title="定位我的位置"
        @click="handleLocate"
      >
        <!-- Spinning indicator while locating -->
        <svg v-if="locating" class="animate-spin w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
        </svg>
        <!-- Location crosshair icon -->
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3" />
          <path stroke-linecap="round" d="M12 2v3m0 14v3M2 12h3m14 0h3" />
          <circle cx="12" cy="12" r="8" stroke-dasharray="2 2" stroke-width="1.5" opacity="0.5"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.err-fade-enter-active, .err-fade-leave-active { transition: all 0.2s ease; }
.err-fade-enter-from, .err-fade-leave-to { opacity: 0; transform: translateY(4px); }
</style>
