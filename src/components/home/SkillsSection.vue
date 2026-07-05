<script setup>
import { ref } from 'vue'
import { ChevronDownIcon } from 'lucide-vue-next'
import SkillIconTile from '@/components/SkillIconTile.vue'

defineProps({
  groups: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const open = ref(true)
</script>

<template>
  <section class="sec">
    <hr class="sec-divider" />

    <button class="sec-header" @click="open = !open" :aria-expanded="open">
      <span class="sec-label">// skills</span>
      <ChevronDownIcon class="sec-chevron" :class="{ 'sec-chevron--open': open }" />
    </button>

    <div class="sec-body" :class="{ 'sec-body--closed': !open }">
      <div class="sec-inner">
        <div v-if="loading" class="skeletons">
          <div class="skel skel--cat"></div>
          <div class="skel-pills">
            <div class="skel skel--tile" v-for="i in 5" :key="i"></div>
          </div>
        </div>

        <div v-else class="skills-list">
          <div v-for="group in groups" :key="group.category" class="skill-group">
            <h4 class="skill-category">{{ group.category }}</h4>
            <div class="tech-pills">
              <SkillIconTile
                v-for="tech in group.technologies"
                :key="tech.name || tech"
                :skill="tech"
                compact
              />
            </div>
          </div>
        </div>

        <div class="sec-gap"></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.sec-divider {
  border: none;
  border-top: 1px solid rgb(var(--theme-white-rgb) / 0.05);
  margin: 3rem 0;
}

.sec-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  margin-bottom: 1.75rem;
}

.sec-label {
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.sec-chevron {
  width: 0.875rem;
  height: 0.875rem;
  color: var(--theme-text-barely);
  transition: transform 0.25s ease;
  flex-shrink: 0;
}

.sec-chevron--open { transform: rotate(180deg); }

.sec-body {
  display: grid;
  grid-template-rows: 1fr;
  transition: grid-template-rows 0.35s ease;
  overflow: hidden;
}

.sec-body--closed { grid-template-rows: 0fr; }

.sec-inner { overflow: hidden; min-height: 0; }
.sec-gap { height: 0.5rem; }

.skeletons { display: flex; flex-direction: column; gap: 0.75rem; }
.skel-pills { display: flex; gap: 0.625rem; flex-wrap: wrap; }

.skel {
  height: 0.875rem;
  border-radius: 4px;
  background: rgb(var(--theme-white-rgb) / 0.05);
  animation: pulse 1.6s ease-in-out infinite;
}

.skel--cat { width: 30%; }
.skel--tile { width: 5.25rem; height: 5.9rem; border-radius: 8px; }

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.9; }
}

.skills-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.skill-category {
  font-size: 0.6875rem;
  font-family: ui-monospace, monospace;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--theme-text-ghost);
  margin-bottom: 0.625rem;
}

.tech-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.85rem 0.625rem;
  align-items: center;
}
</style>
