<!-- src/components/LegendPanel.vue -->
<script setup>
import { ref } from 'vue'

const collapsed = ref(false)

const items = [
  { color: '#1d4ed8', label: '公立收容所' },
  { color: '#15803d', label: '中途動物醫院' },
  { color: '#d97706', label: '益起認養吧' },
  // { color: '#c2410c', label: '民眾送養' },
]
</script>

<template>
  <div class="absolute top-14 right-4 z-[1000]">
    <div
      class="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg overflow-hidden"
      style="box-shadow: 0 4px 16px rgba(0,0,0,0.12);"
    >
      <!-- Header -->
      <button
        class="flex items-center justify-between w-full px-3 py-2 hover:bg-gray-50 transition-colors"
        @click="collapsed = !collapsed"
      >
        <span class="text-xs font-semibold text-gray-600 tracking-wide">地圖圖例</span>
        <span
          class="text-gray-400 text-xs ml-3 transition-transform duration-200"
          :style="{ transform: collapsed ? 'rotate(-90deg)' : 'rotate(0deg)' }"
        >▾</span>
      </button>

      <!-- Legend items -->
      <Transition name="legend-collapse">
        <div v-if="!collapsed" class="px-3 pb-2.5 space-y-1.5">
          <div
            v-for="item in items"
            :key="item.label"
            class="flex items-center gap-2"
          >
            <div
              class="w-3.5 h-3.5 rounded-full flex-shrink-0 border-2 border-white"
              :style="{ background: item.color, boxShadow: `0 1px 3px ${item.color}66` }"
            />
            <span class="text-xs text-gray-600 whitespace-nowrap">{{ item.label }}</span>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.legend-collapse-enter-active,
.legend-collapse-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.legend-collapse-enter-from,
.legend-collapse-leave-to {
  opacity: 0;
  max-height: 0;
}
.legend-collapse-enter-to,
.legend-collapse-leave-from {
  opacity: 1;
  max-height: 120px;
}
</style>
