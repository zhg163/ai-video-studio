<template>
  <div class="h-full flex flex-col">
    <!-- Top bar -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 flex-shrink-0">
      <div>
        <h2 class="text-base font-semibold text-white">时间轴</h2>
        <p class="text-xs text-gray-500 mt-0.5">多轨道装配 — 视频 · 字幕 · 配音 · 背景音乐</p>
      </div>
      <div class="flex items-center gap-3">
        <div v-if="timeline" class="flex items-center gap-2 text-xs text-gray-500">
          <span>总时长</span>
          <span class="text-gray-300 font-mono">{{ formatDuration(totalMs) }}</span>
        </div>
        <span v-if="timeline" class="text-xs text-gray-600">v{{ timeline.version_no ?? 1 }}</span>
      </div>
    </div>

    <div class="flex-1 overflow-hidden flex flex-col min-h-0">
      <!-- Error -->
      <div v-if="error" class="mx-6 mt-4 p-3 bg-red-900/40 border border-red-700/60 rounded-xl text-red-300 text-sm">{{ error }}</div>

      <!-- Loading -->
      <div v-if="loading && !timeline" class="flex flex-col items-center justify-center h-full text-gray-500">
        <svg class="w-8 h-8 animate-spin text-blue-400 mb-3" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <p class="text-sm">装配时间轴...</p>
      </div>

      <!-- Empty -->
      <div v-else-if="!timeline" class="flex flex-col items-center justify-center h-full text-center">
        <div class="w-14 h-14 rounded-2xl bg-gray-900 border border-gray-800 flex items-center justify-center text-2xl mb-4">⏱</div>
        <p class="text-sm text-gray-400 mb-1">时间轴尚未创建</p>
        <p class="text-xs text-gray-600 mb-5">请先确认分镜，自动装配时间轴</p>
        <RouterLink :to="`/projects/${projectId}/storyboard`"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors">
          前往分镜
        </RouterLink>
      </div>

      <!-- Timeline content -->
      <div v-else class="flex-1 flex flex-col min-h-0 overflow-y-auto">
        <!-- Timeline ruler + tracks -->
        <div class="px-6 pt-5 pb-2 flex-shrink-0">
          <!-- Time ruler -->
          <div class="flex items-end mb-1 ml-24">
            <div class="flex-1 relative h-5 overflow-hidden">
              <div
                v-for="tick in timeTicks"
                :key="tick.ms"
                class="absolute bottom-0 flex flex-col items-center"
                :style="{ left: `${(tick.ms / totalMs) * 100}%` }"
              >
                <span class="text-xs text-gray-600 font-mono mb-0.5">{{ tick.label }}</span>
                <div class="w-px h-2 bg-gray-700"/>
              </div>
            </div>
          </div>

          <!-- Tracks -->
          <div class="space-y-2">
            <div
              v-for="track in displayTracks"
              :key="track.type"
              class="flex items-center gap-3"
            >
              <!-- Track label -->
              <div class="w-20 flex-shrink-0 text-right">
                <div class="flex items-center justify-end gap-1.5">
                  <span class="text-lg">{{ track.icon }}</span>
                  <span class="text-xs text-gray-500">{{ track.label }}</span>
                </div>
              </div>

              <!-- Track lane -->
              <div class="flex-1 h-10 bg-gray-900 border border-gray-800 rounded-lg relative overflow-hidden">
                <!-- Clips -->
                <div
                  v-for="(clip, ci) in track.clips"
                  :key="ci"
                  class="absolute top-0.5 bottom-0.5 rounded flex items-center px-2 cursor-pointer hover:brightness-110 transition-all"
                  :class="track.clipClass"
                  :style="{
                    left: `${(clipStart(clip) / totalMs) * 100}%`,
                    width: `${Math.max(1, (clipDuration(clip) / totalMs) * 100)}%`,
                  }"
                  :title="clipTitle(clip)"
                >
                  <span class="text-xs text-white/80 truncate select-none">{{ clipTitle(clip) }}</span>
                </div>

                <!-- Empty lane hint -->
                <div v-if="!track.clips.length" class="absolute inset-0 flex items-center justify-center">
                  <span class="text-xs text-gray-700">{{ track.emptyLabel }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Stats -->
        <div class="px-6 py-4 grid grid-cols-3 gap-3">
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-3.5">
            <p class="text-xs text-gray-500 mb-1">总时长</p>
            <p class="text-lg font-semibold text-white font-mono">{{ formatDuration(totalMs) }}</p>
          </div>
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-3.5">
            <p class="text-xs text-gray-500 mb-1">视频片段</p>
            <p class="text-lg font-semibold text-white">{{ videoClipCount }}</p>
          </div>
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-3.5">
            <p class="text-xs text-gray-500 mb-1">字幕段落</p>
            <p class="text-lg font-semibold text-white">{{ timeline.subtitle_segments?.length ?? 0 }}</p>
          </div>
        </div>

        <!-- Subtitle segments -->
        <div v-if="subtitleSegments.length" class="px-6 pb-4">
          <div class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <div class="px-4 py-2.5 border-b border-gray-800 flex items-center gap-2">
              <span class="text-sm">💬</span>
              <span class="text-xs font-medium text-gray-400">字幕片段</span>
            </div>
            <div class="divide-y divide-gray-800 max-h-40 overflow-y-auto">
              <div v-for="(seg, i) in subtitleSegments" :key="i"
                class="flex items-start gap-3 px-4 py-2.5">
                <span class="text-xs font-mono text-gray-600 flex-shrink-0 mt-0.5">
                  {{ formatDuration(seg.start_ms ?? 0) }}
                </span>
                <p class="text-xs text-gray-300 leading-relaxed">{{ seg.text }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Raw JSON debug -->
        <details class="px-6 pb-4 group">
          <summary class="text-xs text-gray-600 cursor-pointer hover:text-gray-400 flex items-center gap-1">
            <svg class="w-3 h-3 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
            原始时间轴数据
          </summary>
          <pre class="mt-2 text-xs bg-gray-900 border border-gray-800 rounded-xl p-3 overflow-auto text-gray-600 max-h-48">{{ JSON.stringify(timeline, null, 2) }}</pre>
        </details>
      </div>
    </div>

    <!-- Footer -->
    <div v-if="timeline" class="px-6 py-4 border-t border-gray-800 flex-shrink-0">
      <div class="flex items-center justify-end">
        <RouterLink :to="`/projects/${projectId}/render`"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors">
          渲染导出
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
          </svg>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { timelinesApi } from '@/api'
import type { Timeline, TimelineClip, SubtitleSegment } from '@/types'

const route = useRoute()
const projectId = computed(() => route.params.id as string)

const timeline = ref<Timeline | null>(null)
const loading = ref(false)
const error = ref('')

// --- Computed helpers ---
const totalMs = computed(() => {
  const tl = timeline.value
  if (!tl) return 1
  if (tl.duration_ms) return tl.duration_ms
  if (tl.total_duration_seconds) return tl.total_duration_seconds * 1000
  return 30000 // fallback 30s
})

const subtitleSegments = computed<SubtitleSegment[]>(() =>
  Array.isArray(timeline.value?.subtitle_segments) ? (timeline.value!.subtitle_segments as SubtitleSegment[]) : []
)

// Flatten all clips from tracks object
const allVideoClips = computed<TimelineClip[]>(() => {
  const tl = timeline.value
  if (!tl) return []
  if (Array.isArray(tl.clips)) return tl.clips
  const tracks = tl.tracks
  if (!tracks) return []
  if (Array.isArray(tracks)) {
    return tracks.flatMap(t => Array.isArray(t.clips) ? t.clips : [])
  }
  // object keyed by track type
  const obj = tracks as Record<string, unknown>
  return Object.values(obj).flatMap(v => Array.isArray(v) ? v : [])
})

const videoClipCount = computed(() => allVideoClips.value.length)

interface DisplayTrack {
  type: string
  label: string
  icon: string
  clips: TimelineClip[]
  clipClass: string
  emptyLabel: string
}

const displayTracks = computed<DisplayTrack[]>(() => [
  {
    type: 'video',
    label: '视频',
    icon: '🎞',
    clips: allVideoClips.value,
    clipClass: 'bg-blue-600/60 border border-blue-500/30',
    emptyLabel: '无视频片段',
  },
  {
    type: 'subtitle',
    label: '字幕',
    icon: '💬',
    clips: subtitleSegments.value.map(s => ({ start_ms: s.start_ms, end_ms: s.end_ms, shot_id: s.text?.slice(0, 20) })),
    clipClass: 'bg-purple-600/50 border border-purple-500/30',
    emptyLabel: '无字幕',
  },
  {
    type: 'bgm',
    label: '背景音乐',
    icon: '🎵',
    clips: [],
    clipClass: 'bg-green-600/50 border border-green-500/30',
    emptyLabel: '未添加',
  },
])

function clipStart(clip: TimelineClip): number {
  return clip.start_ms ?? (clip.start_time ?? 0) * 1000
}

function clipDuration(clip: TimelineClip): number {
  const end = clip.end_ms ?? (clip.end_time ?? 0) * 1000
  return Math.max(1000, end - clipStart(clip))
}

function clipTitle(clip: TimelineClip): string {
  return clip.shot_id ? String(clip.shot_id).slice(0, 16) : 'clip'
}

const timeTicks = computed(() => {
  const total = totalMs.value
  const steps = 5
  return Array.from({ length: steps + 1 }, (_, i) => ({
    ms: Math.round((i / steps) * total),
    label: formatDuration(Math.round((i / steps) * total)),
  }))
})

function formatDuration(ms: number): string {
  const s = Math.round(ms / 1000)
  const m = Math.floor(s / 60)
  const sec = s % 60
  if (m > 0) return `${m}:${sec.toString().padStart(2, '0')}`
  return `${sec}s`
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await timelinesApi.getByProject(projectId.value)
    const items = data?.items ?? []
    if (items.length > 0) timeline.value = items[0]
  } catch { /* none yet */ } finally {
    loading.value = false
  }
})
</script>
