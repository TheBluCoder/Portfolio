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
      maskImage: 'linear-gradient(to bottom, rgba(0,0,0,1) 10%, rgba(0,0,0,0))',
      animationDelay: `${index * 200}ms`,
    }"
  >
    <div
      class="flex flex-col items-center justify-center p-6 bg-gray-900/30 rounded-lg backdrop-blur-sm border border-gray-700/10"
    >
      <component :is="folder.icon" class="w-16 h-16 md:w-24 md:h-24 text-green-500/50 mb-4" />
      <span class="text-white/50 text-lg md:text-xl">
        {{ folder.name }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.folder-reflection {
  perspective: 1000px;
  -webkit-mask-image: -webkit-linear-gradient(top, rgba(0, 0, 0, 1) 10%, rgba(0, 0, 0, 0));
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
