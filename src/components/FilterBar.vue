<!-- src/components/FilterBar.vue -->
<script setup>
defineProps({
  filterKind: {
    type: String,
    default: 'all',
  },
  filteredCount: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['update:filterKind'])

const kindOptions = [
  { value: 'all', label: '全部' },
  { value: 'cat', label: '🐱 貓' },
  { value: 'dog', label: '🐶 狗' },
]
</script>

<template>
  <div class="fixed top-0 left-0 right-0 z-[1000] flex items-center gap-3 px-4 py-2 bg-white/90 backdrop-blur-sm shadow-md">
    <!-- Title -->
    <span class="font-bold text-gray-800 text-sm whitespace-nowrap">🗺 領養地圖</span>

    <!-- Kind filter buttons -->
    <div class="flex gap-1">
      <button
        v-for="opt in kindOptions"
        :key="opt.value"
        :class="[
          'px-3 py-1 rounded-full text-sm font-medium transition-colors',
          filterKind === opt.value
            ? 'bg-blue-600 text-white shadow-sm'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        ]"
        @click="emit('update:filterKind', opt.value)"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- Count display -->
    <span class="text-xs text-gray-500 ml-auto whitespace-nowrap">
      顯示 {{ filteredCount }} 隻
    </span>
  </div>
</template>
