<script setup>
import { ref, computed } from 'vue'
import { ChevronDownIcon } from 'lucide-vue-next'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: true, breaks: true, linkify: true, typographer: true })

const props = defineProps({
  content: { type: String, default: null },
  loading: { type: Boolean, default: false },
  error:   { type: Boolean, default: false },
})

const open = ref(true)
const rendered = computed(() => props.content ? md.render(props.content) : '')
</script>

<template>
  <section class="sec">
    <hr class="sec-divider" />

    <button class="sec-header" @click="open = !open" :aria-expanded="open">
      <span class="sec-label">// about</span>
      <ChevronDownIcon class="sec-chevron" :class="{ 'sec-chevron--open': open }" />
    </button>

    <div class="sec-body" :class="{ 'sec-body--closed': !open }">
      <div class="sec-inner">

        <!-- Skeleton -->
        <div v-if="loading" class="skeletons">
          <div class="skel skel--lg"></div>
          <div class="skel skel--full"></div>
          <div class="skel skel--md"></div>
          <div class="skel skel--full" style="margin-top: 0.5rem"></div>
          <div class="skel skel--sm"></div>
        </div>

        <!-- Error -->
        <p v-else-if="error" class="about-error">
          README unavailable right now.
          <a href="https://github.com/TheBluCoder/blucoder" target="_blank" rel="noopener noreferrer">
            Read it on GitHub →
          </a>
        </p>

        <!-- Content -->
        <div v-else-if="rendered" class="readme-content" v-html="rendered" />

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

/* Grid-row collapse trick for smooth animation */
.sec-body {
  display: grid;
  grid-template-rows: 1fr;
  transition: grid-template-rows 0.35s ease;
  overflow: hidden;
}
.sec-body--closed { grid-template-rows: 0fr; }

.sec-inner {
  overflow: hidden;
  min-height: 0;
}

.sec-gap { height: 0.5rem; }

/* ── Skeletons ── */
.skeletons { display: flex; flex-direction: column; gap: 0.625rem; }
.skel {
  height: 0.875rem;
  border-radius: 4px;
  background: rgb(var(--theme-white-rgb) / 0.05);
  animation: pulse 1.6s ease-in-out infinite;
}
.skel--full  { width: 100%; }
.skel--lg    { width: 75%; }
.skel--md    { width: 83%; }
.skel--sm    { width: 60%; }

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50%       { opacity: 0.9; }
}

/* ── Error ── */
.about-error { font-size: 0.9rem; color: var(--theme-text-faint); }
.about-error a { color: var(--theme-accent); text-decoration: none; }
.about-error a:hover { text-decoration: underline; }

/* ── README prose ── */
:deep(.readme-content) h1,
:deep(.readme-content) h2,
:deep(.readme-content) h3,
:deep(.readme-content) h4 {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  color: var(--theme-text);
  line-height: 1.3;
  margin-top: 2rem;
  margin-bottom: 0.625rem;
}
:deep(.readme-content) h1 { font-size: 1.625rem; }
:deep(.readme-content) h2 { font-size: 1.25rem; }
:deep(.readme-content) h3 { font-size: 1.0625rem; }
:deep(.readme-content) h4 { font-size: 0.9375rem; color: var(--theme-accent-muted); }
:deep(.readme-content) p {
  color: var(--theme-text-subtle);
  font-size: 0.9375rem;
  line-height: 1.8;
  margin-bottom: 1rem;
}
:deep(.readme-content) a { color: var(--theme-accent); text-decoration: none; }
:deep(.readme-content) a:hover { text-decoration: underline; }
:deep(.readme-content) img { max-width: 100%; height: auto; border-radius: 6px; }
:deep(.readme-content) code {
  font-size: 0.85em;
  background: rgb(var(--theme-white-rgb) / 0.07);
  padding: 0.1em 0.4em;
  border-radius: 3px;
  color: var(--theme-text-soft);
}
:deep(.readme-content) pre {
  background: var(--theme-surface);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.08);
  border-radius: 8px;
  padding: 1rem 1.25rem;
  overflow-x: auto;
  margin: 1.25rem 0;
}
:deep(.readme-content) pre code { background: none; padding: 0; font-size: 0.875rem; }
:deep(.readme-content) ul,
:deep(.readme-content) ol { padding-left: 1.5rem; margin-bottom: 1rem; }
:deep(.readme-content) li {
  color: var(--theme-text-subtle);
  font-size: 0.9375rem;
  line-height: 1.75;
  margin-bottom: 0.3rem;
}
:deep(.readme-content) blockquote {
  border-left: 2px solid rgb(var(--theme-accent-rgb) / 0.4);
  padding-left: 1rem;
  margin: 1rem 0;
  color: var(--theme-text-faint);
  font-style: italic;
}
:deep(.readme-content) hr {
  border: none;
  border-top: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  margin: 1.5rem 0;
}
</style>
