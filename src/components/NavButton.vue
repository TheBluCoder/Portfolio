<template>
  <button
    type="button"
    class="relative block group-hover:rotate-z-0 group-focus:rotate-z-0 group-active:rotate-z-0 transition-all duration-400 md:rotate-z-90 group-hover:text-[var(--theme-accent-soft)] group-focus:text-[var(--theme-accent-soft)] group-active:text-[var(--theme-accent-soft)] md:text-[var(--theme-text-dim)] hover:border hover:border-[var(--theme-accent)] md:p-3 p-2 rounded-md focus:border focus:border-[var(--theme-accent)] active:border active:border-[var(--theme-accent)] cursor-pointer"
    :class="{ 'electric-border bg-[rgb(var(--theme-black-rgb)/0.7)]': hover }"
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
    rgb(var(--theme-accent-rgb) / 0.1),
    rgb(var(--theme-accent-rgb) / 0.8),
    rgb(var(--theme-accent-rgb) / 1),
    rgb(var(--theme-accent-rgb) / 0.8),
    rgb(var(--theme-accent-rgb) / 0.1)
  );
  -webkit-mask:
    linear-gradient(var(--theme-white) 0 0) content-box,
    linear-gradient(var(--theme-white) 0 0);
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
