<script setup>
import { MenuIcon, XIcon } from 'lucide-vue-next'
import Navbar from './Navbar.vue'
import { ref, provide } from 'vue'
import SocialMenu from '@/components/SocialMenu.vue'
import ChatBox from '@/components/ChatBox.vue'

const isOpen = ref(false)
const isChatOpen = ref(false)
const chatProjectContext = ref(null)

const openGlobalChat = () => {
  chatProjectContext.value = null
  isChatOpen.value = true
}

const closeChat = () => {
  isChatOpen.value = false
  chatProjectContext.value = null
}

provide('openProjectChat', (project) => {
  console.log('Opening project chat:', project)
  chatProjectContext.value = project
  isChatOpen.value = true
})
</script>

<template>
  <div class="h-screen flex">
    <div @click="isOpen = !isOpen" class="fixed top-6 left-6 z-50">
      <Component
        :is="isOpen ? XIcon : MenuIcon"
        class="h-10 w-10 bg-gradient-to-br from-purple-900 to-black"
      />
    </div>

    <SocialMenu @open-chat="openGlobalChat" />
    <Navbar :isOpen="isOpen" />
    <div class="bg-gradient-to-r from-blue-200/20 to-black md:15 bg-blend-overlay"></div>
    <div class="flex-grow">
      <slot />
    </div>
    <div id="project-btn" class="h-20 fixed bottom-40 bg-transparent w-full"></div>

    <!-- Chat overlay for mobile -->
    <div
      v-if="isChatOpen"
      class="fixed inset-0 bg-black/20 backdrop-blur-sm md:hidden"
      @click="closeChat"
    ></div>

    <!-- Chat component -->
    <ChatBox :is-open="isChatOpen" :project-context="chatProjectContext" @close="closeChat" />
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
