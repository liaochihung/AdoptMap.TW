<!-- src/components/FilterBar.vue -->
<script setup>
defineProps({
  filterKind: { type: String, default: 'all' },
  filteredCount: { type: Number, default: 0 },
})

const emit = defineEmits(['update:filterKind'])

const kindOptions = [
  { value: 'all',  label: '全部',    emoji: null },
  { value: 'cat',  label: '貓',      emoji: '🐱' },
  { value: 'dog',  label: '狗',      emoji: '🐶' },
]
</script>

<template>
  <div class="fixed top-0 left-0 right-0 z-[1000] flex items-center gap-2 px-3 sm:px-4 py-2 bg-white/92 backdrop-blur-md border-b border-gray-100/80"
    style="box-shadow:0 1px 12px rgba(0,0,0,0.08);"
  >
    <!-- Logo / title -->
    <span class="font-bold text-gray-800 text-sm whitespace-nowrap leading-none select-none">
      🗺&nbsp;<span class="hidden sm:inline">領養地圖</span>
    </span>

    <!-- Kind filter pills -->
    <div class="flex gap-1 ml-1">
      <button
        v-for="opt in kindOptions"
        :key="opt.value"
        :class="[
          'px-2.5 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium transition-all',
          filterKind === opt.value
            ? 'bg-blue-600 text-white shadow-sm scale-105'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 active:scale-95',
        ]"
        @click="emit('update:filterKind', opt.value)"
      >
        <span v-if="opt.emoji">{{ opt.emoji }}&nbsp;</span>{{ opt.label }}
      </button>
    </div>

    <!-- Count badge -->
    <div class="ml-auto flex items-center gap-1.5">
      <span class="text-xs text-gray-400 whitespace-nowrap tabular-nums">
        <span class="font-semibold text-gray-600">{{ filteredCount }}</span> 隻
      </span>
    </div>
  </div>
</template>
