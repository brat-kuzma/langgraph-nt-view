<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectsStore } from '../stores/projects'
import { useTestsStore } from '../stores/tests'
import ProjectForm from '../components/project/ProjectForm.vue'
import TestCard from '../components/test/TestCard.vue'
import TestForm from '../components/test/TestForm.vue'
import type { ProjectCreate } from '../types/api'
import type { TestCreate } from '../types/api'

const route = useRoute()
const router = useRouter()
const projectsStore = useProjectsStore()
const testsStore = useTestsStore()

const projectId = computed(() => Number(route.params.id))
const project = ref<Awaited<ReturnType<typeof projectsStore.getProject>>>(null)
const showEditForm = ref(false)
const showTestForm = ref(false)

const loadProject = async () => {
  if (!projectId.value) return
  project.value = await projectsStore.getProject(projectId.value)
}

const loadTests = async () => {
  if (!projectId.value) return
  await testsStore.fetchTests(projectId.value)
}

onMounted(() => {
  loadProject()
  loadTests()
})

watch(projectId, () => {
  loadProject()
  loadTests()
})

const handleUpdate = async (data: ProjectCreate) => {
  if (!projectId.value) return
  await projectsStore.updateProject(projectId.value, data)
  showEditForm.value = false
  await loadProject()
}

const handleCreateTest = async (data: TestCreate) => {
  await testsStore.createTest({ ...data, project_id: projectId.value })
  showTestForm.value = false
}

const handleDeleteProject = async () => {
  if (!projectId.value || !confirm('Удалить проект и все связанные тесты?')) return
  await projectsStore.deleteProject(projectId.value)
  router.push('/')
}
</script>

<template>
  <div v-if="project" class="space-y-8">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-semibold text-slate-100">{{ project.name }}</h1>
        <p v-if="project.description" class="mt-1 text-slate-400">{{ project.description }}</p>
      </div>
      <div class="flex gap-2">
        <button
          @click="showEditForm = !showEditForm"
          class="px-4 py-2 rounded-lg border border-primary-600 text-primary-300 hover:bg-primary-900/30 transition-colors"
        >
          {{ showEditForm ? 'Отмена' : 'Редактировать' }}
        </button>
        <button
          @click="handleDeleteProject"
          class="px-4 py-2 rounded-lg border border-red-800 text-red-400 hover:bg-red-900/20 transition-colors"
        >
          Удалить
        </button>
      </div>
    </div>

    <ProjectForm
      v-if="showEditForm"
      :initial="project"
      submit-label="Сохранить"
      @submit="handleUpdate"
      @cancel="showEditForm = false"
    />

    <section v-if="!showEditForm" class="rounded-xl border border-primary-800/40 bg-slate-900/50 p-5">
      <h2 class="text-sm font-medium text-slate-400 mb-2">Конфигурация</h2>
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 text-sm">
        <div>
          <span class="text-slate-500">LLM:</span>
          <span class="ml-2 text-slate-300">{{ project.llm_type }} / {{ project.llm_model }}</span>
        </div>
        <div v-if="project.grafana_sources?.length">
          <span class="text-slate-500">Grafana:</span>
          <span class="ml-2 text-slate-300">{{ project.grafana_sources.length }} источник(ов)</span>
        </div>
        <div v-if="project.k8s_config">
          <span class="text-slate-500">Kubernetes:</span>
          <span class="ml-2 text-emerald-400">настроен</span>
        </div>
      </div>
    </section>

    <section>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-medium text-slate-200">Тесты</h2>
        <button
          @click="showTestForm = !showTestForm"
          class="px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-medium transition-colors"
        >
          {{ showTestForm ? 'Отмена' : '+ Новый тест' }}
        </button>
      </div>

      <TestForm
        v-if="showTestForm"
        :project-id="projectId"
        @submit="handleCreateTest"
        @cancel="showTestForm = false"
      />

      <p v-if="testsStore.error" class="text-red-400 text-sm">{{ testsStore.error }}</p>

      <div v-if="testsStore.isLoading" class="text-slate-400">Загрузка тестов...</div>

      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <TestCard
          v-for="test in testsStore.tests"
          :key="test.id"
          :test="test"
          :project-id="projectId"
        />
      </div>

      <div
        v-if="!testsStore.isLoading && testsStore.tests.length === 0 && !showTestForm"
        class="rounded-xl border border-primary-800/40 bg-primary-950/20 p-8 text-center text-slate-400"
      >
        Нет тестов. Создайте первый тест.
      </div>
    </section>
  </div>

  <div v-else class="text-slate-400">Загрузка проекта...</div>
</template>
