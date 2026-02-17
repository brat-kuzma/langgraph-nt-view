<script setup lang="ts">
import { onMounted } from 'vue'
import { useProjectsStore } from '../stores/projects'
import ProjectCard from '../components/project/ProjectCard.vue'
import ProjectForm from '../components/project/ProjectForm.vue'
import { ref } from 'vue'
import type { ProjectCreate } from '../types/api'

const store = useProjectsStore()
const showForm = ref(false)

onMounted(() => store.fetchProjects())

const handleCreate = async (data: ProjectCreate) => {
  await store.createProject(data)
  showForm.value = false
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold text-slate-100">Проекты</h1>
      <button
        type="button"
        @click="showForm = !showForm"
        class="px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-medium transition-colors"
      >
        {{ showForm ? 'Отмена' : '+ Новый проект' }}
      </button>
    </div>

    <ProjectForm
      v-if="showForm"
      submit-label="Создать"
      @submit="handleCreate"
      @cancel="showForm = false"
    />

    <p v-if="store.error" class="text-red-400 text-sm">{{ store.error }}</p>

    <div v-if="store.isLoading" class="text-slate-400">Загрузка...</div>

    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <ProjectCard
        v-for="project in store.projects"
        :key="project.id"
        :project="project"
      />
    </div>

    <div
      v-if="!store.isLoading && store.projects.length === 0 && !showForm"
      class="rounded-xl border border-primary-800/40 bg-primary-950/20 p-12 text-center text-slate-400"
    >
      Нет проектов. Создайте первый.
    </div>
  </div>
</template>
