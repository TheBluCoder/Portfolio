<script setup>
import NavButton from './NavButton.vue'
import router from '@/router'

const isOpen = defineModel('isOpen', { required: true, default: false })
defineOptions({ name: 'NavbarComponent' })
</script>

<template>
  <Transition name="slide">
    <div
      v-show="isOpen"
      class="fixed z-30 text-2xl h-screen w-screen md:w-auto md:border-r-2 md:border-gray-300/10 shadow"
    >
      <nav
        tabindex="0"
        class="group px-2 backdrop-blur-md bg-transparent h-full flex flex-col items-center justify-center gap-20 p-2 hover:text-blue-200/90 focus:text-blue-200/90 active:text-blue-200/90 transition-all duration-200 text-gray-400/40"
      >
        <NavButton @click="router.push('/') && (isOpen = false)">Home</NavButton>
        <NavButton @click="router.push('/about') && (isOpen = false)">About</NavButton>
        <NavButton @click="router.push('/projects') && (isOpen = false)">Projects</NavButton>
        <NavButton @click="router.push('/resume') && (isOpen = false)">Resume</NavButton>
      </nav>
    </div>
  </Transition>
</template>

<style scoped>
.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%) rotateZ(90deg);
  opacity: 0;
}
.slide-enter-to,
.slide-leave-from {
  transform: translateX(0);
  opacity: 1;
}
.slide-enter-active,
.slide-leave-active {
  transition: all 500ms ease-in-out;
}
</style>
