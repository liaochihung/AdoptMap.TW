<!-- src/components/ToastNotification.vue -->
<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  message: { type: String, default: '' },
  duration: { type: Number, default: 3500 },
})

const visible = ref(false)
let timer = null

watch(() => props.message, (msg) => {
  if (!msg) return
  visible.value = true
  clearTimeout(timer)
  timer = setTimeout(() => { visible.value = false }, props.duration)
})
</script>

<template>
  <Transition name="toast">
    <div
      v-if="visible"
      class="fixed top-14 left-1/2 -translate-x-1/2 z-[2000] flex items-center gap-2
             bg-amber-400 text-gray-900 text-sm font-medium px-4 py-2.5 rounded-xl shadow-lg
             whitespace-nowrap pointer-events-none"
    >
      <span>⚠️</span>
      <span>{{ message }}</span>
    </div>
  </Transition>
</template>

<style scoped>
.toast-enter-active { transition: all 0.25s ease-out; }
.toast-leave-active { transition: all 0.3s ease-in; }
.toast-enter-from  { opacity: 0; transform: translate(-50%, -8px); }
.toast-leave-to    { opacity: 0; transform: translate(-50%, -8px); }
</style>
