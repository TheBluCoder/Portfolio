<script setup>
import { Card, CardContent } from '@/components/ui/card'
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '@/components/ui/carousel'
import Autoplay from 'embla-carousel-autoplay'
import { CardDescription, CardHeader, CardTitle } from '@/components/ui/card/index.js'
import { onMounted } from 'vue'

const plugin = Autoplay({
  delay: 2000,
  stopOnMouseEnter: true,
  stopOnInteraction: false,
})

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
      class="relative w-full max-w-md md:max-w-1/2 lg:max-w-3/5"
      :plugins="[plugin]"
      @mouseenter="plugin.stop"
      @mouseleave="[plugin.reset(), plugin.play()]"
    >
      <CarouselContent>
        <CarouselItem
          v-for="(_, index) in 5"
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
                <img
                  src="/public/citeme.png"
                  alt="screen shot of cite me app"
                  class="w-fit h-fit rounded-md"
                />
              </CardContent>
            </Card>
            <Card
              class="bg-gray-600/50 h-auto border-t-0 rounded-t-none hidden group-hover:block group-focus:block gap-2 py-1 px-1"
            >
              <CaHeaderrdHeader
                class="text-orange-200 text-sm md:text-lg font-semibold italic p-2 md:p-4"
              >
                CiteMe - Automatic Citation Generation System
              </CaHeaderrdHeader>
              <CardContent class="flex flex-col items-start justify-start p-2 md:p-4">
                <p
                  class="text-gray-200/60 text-xs md:text-sm lg:text-base font-light font-mono leading-relaxed overflow-y-auto max-h-[150px] custom-scrollbar"
                >
                  CiteMe is a modern, full-stack application designed to help students generate
                  references and in-line citations efficiently. The system provides intelligent
                  citation suggestions, reference management, and seamless integration with academic
                  databases. Students do not have to worry about searching for sources to back
                  essays and thesis. This web app will search the web, format your document with
                  intext citation and include the references, sources and metrics to grade the
                  credibility of the sources. The webapp also offers the choice of providing your
                  own sources, in forms of urls, texts and pdfs and is able to use these sources to
                  format your essays/thesis with intext citation and references in any citation
                  format.
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
