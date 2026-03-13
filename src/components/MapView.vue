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

const emit = defineEmits(['locationClick'])
const { initMap, updateMarkers } = useMap()

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
</script>

<template>
  <div id="map-container" class="w-full h-full" />
</template>
