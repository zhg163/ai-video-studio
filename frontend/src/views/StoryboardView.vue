<template>
  <div class="h-full flex flex-col">
    <!-- Top bar -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 flex-shrink-0">
      <div>
        <h2 class="text-base font-semibold text-white">分镜</h2>
        <p class="text-xs text-gray-500 mt-0.5">场景 · 分镜 · 镜头 — 首尾帧驱动生成</p>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="isConfirmed" class="inline-flex items-center gap-1.5 text-xs text-green-400 bg-green-900/30 border border-green-800/50 px-2.5 py-1 rounded-full">
          <span class="w-1.5 h-1.5 rounded-full bg-green-400"/>已确认
        </span>
        <span v-else-if="storyboard" class="inline-flex items-center gap-1.5 text-xs text-yellow-400 bg-yellow-900/30 border border-yellow-800/50 px-2.5 py-1 rounded-full">
          <span class="w-1.5 h-1.5 rounded-full bg-yellow-400"/>待确认
        </span>
        <span v-if="storyboard" class="text-xs text-gray-600">{{ totalShots }} 镜 · v{{ storyboard.version_no }}</span>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5 min-h-0">
      <!-- Error -->
      <div v-if="error" class="p-3 bg-red-900/40 border border-red-700/60 rounded-xl text-red-300 text-sm">{{ error }}</div>

      <!-- Loading -->
      <div v-if="loading && !storyboard" class="flex flex-col items-center justify-center py-24 text-gray-500">
        <svg class="w-8 h-8 animate-spin text-blue-400 mb-3" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <p class="text-sm">AI 正在生成分镜...</p>
      </div>

      <!-- Empty -->
      <div v-else-if="!storyboard" class="flex flex-col items-center justify-center py-24 text-center">
        <div class="w-14 h-14 rounded-2xl bg-gray-900 border border-gray-800 flex items-center justify-center text-2xl mb-4">🎞</div>
        <p class="text-sm text-gray-400 mb-1">还没有分镜</p>
        <p class="text-xs text-gray-600 mb-5">请先确认脚本</p>
        <RouterLink :to="`/projects/${projectId}/script`"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors">
          前往脚本
        </RouterLink>
      </div>

      <!-- Storyboard scenes -->
      <div v-else class="space-y-6">
        <div
          v-for="scene in storyboard.scenes"
          :key="scene.scene_id ?? scene.scene_number"
          class="space-y-3"
        >
          <!-- Scene header -->
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-2">
              <span class="text-xs font-mono text-purple-400 bg-purple-900/30 border border-purple-800/40 px-2 py-0.5 rounded">
                Scene {{ scene.scene_number }}
              </span>
              <span v-if="scene.title" class="text-sm font-medium text-gray-300">{{ scene.title }}</span>
            </div>
            <div class="flex-1 h-px bg-gray-800"/>
            <span class="text-xs text-gray-600">{{ scene.shots?.length ?? 0 }} 镜头</span>
          </div>

          <!-- Shots grid -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div
              v-for="shot in scene.shots"
              :key="shot.shot_id ?? shot.order_no"
              class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden hover:border-gray-700 transition-colors group"
            >
              <!-- Shot header -->
              <div class="flex items-center justify-between px-3 py-2 bg-gray-800/40 border-b border-gray-800">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-mono text-blue-400">Shot {{ shot.order_no }}</span>
                  <span v-if="shot.shot_type" class="text-xs text-gray-500 bg-gray-700 px-1.5 py-0.5 rounded">{{ shot.shot_type }}</span>
                  <span v-if="shot.camera_movement" class="text-xs text-gray-600 bg-gray-700/50 px-1.5 py-0.5 rounded">{{ shot.camera_movement }}</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <span v-if="shot.duration_sec" class="text-xs text-gray-600">{{ shot.duration_sec }}s</span>
                  <!-- Shot status dot -->
                  <span :class="shotStatusClass(shot.status)" class="w-2 h-2 rounded-full flex-shrink-0"/>
                </div>
              </div>

              <!-- Start / End frame thumbnails -->
              <div class="grid grid-cols-2 gap-px bg-gray-800">
                <div class="bg-gray-950 p-2 flex flex-col items-center justify-center min-h-[72px] relative">
                  <div v-if="shot.start_frame_url"
                    class="w-full h-16 rounded bg-gray-800 overflow-hidden">
                    <img :src="shot.start_frame_url" class="w-full h-full object-cover" alt="首帧"/>
                  </div>
                  <div v-else class="w-full h-16 rounded border border-dashed border-gray-700 flex flex-col items-center justify-center gap-1 cursor-pointer hover:border-blue-500/50 hover:bg-blue-900/10 transition-colors">
                    <svg class="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                    </svg>
                    <span class="text-xs text-gray-600">添加首帧</span>
                  </div>
                  <span class="text-xs text-gray-600 mt-1">首帧</span>
                </div>
                <div class="bg-gray-950 p-2 flex flex-col items-center justify-center min-h-[72px]">
                  <div v-if="shot.end_frame_url"
                    class="w-full h-16 rounded bg-gray-800 overflow-hidden">
                    <img :src="shot.end_frame_url" class="w-full h-full object-cover" alt="尾帧"/>
                  </div>
                  <div v-else class="w-full h-16 rounded border border-dashed border-gray-700 flex flex-col items-center justify-center gap-1 cursor-pointer hover:border-blue-500/50 hover:bg-blue-900/10 transition-colors">
                    <svg class="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                    </svg>
                    <span class="text-xs text-gray-600">添加尾帧</span>
                  </div>
                  <span class="text-xs text-gray-600 mt-1">尾帧</span>
                </div>
              </div>

              <!-- Shot content -->
              <div class="p-3 space-y-2">
                <!-- Action / visual -->
                <div v-if="shot.action_desc || shot.environment_desc">
                  <p class="text-xs text-gray-500 mb-1">画面</p>
                  <p class="text-xs text-gray-300 leading-snug">
                    {{ shot.action_desc || shot.environment_desc }}
                  </p>
                </div>

                <!-- Voiceover -->
                <div v-if="shot.voiceover_text">
                  <p class="text-xs text-gray-500 mb-1 flex items-center gap-1">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
                    </svg>
                    旁白
                  </p>
                  <p class="text-xs text-yellow-300/80 italic">"{{ shot.voiceover_text }}"</p>
                </div>

                <!-- Video prompt preview -->
                <details v-if="shot.video_prompt || shot.image_prompt" class="group/det">
                  <summary class="text-xs text-gray-600 cursor-pointer hover:text-gray-400 flex items-center gap-1">
                    <svg class="w-3 h-3 transition-transform group-open/det:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                    生成提示词
                  </summary>
                  <p class="mt-1 text-xs text-gray-600 leading-relaxed bg-gray-800 rounded p-2">
                    {{ shot.video_prompt || shot.image_prompt }}
                  </p>
                </details>

                <!-- Shot actions -->
                <div class="flex items-center gap-1.5 pt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button class="flex-1 py-1 text-xs text-gray-500 hover:text-blue-400 hover:bg-blue-900/20 rounded transition-colors">
                    重新生成
                  </button>
                  <button class="flex-1 py-1 text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded transition-colors">
                    手动编辑
                  </button>
                  <button class="flex-1 py-1 text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded transition-colors">
                    引用
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div v-if="storyboard" class="px-6 py-4 border-t border-gray-800 flex-shrink-0">
      <div v-if="!isConfirmed" class="flex items-center justify-between">
        <p class="text-xs text-gray-500">确认后自动装配时间轴</p>
        <button
          @click="doConfirm"
          :disabled="loading"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-green-700 hover:bg-green-600 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          {{ loading ? '确认中...' : '确认分镜，装配时间轴' }}
          <svg v-if="!loading" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
          </svg>
        </button>
      </div>
      <div v-else class="flex items-center justify-between">
        <div class="flex items-center gap-2 text-green-400 text-sm">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          分镜已确认，时间轴装配中
        </div>
        <RouterLink :to="`/projects/${projectId}/timeline`"
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors">
          查看时间轴
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
import { storyboardsApi, timelinesApi } from '@/api'
import type { Storyboard } from '@/types'

const route = useRoute()
const projectId = computed(() => route.params.id as string)

const storyboard = ref<Storyboard | null>(null)
const loading = ref(false)
const error = ref('')
const isConfirmed = ref(false)

const totalShots = computed(() =>
  storyboard.value?.scenes?.reduce((n, s) => n + (s.shots?.length ?? 0), 0) ?? 0
)

function shotStatusClass(status?: string) {
  const map: Record<string, string> = {
    done: 'bg-green-400',
    generating: 'bg-blue-400 animate-pulse',
    failed: 'bg-red-400',
    pending: 'bg-gray-600',
  }
  return map[status ?? 'pending'] ?? 'bg-gray-600'
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await storyboardsApi.getByProject(projectId.value)
    const items = data?.items ?? []
    if (items.length > 0) {
      storyboard.value = items[0]
      const { useProjectStore } = await import('@/stores/projects')
      const store = useProjectStore()
      isConfirmed.value = !!store.current?.current_storyboard_version_id
    }
  } catch { /* none yet */ } finally {
    loading.value = false
  }
})

async function doConfirm() {
  if (!storyboard.value) return
  loading.value = true
  error.value = ''
  try {
    await storyboardsApi.confirm(projectId.value, storyboard.value.id)
    isConfirmed.value = true
    try { await timelinesApi.assemble(projectId.value, storyboard.value.id) } catch { /* non-fatal */ }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '确认失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
