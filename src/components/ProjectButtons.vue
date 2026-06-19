<script setup>
import { ExternalLinkIcon, GithubIcon } from 'lucide-vue-next'

defineProps({
  project: {
    type: Object,
    required: true,
  },
})

</script>

<template>
  <div class="grid gap-3 bg-transparent px-0 py-2 sm:flex sm:flex-wrap sm:items-center sm:justify-center sm:p-4">
    <a
      v-if="project.demo"
      :href="project.demo"
      target="_blank"
      rel="noopener noreferrer"
      class="inline-flex w-full items-center justify-center gap-2 rounded-md bg-green-600 px-4 py-3 text-base font-medium text-white transition hover:bg-green-500 sm:w-auto"
    >
      <ExternalLinkIcon class="h-5 w-5" />
      Live demo
    </a>

    <a
      v-if="project.source_code_url"
      :href="project.source_code_url"
      target="_blank"
      rel="noopener noreferrer"
      class="inline-flex w-full items-center justify-center gap-2 rounded-md bg-gray-700 px-4 py-3 text-base font-medium text-white transition hover:bg-gray-600 sm:w-auto"
    >
      <GithubIcon class="h-5 w-5" />
      View code
    </a>
  </div>
</template>
