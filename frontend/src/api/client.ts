import axios from 'axios'
import type {
  ProjectCreate,
  ProjectRead,
  TestCreate,
  TestRead,
  ArtifactRead,
  ReportRead,
} from '../types/api'

const api = axios.create({
  baseURL: '/',
  headers: { 'Content-Type': 'application/json' },
})

// Projects
export const projectsApi = {
  list: () => api.get<ProjectRead[]>('/api/projects/'),
  get: (id: number) => api.get<ProjectRead>(`/api/projects/${id}`),
  create: (data: ProjectCreate) => api.post<ProjectRead>('/api/projects/', data),
  update: (id: number, data: Partial<ProjectCreate>) =>
    api.patch<ProjectRead>(`/api/projects/${id}`, data),
  delete: (id: number) => api.delete(`/api/projects/${id}`),
}

// Tests
export const testsApi = {
  list: (projectId?: number) =>
    api.get<TestRead[]>('/api/tests/', projectId ? { params: { project_id: projectId } } : {}),
  get: (id: number) => api.get<TestRead>(`/api/tests/${id}`),
  create: (data: TestCreate) => api.post<TestRead>('/api/tests/', data),
  runAnalysis: (id: number) =>
    api.post<{ status: string; report_id: number; artifacts_used: unknown[] }>(
      `/api/tests/${id}/run-analysis`
    ),
  delete: (id: number) => api.delete(`/api/tests/${id}`),
}

// Artifacts
export const artifactsApi = {
  list: (testId: number) => api.get<ArtifactRead[]>(`/api/artifacts/test/${testId}`),
  upload: (testId: number, file: File, kind: string, displayName?: string) => {
    const form = new FormData()
    form.append('kind', kind)
    form.append('display_name', displayName ?? file.name)
    form.append('file', file)
    return api.post<ArtifactRead>(`/api/artifacts/test/${testId}/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  downloadAll: (testId: number) =>
    api.get(`/api/artifacts/download-all/${testId}`, { responseType: 'blob' }),
  deleteAll: (testId: number) => api.delete(`/api/artifacts/test/${testId}/artifacts`),
}

// Reports
export const reportsApi = {
  get: (testId: number) => api.get<ReportRead>(`/api/reports/test/${testId}`),
  getText: (testId: number) =>
    api.get<string>(`/api/reports/test/${testId}/text`, { responseType: 'text' }),
  getPdfUrl: (testId: number) => `/api/reports/test/${testId}/pdf`,
  getTextUrl: (testId: number) => `/api/reports/test/${testId}/text`,
}

// Collect
export const collectApi = {
  grafana: (
    testId: number,
    params: { from_ts: string; to_ts: string; dashboard_uid: string; grafana_source_index?: number }
  ) =>
    api.post(`/api/collect/test/${testId}/grafana`, null, {
      params,
    }),
  kubernetes: (
    testId: number,
    params: { from_ts: string; to_ts: string; namespace?: string }
  ) =>
    api.post(`/api/collect/test/${testId}/kubernetes`, null, {
      params,
    }),
}

// Health
export const healthApi = {
  check: () => api.get<{ status: string }>('/health'),
}
