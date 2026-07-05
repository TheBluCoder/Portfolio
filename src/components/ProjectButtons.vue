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
      class="inline-flex w-full items-center justify-center gap-2 rounded-md bg-[var(--theme-success)] px-4 py-3 text-base font-medium text-[var(--theme-on-accent)] transition hover:bg-[rgb(var(--theme-success-rgb)/0.85)] sm:w-auto"
    >
      <ExternalLinkIcon class="h-5 w-5" />
      Live demo
    </a>

    <a
      v-if="project.source_code_url"
      :href="project.source_code_url"
      target="_blank"
      rel="noopener noreferrer"
      class="inline-flex w-full items-center justify-center gap-2 rounded-md bg-[var(--theme-surface)] px-4 py-3 text-base font-medium text-[var(--theme-text)] transition hover:bg-[rgb(var(--theme-white-rgb)/0.08)] sm:w-auto"
    >
      <GithubIcon class="h-5 w-5" />
      View code
    </a>
  </div>
</template>
