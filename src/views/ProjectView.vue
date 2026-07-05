<script setup>
import { computed, inject, nextTick, onUnmounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ExternalLinkIcon, GithubIcon } from 'lucide-vue-next'
import { usePortfolioStore } from '@/stores/portfolio'
import SkillIconTile from '@/components/SkillIconTile.vue'

const setActiveProjectChatContext = inject('setActiveProjectChatContext', () => { })
const clearActiveProjectChatContext = inject('clearActiveProjectChatContext', () => { })
const portfolioStore = usePortfolioStore()
const {
  projects,
  projectsLoading: loading,
  projectsError: loadError,
} = storeToRefs(portfolioStore)
const selectedProjectName = ref('')
const detailRef = ref(null)

const selectedProject = computed(
  () =>
    projects.value.find((project) => project.name === selectedProjectName.value) ||
    projects.value[0],
)

const directVideoExtensions = ['.mp4', '.webm', '.ogg', '.mov', '.m4v']

const normalizeYouTubeEmbedUrl = (url) => {
  const videoId =
    url.hostname === 'youtu.be'
      ? url.pathname.slice(1)
      : url.searchParams.get('v') || url.pathname.split('/').pop()
  return videoId ? `https://www.youtube.com/embed/${videoId}` : ''
}

const normalizeVimeoEmbedUrl = (url) => {
  const videoId = url.pathname
    .split('/')
    .filter(Boolean)
    .find((segment) => /^\d+$/.test(segment))
  return videoId ? `https://player.vimeo.com/video/${videoId}` : ''
}

const normalizeLoomEmbedUrl = (url) => {
  const segments = url.pathname.split('/').filter(Boolean)
  const shareIndex = segments.indexOf('share')
  const videoId = shareIndex >= 0 ? segments[shareIndex + 1] : segments.at(-1)
  return videoId ? `https://www.loom.com/embed/${videoId}` : ''
}

const projectVideo = computed(() => {
  const source = selectedProject.value?.video?.trim()
  if (!source) return null
  try {
    const url = new URL(source, window.location.origin)
    const pathname = url.pathname.toLowerCase()
    const isDirectVideo = directVideoExtensions.some((ext) => pathname.endsWith(ext))
    if (isDirectVideo) return { type: 'direct', source }
    if (url.hostname.includes('youtube.com') || url.hostname.includes('youtu.be')) {
      const embedUrl = normalizeYouTubeEmbedUrl(url)
      return embedUrl ? { type: 'embed', source: embedUrl } : null
    }
    if (url.hostname.includes('vimeo.com')) {
      const embedUrl = normalizeVimeoEmbedUrl(url)
      return embedUrl ? { type: 'embed', source: embedUrl } : null
    }
    if (url.hostname.includes('loom.com')) {
      const embedUrl = normalizeLoomEmbedUrl(url)
      return embedUrl ? { type: 'embed', source: embedUrl } : null
    }
  } catch (e) {
    console.warn('Invalid project video URL:', e)
  }
  return { type: 'embed', source }
})

const selectProject = (project) => {
  selectedProjectName.value = project.name
  if (window.innerWidth < 1024) {
    nextTick(() => {
      detailRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }
}

const stackItems = (project, keys) => {
  for (const key of keys) {
    const value = project?.[key]
    if (Array.isArray(value)) return value
    if (typeof value === 'string' && value.trim()) {
      return value
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
    }
  }
  return []
}

const techStack = computed(() =>
  stackItems(selectedProject.value, ['tech_stack', 'techStack', 'technologies', 'stack']),
)

const deploymentStack = computed(() =>
  stackItems(selectedProject.value, ['deployment_stack', 'deploymentStack', 'deployment']),
)

const stackIconLabel = (item) => {
  if (typeof item === 'string') return item
  return item?.name || item?.label || item?.icon || 'Technology'
}

watch(
  projects,
  (projectList) => {
    if (!projectList.some((project) => project.name === selectedProjectName.value)) {
      selectedProjectName.value = projectList[0]?.name || ''
    }
  },
  { immediate: true },
)

portfolioStore.loadProjects().catch(() => { })

watch(
  selectedProject,
  (project) => {
    setActiveProjectChatContext(project || null)
  },
  { immediate: true },
)

onUnmounted(() => {
  clearActiveProjectChatContext()
})
</script>

<template>
  <div class="pv-page">
    <div class="pv-wrap">

      <!-- ── Sidebar ── -->
      <aside class="pv-sidebar">
        <div class="pv-sidebar-header">
          <p class="section-label">// projects</p>
          <span v-if="!loading" class="pv-count">{{ projects.length }}</span>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="pv-list">
          <div class="pv-fetch-note">
            <span class="pv-fetch-dot"></span>
            fetching from GitHub
          </div>
          <div v-for="i in 3" :key="i" class="pv-skeleton-card"></div>
        </div>

        <!-- Loaded -->
        <div v-else class="pv-list">
          <button v-for="project in projects" :key="project.name" class="pv-item"
            :class="{ 'pv-item--active': selectedProject?.name === project.name }" @click="selectProject(project)">
            <div class="pv-item-top">
              <span class="pv-item-name">{{ project.name }}</span>
              <span class="pv-item-type">{{ project.type || 'project' }}</span>
            </div>
            <p class="pv-item-desc" v-html="project.description"></p>
          </button>
        </div>
      </aside>

      <!-- ── Error state ── -->
      <div v-if="loadError" class="pv-error">
        <p class="pv-error-label">// error</p>
        <p class="pv-error-msg">Couldn't reach GitHub right now.</p>
        <a href="https://github.com/TheBluCoder" target="_blank" rel="noopener noreferrer" class="pv-github-link">
          <GithubIcon class="pv-btn-icon" />
          View projects on GitHub
        </a>
      </div>

      <!-- ── Detail ── -->
      <main v-else-if="selectedProject" ref="detailRef" class="pv-detail">
        <div class="pv-detail-grid">

          <!-- ── Main column ── -->
          <div class="pv-main">

            <!-- Header -->
            <div class="pv-detail-head">
              <span class="pv-detail-type">{{ selectedProject.type || 'project' }}</span>
              <h1 class="pv-detail-name">{{ selectedProject.name }}</h1>
            </div>

            <!-- Media -->
            <div class="pv-media">
              <video v-if="projectVideo?.type === 'direct'" :src="projectVideo.source" :poster="selectedProject.image"
                class="pv-media-inner" controls preload="metadata" playsinline>Your browser does not support the video
                tag.</video>
              <iframe v-else-if="projectVideo?.type === 'embed'" :src="projectVideo.source"
                :title="`${selectedProject.name} demo`" class="pv-media-inner"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen></iframe>
              <img v-else :src="selectedProject.image" :alt="selectedProject.name" class="pv-media-inner pv-media-img"
                onerror="this.src='/placeholder-image.png'" />
            </div>

            <!-- Mobile-only: horizontal icon tiles right under media -->
            <div class="pv-tech-mobile">
              <div v-if="techStack.length" class="tech-tiles-h">
                <SkillIconTile
                  v-for="item in techStack"
                  :key="stackIconLabel(item)"
                  :skill="item"
                  compact
                  fallback-icon
                />
              </div>
              <div v-if="deploymentStack.length" class="deploy-row-h">
                <span class="deploy-label">on</span>
                <SkillIconTile
                  v-for="item in deploymentStack"
                  :key="stackIconLabel(item)"
                  :skill="item"
                  compact
                  fallback-icon
                />
              </div>
            </div>

            <!-- Links -->
            <div class="pv-links">
              <a v-if="selectedProject.demo" :href="selectedProject.demo" target="_blank" rel="noopener noreferrer"
                class="pv-btn pv-btn--primary">
                <ExternalLinkIcon class="pv-btn-icon" />
                Live demo
              </a>
              <a v-if="selectedProject.source_code_url" :href="selectedProject.source_code_url" target="_blank"
                rel="noopener noreferrer" class="pv-btn pv-btn--ghost">
                <GithubIcon class="pv-btn-icon" />
                View code
              </a>
            </div>

            <hr class="divider" />

            <!-- // what -->
            <section class="pv-section">
              <p class="section-label">// what</p>
              <div class="pv-prose" v-html="selectedProject.what || selectedProject.description"></div>
            </section>

            <!-- // why -->
            <template v-if="selectedProject.why">
              <hr class="divider" />
              <section class="pv-section">
                <p class="section-label">// why</p>
                <p class="pv-prose">{{ selectedProject.why }}</p>
              </section>
            </template>

            <!-- // how (mobile: in main flow; desktop: hidden, shown in right column) -->
            <template v-if="!techStack.length && !deploymentStack.length">
              <hr class="divider" />
              <section class="pv-section">
                <p class="section-label">// how</p>
                <p class="pv-empty">No stack metadata yet.</p>
              </section>
            </template>

            <!-- // impact -->
            <template v-if="selectedProject.impact">
              <hr class="divider" />
              <section class="pv-section">
                <p class="section-label">// impact</p>
                <p class="pv-prose">{{ selectedProject.impact }}</p>
              </section>
            </template>

            <p class="chat-hint">Want the deeper version? Ask about this project in the chat →</p>
            <div class="pv-footer"></div>
          </div>

          <!-- ── Desktop-only: floating vertical icon column ── -->
          <aside class="pv-tech-col" v-if="techStack.length || deploymentStack.length">
            <p class="section-label">// how</p>

            <div v-if="techStack.length" class="tech-tiles-v">
                <SkillIconTile
                  v-for="item in techStack"
                  :key="stackIconLabel(item)"
                  :skill="item"
                  compact
                  fallback-icon
                />
            </div>

            <template v-if="deploymentStack.length">
              <p class="deploy-label-v">deployed on</p>
              <div class="deploy-pills-v">
                <SkillIconTile
                  v-for="item in deploymentStack"
                  :key="stackIconLabel(item)"
                  :skill="item"
                  compact
                  fallback-icon
                />
              </div>
            </template>
          </aside>

        </div>
      </main>

    </div>
  </div>
</template>

<style scoped>
/* ── Page ── */
.pv-page {
  background: var(--theme-bg);
  color: var(--theme-text);
  min-height: 100%;
}

.pv-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 1.25rem;
}

/* ── Shared tokens ── */
.section-label {
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 1.25rem;
}

.divider {
  border: none;
  border-top: 1px solid rgb(var(--theme-white-rgb) / 0.05);
  margin: 2.25rem 0;
}

/* ── Sidebar ── */
.pv-sidebar {
  padding: 2.5rem 0;
  border-bottom: 1px solid rgb(var(--theme-white-rgb) / 0.05);
}

.pv-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.pv-count {
  font-family: ui-monospace, monospace;
  font-size: 0.75rem;
  color: var(--theme-text-barely);
}

.pv-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.pv-item {
  width: 100%;
  text-align: left;
  padding: 1rem 1rem 1rem 1.125rem;
  background: transparent;
  border: 1px solid rgb(var(--theme-white-rgb) / 0.04);
  border-left: 2px solid transparent;
  cursor: pointer;
  transition: background 0.15s, border-left-color 0.15s;
  color: inherit;
}

.pv-item:hover {
  background: rgb(var(--theme-white-rgb) / 0.02);
  border-left-color: rgb(var(--theme-accent-rgb) / 0.3);
}

.pv-item--active {
  background: rgb(var(--theme-accent-rgb) / 0.04);
  border-color: rgb(var(--theme-accent-rgb) / 0.1);
  border-left-color: var(--theme-accent);
}

.pv-item-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.45rem;
}

.pv-item-name {
  font-family: 'Syne', sans-serif;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--theme-text-faint);
  line-height: 1.3;
  flex: 1;
  transition: color 0.15s;
}

.pv-item:hover .pv-item-name,
.pv-item--active .pv-item-name {
  color: var(--theme-text);
}

.pv-item-type {
  font-family: ui-monospace, monospace;
  font-size: 0.625rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.06em;
  white-space: nowrap;
  padding-top: 2px;
  flex-shrink: 0;
}

.pv-item-desc {
  font-size: 0.8rem;
  color: var(--theme-text-hidden);
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Detail ── */
.pv-detail {
  padding: 2.5rem 0 0;
}

.pv-detail-head {
  margin-bottom: 1.5rem;
}

.pv-detail-type {
  display: block;
  font-family: ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-accent);
  letter-spacing: 0.1em;
  margin-bottom: 0.5rem;
}

.pv-detail-name {
  font-family: 'Syne', sans-serif;
  font-size: clamp(1.5rem, 4vw, 2.25rem);
  font-weight: 800;
  color: var(--theme-text);
  line-height: 1.15;
  letter-spacing: -0.02em;
}

/* ── Media ── */
.pv-media {
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: var(--theme-surface);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  margin-bottom: 1.25rem;
}

.pv-media-inner {
  width: 100%;
  height: 100%;
  display: block;
}

.pv-media-img {
  object-fit: cover;
}

/* ── Buttons ── */
.pv-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.625rem;
}

.pv-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.5rem 1.125rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 9999px;
  text-decoration: none;
  transition: background 0.15s, border-color 0.15s, transform 0.15s;
}

.pv-btn--primary {
  background: var(--theme-accent);
  color: var(--theme-on-accent);
  border: 1px solid var(--theme-accent);
}

.pv-btn--primary:hover {
  background: var(--theme-accent-hover);
  transform: translateY(-1px);
}

.pv-btn--ghost {
  background: transparent;
  color: var(--theme-text-muted);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.1);
}

.pv-btn--ghost:hover {
  background: rgb(var(--theme-white-rgb) / 0.04);
  color: var(--theme-text);
  border-color: rgb(var(--theme-white-rgb) / 0.18);
  transform: translateY(-1px);
}

.pv-btn-icon {
  width: 0.875rem;
  height: 0.875rem;
  flex-shrink: 0;
}

/* ── Section prose ── */
.pv-prose {
  font-size: 0.9375rem;
  color: var(--theme-text-dim);
  line-height: 1.8;
}

:deep(.pv-prose b),
:deep(.pv-prose strong) {
  color: var(--theme-text-soft);
  font-weight: 600;
}

:deep(.pv-prose a) {
  color: var(--theme-accent);
  text-decoration: none;
}

:deep(.pv-prose a:hover) {
  text-decoration: underline;
}

/* ── Tech pills ── */
.tech-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tech-pill {
  font-size: 0.8125rem;
  padding: 0.3rem 0.8rem;
  border-radius: 9999px;
  background: rgb(var(--theme-white-rgb) / 0.03);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.07);
  color: var(--theme-text-dim);
  cursor: default;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.tech-pill:hover {
  background: rgb(var(--theme-accent-rgb) / 0.08);
  border-color: rgb(var(--theme-accent-rgb) / 0.22);
  color: var(--theme-accent-soft);
}

/* ── Deployment ── */
.deploy-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.deploy-label {
  font-family: ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.08em;
}

.deploy-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.deploy-pill {
  font-size: 0.75rem;
  padding: 0.2rem 0.65rem;
  border-radius: 9999px;
  background: rgb(var(--theme-white-rgb) / 0.02);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  color: var(--theme-text-ghost);
}

.pv-empty {
  font-size: 0.875rem;
  color: var(--theme-text-barely);
}

/* ── Loading state ── */
.pv-fetch-note {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.06em;
  margin-bottom: 1rem;
}

.pv-fetch-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--theme-accent);
  flex-shrink: 0;
  animation: pulse-dot 1.4s ease-in-out infinite;
}

@keyframes pulse-dot {

  0%,
  100% {
    opacity: 0.3;
  }

  50% {
    opacity: 1;
  }
}

.pv-skeleton-card {
  height: 74px;
  border-radius: 4px;
  background: linear-gradient(90deg,
      rgb(var(--theme-white-rgb) / 0.02) 25%,
      rgb(var(--theme-white-rgb) / 0.04) 50%,
      rgb(var(--theme-white-rgb) / 0.02) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.6s infinite;
  border: 1px solid rgb(var(--theme-white-rgb) / 0.04);
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

/* ── Error state ── */
.pv-error {
  padding: 2.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.pv-error-label {
  font-family: ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.pv-error-msg {
  font-size: 0.9375rem;
  color: var(--theme-text-disabled);
}

.pv-github-link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.5rem 1.125rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 9999px;
  text-decoration: none;
  color: var(--theme-text-muted);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.1);
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  align-self: flex-start;
  margin-top: 0.25rem;
}

.pv-github-link:hover {
  background: rgb(var(--theme-white-rgb) / 0.04);
  color: var(--theme-text);
  border-color: rgb(var(--theme-white-rgb) / 0.18);
}

/* ── Chat hint ── */
.chat-hint {
  font-family: ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.06em;
  margin-top: 2.5rem;
}

.pv-footer {
  height: 3rem;
}

/* ── Desktop: sticky sidebar + scrolling detail ── */
@media (min-width: 1024px) {
  .pv-wrap {
    display: grid;
    grid-template-columns: 270px 1fr;
    gap: 0 3.5rem;
    align-items: start;
  }

  .pv-sidebar {
    position: sticky;
    top: 56px;
    max-height: calc(100vh - 56px);
    overflow-y: auto;
    padding: 2.5rem 2.5rem 2.5rem 0;
    border-bottom: none;
    border-right: 1px solid rgb(var(--theme-white-rgb) / 0.05);
    scrollbar-width: thin;
    scrollbar-color: rgb(var(--theme-white-rgb) / 0.05) transparent;
  }

  .pv-detail {
    padding: 2.5rem 0;
  }
}

/* ── Tech stack: shared ── */
.deploy-label {
  font-family: ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.08em;
}

/* Mobile: horizontal icon tiles, vertical column hidden */
.pv-tech-mobile {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  margin-bottom: 1.25rem;
}

.tech-tiles-h {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.85rem 0.625rem;
}

.deploy-row-h {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.375rem;
}

.pv-tech-col {
  display: none;
}

/* Desktop: vertical icon column, mobile strip hidden */
@media (min-width: 1024px) {
  .pv-detail-grid {
    display: grid;
    grid-template-columns: 1fr 112px;
    gap: 0 1.75rem;
    align-items: start;
  }

  .pv-tech-mobile {
    display: none;
  }

  .pv-tech-col {
    display: block;
    position: sticky;
    top: 76px;
    padding-top: 2.5rem;
  }

  .tech-tiles-v {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.875rem;
  }

  .deploy-label-v {
    font-family: ui-monospace, monospace;
    font-size: 0.5625rem;
    color: var(--theme-text-barely);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.375rem;
    margin-top: 0.25rem;
  }

  .deploy-pills-v {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .deploy-pill-v {
    font-size: 0.5625rem;
    padding: 0.25rem 0.375rem;
    text-align: center;
    border-radius: 4px;
    background: rgb(var(--theme-white-rgb) / 0.02);
    border: 1px solid rgb(var(--theme-white-rgb) / 0.05);
    color: var(--theme-text-ghost);
    word-break: break-word;
    line-height: 1.4;
  }
}
</style>
