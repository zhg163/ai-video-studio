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

// Brief
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
    visual_style?: string
    sound_mood?: string
    [key: string]: unknown
  }
  constraints: Record<string, unknown>
  created_by: number
  created_at: string
}

// Script
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

// Storyboard — real backend schema from E2E test
export interface StoryboardShot {
  shot_id?: string
  order_no?: number
  shot_type?: string            // close-up / medium / wide / etc.
  camera_movement?: string
  character_desc?: string
  environment_desc?: string
  action_desc?: string
  voiceover_text?: string
  image_prompt?: string
  video_prompt?: string
  duration_sec?: number
  status?: string               // pending / generating / done / failed
  selected_asset_ids?: string[]
  // UI-only enrichment (not in backend)
  start_frame_url?: string
  end_frame_url?: string
  video_url?: string
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

// Timeline — real backend schema
export interface TimelineTrack {
  track_type?: string            // video / audio / subtitle / bgm
  clips?: TimelineClip[]
  [key: string]: unknown
}

export interface TimelineClip {
  shot_id?: string
  asset_id?: string
  start_ms?: number
  end_ms?: number
  // legacy fields
  start_time?: number
  end_time?: number
  track?: number
  [key: string]: unknown
}

export interface SubtitleSegment {
  text?: string
  start_ms?: number
  end_ms?: number
  [key: string]: unknown
}

export interface Timeline {
  id: string | number
  project_id: number
  version_no?: number
  storyboard_version_id?: string
  tracks?: TimelineTrack[] | Record<string, unknown>
  subtitle_segments?: SubtitleSegment[]
  transitions?: unknown[]
  duration_ms?: number
  // legacy
  clips?: TimelineClip[]
  total_duration_seconds?: number
  status?: string
  created_at?: string
  [key: string]: unknown
}

// Render
export interface RenderJob {
  id: string | number
  project_id: number
  status: string                 // pending / processing / done / failed
  progress?: number
  output_url?: string
  cover_url?: string
  output_asset_id?: string
  render_profile?: string
  error_message?: string
  format?: string
  resolution?: string
  created_at?: string
  updated_at?: string
  [key: string]: unknown
}

// Agent — UI-only types for the chat/agent panel
export type AgentStatus =
  | 'idle'
  | 'thinking'
  | 'searching'
  | 'generating'
  | 'done'
  | 'failed'

export type AgentStepStatus = 'pending' | 'running' | 'done' | 'failed'

export interface AgentThoughtStep {
  id: string
  label: string
  status: AgentStepStatus
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  thoughtSteps?: AgentThoughtStep[]
  agentStatus?: AgentStatus
}
