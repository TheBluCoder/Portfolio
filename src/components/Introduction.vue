<template>
  <section
    class="min-h-screen w-full flex flex-col items-center justify-center bg-black p-8 gap-16"
  >
    <!-- Typing Text Container -->
    <div class="w-full max-w-[90vw] md:max-w-[80vw] lg:max-w-[70vw]">
      <div class="typing-container">
        <h1 class="text-white text-2xl md:text-4xl lg:text-6xl mb-4">Hi👋, I am ike (ee-keh)</h1>
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
      <template v-for="folder in folders" :key="folder.name">
        <!-- Original Folder -->
        <div class="folder-card group cursor-pointer" @click="handleFolderClick(folder.name)">
          <div
            class="flex flex-col items-center justify-center p-6 bg-gray-900/50 rounded-lg backdrop-blur-sm border border-gray-700/30 transition-all duration-300 hover:border-green-500/30 hover:bg-gray-800/50"
          >
            <component :is="folder.icon" class="w-16 h-16 md:w-24 md:h-24 text-green-500 mb-4" />
            <span
              class="text-white/80 text-lg md:text-xl group-hover:text-green-500 transition-colors"
            >
              {{ folder.name }}
            </span>
          </div>
        </div>

        <!-- Reflection -->
        <div
          class="folder-reflection hidden md:block"
          :style="{
            transform: 'rotateX(180deg) translateY(-20px)',
            opacity: '0.4',
            filter: 'blur(3px)',
            maskImage: 'linear-gradient(to bottom, rgba(0,0,0,1) 10%, rgba(0,0,0,0))',
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
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { FolderIcon, BriefcaseIcon, ImageIcon } from 'lucide-vue-next'

const texts = ['<code/>', 'poems', 'melodies']
const currentText = ref('')
const currentIndex = ref(0)
const isDeleting = ref(false)
const typingElement = ref(null)

const folders = [
  { name: 'Projects', icon: FolderIcon },
  { name: 'Resume', icon: BriefcaseIcon },
  { name: 'Gallery', icon: ImageIcon },
]

const handleFolderClick = (folderName) => {
  // Handle folder click - can be implemented later
  console.log(`Clicked ${folderName}`)
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

.folder-card {
  perspective: 1000px;
  animation: none;
}
.folder-card:hover {
  animation: subtleBounce 2s infinite;
}

.folder-reflection {
  perspective: 1000px;
  -webkit-mask-image: -webkit-linear-gradient(top, rgba(0, 0, 0, 1) 10%, rgba(0, 0, 0, 0));
}

@keyframes blink {
  50% {
    border-color: transparent;
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
