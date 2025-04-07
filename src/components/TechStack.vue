<script setup>
import techStackData from '@/data/techstack.json'
</script>

<template>
  <div class="max-w-7xl mx-auto mb-16 fade-in-section">
    <h3 class="text-4xl font-bold mb-10 text-gray-600">&lt;/Tech stack!&gt;</h3>
    <hr class="border-gray-700 mb-10" />

    <div class="grid grid-cols-1 md:grid-cols-3 gap-16">
      <div v-for="(stack, index) in techStackData" :key="index">
        <h2 class="text-2xl font-bold text-green-500 mb-6">{{ stack.category }}</h2>
        <p class="text-gray-300 mb-6">{{ stack.description }}</p>

        <div v-if="stack.category === 'languages'" class="grid grid-cols-2 gap-3">
          <ul class="space-y-3">
            <li
              v-for="(tech, techIndex) in stack.technologies.slice(
                0,
                Math.ceil(stack.technologies.length / 2),
              )"
              :key="techIndex"
              class="flex items-center"
            >
              <span class="text-green-500 mr-2">►</span>
              <span>{{ tech.name }}</span>
              <i :class="tech.icon" class="ml-3 text-gray-400"></i>
            </li>
          </ul>
          <ul class="space-y-3">
            <li
              v-for="(tech, techIndex) in stack.technologies.slice(
                Math.ceil(stack.technologies.length / 2),
              )"
              :key="techIndex"
              class="flex items-center"
            >
              <span class="text-green-500 mr-2">►</span>
              <span>{{ tech.name }}</span>
              <i :class="tech.icon" class="ml-3 text-gray-400"></i>
            </li>
          </ul>
        </div>

        <div
          v-else-if="stack.category === 'Artificial Intelligence'"
          class="grid grid-cols-2 gap-3"
        >
          <ul class="space-y-3">
            <li
              v-for="(tech, techIndex) in stack.technologies.slice(
                0,
                Math.ceil(stack.technologies.length / 2),
              )"
              :key="techIndex"
              class="flex items-center"
            >
              <span class="text-green-500 mr-2">►</span>
              <span>{{ tech.name }}</span>
              <i :class="tech.icon" class="ml-3 text-gray-400"></i>
            </li>
          </ul>
          <ul class="space-y-3">
            <li
              v-for="(tech, techIndex) in stack.technologies.slice(
                Math.ceil(stack.technologies.length / 2),
              )"
              :key="techIndex"
              class="flex items-center"
            >
              <span class="text-green-500 mr-2">►</span>
              <span>{{ tech.name }}</span>
              <i :class="tech.icon" class="ml-3 text-gray-400"></i>
            </li>
          </ul>
        </div>

        <ul v-else class="space-y-3">
          <li
            v-for="(tech, techIndex) in stack.technologies"
            :key="techIndex"
            class="flex items-center"
          >
            <span class="text-green-500 mr-2">►</span>
            <span>{{ tech.name }}</span>
            <i :class="tech.icon" class="ml-3 text-gray-400"></i>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
