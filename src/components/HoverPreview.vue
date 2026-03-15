<!-- src/components/HoverPreview.vue -->
<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  location:     { type: Object, default: null },
  animals:      { type: Array,  default: () => [] },
  position:     { type: Object, default: null },   // { x, y } pixel coords in map container
  mapTopOffset: { type: Number, default: 0 },      // px offset from top (FilterBar height)
})

const emit = defineEmits(['mouseenter', 'mouseleave', 'select'])

const hoveredThumb = ref(null)

const locationAnimals = computed(() =>
  props.animals.filter(a => a.location_id === props.location?.id)
)

// Show all animals in scrollable strip
const visibleAnimals = computed(() => locationAnimals.value)

// Track scroll position to compute remaining animals dynamically
const scrollLeft = ref(0)
const ITEM_W = 90 // w-20 (80px) + gap-2.5 (10px)
const VISIBLE_COUNT = 4

const firstHiddenIndex = computed(() => {
  const firstVisible = Math.floor(scrollLeft.value / ITEM_W)
  return firstVisible + VISIBLE_COUNT
})

const extraCount = computed(() =>
  Math.max(0, locationAnimals.value.length - firstHiddenIndex.value)
)

function onScroll(e) {
  scrollLeft.value = e.target.scrollLeft
}

function scrollToMore() {
  if (!scrollEl.value) return
  scrollEl.value.scrollTo({ left: firstHiddenIndex.value * ITEM_W, behavior: 'smooth' })
}

const PANEL_W = 420
const PANEL_H = 220   // approx height for position calc
const MARKER_R = 22   // marker radius px
const ARROW_H  = 9    // arrow height px
const MARGIN   = 8    // min distance from viewport edge

const panelStyle = computed(() => {
  if (!props.position) return {}

  const vw = window.innerWidth
  const vh = window.innerHeight

  // Absolute Y of the marker center in the viewport
  const markerAbsY = props.position.y + props.mapTopOffset

  // Prefer above; flip below if not enough space
  const spaceAbove = markerAbsY - MARKER_R
  const showBelow  = spaceAbove < PANEL_H + ARROW_H + MARGIN

  const top = showBelow
    ? markerAbsY + MARKER_R + ARROW_H
    : markerAbsY - MARKER_R - ARROW_H - PANEL_H

  // Clamp horizontally so panel never goes off screen
  const rawLeft = props.position.x - PANEL_W / 2
  const left    = Math.max(MARGIN, Math.min(rawLeft, vw - PANEL_W - MARGIN))

  // Arrow x offset from panel center (compensate for horizontal clamping)
  const arrowOffset = props.position.x - (left + PANEL_W / 2)

  return { top: `${top}px`, left: `${left}px`, '--arrow-offset': `${arrowOffset}px`, '--show-below': showBelow ? '1' : '0' }
})

const typeLabel = {
  shelter:    '公立收容所',
  vet_transit:'中途醫院',
  yiqi:       '益起認養',
  // bulletin:   '民眾送養',
}
const typeColor = {
  shelter:    '#1d4ed8',
  vet_transit:'#15803d',
  yiqi:       '#6d28d9',
  // bulletin:   '#c2410c',
}

function animalDisplayName(a) {
  if (a.name) return a.name
  return a.kind === 'cat' ? '貓咪' : a.kind === 'dog' ? '狗狗' : a.id
}

function indexOf(animal) {
  return locationAnimals.value.indexOf(animal)
}

// ── drag-to-scroll ──────────────────────────────────────────────────────────
const scrollEl = ref(null)
const drag = ref({ active: false, captured: false, startX: 0, scrollLeft: 0 })
const DRAG_THRESHOLD = 6 // px — below this is treated as a click, not a drag

function onPointerDown(e) {
  drag.value = { active: true, captured: false, startX: e.clientX, scrollLeft: scrollEl.value.scrollLeft }
}
function onPointerMove(e) {
  if (!drag.value.active) return
  const dx = e.clientX - drag.value.startX
  // Only capture pointer (blocking clicks) once the user has clearly started dragging
  if (!drag.value.captured && Math.abs(dx) > DRAG_THRESHOLD) {
    drag.value.captured = true
    scrollEl.value.setPointerCapture(e.pointerId)
  }
  if (drag.value.captured) {
    scrollEl.value.scrollLeft = drag.value.scrollLeft - dx
  }
}
function onPointerUp() {
  drag.value.active = false
  drag.value.captured = false
}
</script>

<template>
  <Transition name="hover-popup">
    <div
      v-if="location && position"
      class="absolute z-[999] pointer-events-auto select-none"
      :style="panelStyle"
      @mouseenter="emit('mouseenter')"
      @mouseleave="emit('mouseleave')"
    >
      <!-- Arrow: points down when panel is above marker, up when below -->
      <div
        class="absolute w-0 h-0"
        :style="{
          left: `calc(50% + var(--arrow-offset))`,
          transform: 'translateX(-50%)',
          ...(panelStyle['--show-below'] === '1'
            ? { top: '-9px', borderLeft:'8px solid transparent', borderRight:'8px solid transparent', borderBottom:'9px solid white', filter:'drop-shadow(0 -2px 2px rgba(0,0,0,0.08))' }
            : { bottom: '-9px', borderLeft:'8px solid transparent', borderRight:'8px solid transparent', borderTop:'9px solid white', filter:'drop-shadow(0 2px 2px rgba(0,0,0,0.10))' }
          )
        }"
      />

      <div
        class="rounded-2xl overflow-hidden"
        :style="`width:${PANEL_W}px;background:rgba(255,255,255,0.97);backdrop-filter:blur(14px);box-shadow:0 10px 36px rgba(0,0,0,0.16),0 3px 10px rgba(0,0,0,0.08);`"
      >
        <!-- Header -->
        <div class="px-4 pt-3 pb-2 border-b border-gray-100">
          <div class="flex items-center gap-2">
            <div class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ background: typeColor[location.type] || '#6b7280' }" />
            <span class="text-xs text-gray-500">{{ typeLabel[location.type] || location.type }}</span>
          </div>
          <div class="font-semibold text-gray-900 text-sm leading-tight mt-0.5 truncate">{{ location.name }}</div>
        </div>

        <!-- Scrollable thumbnail strip + +N overlay -->
        <div class="relative">
          <div
            ref="scrollEl"
            class="pl-3 pr-3 py-3 flex items-center gap-2.5 overflow-x-auto"
            :class="drag.active ? 'cursor-grabbing' : 'cursor-grab'"
            :style="`scrollbar-width:none;-ms-overflow-style:none;scroll-snap-type:x mandatory;${extraCount > 0 ? 'padding-right: 56px;' : ''}`"
            @scroll="onScroll"
            @wheel.prevent="e => { scrollEl.scrollLeft += e.deltaY !== 0 ? e.deltaY : e.deltaX }"
            @pointerdown="onPointerDown"
            @pointermove="onPointerMove"
            @pointerup="onPointerUp"
            @pointercancel="onPointerUp"
          >
            <div
              v-for="animal in visibleAnimals"
              :key="animal.id"
              class="relative flex-shrink-0"
              style="scroll-snap-align:start;"
              @mouseenter="hoveredThumb = animal.id"
              @mouseleave="hoveredThumb = null"
              @click.stop="emit('select', { location, animalIndex: indexOf(animal) })"
            >
              <div
                class="w-20 h-20 rounded-xl overflow-hidden bg-gray-100 border-2 border-white transition-all duration-150 cursor-pointer"
                :style="{
                  boxShadow: hoveredThumb === animal.id ? '0 6px 16px rgba(0,0,0,0.22)' : '0 2px 6px rgba(0,0,0,0.12)',
                  transform: hoveredThumb === animal.id ? 'scale(1.07)' : 'scale(1)',
                }"
              >
                <img
                  v-if="animal.photo_url"
                  :src="animal.photo_url"
                  :alt="animalDisplayName(animal)"
                  class="w-full h-full object-cover object-center"
                  draggable="false"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-3xl pointer-events-none">
                  {{ animal.kind === 'cat' ? '🐱' : '🐶' }}
                </div>
              </div>

              <!-- Name tooltip -->
              <Transition name="thumb-tip">
                <div
                  v-if="hoveredThumb === animal.id"
                  class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 whitespace-nowrap bg-gray-900 text-white text-xs px-2.5 py-1 rounded-lg pointer-events-none z-10"
                  style="box-shadow:0 2px 8px rgba(0,0,0,0.2);"
                >
                  {{ animalDisplayName(animal) }}
                  <div class="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0" style="border-left:5px solid transparent;border-right:5px solid transparent;border-top:5px solid #111827;" />
                </div>
              </Transition>
            </div>
          </div>

          <!-- +N fade overlay on right edge — only when there are more than 4 animals and not scrolled to end -->
          <Transition name="fade-overlay">
            <div
              v-if="extraCount > 0"
              class="absolute right-0 top-0 bottom-0 flex items-center pr-2 cursor-pointer"
              style="background:linear-gradient(to right, transparent, rgba(255,255,255,0.95) 40%);padding-left:32px;"
              title="捲動查看更多"
              @click.stop="scrollToMore"
            >
              <div class="flex flex-col items-center justify-center w-10 h-10 rounded-xl bg-white border border-gray-200 shadow-sm hover:bg-gray-50 transition-colors">
                <span class="text-xs font-bold text-gray-600">+{{ extraCount }}</span>
                <span class="text-gray-400" style="font-size:10px;">更多</span>
              </div>
            </div>
          </Transition>
        </div>

        <!-- Footer hint -->
        <div class="px-4 pb-2.5 text-xs text-gray-400 text-center">
          拖曳左右滑動・點擊照片查看詳情
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* Hide scrollbar */
div[style*="scrollbar-width"]::-webkit-scrollbar { display: none; }

.hover-popup-enter-active { transition: all 0.18s cubic-bezier(0.16,1,0.3,1); }
.hover-popup-leave-active { transition: all 0.14s ease-in; }
.hover-popup-enter-from   { opacity:0; transform:translateY(6px) scale(0.95); }
.hover-popup-leave-to     { opacity:0; transform:translateY(4px) scale(0.96); }

.thumb-tip-enter-active, .thumb-tip-leave-active { transition: all 0.12s ease; }
.thumb-tip-enter-from, .thumb-tip-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(3px);
}

.fade-overlay-enter-active, .fade-overlay-leave-active { transition: opacity 0.2s ease; }
.fade-overlay-enter-from, .fade-overlay-leave-to { opacity: 0; }
</style>
