<script setup>
import { ref } from 'vue'
import { ChevronDownIcon } from 'lucide-vue-next'

defineProps({
  entries: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const open = ref(true)
</script>

<template>
  <section class="sec">
    <hr class="sec-divider" />

    <button class="sec-header" @click="open = !open" :aria-expanded="open">
      <span class="sec-label">// education</span>
      <ChevronDownIcon class="sec-chevron" :class="{ 'sec-chevron--open': open }" />
    </button>

    <div class="sec-body" :class="{ 'sec-body--closed': !open }">
      <div class="sec-inner">

        <!-- Skeleton -->
        <div v-if="loading" class="skeletons">
          <div class="skel skel--title"></div>
          <div class="skel skel--sub"></div>
          <div class="skel skel--line"></div>
        </div>

        <!-- Entries -->
        <div v-else class="edu-list">
          <article
            v-for="edu in entries"
            :key="`${edu.institution}-${edu.degree}`"
            class="edu-card"
          >
            <h3 class="edu-degree">{{ edu.degree }}</h3>
            <p v-if="edu.program" class="edu-program">{{ edu.program }}</p>
            <div class="edu-meta">
              <span v-if="edu.institution">{{ edu.institution }}</span>
              <span v-if="edu.dateStart">{{ edu.dateStart }} – {{ edu.dateEnd || 'Present' }}</span>
              <span v-if="edu.gpa">GPA {{ edu.gpa }}</span>
            </div>
          </article>
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

/* ── Skeletons ── */
.skeletons { display: flex; flex-direction: column; gap: 0.625rem; }
.skel {
  height: 0.875rem;
  border-radius: 4px;
  background: rgb(var(--theme-white-rgb) / 0.05);
  animation: pulse 1.6s ease-in-out infinite;
}
.skel--title { width: 50%; height: 1.1rem; }
.skel--sub   { width: 35%; }
.skel--line  { width: 70%; }
@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50%       { opacity: 0.9; }
}

/* ── Education cards ── */
.edu-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.edu-card {
  padding: 1.25rem 1.5rem;
  background: rgb(var(--theme-white-rgb) / 0.02);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  border-radius: 10px;
}

.edu-degree {
  font-family: 'Syne', sans-serif;
  font-size: 1.0625rem;
  font-weight: 700;
  color: var(--theme-text);
  margin-bottom: 0.3rem;
}

.edu-program {
  font-size: 0.9rem;
  color: var(--theme-text-dim);
  margin-bottom: 0.875rem;
}

.edu-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem 1.5rem;
  font-size: 0.8125rem;
  color: var(--theme-text-ghost);
  font-family: ui-monospace, monospace;
}
</style>
