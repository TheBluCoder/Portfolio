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
import { inject, ref, watch, computed } from 'vue'

const plugin = Autoplay({
  delay: 4000,
  stopOnMouseEnter: true,
  stopOnFocusIn: true,
  stopOnInteraction: false,
})

const api = ref()

const show_description = ref(false)

const openProjectChat = inject('openProjectChat')
const isFocused = ref(false)

const isMobile = () => window.innerWidth <= 768

const handleAskQuestion = (project) => {
  openProjectChat(project)
}

const setApi = (val) => {
  api.value = val
}

const set_focus = (id) => {
  const carousel = document.getElementById(id)
  isFocused.value = true
  carousel.focus()
  show_description.value = true
}

const remove_focus = (id) => {
  const carousel = document.getElementById(id)
  isFocused.value = false
  carousel.blur()
  plugin.play()
  show_description.value = false
}

watch(api, (val) => {
  if (!api.value) return
  api.value.on('reInit', () => {
    if (isFocused.value) {
      plugin.stop()
    }
  })
})

onMounted(() => {
  if (isMobile) {
    set_focus('carousel')
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
  <div class="h-full w-full">
    <div
      class="h-full place-content-center place-items-center w-full mx-auto"
      @mouseenter="set_focus('carousel')"
      @mouseleave="remove_focus('carousel')"
    >
      <Carousel
        id="carousel"
        class="group relative w-full max-w-xs md:max-w-[75%] md:focus:max-w-[70%] duration-500 focus:outline-none"
        :plugins="[plugin]"
        @focus="show_description = true"
        @blur="show_description = false"
        @init-api="setApi"
        tabindex="0"
      >
        <CarouselContent>
          <CarouselItem
            v-for="(project, index) in projects"
            :key="index"
            class="focus:outline-0"
            id="carouselItem"
          >
            <div class="p-1">
              <Card
                class="bg-gray-600/50 border-b-0 rounded-b-none lg:border-b lg:rounded-b-lg group-hover:border-b-0 group-hover:rounded-b-none group-focus:rounded-b-none group-focus:border-b-0 gap-2 py-1 px-1"
              >
                <CardContent class="p-0">
                  <div class="relative group">
                    <img
                      :src="project.image"
                      :alt="project.name"
                      class="w-fit h-fit rounded-t-md lg:rounded-md"
                    />
                    <Teleport to="#project-btn" defer :disabled="!isMobile()">
                      <ProjectButtons :project="project" @ask-question="handleAskQuestion" />
                    </Teleport>
                  </div>
                </CardContent>
              </Card>
              <Card
                class="bg-gray-600/50 h-auto border-t-0 rounded-t-none lg:hidden gap-2 py-1 px-1"
                :class="{ 'lg:block': show_description }"
              >
                <CardHeader
                  class="text-orange-200 text-sm md:text-lg font-semibold italic p-2 md:px-4"
                >
                  {{ project.name }}
                </CardHeader>
                <CardContent class="flex flex-col items-start justify-start p-2 md:px-4">
                  <p
                    class="text-gray-200/60 text-md md:text-lg font-light font-mono leading-relaxed overflow-y-auto max-h-[150px] custom-scrollbar break-words w-full"
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
  </div>
</template>
