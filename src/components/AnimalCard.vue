<!-- src/components/AnimalCard.vue -->
<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  location: {
    type: Object,
    default: null,
  },
  animals: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['close'])

// Paginate through animals at this location
const currentIndex = ref(0)

const locationAnimals = computed(() =>
  props.animals.filter(a => a.location_id === props.location?.id)
)

const currentAnimal = computed(() => locationAnimals.value[currentIndex.value] || null)

function prev() {
  if (currentIndex.value > 0) currentIndex.value--
}
function next() {
  if (currentIndex.value < locationAnimals.value.length - 1) currentIndex.value++
}

// Reset page when location changes
watch(() => props.location?.id, () => { currentIndex.value = 0 })

const sexLabel = { M: '♂ 公', F: '♀ 母', N: '未知' }
const ageLabel = { adult: '成年', child: '幼年' }
const bodytypeLabel = { small: '小型', medium: '中型', large: '大型' }

const typeLabel = {
  shelter: '公立收容所',
  vet_transit: '中途動物醫院',
  bulletin: '民眾送養',
}

const typeColor = {
  shelter: 'bg-blue-100 text-blue-700',
  vet_transit: 'bg-green-100 text-green-700',
  bulletin: 'bg-orange-100 text-orange-700',
}
</script>

<template>
  <div
    v-if="location"
    class="absolute bottom-6 right-4 z-[1000] w-72 bg-white rounded-xl shadow-2xl overflow-hidden"
  >
    <!-- Header: location info -->
    <div class="flex items-start justify-between px-4 pt-3 pb-2 bg-gray-50 border-b">
      <div class="flex-1 min-w-0">
        <div class="font-semibold text-gray-800 text-sm leading-tight truncate">{{ location.name }}</div>
        <div class="text-xs text-gray-500 mt-0.5 truncate">{{ location.address }}</div>
      </div>
      <button
        class="ml-2 text-gray-400 hover:text-gray-600 text-lg leading-none flex-shrink-0"
        @click="emit('close')"
      >✕</button>
    </div>

    <!-- Animal info -->
    <div v-if="currentAnimal" class="px-4 py-3">
      <!-- Photo placeholder -->
      <div class="w-full h-28 bg-gray-100 rounded-lg flex items-center justify-center mb-3 overflow-hidden">
        <img
          v-if="currentAnimal.photo_url"
          :src="currentAnimal.photo_url"
          :alt="currentAnimal.name || '待領養動物'"
          class="w-full h-full object-cover"
        />
        <span v-else class="text-5xl">{{ currentAnimal.kind === 'cat' ? '🐱' : '🐶' }}</span>
      </div>

      <!-- Name -->
      <div class="flex items-center gap-2 mb-2">
        <span class="font-semibold text-gray-800">
          {{ currentAnimal.name || (currentAnimal.kind === 'cat' ? '無名貓咪' : '無名狗狗') }}
        </span>
        <span :class="['text-xs px-2 py-0.5 rounded-full', typeColor[location.type] || 'bg-gray-100 text-gray-600']">
          {{ typeLabel[location.type] || location.type }}
        </span>
      </div>

      <!-- Tags -->
      <div class="flex flex-wrap gap-1 mb-2">
        <span class="tag">{{ sexLabel[currentAnimal.sex] || currentAnimal.sex }}</span>
        <span class="tag">{{ ageLabel[currentAnimal.age] || currentAnimal.age }}</span>
        <span class="tag">{{ bodytypeLabel[currentAnimal.bodytype] || currentAnimal.bodytype }}</span>
        <span v-if="currentAnimal.colour" class="tag">{{ currentAnimal.colour }}</span>
        <span v-if="currentAnimal.sterilized === true" class="tag bg-green-50 text-green-700">已絕育</span>
        <span v-if="currentAnimal.vaccinated === true" class="tag bg-blue-50 text-blue-700">已打疫苗</span>
      </div>

      <!-- Remark -->
      <p v-if="currentAnimal.remark" class="text-xs text-gray-600 mb-2 leading-relaxed line-clamp-2">
        {{ currentAnimal.remark }}
      </p>

      <!-- Contact (bulletin only) -->
      <div v-if="currentAnimal.contact_phone" class="text-xs text-gray-600 mb-2">
        📞 {{ currentAnimal.contact_name }} {{ currentAnimal.contact_phone }}
      </div>
      <div v-else-if="location.phone" class="text-xs text-gray-600 mb-2">
        📞 {{ location.phone }}
      </div>

      <!-- Source link -->
      <a
        v-if="currentAnimal.source_url"
        :href="currentAnimal.source_url"
        target="_blank"
        rel="noopener noreferrer"
        class="text-xs text-blue-600 hover:underline"
      >查看原始資料 →</a>
    </div>

    <!-- Empty state -->
    <div v-else class="px-4 py-6 text-center text-gray-400 text-sm">
      此地點目前無符合條件的動物
    </div>

    <!-- Pagination -->
    <div
      v-if="locationAnimals.length > 1"
      class="flex items-center justify-between px-4 py-2 border-t bg-gray-50 text-sm"
    >
      <button
        :disabled="currentIndex === 0"
        class="px-2 py-0.5 rounded disabled:opacity-30 hover:bg-gray-200"
        @click="prev"
      >← 上一隻</button>
      <span class="text-xs text-gray-500">{{ currentIndex + 1 }} / {{ locationAnimals.length }}</span>
      <button
        :disabled="currentIndex === locationAnimals.length - 1"
        class="px-2 py-0.5 rounded disabled:opacity-30 hover:bg-gray-200"
        @click="next"
      >下一隻 →</button>
    </div>
  </div>
</template>

<style scoped>
.tag {
  @apply text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full;
}
</style>
