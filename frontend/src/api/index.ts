import client from './client'
import type { Project } from '@/types'

export const projectsApi = {
  list: () => client.get<Project[]>('/projects').then(r => r.data),

  get: (id: string) => client.get<Project>(`/projects/${id}`).then(r => r.data),

  create: (data: { name: string; description?: string }) =>
    client.post<Project>('/projects', data).then(r => r.data),

  update: (id: string, data: { name?: string; description?: string }) =>
    client.put<Project>(`/projects/${id}`, data).then(r => r.data),

  delete: (id: string) => client.delete(`/projects/${id}`),
}

export const briefsApi = {
  getByProject: (projectId: string) =>
    client.get(`/projects/${projectId}/briefs`).then(r => r.data),

  generate: (projectId: string, rawInput: string) =>
    client.post(`/briefs/generate`, { project_id: projectId, raw_input: rawInput }).then(r => r.data),

  get: (id: string) => client.get(`/briefs/${id}`).then(r => r.data),

  confirm: (id: string) => client.post(`/briefs/${id}/confirm`).then(r => r.data),

  regenerate: (id: string) => client.post(`/briefs/${id}/regenerate`).then(r => r.data),
}

export const scriptsApi = {
  generate: (projectId: string, briefId: string) =>
    client.post(`/scripts/generate`, { project_id: projectId, brief_id: briefId }).then(r => r.data),

  getByProject: (projectId: string) =>
    client.get(`/projects/${projectId}/scripts`).then(r => r.data),

  get: (id: string) => client.get(`/scripts/${id}`).then(r => r.data),

  confirm: (id: string) => client.post(`/scripts/${id}/confirm`).then(r => r.data),

  regenerate: (id: string) => client.post(`/scripts/${id}/regenerate`).then(r => r.data),
}

export const storyboardsApi = {
  generate: (projectId: string, scriptId: string) =>
    client.post(`/storyboards/generate`, { project_id: projectId, script_id: scriptId }).then(r => r.data),

  getByProject: (projectId: string) =>
    client.get(`/projects/${projectId}/storyboards`).then(r => r.data),

  get: (id: string) => client.get(`/storyboards/${id}`).then(r => r.data),

  confirm: (id: string) => client.post(`/storyboards/${id}/confirm`).then(r => r.data),
}

export const shotsApi = {
  list: (projectId: string) =>
    client.get(`/projects/${projectId}/shots`).then(r => r.data),

  generateImage: (shotId: string) =>
    client.post(`/shots/${shotId}/generate-image`).then(r => r.data),

  generateVideo: (shotId: string) =>
    client.post(`/shots/${shotId}/generate-video`).then(r => r.data),
}

export const timelinesApi = {
  assemble: (projectId: string) =>
    client.post(`/timelines/assemble`, { project_id: projectId }).then(r => r.data),

  getByProject: (projectId: string) =>
    client.get(`/projects/${projectId}/timelines`).then(r => r.data),

  get: (id: string) => client.get(`/timelines/${id}`).then(r => r.data),
}

export const rendersApi = {
  render: (projectId: string, timelineId: string, format = 'mp4') =>
    client.post(`/renders`, { project_id: projectId, timeline_id: timelineId, format }).then(r => r.data),

  get: (id: string) => client.get(`/renders/${id}`).then(r => r.data),
}
