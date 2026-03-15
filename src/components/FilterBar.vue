<!-- src/components/FilterBar.vue -->
<script setup>
import { ref, computed } from 'vue'
import TaiwanCityPicker from './TaiwanCityPicker.vue'

const props = defineProps({
  currentCity:      { type: String,  default: '臺中市' },
  filterKind:       { type: String,  default: 'all' },
  filterSource:     { type: String,  default: 'all' },
  filterSex:        { type: String,  default: 'all' },
  filterColour:     { type: String,  default: 'all' },
  availableSources: { type: Array,   default: () => [] },
  availableColours: { type: Array,   default: () => [] },
  filteredCount:    { type: Number,  default: 0 },
})

const emit = defineEmits([
  'update:currentCity',
  'update:filterKind',
  'update:filterSource',
  'update:filterSex',
  'update:filterColour',
])

const panelOpen = ref(false)

const kindOptions = [
  { value: 'all', label: '全部', emoji: null },
  { value: 'cat', label: '貓',   emoji: '🐱' },
  { value: 'dog', label: '狗',   emoji: '🐶' },
]

const sexOptions = [
  { value: 'all', label: '全部' },
  { value: 'M',   label: '♂ 公' },
  { value: 'F',   label: '♀ 母' },
]

const SOURCE_LABELS = {
  all:         '全部',
  shelter:     '🏛️ 收容所',
  vet_transit: '🏥 中途醫院',
  yiqi:        '🟣 益起認養吧',
}

const sourceOptions = computed(() => {
  const opts = [{ value: 'all', label: '全部' }]
  for (const src of props.availableSources) {
    if (SOURCE_LABELS[src]) opts.push({ value: src, label: SOURCE_LABELS[src] })
  }
  return opts
})

// Count active secondary filters
const activeSecondaryCount = computed(() => {
  let n = 0
  if (props.filterSource !== 'all') n++
  if (props.filterSex !== 'all') n++
  if (props.filterColour !== 'all') n++
  return n
})
</script>

<template>
  <div
    class="fixed top-0 left-0 right-0 z-[1000] bg-white/92 backdrop-blur-md border-b border-gray-100/80"
    style="box-shadow: 0 1px 12px rgba(0,0,0,0.08);"
  >
    <!-- Main row -->
    <div class="flex items-center gap-2 px-3 sm:px-4 py-2">
      <!-- Logo -->
      <span class="font-bold text-gray-800 text-sm whitespace-nowrap leading-none select-none">
        🗺&nbsp;<span class="hidden sm:inline">領養地圖</span>
      </span>

      <!-- City selector -->
      <TaiwanCityPicker
        :current-city="currentCity"
        @update:current-city="emit('update:currentCity', $event)"
      />

      <!-- Kind pills -->
      <div class="flex gap-1">
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

      <!-- More filters button -->
      <button
        :class="[
          'ml-auto flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all',
          panelOpen
            ? 'bg-blue-50 text-blue-700 border border-blue-200'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        ]"
        @click="panelOpen = !panelOpen"
      >
        <span>⚙️ 更多篩選</span>
        <span
          v-if="activeSecondaryCount > 0"
          class="bg-amber-400 text-gray-900 rounded-full px-1.5 py-0 text-[10px] font-bold leading-4"
        >{{ activeSecondaryCount }}</span>
      </button>

      <!-- Count badge -->
      <span class="text-xs text-gray-400 whitespace-nowrap tabular-nums">
        <span class="font-semibold text-gray-600">{{ filteredCount }}</span> 隻
      </span>
    </div>

    <!-- Expandable secondary panel -->
    <Transition name="panel">
      <div
        v-if="panelOpen"
        class="flex flex-wrap items-center gap-x-4 gap-y-2 px-3 sm:px-4 py-2 border-t border-gray-100 bg-gray-50/80"
      >
        <!-- Source filter -->
        <div v-if="sourceOptions.length > 1" class="flex items-center gap-1.5">
          <span class="text-[11px] text-gray-400 font-medium">來源</span>
          <div class="flex gap-1">
            <button
              v-for="opt in sourceOptions"
              :key="opt.value"
              :class="[
                'px-2 py-0.5 rounded-full text-[11px] font-medium transition-all',
                filterSource === opt.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-100',
              ]"
              @click="emit('update:filterSource', opt.value)"
            >{{ opt.label }}</button>
          </div>
        </div>

        <!-- Sex filter -->
        <div class="flex items-center gap-1.5">
          <span class="text-[11px] text-gray-400 font-medium">性別</span>
          <div class="flex gap-1">
            <button
              v-for="opt in sexOptions"
              :key="opt.value"
              :class="[
                'px-2 py-0.5 rounded-full text-[11px] font-medium transition-all',
                filterSex === opt.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-100',
              ]"
              @click="emit('update:filterSex', opt.value)"
            >{{ opt.label }}</button>
          </div>
        </div>

        <!-- Colour filter -->
        <div v-if="availableColours.length > 0" class="flex items-center gap-1.5">
          <span class="text-[11px] text-gray-400 font-medium">毛色</span>
          <select
            :value="filterColour"
            class="text-[11px] border border-gray-200 rounded-lg px-2 py-0.5 bg-white text-gray-700
                   focus:outline-none focus:ring-1 focus:ring-blue-400 cursor-pointer"
            @change="emit('update:filterColour', $event.target.value)"
          >
            <option value="all">全部</option>
            <option v-for="colour in availableColours" :key="colour" :value="colour">
              {{ colour }}
            </option>
          </select>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.panel-enter-active { transition: all 0.2s ease-out; }
.panel-leave-active { transition: all 0.15s ease-in; }
.panel-enter-from   { opacity: 0; transform: translateY(-4px); }
.panel-leave-to     { opacity: 0; transform: translateY(-4px); }
</style>
