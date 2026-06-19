<script setup>
import { ref } from 'vue'
import { ChevronDownIcon } from 'lucide-vue-next'

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

        <!-- Skeleton -->
        <div v-if="loading" class="skeletons">
          <div class="skel skel--cat"></div>
          <div class="skel-pills">
            <div class="skel skel--pill" v-for="i in 5" :key="i"></div>
          </div>
        </div>

        <!-- Groups -->
        <div v-else class="skills-list">
          <div v-for="group in groups" :key="group.category" class="skill-group">
            <h4 class="skill-category">{{ group.category }}</h4>
            <div class="tech-pills">
              <span
                v-for="tech in group.technologies"
                :key="tech.name || tech"
                class="tech-pill"
              >{{ tech.name || tech }}</span>
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
  border-top: 1px solid rgba(255, 255, 255, 0.05);
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
  color: #3e3c52;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.sec-chevron {
  width: 0.875rem;
  height: 0.875rem;
  color: #3e3c52;
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

/* ── Skeletons ── */
.skeletons { display: flex; flex-direction: column; gap: 0.75rem; }
.skel-pills { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.skel {
  height: 0.875rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  animation: pulse 1.6s ease-in-out infinite;
}
.skel--cat  { width: 30%; }
.skel--pill { width: 4rem; height: 1.75rem; border-radius: 9999px; }
@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50%       { opacity: 0.9; }
}

/* ── Skills ── */
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
  color: #4a4860;
  margin-bottom: 0.625rem;
}

.tech-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tech-pill {
  font-size: 0.8125rem;
  padding: 0.3rem 0.8rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.07);
  color: #7a7888;
  cursor: default;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.tech-pill:hover {
  background: rgba(139, 124, 248, 0.08);
  border-color: rgba(139, 124, 248, 0.22);
  color: #b5aef8;
}
</style>
