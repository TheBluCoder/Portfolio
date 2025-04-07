<script setup>
import educationData from '@/data/education.json'
</script>

<template>
  <div class="max-w-7xl mx-auto fade-in-section mt-20">
    <h1 class="text-4xl font-bold mb-10">Education</h1>

    <!-- Education Timeline -->
    <div class="relative">
      <!-- Timeline line -->
      <div class="absolute left-3 top-0 bottom-0 w-0.5 bg-gray-700"></div>

      <!-- Education items -->
      <div v-for="(education, index) in educationData" :key="index" class="mb-14 pl-12 relative">
        <div class="absolute left-0 top-2 bg-blue-600 rounded-full w-6 h-6"></div>
        <div class="timeline-content">
          <h2 class="text-2xl font-bold">{{ education.degree }}</h2>
          <p class="text-gray-400 mt-1">
            {{ education.institution }} • {{ education.dateStart }} - {{ education.dateEnd }}
          </p>
          <p class="text-gray-400 mt-1">{{ education.program }}</p>
          <p class="text-gray-400 mt-1">
            <span>GPA: {{ education.gpa }}</span>
          </p>
          <p class="text-gray-400 mt-1">Specialization: {{ education.specialization }}</p>
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
  background-color: #6b7280;
}
</style>
