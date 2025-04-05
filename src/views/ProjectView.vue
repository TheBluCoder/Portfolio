<script setup>
import { Card, CardContent } from '@/components/ui/card'
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from '@/components/ui/carousel'
import Autoplay from 'embla-carousel-autoplay'
import { CardDescription, CardHeader, CardTitle } from '@/components/ui/card/index.js'
import { onMounted } from 'vue'

const plugin = Autoplay({
  delay: 2000,
  stopOnMouseEnter: true,
  stopOnInteraction: false,
})

onMounted(()=>{
  const carousel = document.getElementById("carouselItem")

  if(window.innerWidth <= 768){
    carousel.focus()
  }
})
</script>

<template>
  <div class="h-full w-full place-content-center place-items-center">
    <Carousel
      class="relative w-full max-w-xs md:max-w-1/2 lg:max-w-3/5"
      :plugins="[plugin]"
      @mouseenter="plugin.stop"
      @mouseleave="[plugin.reset(), plugin.play()];"
    >
      <CarouselContent>
        <CarouselItem v-for="(_, index) in 5" :key="index" class="group focus:outline-0" tabindex="0" id="carouselItem">
          <div class="p-1">
            <Card class="bg-gray-600/50 group-hover:border-b-0 group-hover:rounded-b-none group-focus:rounded-b-none group-focus:border-b-0">
              <CardContent class="p-0 ">
                <img src="/public/citeme.png" alt="screen shot of cite me app" class="w-fit h-fit">
              </CardContent>
            </Card>
            <Card class="bg-gray-600/50 h-50 border-t-0 rounded-t-none hidden group-hover:block group-focus:block">
              <CardHeader>
                <CardDescription class="text-orange-200 md:text-lg font-semibold italic">
                  CiteMe - Automatic Citation Generation System
                </CardDescription>
              </CardHeader>
              <CardContent class="flex items-center justify-center py-1 px-6 text-gray-200/60 font-light font-mono  ">
                CiteMe is a modern, full-stack application designed to help students generate references and in-line citations efficiently. The system provides intelligent citation suggestions, reference management, and seamless integration with academic databases.
                Students do not have to worry about searching for sources to back essays and thesis. This web app will search the web, format your document with intext citation and include the references, sources and metrics to grade the credibility of the sources.
                The webapp also offers the choice of providing your own sources, in forms of urls, texts and pdfs and is able to use these sources to format your essays/thesis with intext citation and references in any citation format.
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
