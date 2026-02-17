<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTestsStore } from '../stores/tests'
import { artifactsApi, reportsApi, collectApi } from '../api/client'
import { TEST_TYPES } from '../types/api'
import { ARTIFACT_KINDS } from '../types/api'

const route = useRoute()
const router = useRouter()
const testsStore = useTestsStore()

const projectId = computed(() => Number(route.params.projectId))
const testId = computed(() => Number(route.params.testId))

const test = ref<Awaited<ReturnType<typeof testsStore.fetchTest>>>(null)
const artifacts = ref<Awaited<ReturnType<typeof artifactsApi.list>>['data']>([])
const report = ref<Awaited<ReturnType<typeof reportsApi.get>>['data'] | null>(null)
const reportText = ref<string | null>(null)

const isLoadingArtifacts = ref(false)
const isLoadingReport = ref(false)
const isRunningAnalysis = ref(false)
const isUploading = ref(false)
const collectGrafanaLoading = ref(false)
const collectK8sLoading = ref(false)

// Collect forms
const grafanaFrom = ref('')
const grafanaTo = ref('')
const grafanaDashboardUid = ref('')
const grafanaSourceIndex = ref(0)
const k8sFrom = ref('')
const k8sTo = ref('')
const k8sNamespace = ref('')

// Upload
const uploadKind = ref('custom_java_log')
const uploadFile = ref<File | null>(null)
const uploadDisplayName = ref('')

const loadTest = async () => {
  test.value = await testsStore.fetchTest(testId.value)
}

const loadArtifacts = async () => {
  isLoadingArtifacts.value = true
  try {
    const { data } = await artifactsApi.list(testId.value)
    artifacts.value = data
  } catch {
    artifacts.value = []
  } finally {
    isLoadingArtifacts.value = false
  }
}

const loadReport = async () => {
  isLoadingReport.value = true
  report.value = null
  reportText.value = null
  try {
    const [r, rt] = await Promise.all([
      reportsApi.get(testId.value),
      reportsApi.getText(testId.value),
    ])
    report.value = r.data
    reportText.value = typeof rt.data === 'string' ? rt.data : null
  } catch {
    report.value = null
    reportText.value = null
  } finally {
    isLoadingReport.value = false
  }
}

onMounted(() => {
  loadTest()
  loadArtifacts()
  loadReport()
})

watch(testId, () => {
  loadTest()
  loadArtifacts()
  loadReport()
})

const runAnalysis = async () => {
  isRunningAnalysis.value = true
  try {
    await testsStore.runAnalysis(testId.value)
    await loadTest()
    await loadReport()
  } finally {
    isRunningAnalysis.value = false
  }
}

const downloadAllArtifacts = async () => {
  try {
    const { data } = await artifactsApi.downloadAll(testId.value)
    const url = URL.createObjectURL(data as Blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `test_${testId.value}_artifacts.zip`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    alert(e instanceof Error ? e.message : 'Ошибка скачивания')
  }
}

const deleteAllArtifacts = async () => {
  if (!confirm('Удалить все артефакты теста?')) return
  try {
    await artifactsApi.deleteAll(testId.value)
    await loadArtifacts()
  } catch (e) {
    alert(e instanceof Error ? e.message : 'Ошибка удаления')
  }
}

const uploadArtifact = async () => {
  if (!uploadFile.value) return
  isUploading.value = true
  try {
    await artifactsApi.upload(
      testId.value,
      uploadFile.value,
      uploadKind.value,
      uploadDisplayName.value || undefined
    )
    uploadFile.value = null
    uploadDisplayName.value = ''
    await loadArtifacts()
  } catch (e) {
    alert(e instanceof Error ? e.message : 'Ошибка загрузки')
  } finally {
    isUploading.value = false
  }
}

const collectGrafana = async () => {
  if (!grafanaFrom.value || !grafanaTo.value || !grafanaDashboardUid.value) return
  collectGrafanaLoading.value = true
  try {
    await collectApi.grafana(testId.value, {
      from_ts: grafanaFrom.value,
      to_ts: grafanaTo.value,
      dashboard_uid: grafanaDashboardUid.value,
      grafana_source_index: grafanaSourceIndex.value,
    })
    await loadArtifacts()
  } catch (e) {
    alert(e instanceof Error ? e.message : 'Ошибка сбора Grafana')
  } finally {
    collectGrafanaLoading.value = false
  }
}

const collectK8s = async () => {
  if (!k8sFrom.value || !k8sTo.value) return
  collectK8sLoading.value = true
  try {
    await collectApi.kubernetes(testId.value, {
      from_ts: k8sFrom.value,
      to_ts: k8sTo.value,
      namespace: k8sNamespace.value || undefined,
    })
    await loadArtifacts()
  } catch (e) {
    alert(e instanceof Error ? e.message : 'Ошибка сбора K8s')
  } finally {
    collectK8sLoading.value = false
  }
}

const deleteTest = async () => {
  if (!confirm('Удалить тест и все артефакты?')) return
  try {
    await testsStore.deleteTest(testId.value)
    router.push({ name: 'project', params: { id: projectId.value } })
  } catch (e) {
    alert(e instanceof Error ? e.message : 'Ошибка удаления')
  }
}

const testTypeLabel = (type: string) => TEST_TYPES[type as keyof typeof TEST_TYPES] ?? type
const artifactKindLabel = (kind: string) =>
  ARTIFACT_KINDS[kind as keyof typeof ARTIFACT_KINDS] ?? kind

const pdfUrl = computed(() => `/api/reports/test/${testId.value}/pdf`)
</script>

<template>
  <div v-if="test" class="space-y-8">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <div class="flex items-center gap-3">
          <router-link
            :to="{ name: 'project', params: { id: projectId } }"
            class="text-slate-400 hover:text-primary-300 text-sm"
          >
            ← Назад
          </router-link>
          <h1 class="text-2xl font-semibold text-slate-100">Тест #{{ test.id }}</h1>
          <span
            :class="{
              'bg-amber-900/40 text-amber-300': test.status === 'pending',
              'bg-primary-900/50 text-primary-300': test.status === 'done',
              'bg-red-900/40 text-red-300': test.status === 'failed',
            }"
            class="rounded-full px-2 py-0.5 text-xs"
          >
            {{ test.status }}
          </span>
        </div>
        <p class="mt-1 text-primary-300">{{ testTypeLabel(test.test_type) }}</p>
        <p v-if="test.started_at || test.ended_at" class="mt-1 text-sm text-slate-500">
          {{ test.started_at ? new Date(test.started_at).toLocaleString() : '—' }}
          —
          {{ test.ended_at ? new Date(test.ended_at).toLocaleString() : '—' }}
        </p>
      </div>
      <div class="flex gap-2">
        <button
          @click="runAnalysis"
          :disabled="isRunningAnalysis"
          class="px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white font-medium transition-colors"
        >
          {{ isRunningAnalysis ? 'Запуск анализа...' : 'Запустить анализ' }}
        </button>
        <button
          @click="deleteTest"
          class="px-4 py-2 rounded-lg border border-red-800 text-red-400 hover:bg-red-900/20 transition-colors"
        >
          Удалить тест
        </button>
      </div>
    </div>

    <p v-if="test.system_prompt" class="rounded-xl border border-primary-800/40 bg-slate-900/50 p-4 text-sm text-slate-300">
      {{ test.system_prompt }}
    </p>

    <!-- Collect -->
    <section class="rounded-xl border border-primary-800/40 bg-slate-900/50 p-6">
      <h2 class="text-lg font-medium text-slate-200 mb-4">Сбор данных</h2>
      <div class="grid gap-6 sm:grid-cols-2">
        <div class="space-y-3">
          <h3 class="text-sm font-medium text-primary-300">Grafana</h3>
          <div class="space-y-2">
            <input
              v-model="grafanaFrom"
              type="datetime-local"
              class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 text-sm"
              placeholder="from"
            />
            <input
              v-model="grafanaTo"
              type="datetime-local"
              class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 text-sm"
              placeholder="to"
            />
            <input
              v-model="grafanaDashboardUid"
              type="text"
              class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 text-sm"
              placeholder="Dashboard UID"
            />
            <input
              v-model.number="grafanaSourceIndex"
              type="number"
              min="0"
              class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 text-sm"
              placeholder="Grafana source index"
            />
            <button
              @click="collectGrafana"
              :disabled="collectGrafanaLoading"
              class="w-full px-3 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white text-sm disabled:opacity-50"
            >
              {{ collectGrafanaLoading ? '...' : 'Собрать Grafana' }}
            </button>
          </div>
        </div>
        <div class="space-y-3">
          <h3 class="text-sm font-medium text-primary-300">Kubernetes</h3>
          <div class="space-y-2">
            <input
              v-model="k8sFrom"
              type="datetime-local"
              class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 text-sm"
            />
            <input
              v-model="k8sTo"
              type="datetime-local"
              class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 text-sm"
            />
            <input
              v-model="k8sNamespace"
              type="text"
              class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 text-sm"
              placeholder="Namespace (optional)"
            />
            <button
              @click="collectK8s"
              :disabled="collectK8sLoading"
              class="w-full px-3 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white text-sm disabled:opacity-50"
            >
              {{ collectK8sLoading ? '...' : 'Собрать K8s логи' }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Artifacts -->
    <section class="rounded-xl border border-primary-800/40 bg-slate-900/50 p-6">
      <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
        <h2 class="text-lg font-medium text-slate-200">Артефакты</h2>
        <div class="flex gap-2">
          <button
            @click="downloadAllArtifacts"
            :disabled="!artifacts.length"
            class="px-3 py-1.5 rounded-lg border border-primary-600 text-primary-300 hover:bg-primary-900/30 text-sm disabled:opacity-50"
          >
            Скачать всё (ZIP)
          </button>
          <button
            @click="deleteAllArtifacts"
            :disabled="!artifacts.length"
            class="px-3 py-1.5 rounded-lg border border-red-800 text-red-400 hover:bg-red-900/20 text-sm disabled:opacity-50"
          >
            Удалить всё
          </button>
        </div>
      </div>

      <div class="mb-4 flex flex-wrap gap-3 items-end">
        <div>
          <label class="block text-xs text-slate-500 mb-1">Тип</label>
          <select
            v-model="uploadKind"
            class="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 text-sm"
          >
            <option
              v-for="(label, key) in ARTIFACT_KINDS"
              :key="key"
              :value="key"
            >
              {{ label }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-slate-500 mb-1">Файл</label>
          <input
            type="file"
            @change="(e: Event) => { uploadFile = (e.target as HTMLInputElement).files?.[0] ?? null }"
            class="text-sm text-slate-300"
          />
        </div>
        <div>
          <label class="block text-xs text-slate-500 mb-1">Отображаемое имя</label>
          <input
            v-model="uploadDisplayName"
            type="text"
            class="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-slate-100 text-sm"
            placeholder="опционально"
          />
        </div>
        <button
          @click="uploadArtifact"
          :disabled="!uploadFile || isUploading"
          class="px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white text-sm disabled:opacity-50"
        >
          {{ isUploading ? '...' : 'Загрузить' }}
        </button>
      </div>

      <div v-if="isLoadingArtifacts" class="text-slate-400 text-sm">Загрузка...</div>
      <ul v-else class="space-y-1">
        <li
          v-for="a in artifacts"
          :key="a.id"
          class="flex items-center gap-2 py-2 border-b border-slate-700/50 text-sm"
        >
          <span class="text-primary-300">{{ artifactKindLabel(a.kind) }}</span>
          <span class="text-slate-400">{{ a.display_name ?? a.file_path ?? '—' }}</span>
        </li>
        <li v-if="!artifacts.length" class="py-4 text-slate-500">Нет артефактов</li>
      </ul>
    </section>

    <!-- Report -->
    <section class="rounded-xl border border-primary-800/40 bg-slate-900/50 p-6">
      <h2 class="text-lg font-medium text-slate-200 mb-4">Отчёт</h2>
      <div v-if="isLoadingReport" class="text-slate-400">Загрузка...</div>
      <div v-else-if="report">
        <div class="flex flex-wrap gap-3 mb-4">
          <a
            :href="pdfUrl"
            target="_blank"
            rel="noopener"
            class="px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white text-sm"
          >
            Просмотр PDF
          </a>
          <a
            :href="pdfUrl"
            download
            class="px-4 py-2 rounded-lg border border-primary-600 text-primary-300 hover:bg-primary-900/30 text-sm"
          >
            Скачать PDF
          </a>
          <a
            :href="`/api/reports/test/${testId}/text`"
            target="_blank"
            rel="noopener"
            class="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-800 text-sm"
          >
            Просмотр текста
          </a>
          <a
            :href="`/api/reports/test/${testId}/text`"
            download="report.txt"
            class="px-4 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-800 text-sm"
          >
            Скачать текст
          </a>
        </div>
        <div
          v-if="reportText"
          class="rounded-lg bg-slate-800/50 p-4 max-h-96 overflow-y-auto text-sm text-slate-300 whitespace-pre-wrap font-mono"
        >
          {{ reportText }}
        </div>
      </div>
      <p v-else class="text-slate-500">Отчёт ещё не сформирован. Запустите анализ.</p>
    </section>
  </div>

  <div v-else class="text-slate-400">Загрузка теста...</div>
</template>
