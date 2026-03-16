// src/composables/useAnimals.js
import { ref, computed } from 'vue'

// Estimate lat/lng bounds from a city center + zoom level.
// Uses the Web Mercator tile size formula: at zoom Z, one tile covers 360/2^Z degrees longitude.
// We assume a ~800×600 viewport as reference.
function estimateBounds(lat, lng, zoom) {
  const lngDelta = 360 / Math.pow(2, zoom) * (800 / 256) / 2
  const latDelta = lngDelta * 0.7 // rough aspect correction
  return {
    minLat: lat - latDelta,
    maxLat: lat + latDelta,
    minLng: lng - lngDelta,
    maxLng: lng + lngDelta,
  }
}

let preloadIdleHandle = null

// City centers for map flyTo (mirrors config.py CITY_CENTERS)
export const CITY_CENTERS = {
  '臺北市':  { lat: 25.0478, lng: 121.5319, zoom: 12 },
  '新北市':  { lat: 25.0120, lng: 121.4653, zoom: 11 },
  '基隆市':  { lat: 25.1283, lng: 121.7419, zoom: 13 },
  '桃園市':  { lat: 24.9937, lng: 121.3009, zoom: 11 },
  '新竹市':  { lat: 24.8138, lng: 120.9675, zoom: 13 },
  '新竹縣':  { lat: 24.7036, lng: 121.1542, zoom: 11 },
  '苗栗縣':  { lat: 24.5602, lng: 120.8214, zoom: 11 },
  '臺中市':  { lat: 24.1477, lng: 120.6736, zoom: 12 },
  '彰化縣':  { lat: 23.9921, lng: 120.5161, zoom: 11 },
  '南投縣':  { lat: 23.9610, lng: 120.9718, zoom: 11 },
  '雲林縣':  { lat: 23.7092, lng: 120.4313, zoom: 11 },
  '嘉義市':  { lat: 23.4801, lng: 120.4491, zoom: 13 },
  '嘉義縣':  { lat: 23.4518, lng: 120.2555, zoom: 11 },
  '臺南市':  { lat: 22.9999, lng: 120.2270, zoom: 11 },
  '高雄市':  { lat: 22.6273, lng: 120.3014, zoom: 11 },
  '屏東縣':  { lat: 22.5519, lng: 120.5487, zoom: 11 },
  '宜蘭縣':  { lat: 24.7021, lng: 121.7378, zoom: 11 },
  '花蓮縣':  { lat: 23.9871, lng: 121.6015, zoom: 10 },
  '臺東縣':  { lat: 22.7972, lng: 121.0713, zoom: 10 },
  '澎湖縣':  { lat: 23.5654, lng: 119.5793, zoom: 12 },
  '金門縣':  { lat: 24.4493, lng: 118.3765, zoom: 12 },
  '連江縣':  { lat: 26.1605, lng: 119.9497, zoom: 13 },
  '全台灣':  { lat: 23.9739, lng: 120.9820, zoom:  8 },
}

export const ALL_CITIES = Object.keys(CITY_CENTERS)

export function useAnimals() {
  const animals = ref([])
  const locations = ref([])
  const loading = ref(true)
  const error = ref(null)
  const noData = ref(false)
  const updatedAt = ref('')

  // Primary filters
  const currentCity = ref('臺中市')
  const filterKind = ref('all')       // 'all' | 'cat' | 'dog'

  // Secondary filters (shown in expandable panel)
  const filterSource = ref('all')     // 'all' | 'shelter' | 'vet_transit' | 'yiqi'
  const filterSex = ref('all')        // 'all' | 'M' | 'F'
  const filterColour = ref('all')     // 'all' | colour string

  // Derived: which source types exist in current city data
  const availableSources = computed(() => {
    const types = new Set(locations.value.map(l => l.type).filter(Boolean))
    return [...types]
  })

  // Derived: which colours exist in current city data
  const availableColours = computed(() => {
    const colours = new Set(animals.value.map(a => a.colour).filter(Boolean))
    return [...colours].sort()
  })

  // Build a location_id → location.type lookup
  const locationTypeMap = computed(() => {
    const map = {}
    locations.value.forEach(l => { map[l.id] = l.type })
    return map
  })

  const filteredAnimals = computed(() => {
    return animals.value.filter(a => {
      if (filterKind.value !== 'all' && a.kind !== filterKind.value) return false
      if (filterSource.value !== 'all') {
        const locType = locationTypeMap.value[a.location_id]
        if (locType !== filterSource.value) return false
      }
      if (filterSex.value !== 'all' && a.sex !== filterSex.value) return false
      if (filterColour.value !== 'all' && a.colour !== filterColour.value) return false
      return true
    })
  })

  const filteredLocations = computed(() => {
    const countMap = {}
    filteredAnimals.value.forEach(a => {
      if (!countMap[a.location_id]) countMap[a.location_id] = { cat: 0, dog: 0 }
      if (a.kind === 'cat') countMap[a.location_id].cat++
      else if (a.kind === 'dog') countMap[a.location_id].dog++
    })
    return locations.value
      .map(loc => ({ ...loc, counts: countMap[loc.id] || { cat: 0, dog: 0 } }))
      .filter(loc => loc.counts.cat + loc.counts.dog > 0)
  })

  function resetSecondaryFilters() {
    filterSource.value = 'all'
    filterSex.value = 'all'
    filterColour.value = 'all'
  }

  async function loadData(city = '臺中市') {
    loading.value = true
    error.value = null
    noData.value = false
    currentCity.value = city
    resetSecondaryFilters()

    try {
      const base = import.meta.env.BASE_URL
      const suffix = city === '全台灣' ? '全台' : city
      const [animalsRes, locationsRes] = await Promise.all([
        fetch(`${base}data/animals_${suffix}.json`),
        fetch(`${base}data/locations_${suffix}.json`),
      ])

      if (!animalsRes.ok || !locationsRes.ok) {
        noData.value = true
        animals.value = []
        locations.value = []
        return
      }

      const animalsText = await animalsRes.text()
      const locationsText = await locationsRes.text()
      if (!animalsText.trimStart().startsWith('{')) {
        noData.value = true
        animals.value = []
        locations.value = []
        return
      }

      const animalsData = JSON.parse(animalsText)
      const locationsData = JSON.parse(locationsText)

      animals.value = animalsData.animals
      locations.value = locationsData.locations
      updatedAt.value = animalsData.updated_at
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }

    preloadVisibleThumbs(city)
  }

  function preloadVisibleThumbs(city) {
    if (preloadIdleHandle) cancelIdleCallback(preloadIdleHandle)

    const center = CITY_CENTERS[city]
    if (!center || !animals.value.length) return

    const bounds = estimateBounds(center.lat, center.lng, center.zoom)

    // Collect photo URLs from animals whose location falls within the initial viewport
    const locationSet = new Set(
      locations.value
        .filter(l => l.lat >= bounds.minLat && l.lat <= bounds.maxLat &&
                     l.lng >= bounds.minLng && l.lng <= bounds.maxLng)
        .map(l => l.id)
    )
    const urls = animals.value
      .filter(a => locationSet.has(a.location_id) && a.photo_url)
      .map(a => a.photo_url)

    if (!urls.length) return

    // Batch-preload via requestIdleCallback so we don't block the main thread
    let i = 0
    function loadBatch(deadline) {
      while (i < urls.length && (deadline.timeRemaining() > 0 || deadline.didTimeout)) {
        const img = new Image()
        img.src = urls[i++]
      }
      if (i < urls.length) {
        preloadIdleHandle = requestIdleCallback(loadBatch, { timeout: 2000 })
      }
    }
    preloadIdleHandle = requestIdleCallback(loadBatch, { timeout: 2000 })
  }

  return {
    animals,
    locations,
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
    resetSecondaryFilters,
    CITY_CENTERS,
    ALL_CITIES,
  }
}
