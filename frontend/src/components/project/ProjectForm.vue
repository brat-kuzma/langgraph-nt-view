<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ProjectCreate, GrafanaSource, K8sConfig } from '../../types/api'

const props = defineProps<{
  initial?: Partial<ProjectCreate> | null
  submitLabel?: string
}>()

const emit = defineEmits<{
  submit: [data: ProjectCreate]
  cancel: []
}>()

const name = ref(props.initial?.name ?? '')
const description = ref(props.initial?.description ?? '')
const llmType = ref(props.initial?.llm_type ?? 'ollama')
const llmModel = ref(props.initial?.llm_model ?? 'qwen2.5:7b')
const llmApiKey = ref(props.initial?.llm_api_key ?? '')

const grafanaJson = ref(
  props.initial?.grafana_sources
    ? JSON.stringify(props.initial.grafana_sources, null, 2)
    : ''
)
const k8sJson = ref(
  props.initial?.k8s_config
    ? JSON.stringify(props.initial.k8s_config, null, 2)
    : ''
)

const grafanaSources = computed<GrafanaSource[] | null>(() => {
  if (!grafanaJson.value.trim()) return null
  try {
    const parsed = JSON.parse(grafanaJson.value)
    return Array.isArray(parsed) ? parsed : null
  } catch {
    return null
  }
})

const k8sConfig = computed<K8sConfig | null>(() => {
  if (!k8sJson.value.trim()) return null
  try {
    return JSON.parse(k8sJson.value)
  } catch {
    return null
  }
})

const submit = () => {
  emit('submit', {
    name: name.value,
    description: description.value || undefined,
    llm_type: llmType.value,
    llm_model: llmModel.value,
    llm_api_key: llmApiKey.value || undefined,
    grafana_sources: grafanaSources.value,
    k8s_config: k8sConfig.value,
  })
}

const hasJsonError = computed(() => {
  if (grafanaJson.value.trim()) {
    try {
      JSON.parse(grafanaJson.value)
    } catch {
      return true
    }
  }
  if (k8sJson.value.trim()) {
    try {
      JSON.parse(k8sJson.value)
    } catch {
      return true
    }
  }
  return false
})
</script>

<template>
  <form
    @submit.prevent="submit"
    class="rounded-xl border border-primary-800/40 bg-slate-900/50 p-6 space-y-4"
  >
    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">Название</label>
      <input
        v-model="name"
        required
        class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-primary-500 focus:outline-none"
        placeholder="Тестовый проект"
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">Описание</label>
      <textarea
        v-model="description"
        rows="2"
        class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-primary-500 focus:outline-none"
        placeholder="Описание проекта"
      />
    </div>

    <div class="grid gap-4 sm:grid-cols-2">
      <div>
        <label class="block text-sm font-medium text-slate-300 mb-1">LLM тип</label>
        <select
          v-model="llmType"
          class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 focus:border-primary-500 focus:outline-none"
        >
          <option value="ollama">Ollama</option>
          <option value="openai">OpenAI</option>
          <option value="gigachat">GigaChat</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-300 mb-1">LLM модель</label>
        <input
          v-model="llmModel"
          class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-primary-500 focus:outline-none"
          placeholder="qwen2.5:7b"
        />
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">LLM API ключ (если нужен)</label>
      <input
        v-model="llmApiKey"
        type="password"
        class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 placeholder-slate-500 focus:border-primary-500 focus:outline-none"
        placeholder="sk-..."
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1"
        >Grafana источники (JSON)</label
      >
      <textarea
        v-model="grafanaJson"
        rows="4"
        class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 font-mono text-sm text-slate-100 placeholder-slate-500 focus:border-primary-500 focus:outline-none"
        :class="{ 'border-red-500': grafanaJson && hasJsonError }"
        placeholder='[{"name":"business","url":"https://grafana.example.com","token":"YOUR_TOKEN"}]'
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1"
        >Kubernetes конфиг (JSON)</label
      >
      <textarea
        v-model="k8sJson"
        rows="4"
        class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 font-mono text-sm text-slate-100 placeholder-slate-500 focus:border-primary-500 focus:outline-none"
        :class="{ 'border-red-500': k8sJson && hasJsonError }"
        placeholder='{"server":"https://k8s.example.com","token":"YOUR_K8S_TOKEN"}'
      />
    </div>

    <div class="flex gap-3 pt-2">
      <button
        type="submit"
        :disabled="hasJsonError"
        class="px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white font-medium transition-colors"
      >
        {{ submitLabel ?? 'Сохранить' }}
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
