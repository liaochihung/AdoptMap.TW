<!-- src/components/MapView.vue -->
<script setup>
import { onMounted, watch } from 'vue'
import { useMap } from '../composables/useMap.js'

const props = defineProps({
  locations: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['locationClick', 'locationHover'])
const { initMap, updateMarkers } = useMap()

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
</script>

<template>
  <div id="map-container" class="w-full h-full" />
</template>
