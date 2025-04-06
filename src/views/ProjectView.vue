<script setup>
import { Card, CardContent } from '@/components/ui/card'
import projects from '@/data/projects.json'
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '@/components/ui/carousel'
import Autoplay from 'embla-carousel-autoplay'
import { CardHeader } from '@/components/ui/card/index.js'
import { onMounted } from 'vue'
import ProjectButtons from '@/components/ProjectButtons.vue'
import { inject } from 'vue'

const plugin = Autoplay({
  delay: 2000,
  stopOnMouseEnter: true,
  stopOnInteraction: false,
})

const openProjectChat = inject('openProjectChat')

const handleAskQuestion = (project) => {
  openProjectChat(project)
}

onMounted(() => {
  const carousel = document.getElementById('carouselItem')

  if (window.innerWidth <= 768) {
    carousel.focus()
  }
})
</script>

<style>
.custom-scrollbar {
  scrollbar-width: calc(4px);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.3);
  border-radius: 4px;
}
</style>

<template>
  <div class="h-full w-full place-content-center place-items-center">
    <Carousel
      class="relative w-full max-w-md md:max-w-[90%] md:hover:max-w-3/5 duration-500"
      :plugins="[plugin]"
      @mouseenter="plugin.stop"
      @mouseleave="[plugin.reset(), plugin.play(), console.log('mouseleave')]"
    >
      <CarouselContent>
        <CarouselItem
          v-for="(project, index) in projects"
          :key="index"
          class="group focus:outline-0"
          tabindex="0"
          id="carouselItem"
        >
          <div class="p-1">
            <Card
              class="bg-gray-600/50 group-hover:border-b-0 group-hover:rounded-b-none group-focus:rounded-b-none group-focus:border-b-0 gap-2 py-1 px-1"
            >
              <CardContent class="p-0">
                <div class="relative group">
                  <img :src="project.image" :alt="project.name" class="w-fit h-fit rounded-md" />
                  <ProjectButtons :project="project" @ask-question="handleAskQuestion" />
                </div>
              </CardContent>
            </Card>
            <Card
              class="bg-gray-600/50 h-auto border-t-0 rounded-t-none hidden group-hover:block group-focus:block gap-2 py-1 px-1"
            >
              <CardHeader
                class="text-orange-200 text-sm md:text-lg font-semibold italic p-2 md:px-4"
              >
                {{ project.name }}
              </CardHeader>
              <CardContent class="flex flex-col items-start justify-start p-2 md:px-4">
                <p
                  class="text-gray-200/60 text-md md:text-lg font-light font-mono leading-relaxed overflow-y-auto max-h-[150px] custom-scrollbar"
                >
                  {{ project.description }}
                </p>
              </CardContent>
            </Card>
          </div>
        </CarouselItem>
      </CarouselContent>
      <CarouselPrevious />
      <CarouselNext />
    </Carousel>
  </div>
</template>
