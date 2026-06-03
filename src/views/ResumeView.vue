<script setup>
import { computed } from 'vue'
import { BriefcaseIcon, Code2Icon, DownloadIcon, GraduationCapIcon } from 'lucide-vue-next'
import experienceData from '@/data/experience.json'
import educationData from '@/data/education.json'
import techStackData from '@/data/techstack.json'

const resumeUrl = import.meta.env.VITE_RESUME_URL

const totalTechnologies = computed(() =>
  techStackData.reduce((count, stack) => count + stack.technologies.length, 0),
)
</script>

<template>
  <section class="min-h-screen w-full bg-black px-4 py-8 text-white md:px-8">
    <div class="mx-auto max-w-7xl">
      <header class="grid gap-8 border-b border-gray-800 pb-8 lg:grid-cols-[1.3fr_0.7fr]">
        <div>
          <p class="mb-3 text-sm uppercase tracking-wide text-blue-300">Resume</p>
          <h1 class="text-4xl font-bold text-white md:text-5xl">Ikeoluwa Oladele</h1>
          <p class="mt-4 max-w-3xl text-lg leading-8 text-gray-300">
            Software developer focused on practical systems, AI-assisted tooling, backend
            services, and cloud-ready applications.
          </p>
        </div>

        <div class="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
          <div class="border border-gray-800 bg-gray-950 p-4">
            <BriefcaseIcon class="mb-3 h-5 w-5 text-blue-300" />
            <p class="text-2xl font-semibold">{{ experienceData.length }}</p>
            <p class="text-sm text-gray-400">Experience entries</p>
          </div>
          <div class="border border-gray-800 bg-gray-950 p-4">
            <Code2Icon class="mb-3 h-5 w-5 text-green-300" />
            <p class="text-2xl font-semibold">{{ totalTechnologies }}</p>
            <p class="text-sm text-gray-400">Technologies listed</p>
          </div>
          <a
            :href="resumeUrl || '#'"
            target="_blank"
            rel="noopener noreferrer"
            download="Ikeoluwa_Oladele_Resume_SWE.pdf"
            class="flex items-center justify-between border border-blue-800 bg-blue-950/40 p-4 text-blue-100 transition hover:bg-blue-900/50"
          >
            <span>Download resume</span>
            <DownloadIcon class="h-5 w-5" />
          </a>
        </div>
      </header>

      <div class="grid gap-10 py-10 lg:grid-cols-[1fr_360px]">
        <main class="space-y-12">
          <section>
            <div class="mb-6 flex items-center gap-3">
              <BriefcaseIcon class="h-6 w-6 text-blue-300" />
              <h2 class="text-3xl font-bold">Experience</h2>
            </div>

            <div class="space-y-6">
              <article
                v-for="experience in experienceData"
                :key="`${experience.company}-${experience.jobTitle}`"
                class="border-l-2 border-blue-800 pl-5"
              >
                <div class="flex flex-wrap items-baseline justify-between gap-3">
                  <div>
                    <h3 class="text-2xl font-semibold text-orange-100">
                      {{ experience.jobTitle }}
                    </h3>
                    <p class="mt-1 text-gray-400">
                      {{ experience.company }} - {{ experience.position }}
                    </p>
                  </div>
                  <p class="text-sm text-gray-500">
                    {{ experience.dateStart }} - {{ experience.dateEnd }}
                  </p>
                </div>
                <ul class="mt-4 list-disc space-y-3 pl-5 text-gray-300">
                  <li v-for="task in experience.tasks" :key="task">{{ task }}</li>
                </ul>
              </article>
            </div>
          </section>

          <section>
            <div class="mb-6 flex items-center gap-3">
              <GraduationCapIcon class="h-6 w-6 text-blue-300" />
              <h2 class="text-3xl font-bold">Education</h2>
            </div>

            <article
              v-for="education in educationData"
              :key="`${education.institution}-${education.degree}`"
              class="border border-gray-800 bg-gray-950 p-5"
            >
              <h3 class="text-2xl font-semibold text-orange-100">{{ education.degree }}</h3>
              <p class="mt-2 text-gray-300">{{ education.program }}</p>
              <p class="mt-2 text-gray-400">
                {{ education.institution }} - {{ education.dateStart }} - {{ education.dateEnd }}
              </p>
              <p class="mt-2 text-gray-400">
                GPA: {{ education.gpa }} - {{ education.specialization }}
              </p>
            </article>
          </section>
        </main>

        <aside>
          <div class="sticky top-6 space-y-5">
            <section
              v-for="stack in techStackData"
              :key="stack.category"
              class="border border-gray-800 bg-gray-950 p-5"
            >
              <h2 class="text-xl font-semibold text-green-300">{{ stack.category }}</h2>
              <p class="mt-2 text-sm leading-6 text-gray-400">{{ stack.description }}</p>
              <div class="mt-4 flex flex-wrap gap-2">
                <span
                  v-for="tech in stack.technologies"
                  :key="tech.name"
                  class="border border-gray-700 px-2 py-1 text-sm text-gray-200"
                >
                  {{ tech.name }}
                </span>
              </div>
            </section>
          </div>
        </aside>
      </div>
    </div>
  </section>
</template>
