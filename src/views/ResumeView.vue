<script setup>
import Experience from '@/components/Experience.vue'
import Education from '@/components/Education.vue'
import TechStack from '@/components/TechStack.vue'
</script>

<template>
  <section class="min-h-screen w-full bg-black p-8 text-white">
    <!-- Tech Stack Section -->
    <TechStack />

    <!-- Experience Section -->
    <Experience resumeUrl="#" />

    <!-- Education Section -->
    <Education />
  </section>
</template>

<style scoped>
.fade-in-section {
  opacity: 0;
  transform: translateY(20px);
  animation: fadeIn 0.8s ease forwards;
}

@keyframes fadeIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-section:nth-child(2) {
  animation-delay: 0.3s;
}

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
  background-color: #6b7280;
}
</style>
