<script setup>
import { ref, computed, provide, watch } from 'vue'
import { useRoute } from 'vue-router'
import { MessageCircleIcon, HomeIcon, Code2Icon, BookOpenIcon } from 'lucide-vue-next'
import ChatBox from '@/components/ChatBox.vue'

const route = useRoute()
const isChatOpen = ref(false)
const chatProjectContext = ref(null)
const activeProjectContext = ref(null)

const navLinks = [
  { to: '/', label: 'home', icon: HomeIcon, exact: true },
  { to: '/projects', label: 'projects', icon: Code2Icon, exact: false },
  { to: '/gallery', label: 'gallery', icon: BookOpenIcon, exact: false },
]

const isActive = (link) =>
  link.exact ? route.path === link.to : route.path.startsWith(link.to)

const openGlobalChat = () => {
  chatProjectContext.value = activeProjectContext.value
  isChatOpen.value = true
}

const closeChat = () => {
  isChatOpen.value = false
  chatProjectContext.value = null
}

const hasProjectContext = computed(() => !!activeProjectContext.value)

const askBtnLabel = computed(() => {
  if (!activeProjectContext.value?.name) return 'ask me anything →'
  const name = activeProjectContext.value.name
  const short = name.length > 24 ? name.slice(0, 24).trimEnd() + '…' : name
  return `chat about ${short} →`
})

watch(() => route.path, () => { if (isChatOpen.value) closeChat() })

provide('openChat', openGlobalChat)
provide('setActiveProjectChatContext', (project) => { activeProjectContext.value = project })
provide('clearActiveProjectChatContext', () => { activeProjectContext.value = null })
</script>

<template>
  <div class="layout-root">
    <!-- ── Desktop top nav ── -->
    <header class="top-nav">
      <router-link to="/" class="logo">ike.</router-link>

      <nav class="desktop-links">
        <router-link
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          class="desktop-link"
          :class="{ 'desktop-link--active': isActive(link) }"
        >{{ link.label }}</router-link>
      </nav>

      <button
        class="ask-btn"
        :class="{ 'ask-btn--active': hasProjectContext }"
        @click="openGlobalChat"
      >{{ askBtnLabel }}</button>
    </header>

    <!-- ── Mobile top bar (logo only) ── -->
    <header class="mobile-top">
      <router-link to="/" class="logo">ike.</router-link>
    </header>

    <!-- ── Page content ── -->
    <main class="main-content">
      <slot />
    </main>

    <!-- ── Mobile bottom nav ── -->
    <nav class="bottom-nav">
      <router-link
        v-for="link in navLinks"
        :key="link.to"
        :to="link.to"
        class="bottom-link"
        :class="{ 'bottom-link--active': isActive(link) }"
      >
        <component :is="link.icon" class="bottom-link-icon" />
        <span>{{ link.label }}</span>
      </router-link>
    </nav>

    <!-- ── Mobile chat FAB ── -->
    <button
      class="chat-fab"
      :class="{ 'chat-fab--active': hasProjectContext }"
      @click="openGlobalChat"
      aria-label="Open chat"
    >
      <MessageCircleIcon class="h-5 w-5" />
      <span v-if="hasProjectContext" class="chat-fab-dot"></span>
    </button>

    <!-- ── Chat backdrop (mobile) ── -->
    <div v-if="isChatOpen" class="chat-backdrop" @click="closeChat" />

    <!-- ── Chat panel ── -->
    <ChatBox :is-open="isChatOpen" :project-context="chatProjectContext" @close="closeChat" />
  </div>
</template>

<style scoped>
/* ── Palette tokens ── */
.layout-root {
  min-height: 100vh;
  background: var(--theme-bg);
  color: var(--theme-text);
}

/* ── Top nav (desktop only) ── */
.top-nav {
  display: none; /* hidden on mobile */
}
@media (min-width: 768px) {
  .top-nav {
    display: flex;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 40;
    height: 56px;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
    background: rgb(var(--theme-bg-rgb) / 0.88);
    border-bottom: 1px solid rgb(var(--theme-white-rgb) / 0.06);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
  }
}

/* ── Mobile top bar (mobile only) ── */
.mobile-top {
  display: flex; /* shown on mobile */
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 40;
  height: 48px;
  align-items: center;
  padding: 0 1.25rem;
  background: rgb(var(--theme-bg-rgb) / 0.95);
  border-bottom: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
@media (min-width: 768px) {
  .mobile-top { display: none; }
}

/* ── Logo ── */
.logo {
  font-family: 'Syne', sans-serif;
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--theme-text);
  text-decoration: none;
  transition: opacity 0.15s;
  flex-shrink: 0;
}
.logo:hover { opacity: 0.7; }

/* ── Desktop nav links ── */
.desktop-links {
  display: flex;
  align-items: center;
  gap: 2.5rem;
}

.desktop-link {
  font-size: 0.875rem;
  letter-spacing: 0.02em;
  color: var(--theme-text-faint);
  text-decoration: none;
  padding-bottom: 2px;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.desktop-link:hover { color: var(--theme-accent-muted); }
.desktop-link--active {
  color: var(--theme-text);
  border-bottom-color: var(--theme-accent);
}

/* ── Ask button ── */
.ask-btn {
  font-size: 0.8125rem;
  padding: 0.4rem 1.1rem;
  border-radius: 9999px;
  background: rgb(var(--theme-accent-rgb) / 0.1);
  border: 1px solid rgb(var(--theme-accent-rgb) / 0.25);
  color: var(--theme-accent-soft);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, color 0.2s,
              box-shadow 0.2s, transform 0.15s;
  white-space: nowrap;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ask-btn:hover {
  background: rgb(var(--theme-accent-rgb) / 0.18);
  border-color: rgb(var(--theme-accent-rgb) / 0.4);
}

/* Project-context active state */
.ask-btn--active {
  background: var(--theme-accent);
  border-color: var(--theme-accent);
  color: var(--theme-white);
  box-shadow: 0 0 16px rgb(var(--theme-accent-rgb) / 0.35);
  animation: btnPop 0.35s ease;
}
.ask-btn--active:hover {
  background: var(--theme-accent-hover);
  border-color: var(--theme-accent-hover);
  box-shadow: 0 0 20px rgb(var(--theme-accent-rgb) / 0.5);
  transform: translateY(-1px);
}

@keyframes btnPop {
  0%   { transform: scale(1); }
  45%  { transform: scale(1.05); }
  100% { transform: scale(1); }
}

/* ── Main content ── */
.main-content {
  padding-top: 48px;  /* mobile: clears mobile top bar */
  padding-bottom: 64px; /* mobile: clears bottom nav */
}
@media (min-width: 768px) {
  .main-content {
    padding-top: 56px;  /* desktop: clears top nav */
    padding-bottom: 0;
  }
}

/* ── Bottom nav (mobile only) ── */
.bottom-nav {
  display: flex; /* shown on mobile */
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 40;
  height: 64px;
  align-items: center;
  justify-content: space-around;
  background: rgb(var(--theme-bg-rgb) / 0.97);
  border-top: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}
@media (min-width: 768px) {
  .bottom-nav { display: none; }
}

.bottom-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 0.5rem 1.25rem;
  color: var(--theme-text-hidden);
  text-decoration: none;
  font-size: 0.6875rem;
  letter-spacing: 0.04em;
  transition: color 0.15s;
  min-width: 64px;
}
.bottom-link:hover { color: var(--theme-text-dim); }
.bottom-link--active { color: var(--theme-accent); }
.bottom-link-icon { width: 1.25rem; height: 1.25rem; }

/* ── Chat FAB (mobile only) ── */
.chat-fab {
  display: flex; /* shown on mobile */
  position: fixed;
  bottom: 80px;
  right: 1rem;
  z-index: 50;
  width: 44px;
  height: 44px;
  border-radius: 9999px;
  align-items: center;
  justify-content: center;
  background: var(--theme-accent);
  color: var(--theme-white);
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 20px rgb(var(--theme-accent-rgb) / 0.4);
  transition: transform 0.15s, box-shadow 0.15s;
}
.chat-fab:active { transform: scale(0.94); }

.chat-fab--active {
  box-shadow: 0 4px 24px rgb(var(--theme-accent-rgb) / 0.65);
  animation: btnPop 0.35s ease;
}

/* Notification dot on the FAB */
.chat-fab-dot {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--theme-success);
  border: 2px solid var(--theme-bg);
  animation: pulseDot 2.5s ease-in-out infinite;
}

@keyframes pulseDot {
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50%       { opacity: 1;   transform: scale(1.2); }
}

@media (min-width: 768px) {
  .chat-fab { display: none; }
}

/* ── Chat backdrop ── */
.chat-backdrop {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgb(var(--theme-black-rgb) / 0.25);
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}

@media (min-width: 768px) {
  .chat-backdrop {
    background: transparent;
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
  }
}
</style>
