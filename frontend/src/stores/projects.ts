import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectsApi } from '@/api'
import type { Project } from '@/types'

export const useProjectStore = defineStore('projects', () => {
  const projects = ref<Project[]>([])
  const current = ref<Project | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const data = await projectsApi.list()
      // data is PagedData<Project>
      projects.value = data?.items ?? data ?? []
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load projects'
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: string | number) {
    loading.value = true
    error.value = null
    try {
      current.value = await projectsApi.get(id)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load project'
    } finally {
      loading.value = false
    }
  }

  async function create(name: string, description?: string) {
    loading.value = true
    error.value = null
    try {
      const p = await projectsApi.create({ name, description })
      projects.value.unshift(p)
      return p
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to create project'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function remove(id: string | number) {
    await projectsApi.archive(id)
    projects.value = projects.value.filter(p => p.id !== id)
    if (current.value?.id === id) current.value = null
  }

  return { projects, current, loading, error, fetchAll, fetchOne, create, remove }
})
