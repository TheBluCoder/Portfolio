<template>
  <button
    type="button"
    class="relative block group-hover:rotate-z-0 group-focus:rotate-z-0 group-active:rotate-z-0 transition-all duration-400 md:rotate-z-90 group-hover:text-blue-200 group-focus:text-blue-200 group-active:text-blue-200 md:text-gray-700 hover:border hover:border-purple-800 md:p-3 p-2 rounded-md focus:border foucs:border-purple-800 active:border active:border-purple-800 cursor-pointer"
    :class="{ 'electric-border bg-black/70': hover }"
    @mouseenter="hover = true"
    @mouseleave="hover = false"
  >
    <slot />
  </button>
</template>

<script setup>
import { ref } from 'vue'

const hover = ref(false)
</script>

<style scoped>
.electric-border::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: inherit;
  padding: 2px;
  background: linear-gradient(
    var(--angle, 0deg),
    rgba(149, 0, 255, 0.1),
    rgba(149, 0, 255, 0.8),
    rgba(149, 0, 255, 1),
    rgba(149, 0, 255, 0.8),
    rgba(149, 0, 255, 0.1)
  );
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  animation: rotate 2s linear infinite;
}

@property --angle {
  syntax: '<angle>';
  initial-value: 0deg;
  inherits: false;
}

@keyframes rotate {
  to {
    --angle: 360deg;
  }
}
</style>
