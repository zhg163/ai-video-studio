import client from './client'

// ---- Projects ----
export const projectsApi = {
  list: (page = 1, pageSize = 20) =>
    client.get(`/projects`, { params: { page, page_size: pageSize } }).then(r => r.data),

  get: (id: string | number) =>
    client.get(`/projects/${id}`).then(r => r.data),

  create: (data: { name: string; description?: string; aspect_ratio?: string; language?: string }) =>
    client.post(`/projects`, data).then(r => r.data),

  patch: (id: string | number, data: { name?: string; description?: string }) =>
    client.patch(`/projects/${id}`, data).then(r => r.data),

  archive: (id: string | number) =>
    client.post(`/projects/${id}/archive`).then(r => r.data),
}

// ---- Briefs ----
// POST /projects/{id}/briefs/generate  body: { text, references? }
// GET  /projects/{id}/briefs           → PagedData<BriefOut>
// GET  /projects/{id}/briefs/{vid}     → BriefOut
// POST /projects/{id}/briefs/{vid}/confirm
export const briefsApi = {
  getByProject: (projectId: string | number, page = 1) =>
    client.get(`/projects/${projectId}/briefs`, { params: { page } }).then(r => r.data),

  generate: (projectId: string | number, text: string, references: string[] = []) =>
    client.post(`/projects/${projectId}/briefs/generate`, { text, references }).then(r => r.data),

  get: (projectId: string | number, versionId: string) =>
    client.get(`/projects/${projectId}/briefs/${versionId}`).then(r => r.data),

  confirm: (projectId: string | number, versionId: string) =>
    client.post(`/projects/${projectId}/briefs/${versionId}/confirm`).then(r => r.data),
}

// ---- Scripts ----
// POST /projects/{id}/scripts/generate  body: { brief_version_id }
// GET  /projects/{id}/scripts
// GET  /projects/{id}/scripts/{vid}
// POST /projects/{id}/scripts/{vid}/confirm
export const scriptsApi = {
  getByProject: (projectId: string | number, page = 1) =>
    client.get(`/projects/${projectId}/scripts`, { params: { page } }).then(r => r.data),

  generate: (projectId: string | number, briefVersionId: string) =>
    client.post(`/projects/${projectId}/scripts/generate`, { brief_version_id: briefVersionId }).then(r => r.data),

  get: (projectId: string | number, versionId: string) =>
    client.get(`/projects/${projectId}/scripts/${versionId}`).then(r => r.data),

  confirm: (projectId: string | number, versionId: string) =>
    client.post(`/projects/${projectId}/scripts/${versionId}/confirm`).then(r => r.data),
}

// ---- Storyboards ----
// POST /projects/{id}/storyboards/generate  body: { script_version_id }
// GET  /projects/{id}/storyboards
// GET  /projects/{id}/storyboards/{vid}
// POST /projects/{id}/storyboards/{vid}/confirm
export const storyboardsApi = {
  getByProject: (projectId: string | number, page = 1) =>
    client.get(`/projects/${projectId}/storyboards`, { params: { page } }).then(r => r.data),

  generate: (projectId: string | number, scriptVersionId: string) =>
    client.post(`/projects/${projectId}/storyboards/generate`, { script_version_id: scriptVersionId }).then(r => r.data),

  get: (projectId: string | number, versionId: string) =>
    client.get(`/projects/${projectId}/storyboards/${versionId}`).then(r => r.data),

  confirm: (projectId: string | number, versionId: string) =>
    client.post(`/projects/${projectId}/storyboards/${versionId}/confirm`).then(r => r.data),
}

// ---- Timelines ----
// POST /projects/{id}/timelines/assemble  body: { storyboard_version_id }
// GET  /projects/{id}/timelines
// GET  /projects/{id}/timelines/{vid}
// POST /projects/{id}/timelines/{vid}/confirm
export const timelinesApi = {
  getByProject: (projectId: string | number, page = 1) =>
    client.get(`/projects/${projectId}/timelines`, { params: { page } }).then(r => r.data),

  assemble: (projectId: string | number, storyboardVersionId: string) =>
    client.post(`/projects/${projectId}/timelines/assemble`, { storyboard_version_id: storyboardVersionId }).then(r => r.data),

  get: (projectId: string | number, versionId: string) =>
    client.get(`/projects/${projectId}/timelines/${versionId}`).then(r => r.data),

  confirm: (projectId: string | number, versionId: string) =>
    client.post(`/projects/${projectId}/timelines/${versionId}/confirm`).then(r => r.data),
}

// ---- Renders ----
// POST /projects/{id}/renders  body: { timeline_version_id, format?, resolution? }
// GET  /projects/{id}/renders/{render_id}
export const rendersApi = {
  create: (projectId: string | number, timelineVersionId: string, format = 'mp4', resolution = '1920x1080') =>
    client.post(`/projects/${projectId}/renders`, { timeline_version_id: timelineVersionId, format, resolution }).then(r => r.data),

  get: (projectId: string | number, renderId: string) =>
    client.get(`/projects/${projectId}/renders/${renderId}`).then(r => r.data),
}
