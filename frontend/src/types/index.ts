// Domain types matching actual backend schemas

export interface Project {
  id: number
  name: string
  description?: string
  status: string
  aspect_ratio?: string
  language?: string
  current_brief_version_id?: string | null
  current_script_version_id?: string | null
  current_storyboard_version_id?: string | null
  current_timeline_version_id?: number | null
  created_at: string
  updated_at: string
}

export interface PagedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// Brief: structured_brief contains AI output (theme, tone, key_messages, etc.)
export interface Brief {
  id: string
  project_id: number
  version_no: number
  source_input: { text?: string; references?: string[] }
  structured_brief: {
    theme?: string
    tone?: string
    target_audience?: string
    duration_seconds?: number
    key_messages?: string[]
    style_references?: string[]
    [key: string]: unknown
  }
  constraints: Record<string, unknown>
  created_by: number
  created_at: string
}

// Script: sections contains scenes array
export interface ScriptSection {
  scene_number?: number
  title?: string
  narration?: string
  visual_description?: string
  duration_seconds?: number
  [key: string]: unknown
}

export interface Script {
  id: string
  project_id: number
  version_no: number
  brief_version_id: string
  title: string
  language: string
  sections: ScriptSection[]
  full_text: string
  created_by?: number
  created_at: string
}

// Storyboard: scenes[].shots
export interface StoryboardShot {
  shot_id?: string
  shot_number?: number
  shot_type?: string
  composition?: string
  action?: string
  dialogue?: string
  duration_seconds?: number
  [key: string]: unknown
}

export interface StoryboardScene {
  scene_id?: string
  scene_number?: number
  title?: string
  shots: StoryboardShot[]
  [key: string]: unknown
}

export interface Storyboard {
  id: string
  project_id: number
  version_no: number
  script_version_id: string
  scenes: StoryboardScene[]
  created_at: string
}

// Timeline
export interface TimelineClip {
  shot_id?: string
  start_time: number
  end_time: number
  track?: number
  [key: string]: unknown
}

export interface Timeline {
  id: string | number
  project_id: number
  version_no?: number
  storyboard_version_id?: string
  clips?: TimelineClip[]
  total_duration_seconds?: number
  status?: string
  created_at?: string
  [key: string]: unknown
}

export interface RenderJob {
  id: string
  project_id: number
  status: string
  output_url?: string
  format?: string
  resolution?: string
  created_at?: string
  [key: string]: unknown
}
