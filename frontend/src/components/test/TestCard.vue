<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { TestRead } from '../../types/api'
import { TEST_TYPES } from '../../types/api'

defineProps<{
  test: TestRead
  projectId: number
}>()

const testTypeLabel = (type: string) =>
  TEST_TYPES[type as keyof typeof TEST_TYPES] ?? type
</script>

<template>
  <RouterLink
    :to="{ name: 'test', params: { projectId, testId: test.id } }"
    class="block rounded-xl border border-primary-800/40 bg-slate-900/50 p-5 hover:border-primary-600/50 hover:bg-slate-800/50 transition-colors"
  >
    <div class="flex items-start justify-between">
      <h3 class="font-medium text-slate-100">Тест #{{ test.id }}</h3>
      <span
        :class="{
          'bg-amber-900/40 text-amber-300': test.status === 'pending',
          'bg-primary-900/50 text-primary-300': test.status === 'done',
          'bg-red-900/40 text-red-300': test.status === 'failed',
          'bg-slate-700 text-slate-400': !['pending', 'done', 'failed'].includes(test.status),
        }"
        class="rounded-full px-2 py-0.5 text-xs"
      >
        {{ test.status }}
      </span>
    </div>
    <p class="mt-1 text-sm text-primary-300">{{ testTypeLabel(test.test_type) }}</p>
    <p v-if="test.started_at || test.ended_at" class="mt-1 text-xs text-slate-500">
      {{ test.started_at ? new Date(test.started_at).toLocaleString() : '—' }}
      —
      {{ test.ended_at ? new Date(test.ended_at).toLocaleString() : '—' }}
    </p>
    <p v-if="test.system_prompt" class="mt-2 text-sm text-slate-400 line-clamp-2">
      {{ test.system_prompt }}
    </p>
  </RouterLink>
</template>
