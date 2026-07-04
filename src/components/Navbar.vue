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
      class="fixed z-30 text-2xl h-screen w-screen md:w-auto md:border-r-2 md:border-[rgb(var(--theme-white-rgb)/0.1)] shadow"
    >
      <nav
        tabindex="0"
        class="group px-2 backdrop-blur-md bg-transparent h-full flex flex-col items-center justify-center gap-20 p-2 hover:text-[rgb(var(--theme-accent-rgb)/0.9)] focus:text-[rgb(var(--theme-accent-rgb)/0.9)] active:text-[rgb(var(--theme-accent-rgb)/0.9)] transition-all duration-200 text-[rgb(var(--theme-text-dim-rgb)/0.4)]"
      >
        <NavButton @click="router.push('/') && (isOpen = false)">Home</NavButton>
        <NavButton @click="router.push('/about') && (isOpen = false)">About</NavButton>
        <NavButton @click="router.push('/projects') && (isOpen = false)">Projects</NavButton>
        <NavButton @click="router.push('/gallery') && (isOpen = false)">Gallery</NavButton>
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
