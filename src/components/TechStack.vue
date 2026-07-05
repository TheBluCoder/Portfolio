<script setup>
import SkillIconTile from '@/components/SkillIconTile.vue'
import techStackData from '@/data/techstack.json'
</script>

<template>
  <div class="max-w-7xl mx-auto my-12 fade-in-section">
    <h3 class="text-2xl md:text-4xl font-bold mb-4 text-[var(--theme-text-faint)]">
      &lt;/Tech stack!&gt;
    </h3>
    <hr class="border-[var(--theme-border-strong)] mb-10" />

    <div class="grid grid-cols-1 md:grid-cols-3 gap-12">
      <div v-for="(stack, index) in techStackData" :key="index">
        <h2 class="text-2xl font-bold text-[var(--theme-success)] mb-6">
          {{ stack.category }}
        </h2>
        <p class="text-[var(--theme-text-soft)] mb-6">{{ stack.description }}</p>

        <div class="tech-icon-grid">
          <SkillIconTile
            v-for="(tech, techIndex) in stack.technologies"
            :key="techIndex"
            :skill="tech"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tech-icon-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem 0.75rem;
  align-items: stretch;
}
</style>
