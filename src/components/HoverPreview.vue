<!-- src/components/HoverPreview.vue -->
<script setup>
import { computed, ref, watch } from 'vue'

const tooltipStyle = ref({})

function onThumbEnter(event, animal) {
  hoveredThumb.value = animal.id
  const rect = event.currentTarget.getBoundingClientRect()
  const TOOLTIP_W = 180
  const cx = rect.left + rect.width / 2
  const left = Math.max(8, Math.min(cx - TOOLTIP_W / 2, window.innerWidth - TOOLTIP_W - 8))
  tooltipStyle.value = {
    position: 'fixed',
    left: `${left}px`,
    bottom: `${window.innerHeight - rect.top + 8}px`,
    width: `${TOOLTIP_W}px`,
    zIndex: 99999,
  }
}

const props = defineProps({
  location:     { type: Object, default: null },
  animals:      { type: Array,  default: () => [] },
  position:     { type: Object, default: null },   // { x, y } pixel coords in map container
  mapTopOffset: { type: Number, default: 0 },      // px offset from top (FilterBar height)
})

const emit = defineEmits(['mouseenter', 'mouseleave', 'select'])

const hoveredThumb = ref(null)
const loadedPhotos = ref(new Set())
const failedPhotos = ref(new Set())
const photoTimers = {}
const PHOTO_TIMEOUT = 60000 // ms

const locationAnimals = computed(() =>
  props.animals.filter(a => a.location_id === props.location?.id)
)

// Show all animals in grid
const visibleAnimals = computed(() => locationAnimals.value)

const PANEL_W = 420   // fixed width: 4 cols × 96px + padding
const PANEL_H = 440   // approx height for position calc (4 rows max)
const MARKER_R = 22   // marker radius px
const ARROW_H  = 9    // arrow height px
const MARGIN   = 8    // min distance from viewport edge

const panelStyle = computed(() => {
  if (!props.position) return {}

  const vw = window.innerWidth

  // Absolute Y of the marker center in the viewport
  const markerAbsY = props.position.y + props.mapTopOffset

  // Prefer above; flip below if not enough space
  const spaceAbove = markerAbsY - MARKER_R
  const showBelow  = spaceAbove < PANEL_H + ARROW_H + MARGIN

  const top = showBelow
    ? markerAbsY + MARKER_R + ARROW_H
    : markerAbsY - MARKER_R - ARROW_H - PANEL_H

  // Clamp horizontally so panel never goes off screen
  const pw = PANEL_W
  const rawLeft = props.position.x - pw / 2
  const left    = Math.max(MARGIN, Math.min(rawLeft, vw - pw - MARGIN))

  // Arrow x offset from panel center (compensate for horizontal clamping)
  const arrowOffset = props.position.x - (left + pw / 2)

  return { top: `${top}px`, left: `${left}px`, '--arrow-offset': `${arrowOffset}px`, '--show-below': showBelow ? '1' : '0' }
})

const sexLabel    = { M: '公', F: '母' }
const ageLabel    = { child: '幼年', adult: '成年', senior: '老年' }
const bodytypeLabel = { small: '小型', medium: '中型', large: '大型' }

const typeLabel = {
  shelter:    '公立收容所',
  vet_transit:'中途醫院',
  yiqi:       '益起認養',
  // bulletin:   '民眾送養',
}
const typeColor = {
  shelter:    '#1d4ed8',
  vet_transit:'#15803d',
  yiqi:       '#d97706',
  // bulletin:   '#c2410c',
}

function animalDisplayName(a) {
  if (a.name) return a.name
  return a.kind === 'cat' ? '貓咪' : a.kind === 'dog' ? '狗狗' : a.id
}

function indexOf(animal) {
  return locationAnimals.value.indexOf(animal)
}

function onPhotoLoad(id) {
  clearTimeout(photoTimers[id])
  delete photoTimers[id]
  loadedPhotos.value = new Set([...loadedPhotos.value, id])
}

function onPhotoError(id) {
  clearTimeout(photoTimers[id])
  delete photoTimers[id]
  failedPhotos.value = new Set([...failedPhotos.value, id])
}

function onPhotoMounted(id) {
  if (loadedPhotos.value.has(id) || failedPhotos.value.has(id)) return
  photoTimers[id] = setTimeout(() => onPhotoError(id), PHOTO_TIMEOUT)
}

watch(() => props.location?.id, () => {
  // clear all pending timers
  Object.keys(photoTimers).forEach(id => clearTimeout(photoTimers[id]))
  Object.keys(photoTimers).forEach(id => delete photoTimers[id])
  loadedPhotos.value = new Set()
  failedPhotos.value = new Set()
})

const allPhotosLoaded = computed(() => {
  const withPhoto = visibleAnimals.value.filter(a => a.photo_url)
  return withPhoto.length === 0 || withPhoto.every(a =>
    loadedPhotos.value.has(a.id) || failedPhotos.value.has(a.id)
  )
})

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
          <div class="flex items-center justify-between gap-2 mt-0.5">
            <div class="font-semibold text-gray-900 text-sm leading-tight truncate">{{ location.name }}</div>
            <div v-if="!allPhotosLoaded" class="flex items-center gap-1 flex-shrink-0">
              <svg class="w-3 h-3 text-gray-400 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
              </svg>
              <span class="text-xs text-gray-400">載入中</span>
            </div>
          </div>
        </div>

        <!-- Grid thumbnail area -->
        <div
          class="px-3 py-3 grid gap-2 overflow-y-auto"
          style="grid-template-columns:repeat(4,1fr);max-height:420px;"
        >
          <div
            v-for="animal in visibleAnimals"
            :key="animal.id"
            class="relative"
            @mouseenter="onThumbEnter($event, animal)"
            @mouseleave="hoveredThumb = null"
            @click.stop="emit('select', { location, animalIndex: indexOf(animal) })"
          >
            <div
              class="w-full aspect-square rounded-xl overflow-hidden border-2 border-white transition-all duration-150 cursor-pointer relative"
              :class="animal.photo_url && !loadedPhotos.has(animal.id) && !failedPhotos.has(animal.id) ? 'skeleton' : 'bg-gray-100'"
              :style="{
                boxShadow: hoveredThumb === animal.id ? '0 6px 16px rgba(0,0,0,0.22)' : '0 2px 6px rgba(0,0,0,0.12)',
                transform: hoveredThumb === animal.id ? 'scale(1.07)' : 'scale(1)',
              }"
            >
              <!-- emoji placeholder (always shown until photo loads, re-shown on failure) -->
              <div
                class="absolute inset-0 flex items-center justify-center text-3xl pointer-events-none"
                :class="loadedPhotos.has(animal.id) ? 'opacity-0' : 'opacity-100'"
              >
                {{ animal.kind === 'cat' ? '🐱' : '🐶' }}
              </div>
              <!-- real photo -->
              <img
                v-if="animal.photo_url"
                :src="animal.photo_url"
                :alt="animalDisplayName(animal)"
                class="absolute inset-0 w-full h-full object-cover object-center transition-opacity duration-300"
                :class="loadedPhotos.has(animal.id) ? 'opacity-100' : 'opacity-0'"
                draggable="false"
                @load="onPhotoLoad(animal.id)"
                @error="onPhotoError(animal.id)"
                @vue:mounted="onPhotoMounted(animal.id)"
              />
            </div>
          </div>
        </div>

        <!-- Footer hint -->
        <div class="px-4 pb-2.5 text-xs text-gray-400 text-center">
          點擊照片查看詳情
        </div>
      </div>
    </div>
  </Transition>

  <!-- Tooltip teleported to body to escape overflow:hidden -->
  <Teleport to="body">
    <Transition name="thumb-tip">
      <div
        v-if="hoveredThumb"
        :style="tooltipStyle"
        class="pointer-events-none"
      >
        <template v-for="animal in visibleAnimals" :key="animal.id">
          <div
            v-if="animal.id === hoveredThumb"
            class="bg-white text-gray-700 text-[11px] leading-snug rounded-lg px-2.5 py-2 shadow-lg border border-gray-200 flex flex-wrap gap-x-2 gap-y-0.5"
          >
            <span v-if="animal.sex">{{ sexLabel[animal.sex] ?? animal.sex }}</span>
            <span v-if="animal.age">{{ ageLabel[animal.age] ?? animal.age }}</span>
            <span v-if="animal.bodytype">{{ bodytypeLabel[animal.bodytype] ?? animal.bodytype }}</span>
            <span v-if="animal.colour">{{ animal.colour }}</span>
            <span v-if="animal.sterilized != null">{{ animal.sterilized ? '已結紮' : '未結紮' }}</span>
          </div>
        </template>
        <!-- Arrow -->
        <div class="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-white" />
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Hide scrollbar */
div[style*="scrollbar-width"]::-webkit-scrollbar { display: none; }

.skeleton {
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.thumb-tip-enter-active { transition: opacity 0.1s ease; }
.thumb-tip-leave-active { transition: opacity 0.1s ease; }
.thumb-tip-enter-from, .thumb-tip-leave-to { opacity: 0; }

.hover-popup-enter-active { transition: all 0.18s cubic-bezier(0.16,1,0.3,1); }
.hover-popup-leave-active { transition: all 0.14s ease-in; }
.hover-popup-enter-from   { opacity:0; transform:translateY(6px) scale(0.95); }
.hover-popup-leave-to     { opacity:0; transform:translateY(4px) scale(0.96); }
</style>
