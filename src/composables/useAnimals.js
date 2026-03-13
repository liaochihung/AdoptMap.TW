// src/composables/useAnimals.js
import { ref, computed } from 'vue'

export function useAnimals() {
  const animals = ref([])
  const locations = ref([])
  const loading = ref(true)
  const error = ref(null)
  const updatedAt = ref('')

  const filterKind = ref('all')  // 'all' | 'cat' | 'dog'
  const filterArea = ref('all')  // 'all' | location id

  const filteredAnimals = computed(() => {
    return animals.value.filter(a => {
      if (filterKind.value !== 'all' && a.kind !== filterKind.value) return false
      if (filterArea.value !== 'all' && a.location_id !== filterArea.value) return false
      return true
    })
  })

  // Recompute per-location counts based on filtered animals
  const filteredLocations = computed(() => {
    const countMap = {}
    filteredAnimals.value.forEach(a => {
      if (!countMap[a.location_id]) countMap[a.location_id] = { cat: 0, dog: 0 }
      if (a.kind === 'cat') countMap[a.location_id].cat++
      else if (a.kind === 'dog') countMap[a.location_id].dog++
    })

    return locations.value
      .map(loc => ({
        ...loc,
        counts: countMap[loc.id] || { cat: 0, dog: 0 }
      }))
      .filter(loc => {
        const c = loc.counts
        return c.cat + c.dog > 0
      })
  })

  async function loadData() {
    loading.value = true
    error.value = null
    try {
      const base = import.meta.env.BASE_URL
      const [animalsRes, locationsRes] = await Promise.all([
        fetch(`${base}data/animals.json`),
        fetch(`${base}data/locations.json`)
      ])
      if (!animalsRes.ok) throw new Error(`Failed to load animals: ${animalsRes.status}`)
      if (!locationsRes.ok) throw new Error(`Failed to load locations: ${locationsRes.status}`)

      const animalsData = await animalsRes.json()
      const locationsData = await locationsRes.json()

      animals.value = animalsData.animals
      locations.value = locationsData.locations
      updatedAt.value = animalsData.updated_at
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return {
    animals,
    locations,
    loading,
    error,
    updatedAt,
    filterKind,
    filterArea,
    filteredAnimals,
    filteredLocations,
    loadData,
  }
}
