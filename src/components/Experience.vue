<script setup>
import { DownloadIcon } from 'lucide-vue-next'
import experienceData from '@/data/experience.json'

defineProps({
  resumeUrl: {
    type: String,
    default: '#',
  },
})
</script>

<template>
  <div class="max-w-7xl mx-auto fade-in-section">
    <div class="flex justify-between items-center mb-10 gap-2">
      <h1 class="text-4xl font-bold mr-1">Experience</h1>
      <a
        :href="resumeUrl"
        type="application/pdf"
        target="_blank"
        rel="noopener noreferrer"
        download="Ikeoluwa_Oladele_Resume_SWE.pdf"
        class="bg-[var(--theme-accent)] hover:bg-[var(--theme-accent-hover)] text-[var(--theme-on-accent)] py-2 px-4 rounded-md flex items-center transition-colors"
      >
        <DownloadIcon class="mr-2 h-5 w-5" />
        <span>Download Resume</span>
      </a>
    </div>

    <!-- Experience Timeline -->
    <div class="relative">
      <!-- Timeline line -->
      <div class="absolute left-3 top-0 bottom-0 w-0.5 bg-[var(--theme-surface)]"></div>

      <!-- Experience items -->
      <div v-for="(experience, index) in experienceData" :key="index" class="mb-14 pl-12 relative">
        <div class="absolute left-0 top-2 bg-[var(--theme-accent)] rounded-full w-6 h-6"></div>
        <div class="timeline-content">
          <h2 class="text-2xl font-bold flex items-baseline whitespace-nowrap">
            {{ experience.jobTitle }}
            <span class="text-[rgb(var(--theme-text-disabled-rgb)/0.8)] text-sm font-light ml-2">{{ experience.position }}</span>
          </h2>
          <p class="text-[var(--theme-text-dim)] mt-1">
            {{ experience.company }} • {{ experience.dateStart }} - {{ experience.dateEnd }}
          </p>
          <ul class="mt-4 text-[var(--theme-text-soft)] space-y-3 list-disc pl-5">
            <li v-for="(task, taskIndex) in experience.tasks" :key="taskIndex">
              {{ task }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline-content {
  position: relative;
  border-left: none;
  padding-left: 0;
}

.timeline-content::before {
  content: '';
  position: absolute;
  top: 13px;
  left: -20px;
  width: 14px;
  height: 2px;
  background-color: var(--theme-text-faint);
}
</style>
