import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { testsApi } from '../api/client'
import type { TestRead, TestCreate } from '../types/api'

export const useTestsStore = defineStore('tests', () => {
  const tests = ref<TestRead[]>([])
  const currentTest = ref<TestRead | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const fetchTests = async (projectId?: number) => {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await testsApi.list(projectId)
      tests.value = data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Ошибка загрузки тестов'
    } finally {
      isLoading.value = false
    }
  }

  const fetchTest = async (id: number) => {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await testsApi.get(id)
      currentTest.value = data
      return data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Тест не найден'
      currentTest.value = null
      return null
    } finally {
      isLoading.value = false
    }
  }

  const createTest = async (payload: TestCreate) => {
    error.value = null
    try {
      const { data } = await testsApi.create(payload)
      tests.value.unshift(data)
      return data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Ошибка создания теста'
      throw e
    }
  }

  const runAnalysis = async (id: number) => {
    error.value = null
    try {
      const { data } = await testsApi.runAnalysis(id)
      await fetchTest(id)
      return data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Ошибка запуска анализа'
      throw e
    }
  }

  const deleteTest = async (id: number) => {
    error.value = null
    try {
      await testsApi.delete(id)
      tests.value = tests.value.filter((t) => t.id !== id)
      if (currentTest.value?.id === id) currentTest.value = null
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Ошибка удаления теста'
      throw e
    }
  }

  return {
    tests: computed(() => tests.value),
    currentTest: computed(() => currentTest.value),
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    fetchTests,
    fetchTest,
    createTest,
    runAnalysis,
    deleteTest,
  }
})
