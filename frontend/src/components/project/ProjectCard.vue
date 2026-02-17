<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { ProjectRead } from '../../types/api'

defineProps<{
  project: ProjectRead
}>()
</script>

<template>
  <RouterLink
    :to="{ name: 'project', params: { id: project.id } }"
    class="block rounded-xl border border-primary-800/40 bg-slate-900/50 p-5 hover:border-primary-600/50 hover:bg-slate-800/50 transition-colors"
  >
    <h3 class="font-semibold text-slate-100">{{ project.name }}</h3>
    <p v-if="project.description" class="mt-1 text-sm text-slate-400 line-clamp-2">
      {{ project.description }}
    </p>
    <div class="mt-3 flex flex-wrap gap-2">
      <span
        class="rounded-full bg-primary-900/50 px-2 py-0.5 text-xs text-primary-300"
      >
        {{ project.llm_type }} / {{ project.llm_model }}
      </span>
      <span
        v-if="project.grafana_sources && project.grafana_sources.length"
        class="rounded-full bg-emerald-900/40 px-2 py-0.5 text-xs text-emerald-300"
      >
        Grafana
      </span>
      <span
        v-if="project.k8s_config"
        class="rounded-full bg-amber-900/40 px-2 py-0.5 text-xs text-amber-300"
      >
        K8s
      </span>
    </div>
  </RouterLink>
</template>
