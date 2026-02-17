<script setup lang="ts">
import { ref } from 'vue'
import type { TestCreate, TestType } from '../../types/api'
import { TEST_TYPES } from '../../types/api'

const props = defineProps<{
  projectId: number
}>()

const emit = defineEmits<{
  submit: [data: TestCreate]
  cancel: []
}>()

const testType = ref<TestType>('max_search')
const startedAt = ref('')
const endedAt = ref('')
const systemPrompt = ref('')

const testTypeOptions = Object.entries(TEST_TYPES).map(([value, label]) => ({ value, label }))

const submit = () => {
  emit('submit', {
    project_id: props.projectId,
    test_type: testType.value,
    started_at: startedAt.value ? new Date(startedAt.value).toISOString() : undefined,
    ended_at: endedAt.value ? new Date(endedAt.value).toISOString() : undefined,
    system_prompt: systemPrompt.value || undefined,
  })
}

const formatDateTimeLocal = (d: Date) => {
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const setDefaultTimeRange = () => {
  const now = new Date()
  const start = new Date(now)
  start.setHours(start.getHours() - 2)
  startedAt.value = formatDateTimeLocal(start)
  endedAt.value = formatDateTimeLocal(now)
}
</script>

<template>
  <form
    @submit.prevent="submit"
    class="rounded-xl border border-primary-800/40 bg-slate-900/50 p-6 space-y-4"
  >
    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">Тип теста</label>
      <select
        v-model="testType"
        class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 focus:border-primary-500 focus:outline-none"
      >
        <option v-for="opt in testTypeOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <div class="grid gap-4 sm:grid-cols-2">
      <div>
        <label class="block text-sm font-medium text-slate-300 mb-1">Начало</label>
        <input
          v-model="startedAt"
          type="datetime-local"
          class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 focus:border-primary-500 focus:outline-none"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-300 mb-1">Окончание</label>
        <div class="flex gap-2">
          <input
            v-model="endedAt"
            type="datetime-local"
            class="flex-1 rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 focus:border-primary-500 focus:outline-none"
          />
          <button
            type="button"
            @click="setDefaultTimeRange"
            class="px-3 py-2 rounded-lg border border-slate-600 text-slate-400 hover:bg-slate-800 text-sm"
            title="Последние 2 часа"
          >
            +2ч
          </button>
        </div>
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1"
        >Системный промпт (особенности системы для агента)</label
      >
      <textarea
        v-model="systemPrompt"
        rows="4"
        class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-primary-500 focus:outline-none"
        placeholder="Система X, акцент на памяти и GC..."
      />
    </div>

    <div class="flex gap-3 pt-2">
      <button
        type="submit"
        class="px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-medium transition-colors"
      >
        Создать тест
      </button>
      <button
        type="button"
        @click="emit('cancel')"
        class="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-800 transition-colors"
      >
        Отмена
      </button>
    </div>
  </form>
</template>
