<script setup>
import { inject } from 'vue'
import { storeToRefs } from 'pinia'
import {
  DownloadIcon,
  MessageCircleIcon,
  GithubIcon,
  LinkedinIcon,
  MailIcon,
  Code2Icon,
  BookOpenIcon,
} from 'lucide-vue-next'
import AboutSection from '@/components/home/AboutSection.vue'
import ExperienceSection from '@/components/home/ExperienceSection.vue'
import EducationSection from '@/components/home/EducationSection.vue'
import SkillsSection from '@/components/home/SkillsSection.vue'
import { usePortfolioStore } from '@/stores/portfolio'

const resumeUrl = import.meta.env.VITE_RESUME_URL
const openChat = inject('openChat', () => { })
const portfolioStore = usePortfolioStore()
const { resumeData, resumeLoading, resumeError } = storeToRefs(portfolioStore)

portfolioStore.loadResume().catch(() => {})
</script>

<template>
  <div class="home">

    <!-- ─── Hero ─── -->
    <section class="hero">
      <h1 class="hero-name">Ikeoluwa Oladele</h1>
      <div class="hero-accent-line"></div>

      <p class="hero-tagline">
        Software developer. Student. Occasional poet.
      </p>
      <p class="hero-sub">
        Algonquin College, Ottawa&thinsp;—&thinsp;graduating 2026
      </p>

      <div class="status-indicator">
        <span class="status-dot"></span>
        <span>open to new opportunities</span>
      </div>

      <div class="hero-actions">
        <a :href="resumeUrl || '#'" target="_blank" rel="noopener noreferrer" class="btn-primary">
          <DownloadIcon class="btn-icon" />
          Download resume
        </a>
        <button class="btn-secondary" @click="openChat">
          <MessageCircleIcon class="btn-icon" />
          Chat with me
        </button>
      </div>

      <div class="hero-socials">
        <a href="https://github.com/TheBluCoder" target="_blank" rel="noopener noreferrer" aria-label="GitHub"
          class="social-link">
          <GithubIcon class="social-icon" />
        </a>
        <a href="https://www.linkedin.com/in/ikeoluwa-oladele-15100820a/" target="_blank" rel="noopener noreferrer"
          aria-label="LinkedIn" class="social-link">
          <LinkedinIcon class="social-icon" />
        </a>
        <a href="mailto:oladeleikeoluwa508@gmail.com" aria-label="Email" class="social-link">
          <MailIcon class="social-icon" />
        </a>
      </div>
    </section>

    <!-- ─── Resume-driven sections ─── -->
    <AboutSection :content="resumeData?.about ?? null" :loading="resumeLoading" :error="resumeError" />

    <ExperienceSection
      v-if="resumeLoading || resumeData?.experience?.length"
      :entries="resumeData?.experience ?? []"
      :loading="resumeLoading"
    />

    <EducationSection
      v-if="resumeLoading || resumeData?.education?.length"
      :entries="resumeData?.education ?? []"
      :loading="resumeLoading"
    />

    <SkillsSection
      v-if="resumeLoading || resumeData?.skills?.length"
      :groups="resumeData?.skills ?? []"
      :loading="resumeLoading"
    />

    <!-- ─── Explore ─── -->
    <hr class="divider" />

    <section class="section">
      <p class="section-label">// explore</p>

      <div class="explore-grid">
        <router-link to="/projects" class="explore-card">
          <Code2Icon class="explore-card-icon" />
          <h3 class="explore-card-title">Projects</h3>
          <p class="explore-card-desc">What I build when I'm not studying</p>
          <span class="explore-card-cta">View all →</span>
        </router-link>

        <router-link to="/gallery" class="explore-card">
          <BookOpenIcon class="explore-card-icon" />
          <h3 class="explore-card-title">Gallery</h3>
          <p class="explore-card-desc">Poems, books, and things that rhyme</p>
          <span class="explore-card-cta">Explore →</span>
        </router-link>
      </div>
    </section>

    <div class="page-footer-space"></div>
  </div>
</template>

<style scoped>
/* ── Layout ── */
.home {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 1.25rem;
}

/* ── Hero ── */
.hero {
  padding: 4rem 0 3.5rem;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.hero-name {
  font-family: 'Syne', sans-serif;
  font-size: clamp(2.75rem, 9vw, 5rem);
  font-weight: 800;
  line-height: 1.04;
  letter-spacing: -0.025em;
  color: var(--theme-text);
  margin-bottom: 0.5rem;
  animation: fadeUp 0.65s ease both;
}

.hero-accent-line {
  height: 2px;
  width: 0;
  background: rgb(var(--theme-accent-rgb) / 0.5);
  border-radius: 2px;
  margin-bottom: 1.25rem;
  animation: drawLine 0.5s 0.45s ease-out both;
}

.hero-tagline {
  font-size: 1.0625rem;
  color: var(--theme-text-muted);
  line-height: 1.6;
  margin-bottom: 0.375rem;
  animation: fadeUp 0.55s 0.12s ease both;
}

.hero-sub {
  font-size: 0.8125rem;
  color: var(--theme-text-ghost);
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  margin-bottom: 0.75rem;
  animation: fadeUp 0.55s 0.22s ease both;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  color: var(--theme-text-ghost);
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  margin-bottom: 1.875rem;
  animation: fadeUp 0.5s 0.3s ease both;
}

.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--theme-success);
  flex-shrink: 0;
  animation: pulseDot 2.5s ease-in-out infinite;
}

/* CTAs */
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 2rem;
  animation: fadeUp 0.55s 0.38s ease both;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.3rem;
  background: var(--theme-accent);
  color: var(--theme-white);
  border: none;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s, transform 0.15s;
}

.btn-primary:hover {
  background: var(--theme-accent-hover);
  transform: translateY(-1px);
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.3rem;
  background: transparent;
  color: var(--theme-text-muted);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.1);
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.btn-secondary:hover {
  background: rgb(var(--theme-white-rgb) / 0.04);
  color: var(--theme-text);
  border-color: rgb(var(--theme-white-rgb) / 0.18);
}

.btn-icon {
  width: 0.9375rem;
  height: 0.9375rem;
  flex-shrink: 0;
}

/* Socials */
.hero-socials {
  display: flex;
  gap: 1rem;
  align-items: center;
  animation: fadeUp 0.5s 0.52s ease both;
}

.social-link {
  color: var(--theme-text-hidden);
  display: flex;
  transition: color 0.15s;
}

.social-link:hover {
  color: var(--theme-text-subtle);
}

.social-icon {
  width: 1.125rem;
  height: 1.125rem;
}

/* ── Shared divider (between sections and explore) ── */
.divider {
  border: none;
  border-top: 1px solid rgb(var(--theme-white-rgb) / 0.05);
  margin: 3rem 0;
}

/* ── Section label ── */
.section-label {
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 1.75rem;
}

/* ── Explore ── */
.explore-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.explore-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.5rem;
  background: rgb(var(--theme-white-rgb) / 0.02);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  border-radius: 10px;
  text-decoration: none;
  transition: background 0.2s, border-color 0.2s, transform 0.2s;
}

.explore-card:hover {
  background: rgb(var(--theme-accent-rgb) / 0.05);
  border-color: rgb(var(--theme-accent-rgb) / 0.18);
  transform: translateY(-2px);
}

.explore-card-icon {
  width: 1.375rem;
  height: 1.375rem;
  color: var(--theme-accent);
  opacity: 0.7;
  margin-bottom: 0.25rem;
}

.explore-card-title {
  font-family: 'Syne', sans-serif;
  font-size: 1.0625rem;
  font-weight: 700;
  color: var(--theme-text);
}

.explore-card-desc {
  font-size: 0.875rem;
  color: var(--theme-text-faint);
  flex: 1;
  line-height: 1.5;
}

.explore-card-cta {
  font-size: 0.8125rem;
  color: var(--theme-accent);
  font-family: ui-monospace, monospace;
  margin-top: 0.25rem;
}

.page-footer-space {
  height: 3rem;
}

/* ── Mobile ── */
@media (max-width: 640px) {
  .hero {
    padding: 2.5rem 0;
  }

  .explore-grid {
    grid-template-columns: 1fr;
  }
}

/* ── Entrance animations ── */
@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(14px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes drawLine {
  from {
    width: 0;
  }

  to {
    width: 2.5rem;
  }
}

@keyframes pulseDot {

  0%,
  100% {
    opacity: 0.5;
    box-shadow: 0 0 0 0 rgb(var(--theme-success-rgb) / 0);
  }

  50% {
    opacity: 1;
    box-shadow: 0 0 0 3px rgb(var(--theme-success-rgb) / 0.12);
  }
}

@media (prefers-reduced-motion: reduce) {

  .hero-name,
  .hero-accent-line,
  .hero-tagline,
  .hero-sub,
  .status-indicator,
  .hero-actions,
  .hero-socials {
    animation: none;
    opacity: 1;
    transform: none;
  }

  .hero-accent-line {
    width: 2.5rem;
  }

  .status-dot {
    animation: none;
  }
}
</style>
