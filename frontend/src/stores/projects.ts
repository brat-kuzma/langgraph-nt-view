import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectsApi } from '../api/client'
import type { ProjectRead, ProjectCreate } from '../types/api'

export const useProjectsStore = defineStore('projects', () => {
  const projects = ref<ProjectRead[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const fetchProjects = async () => {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await projectsApi.list()
      projects.value = data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Ошибка загрузки проектов'
    } finally {
      isLoading.value = false
    }
  }

  const createProject = async (payload: ProjectCreate) => {
    error.value = null
    try {
      const { data } = await projectsApi.create(payload)
      projects.value.push(data)
      return data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Ошибка создания проекта'
      throw e
    }
  }

  const updateProject = async (id: number, payload: Partial<ProjectCreate>) => {
    error.value = null
    try {
      const { data } = await projectsApi.update(id, payload)
      const idx = projects.value.findIndex((p) => p.id === id)
      if (idx >= 0) projects.value[idx] = data
      return data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Ошибка обновления проекта'
      throw e
    }
  }

  const deleteProject = async (id: number) => {
    error.value = null
    try {
      await projectsApi.delete(id)
      projects.value = projects.value.filter((p) => p.id !== id)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Ошибка удаления проекта'
      throw e
    }
  }

  const getProject = async (id: number) => {
    try {
      const { data } = await projectsApi.get(id)
      return data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Проект не найден'
      return null
    }
  }

  return {
    projects: computed(() => projects.value),
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    getProject,
  }
})
