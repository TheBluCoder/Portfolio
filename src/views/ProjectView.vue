<script setup>
import projects from '@/data/projects.json'
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '@/components/ui/carousel'
import Autoplay from 'embla-carousel-autoplay'
import { inject, ref, onMounted, computed } from 'vue'
import ProjectButtons from '@/components/ProjectButtons.vue'
import { Teleport } from 'vue'

// Setup autoplay with reasonable defaults
const plugin = Autoplay({
  delay: 5000,
  stopOnMouseEnter: true,
  stopOnInteraction: false,
})

const api = ref(null)
const showDescription = ref(true)
const openProjectChat = inject('openProjectChat')
const isMobile = computed(() => window.innerWidth <= 768)
const currentSlideIndex = ref(0)

// Add a computed property that returns the current project
const currentProject = computed(() => projects[currentSlideIndex.value])

const handleAskQuestion = (project) => {
  openProjectChat(project)
}

const setApi = (val) => {
  api.value = val

  // Add a change event listener to update the currentSlideIndex
  api.value.on('select', () => {
    currentSlideIndex.value = api.value.selectedScrollSnap()
  })
}

onMounted(() => {
  // Adjust initial state based on screen size
  window.addEventListener('resize', () => {
    showDescription.value = !isMobile.value
  })

  // Set initial state
  showDescription.value = !isMobile.value
})
</script>

<style scoped>
@reference '@/assets/main.css';
.project-card {
  @apply bg-gray-800/80 border border-gray-700 rounded-lg overflow-hidden transition-all duration-300;
}

.project-image {
  @apply w-full h-auto object-cover rounded-t-lg;
}

.project-title {
  @apply text-orange-200 text-lg md:text-xl font-semibold p-3 pb-1 italic;
}

.project-description {
  @apply text-gray-300 text-sm md:text-base p-3 pt-1 font-light leading-relaxed;
  max-height: 150px;
  overflow-y: auto;
}

.project-description a {
  @apply text-orange-200 hover:text-orange-300 transition-colors duration-200;
}

.project-description::-webkit-scrollbar {
  width: 4px;
}

.project-description::-webkit-scrollbar-track {
  background: transparent;
}

.project-description::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.3);
  border-radius: 4px;
}

.carousel-container {
  @apply relative w-full max-w-[310px] sm:max-w-md md:max-w-xl lg:max-w-3xl mx-auto;
}

.carousel-navigation {
  @apply opacity-50 hover:opacity-100 transition-opacity duration-200;
}
</style>

<template>
  <div class="flex items-center justify-center h-full w-full p-4">
    <Carousel id="carousel" class="carousel-container" :plugins="[plugin]" @init-api="setApi">
      <CarouselContent>
        <CarouselItem
          v-for="(project, index) in projects"
          :key="index"
          class="flex flex-col items-center justify-center"
        >
          <div class="project-card w-full">
            <!-- Project Image -->
            <div class="relative overflow-hidden group">
              <img
                :src="project.image"
                :alt="project.name"
                class="project-image"
                onerror="this.src='/placeholder-image.png'"
              />
              <!-- Project Buttons (shown on hover on desktop) -->
              <div
                class="absolute inset-0 flex items-center justify-center bg-black/60 transition-opacity duration-300 ease-linear lg:flex lg:opacity-0 lg:group-hover:opacity-100 lg:pointer-events-none lg:group-hover:pointer-events-auto"
                v-if="!isMobile"
              >
                <ProjectButtons :project="project" @ask-question="handleAskQuestion" />
              </div>
            </div>

            <!-- Project Info -->
            <div v-if="showDescription || isMobile">
              <h3 class="project-title">{{ project.name }}</h3>
              <div class="project-description text-base" v-html="project.description"></div>
            </div>
          </div>
        </CarouselItem>
      </CarouselContent>

      <!-- Navigation Controls -->
      <CarouselPrevious class="carousel-navigation" />
      <CarouselNext class="carousel-navigation" />
    </Carousel>

    <!-- Teleported Mobile/Medium Buttons -->
    <Teleport to="#project-btn">
      <div v-if="isMobile" class="flex items-center justify-center gap-3 p-3 w-full">
        <ProjectButtons :project="currentProject" @ask-question="handleAskQuestion" />
      </div>
    </Teleport>
  </div>
</template>
