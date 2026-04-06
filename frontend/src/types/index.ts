// Domain types matching backend schemas

export interface Project {
  id: string
  name: string
  description?: string
  status: string
  created_at: string
  updated_at: string
}

export interface Brief {
  id: string
  project_id: string
  raw_input?: string
  theme?: string
  tone?: string
  duration_seconds?: number
  target_audience?: string
  key_messages?: string[]
  style_references?: string[]
  status: string
  created_at: string
  updated_at: string
}

export interface ScriptScene {
  scene_number: number
  title: string
  narration: string
  visual_description: string
  duration_seconds: number
}

export interface Script {
  id: string
  project_id: string
  brief_id?: string
  title?: string
  scenes?: ScriptScene[]
  total_duration_seconds?: number
  status: string
  created_at: string
  updated_at: string
}

export interface StoryboardShot {
  shot_number: number
  scene_number: number
  shot_type: string
  composition: string
  action: string
  dialogue?: string
  duration_seconds: number
}

export interface Storyboard {
  id: string
  project_id: string
  script_id?: string
  shots?: StoryboardShot[]
  status: string
  created_at: string
  updated_at: string
}

export interface Shot {
  id: string
  project_id: string
  storyboard_id?: string
  shot_number: number
  image_url?: string
  video_url?: string
  audio_url?: string
  duration_seconds?: number
  status: string
  created_at: string
  updated_at: string
}

export interface TimelineClip {
  shot_id: string
  start_time: number
  end_time: number
  track: number
}

export interface Timeline {
  id: string
  project_id: string
  clips?: TimelineClip[]
  total_duration_seconds?: number
  status: string
  created_at: string
  updated_at: string
}

export interface RenderJob {
  id: string
  project_id: string
  timeline_id?: string
  output_url?: string
  format?: string
  resolution?: string
  status: string
  created_at: string
  updated_at: string
}

export interface ApiError {
  detail: string
}

export type ProjectStatus = 'draft' | 'brief_ready' | 'script_ready' | 'storyboard_ready' | 'shots_ready' | 'timeline_ready' | 'rendering' | 'completed'
