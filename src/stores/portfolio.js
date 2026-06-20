import { ref } from 'vue'
import { defineStore } from 'pinia'

export const usePortfolioStore = defineStore('portfolio', () => {
  const resumeData = ref(null)
  const resumeLoading = ref(false)
  const resumeError = ref(false)
  const projects = ref([])
  const projectsLoading = ref(false)
  const projectsError = ref(false)

  let resumeRequest = null
  let projectsRequest = null

  const loadResume = (force = false) => {
    if (resumeRequest) return resumeRequest
    if (resumeData.value && !force) return Promise.resolve(resumeData.value)

    resumeLoading.value = true
    resumeError.value = false
    const apiBase = import.meta.env.VITE_API_BASE_URL || ''

    resumeRequest = fetch(`${apiBase}/api/resume`)
      .then((response) => {
        if (!response.ok) throw new Error(`Resume request failed: ${response.status}`)
        return response.json()
      })
      .then((data) => {
        resumeData.value = data
        return data
      })
      .catch((error) => {
        resumeError.value = true
        throw error
      })
      .finally(() => {
        resumeLoading.value = false
        resumeRequest = null
      })

    return resumeRequest
  }

  const loadProjects = (force = false) => {
    if (projectsRequest) return projectsRequest
    if (projects.value.length && !force) return Promise.resolve(projects.value)

    projectsLoading.value = true
    projectsError.value = false
    const projectsUrl = import.meta.env.VITE_PROJECTS_URL || '/api/projects'

    projectsRequest = fetch(projectsUrl)
      .then((response) => {
        if (!response.ok) throw new Error(`Projects request failed: ${response.status}`)
        return response.json()
      })
      .then((data) => {
        if (!Array.isArray(data.projects) || data.projects.length === 0) {
          throw new Error('Projects response did not contain any projects')
        }
        projects.value = data.projects
        return projects.value
      })
      .catch((error) => {
        projectsError.value = true
        throw error
      })
      .finally(() => {
        projectsLoading.value = false
        projectsRequest = null
      })

    return projectsRequest
  }

  return {
    resumeData,
    resumeLoading,
    resumeError,
    projects,
    projectsLoading,
    projectsError,
    loadResume,
    loadProjects,
  }
})
