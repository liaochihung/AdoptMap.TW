<!-- src/components/AnimalCard.vue -->
<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  location: { type: Object, default: null },
  animals:  { type: Array,  default: () => [] },
  initialIndex: { type: Number, default: 0 },
  mobile: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

const currentIndex = ref(0)

const locationAnimals = computed(() =>
  props.animals.filter(a => a.location_id === props.location?.id)
)
const currentAnimal = computed(() => locationAnimals.value[currentIndex.value] || null)
const total = computed(() => locationAnimals.value.length)

function prev() { if (currentIndex.value > 0) currentIndex.value-- }
function next() { if (currentIndex.value < total.value - 1) currentIndex.value++ }

watch(
  [() => props.location?.id, () => props.initialIndex],
  () => { currentIndex.value = props.initialIndex ?? 0 },
)

// ── Touch swipe (mobile) ────────────────────────────────────────────────────
const touchStartX = ref(null)
function onTouchStart(e) { touchStartX.value = e.touches[0].clientX }
function onTouchEnd(e) {
  if (touchStartX.value === null) return
  const dx = e.changedTouches[0].clientX - touchStartX.value
  if (dx > 40) prev()
  else if (dx < -40) next()
  touchStartX.value = null
}

// ── Mouse drag to navigate (desktop) ───────────────────────────────────────
const dragStart = ref(null)
const isDragging = ref(false)
const DRAG_THRESHOLD = 8

function onMouseDown(e) {
  dragStart.value = e.clientX
  isDragging.value = false
}
function onMouseMove(e) {
  if (dragStart.value === null) return
  if (Math.abs(e.clientX - dragStart.value) > DRAG_THRESHOLD) isDragging.value = true
}
function onMouseUp(e) {
  if (dragStart.value === null) return
  const dx = e.clientX - dragStart.value
  if (isDragging.value) {
    if (dx > 40) prev()
    else if (dx < -40) next()
  }
  dragStart.value = null
  isDragging.value = false
}

// ── Mouse wheel to navigate ─────────────────────────────────────────────────
let wheelDebounce = null
function onWheel(e) {
  e.preventDefault()
  clearTimeout(wheelDebounce)
  wheelDebounce = setTimeout(() => {
    if (e.deltaX > 30 || e.deltaY > 30) next()
    else if (e.deltaX < -30 || e.deltaY < -30) prev()
  }, 30)
}

// ── Remark expand/collapse ──────────────────────────────────────────────────
const remarkExpanded = ref(false)
watch(() => currentAnimal.value?.id, () => { remarkExpanded.value = false })

const REMARK_LIMIT = 60
const remarkNeedsExpand = computed(() =>
  (currentAnimal.value?.remark?.length ?? 0) > REMARK_LIMIT
)
const displayRemark = computed(() => {
  const r = currentAnimal.value?.remark
  if (!r) return ''
  if (remarkExpanded.value || !remarkNeedsExpand.value) return r
  return r.slice(0, REMARK_LIMIT) + '…'
})

const sexLabel    = { M: '公', F: '母', N: '未知' }
const sexIcon     = { M: '♂', F: '♀', N: '?' }
const ageLabel    = { adult: '成年', child: '幼年' }
const bodytypeLabel = { small: '小型', medium: '中型', large: '大型' }

const typeLabel = {
  shelter:    '公立收容所',
  vet_transit:'中途動物醫院',
  yiqi:       '益起認養吧',
}
const typeBadge = {
  shelter:    'bg-blue-100 text-blue-700 border-blue-200',
  vet_transit:'bg-green-100 text-green-700 border-green-200',
  yiqi:       'bg-purple-100 text-purple-700 border-purple-200',
}
const typeAccent = {
  shelter:    '#1d4ed8',
  vet_transit:'#15803d',
  yiqi:       '#6d28d9',
}

const kindEmoji = computed(() => currentAnimal.value?.kind === 'cat' ? '🐱' : '🐶')
const kindLabel = computed(() => currentAnimal.value?.kind === 'cat' ? '貓' : '狗')

const displayName = computed(() => {
  const a = currentAnimal.value
  if (!a) return ''
  return a.name || (a.kind === 'cat' ? '貓咪' : a.kind === 'dog' ? '狗狗' : a.id)
})

// ── Photo state ─────────────────────────────────────────────────────────────
const imgError = ref(false)
const imgLoaded = ref(false)
watch(() => currentAnimal.value?.id, () => {
  imgError.value = false
  imgLoaded.value = false
})

// Compute dominant blur color from type accent for the photo background
const photoBg = computed(() => {
  const c = typeAccent[props.location?.type] || '#9ca3af'
  return `color-mix(in srgb, ${c} 15%, #f3f4f6)`
})
</script>

<template>
  <Transition :name="mobile ? 'none' : 'card-slide'">
  <div
    v-if="location"
    :class="[
      'overflow-hidden select-none',
      mobile
        ? 'w-full rounded-none'
        : 'absolute bottom-6 right-4 z-[1000] w-80 rounded-2xl',
    ]"
    :style="mobile ? '' : 'background:rgba(255,255,255,0.98);backdrop-filter:blur(20px);box-shadow:0 20px 60px rgba(0,0,0,0.22),0 4px 16px rgba(0,0,0,0.1);'"
  >
    <!-- Accent bar -->
    <div class="h-1 w-full" :style="{ background: typeAccent[location.type] || '#6b7280' }" />

    <!-- ── Photo section ──────────────────────────────────────────────────── -->
    <div
      class="relative w-full overflow-hidden"
      :class="isDragging ? 'cursor-grabbing' : (total > 1 ? 'cursor-grab' : '')"
      style="height: 220px;"
      :style="{ background: photoBg }"
      @touchstart.passive="onTouchStart"
      @touchend.passive="onTouchEnd"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="dragStart = null"
      @wheel.prevent="onWheel"
    >
      <template v-if="currentAnimal">
        <!-- Blurred bg layer (fills space around letterboxed image) -->
        <img
          v-if="currentAnimal.photo_url && !imgError"
          :src="currentAnimal.photo_url"
          aria-hidden="true"
          class="absolute inset-0 w-full h-full object-cover scale-110 blur-xl opacity-50 pointer-events-none"
          draggable="false"
        />
        <!-- Main image: contain = no crop, full animal visible -->
        <img
          v-if="currentAnimal.photo_url && !imgError"
          :src="currentAnimal.photo_url"
          :alt="displayName"
          class="relative w-full h-full object-contain pointer-events-none"
          draggable="false"
          @error="imgError = true"
          @load="imgLoaded = true"
        />
        <div v-else class="w-full h-full flex flex-col items-center justify-center gap-1">
          <span class="text-6xl">{{ kindEmoji }}</span>
          <span class="text-xs text-gray-400">尚無照片</span>
        </div>
      </template>

      <!-- Top gradient overlay -->
      <div class="absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-black/35 to-transparent pointer-events-none" />

      <!-- Close button (desktop) -->
      <button
        v-if="!mobile"
        class="absolute top-2.5 right-2.5 w-7 h-7 rounded-full bg-black/35 hover:bg-black/55 flex items-center justify-center text-white transition-colors backdrop-blur-sm"
        @click.stop="emit('close')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>

      <!-- Kind badge (top left) -->
      <div class="absolute top-2.5 left-2.5 bg-black/35 backdrop-blur-sm rounded-full px-2.5 py-0.5 text-white text-xs font-medium pointer-events-none">
        {{ kindEmoji }} {{ kindLabel }}
      </div>

      <!-- Prev / Next arrows + dot indicators -->
      <template v-if="total > 1">
        <button
          v-if="currentIndex > 0"
          class="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/30 hover:bg-black/50 backdrop-blur-sm flex items-center justify-center text-white transition-all"
          @click.stop="prev"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/>
          </svg>
        </button>
        <button
          v-if="currentIndex < total - 1"
          class="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/30 hover:bg-black/50 backdrop-blur-sm flex items-center justify-center text-white transition-all"
          @click.stop="next"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
          </svg>
        </button>
        <!-- Dots -->
        <div class="absolute bottom-2 left-1/2 -translate-x-1/2 flex items-center gap-1 pointer-events-none">
          <div
            v-for="i in Math.min(total, 7)"
            :key="i"
            class="rounded-full transition-all duration-200"
            :style="{
              width: (i-1) === currentIndex ? '18px' : '5px',
              height: '5px',
              background: (i-1) === currentIndex ? 'white' : 'rgba(255,255,255,0.5)',
            }"
          />
          <span v-if="total > 7" class="text-white/70 text-xs ml-1">+{{ total - 7 }}</span>
        </div>
      </template>

      <!-- Drag hint (only when multiple animals, fades out after first drag) -->
      <div
        v-if="total > 1 && !isDragging"
        class="absolute bottom-2 right-3 text-white/50 text-xs pointer-events-none"
        style="font-size:10px;"
      >
        ← 拖曳/滾輪 →
      </div>
    </div>

    <!-- ── Info section ───────────────────────────────────────────────────── -->
    <div v-if="currentAnimal" class="px-4 pt-3 pb-3">
      <!-- Name + counter -->
      <div class="flex items-start justify-between gap-2 mb-2.5">
        <div class="min-w-0">
          <h3 class="font-bold text-gray-900 text-base leading-tight">{{ displayName }}</h3>
          <div class="text-xs text-gray-400 mt-0.5 truncate">{{ location.name }}</div>
        </div>
        <span v-if="total > 1" class="flex-shrink-0 text-xs text-gray-400 bg-gray-100 rounded-full px-2 py-0.5 mt-0.5 tabular-nums">
          {{ currentIndex + 1 }}&thinsp;/&thinsp;{{ total }}
        </span>
      </div>

      <!-- Tags -->
      <div class="flex flex-wrap gap-1.5 mb-2.5">
        <span class="inline-flex items-center gap-0.5 text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
          {{ sexIcon[currentAnimal.sex] }} {{ sexLabel[currentAnimal.sex] || currentAnimal.sex }}
        </span>
        <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
          {{ ageLabel[currentAnimal.age] || currentAnimal.age }}
        </span>
        <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
          {{ bodytypeLabel[currentAnimal.bodytype] || currentAnimal.bodytype }}
        </span>
        <span v-if="currentAnimal.colour" class="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
          {{ currentAnimal.colour }}
        </span>
        <span v-if="currentAnimal.sterilized === true" class="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
          ✓ 已絕育
        </span>
        <span v-if="currentAnimal.vaccinated === true" class="text-xs font-medium px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
          💉 已打疫苗
        </span>
      </div>

      <!-- Location type + address -->
      <div class="flex items-center gap-1.5 mb-2.5">
        <span :class="['text-xs px-2 py-0.5 rounded-full font-medium border flex-shrink-0', typeBadge[location.type] || 'bg-gray-100 text-gray-600 border-gray-200']">
          {{ typeLabel[location.type] || location.type }}
        </span>
        <span v-if="location.address" class="text-xs text-gray-400 truncate">{{ location.address }}</span>
      </div>

      <!-- Remark: expandable -->
      <div v-if="currentAnimal.remark" class="mb-2.5 bg-gray-50 rounded-lg px-2.5 py-2">
        <p class="text-xs text-gray-500 leading-relaxed">{{ displayRemark }}<button
          v-if="remarkNeedsExpand"
          class="ml-1 text-blue-500 hover:text-blue-700 font-medium transition-colors"
          @click.stop="remarkExpanded = !remarkExpanded"
        >{{ remarkExpanded ? '收起' : '展開' }}</button></p>
      </div>

      <!-- Phone + source link -->
      <div class="flex items-center justify-between">
        <a
          v-if="currentAnimal.contact_phone || location.phone"
          :href="`tel:${currentAnimal.contact_phone || location.phone}`"
          class="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-blue-600 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
          </svg>
          {{ currentAnimal.contact_phone || location.phone }}
        </a>
        <a
          v-if="currentAnimal.source_url"
          :href="currentAnimal.source_url"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium ml-auto transition-colors"
        >
          查看詳情
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
          </svg>
        </a>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="px-4 py-8 text-center">
      <div class="text-3xl mb-2">🔍</div>
      <div class="text-sm text-gray-400">此地點目前無符合條件的動物</div>
    </div>
  </div>
  </Transition>
</template>

<style scoped>
.card-slide-enter-active {
  transition: all 0.26s cubic-bezier(0.16, 1, 0.3, 1);
}
.card-slide-leave-active {
  transition: all 0.18s ease-in;
}
.card-slide-enter-from {
  opacity: 0;
  transform: translateX(20px) scale(0.96);
}
.card-slide-leave-to {
  opacity: 0;
  transform: translateX(12px) scale(0.97);
}
</style>
