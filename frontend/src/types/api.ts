/** API types matching backend schemas */

export type GrafanaSource = {
  name: string
  url: string
  token: string
}

export type K8sConfig = {
  server?: string
  token?: string
  kubeconfig_base64?: string
}

export type ProjectCreate = {
  name: string
  description?: string | null
  grafana_sources?: GrafanaSource[] | null
  k8s_config?: K8sConfig | null
  llm_type?: string
  llm_model?: string
  llm_api_key?: string | null
}

export type ProjectRead = {
  id: number
  name: string
  description?: string | null
  grafana_sources?: GrafanaSource[] | null
  k8s_config?: K8sConfig | null
  llm_type: string
  llm_model: string
  created_at: string
}

export const TEST_TYPES = {
  max_search: 'Поиск максимума',
  max_confirmation: 'Подтверждение максимума',
  reliability: 'Надёжность',
  destructive: 'Деструктивный тест',
} as const

export type TestType = keyof typeof TEST_TYPES

export type TestCreate = {
  project_id: number
  test_type: TestType
  started_at?: string | null
  ended_at?: string | null
  system_prompt?: string | null
}

export type TestRead = {
  id: number
  project_id: number
  test_type: string
  started_at?: string | null
  ended_at?: string | null
  system_prompt?: string | null
  status: string
  error_message?: string | null
  created_at: string
}

export type ArtifactRead = {
  id: number
  test_id: number
  kind: string
  display_name?: string | null
  file_path?: string | null
  metadata?: Record<string, unknown> | null
  created_at: string
}

export type ReportRead = {
  id: number
  test_id: number
  report_text: string
  pdf_path?: string | null
  artifacts_used_snapshot?: Record<string, unknown>[] | null
  created_at: string
}

export const ARTIFACT_KINDS = {
  custom_java_log: 'Java лог',
  custom_gc: 'GC лог',
  custom_thread_dump: 'Thread dump',
  custom_heap_dump: 'Heap dump',
  custom_jvm_opts: 'JVM opts',
  custom_jfr: 'JFR',
  custom_other: 'Другое',
  grafana_slice: 'Grafana',
  k8s_pods: 'K8s поды',
  k8s_logs: 'K8s логи',
} as const
