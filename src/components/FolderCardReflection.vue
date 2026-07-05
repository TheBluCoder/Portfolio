<script setup>
defineProps({
  folder: {
    type: Object,
    required: true,
  },
  index: {
    type: Number,
    default: 0,
  },
})
</script>

<template>
  <!-- Reflection -->
  <div
    class="folder-reflection hidden md:block"
    :style="{
      transform: 'rotateX(180deg) translateY(-20px)',
      opacity: '0.4',
      filter: 'blur(3px)',
      maskImage: 'linear-gradient(to bottom, rgb(var(--theme-black-rgb) / 1) 10%, rgb(var(--theme-black-rgb) / 0))',
      animationDelay: `${index * 200}ms`,
    }"
  >
    <div
      class="flex flex-col items-center justify-center p-6 bg-[rgb(var(--theme-white-rgb)/0.03)] rounded-lg backdrop-blur-sm border border-[rgb(var(--theme-white-rgb)/0.1)]"
    >
      <component :is="folder.icon" class="w-16 h-16 md:w-24 md:h-24 text-[rgb(var(--theme-success-rgb)/0.5)] mb-4" />
      <span class="text-[rgb(var(--theme-white-rgb)/0.5)] text-lg md:text-xl">
        {{ folder.name }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.folder-reflection {
  perspective: 1000px;
  -webkit-mask-image: -webkit-linear-gradient(top, rgb(var(--theme-black-rgb) / 1) 10%, rgb(var(--theme-black-rgb) / 0));
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: rotateX(180deg) translateY(0);
  }
  to {
    opacity: 0.4;
    transform: rotateX(180deg) translateY(-20px);
  }
}
</style>
