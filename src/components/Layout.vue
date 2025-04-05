<script setup>
import { MenuIcon, XIcon } from 'lucide-vue-next'
import Navbar from './Navbar.vue'
import { ref } from 'vue'
import SocialMenu from '@/components/SocialMenu.vue'
const isOpen = ref(false)

const openGlobalChat = () => {
  console.log('openGlobalChat')
}
</script>

<template>
  <div class="h-full flex">
    <div @click="isOpen = !isOpen" class="fixed top-6 left-6 z-50">
      <Component
        :is="isOpen ? XIcon : MenuIcon"
        class="h-10 w-10 bg-gradient-to-br from-purple-900 to-black"
      />
    </div>

    <SocialMenu @open-chat="openGlobalChat" />
    <Navbar :isOpen="isOpen" />
    <div class="bg-gradient-to-r from-blue-200/20 to-black md:15 bg-blend-overlay"></div>
    <div class="flex-grow"><slot /></div>
  </div>
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
