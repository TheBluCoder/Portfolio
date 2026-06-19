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
      <span class="sec-label">// experience</span>
      <ChevronDownIcon class="sec-chevron" :class="{ 'sec-chevron--open': open }" />
    </button>

    <div class="sec-body" :class="{ 'sec-body--closed': !open }">
      <div class="sec-inner">

        <!-- Skeleton -->
        <div v-if="loading" class="skeletons">
          <div class="skel skel--title"></div>
          <div class="skel skel--sub"></div>
          <div class="skel skel--line"></div>
          <div class="skel skel--line skel--short"></div>
        </div>

        <!-- Entries -->
        <div v-else class="experience-list">
          <article v-for="job in entries" :key="`${job.company}-${job.jobTitle}`" class="exp-entry">
            <div class="exp-header">
              <div class="exp-title-group">
                <h3 class="exp-title">{{ job.jobTitle }}</h3>
                <p class="exp-sub">{{ job.company }}<span v-if="job.position"> · {{ job.position }}</span></p>
              </div>
              <span v-if="job.dateStart" class="exp-date">
                {{ job.dateStart }} – {{ job.dateEnd || 'Present' }}
              </span>
            </div>
            <ul v-if="job.tasks.length" class="exp-tasks">
              <li v-for="task in job.tasks" :key="task">{{ task }}</li>
            </ul>
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
.skeletons { display: flex; flex-direction: column; gap: 0.625rem; }
.skel {
  height: 0.875rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  animation: pulse 1.6s ease-in-out infinite;
}
.skel--title  { width: 50%; height: 1.1rem; }
.skel--sub    { width: 35%; }
.skel--line   { width: 100%; }
.skel--short  { width: 75%; }
@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50%       { opacity: 0.9; }
}

/* ── Experience list ── */
.experience-list {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.exp-entry {
  padding-left: 1rem;
  border-left: 2px solid rgba(139, 124, 248, 0.2);
}

.exp-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.875rem;
}

.exp-title-group { flex: 1; min-width: 0; }

.exp-title {
  font-family: 'Syne', sans-serif;
  font-size: 1.0625rem;
  font-weight: 700;
  color: #e0ddf5;
  margin-bottom: 0.2rem;
}

.exp-sub {
  font-size: 0.875rem;
  color: #6a6878;
}

.exp-date {
  font-size: 0.8rem;
  color: #3e3c52;
  font-family: ui-monospace, monospace;
  white-space: nowrap;
  flex-shrink: 0;
  padding-top: 2px;
}

.exp-tasks {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.exp-tasks li {
  position: relative;
  padding-left: 1rem;
  font-size: 0.9rem;
  color: #6a6878;
  line-height: 1.7;
}

.exp-tasks li::before {
  content: '·';
  position: absolute;
  left: 0;
  color: #3e3c52;
}
</style>
