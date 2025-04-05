<script setup>
import { BrainIcon } from 'lucide-vue-next'
import { MenuIcon, XIcon } from 'lucide-vue-next'
import Navbar from './Navbar.vue'
import { ref } from 'vue'
const isOpen = ref(true)
</script>

<template>
  <div class="h-full flex">
    <div @click="isOpen = !isOpen" class="fixed top-6 left-6 z-50">
      <Component
        :is="isOpen ? XIcon : MenuIcon"
        class="h-10 w-10 bg-gradient-to-br from-purple-900 to-black"
      />
    </div>

    <Navbar :isOpen="isOpen" />
    <div class="bg-gradient-to-r from-blue-200/20 to-black w-15 bg-blend-overlay"></div>
    <div class="flex-grow"><slot /></div>
  </div>
  <button
    @click="openGlobalChat"
    class="fixed bottom-6 left-8 md:left-22 w-14 h-14 bg-gray-900 rounded-full flex items-center justify-center shadow-lg bg-gradient-to-r to-white/50 transition-colors z-50 ai-chat-button border border-purple-900/30"
  >
    <BrainIcon class="w-6 h-6" />
  </button>
</template>

<style scoped>
@font-face {
  font-family: Oswald;
  font-style: normal;
  font-weight: 200 700;
  font-display: swap;
  src: url('/fonts/Oswald.woff2') format('woff2');
}
</style>
