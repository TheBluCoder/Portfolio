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
  <!-- Original Folder -->
  <div
    class="folder-card group cursor-pointer fade-in-up"
    :style="{ animationDelay: `${index * 200}ms` }"
  >
    <div
      class="flex flex-col items-center justify-center p-6 bg-gray-900/50 rounded-lg backdrop-blur-sm border border-gray-700/30 transition-all duration-300 hover:border-green-500/30 hover:bg-gray-800/50"
    >
      <component :is="folder.icon" class="w-16 h-16 md:w-24 md:h-24 text-green-500 mb-4" />
      <span class="text-white/80 text-lg md:text-xl group-hover:text-green-500 transition-colors">
        {{ folder.name }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.folder-card {
  perspective: 1000px;
  animation: none;
}

.folder-card:hover {
  animation: subtleBounce 1.5s infinite;
}

.fade-in-up {
  animation: fadeInUp 1s ease forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes subtleBounce {
  0% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
  100% {
    transform: translateY(0);
  }
}
</style>
