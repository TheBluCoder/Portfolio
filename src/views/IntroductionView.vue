<template>
  <section
    class="min-h-screen w-full flex flex-col items-center justify-center bg-black p-8 gap-16"
    :class="{ 'animate-slide-out': isNavigating }"
  >
    <!-- Typing Text Container -->
    <div class="w-full max-w-[90vw] md:max-w-[80vw] lg:max-w-[70vw] animate-slide-fade">
      <div class="typing-container">
        <h1 class="text-white text-2xl md:text-4xl lg:text-6xl mb-4 whitespace-nowrap">
          Hi<a href="https://www.animatedimages.org/cat-waving-1645.htm"
            ><img
              src="https://www.animatedimages.org/data/media/1645/animated-waving-image-0064.gif"
              border="0"
              alt="animated-waving-image-0064"
              class="inline-block h-16 w-16"
          /></a>
          , I am ike (ee-keh)
        </h1>
        <div class="flex items-center text-xl md:text-3xl lg:text-5xl">
          <span class="text-white/80 mr-3">And... I write</span>
          <span class="text-green-500 typing-text" ref="typingElement">{{ currentText }}</span>
        </div>
      </div>
    </div>

    <!-- Folders Container -->
    <div
      class="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-[90vw] md:max-w-[80vw] lg:max-w-[70vw]"
    >
      <template v-for="(folder, index) in folders" :key="folder.name">
        <router-link :to="folder.name.toLowerCase()">
          <FolderCard :folder="folder" :index="index" @click="handleFolderClick(folder.name)" />
        </router-link>
        <FolderCardReflection :folder="folder" :index="index" />
      </template>
    </div>

    <!-- Down Arrow -->
    <div class="absolute bottom-8 w-full flex justify-center">
      <button
        @click="handleFolderClick('about')"
        class="text-white animate-bounce p-2 rounded-full hover:bg-white/10 transition-colors"
        aria-label="Scroll to About section"
      >
        <chevron-down class="h-10 w-10"></chevron-down>
      </button>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { FolderIcon, BriefcaseIcon, ImageIcon } from 'lucide-vue-next'
import FolderCard from '../components/FolderCard.vue'
import FolderCardReflection from '../components/FolderCardReflection.vue'
import { ChevronDown } from 'lucide-vue-next'
const texts = ['<code/>', 'poems', 'melodies']
const currentText = ref('')
const currentIndex = ref(0)
const isDeleting = ref(false)
const typingElement = ref(null)
const isNavigating = ref(false)

const folders = [
  { name: 'Projects', icon: FolderIcon },
  { name: 'Resume', icon: BriefcaseIcon },
  { name: 'Gallery', icon: ImageIcon },
]

const emits = defineEmits(['switch-view'])

const handleFolderClick = (folderName) => {
  // Handle folder click - can be implemented later
  emits('switch-view', folderName.toLowerCase())
}

const typeText = async () => {
  const text = texts[currentIndex.value]

  if (!isDeleting.value) {
    currentText.value = text.substring(0, currentText.value.length + 1)

    if (currentText.value === text) {
      isDeleting.value = true
      await new Promise((resolve) => setTimeout(resolve, 1500)) // Pause at the end
    }
  } else {
    currentText.value = text.substring(0, currentText.value.length - 1)

    if (currentText.value === '') {
      isDeleting.value = false
      currentIndex.value = (currentIndex.value + 1) % texts.length
    }
  }

  const timeout = isDeleting.value ? 100 : 200
  setTimeout(typeText, timeout)
}

onMounted(() => {
  typeText()
})
</script>

<style scoped>
.typing-container {
  display: inline-block;
}

.typing-text {
  border-right: 0.1em solid white;
  white-space: nowrap;
  overflow: hidden;
}

@keyframes blink {
  50% {
    border-color: transparent;
  }
}

.animate-slide-fade {
  animation: slide-fade 0.5s ease forwards;
}

.animate-slide-out {
  animation: slide-out 0.5s ease forwards;
}

@keyframes slide-fade {
  from {
    opacity: 0;
    transform: translateX(-100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slide-out {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-100%);
  }
}
</style>
