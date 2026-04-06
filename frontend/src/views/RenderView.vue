<template>
  <div class="h-full flex flex-col">
    <!-- Top bar -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 flex-shrink-0">
      <div>
        <h2 class="text-base font-semibold text-white">渲染导出</h2>
        <p class="text-xs text-gray-500 mt-0.5">将时间轴合成为完整视频文件</p>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5 min-h-0">
      <div v-if="error" class="p-3 bg-red-900/40 border border-red-700/60 rounded-xl text-red-300 text-sm">{{ error }}</div>

      <!-- Settings -->
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-5">
        <p class="text-sm font-medium text-gray-300">导出设置</p>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-gray-500 mb-2">输出格式</label>
            <div class="flex gap-2">
              <button
                v-for="f in ['mp4', 'webm']"
                :key="f"
                @click="format = f"
                :class="format === f
                  ? 'bg-blue-600/30 border-blue-500/60 text-blue-300'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white'"
                class="flex-1 py-2 text-xs font-medium border rounded-lg transition-colors uppercase"
              >
                {{ f }}
              </button>
            </div>
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-2">分辨率</label>
            <div class="grid grid-cols-2 gap-1.5">
              <button
                v-for="r in resolutionOptions"
                :key="r.value"
                @click="resolution = r.value"
                :class="resolution === r.value
                  ? 'bg-blue-600/30 border-blue-500/60 text-blue-300'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white'"
                class="py-2 text-xs border rounded-lg transition-colors"
              >
                {{ r.label }}
              </button>
            </div>
          </div>
        </div>

        <button
          @click="doRender"
          :disabled="loading"
          class="w-full py-3 inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-sm font-medium rounded-xl transition-colors"
        >
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          {{ loading ? '提交渲染任务...' : '开始渲染' }}
        </button>
      </div>

      <!-- Render job result -->
      <div v-if="job" class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
          <span class="text-sm font-medium text-gray-300">渲染任务</span>
          <div class="flex items-center gap-2">
            <span
              :class="{
                'text-yellow-400 bg-yellow-900/30 border-yellow-800/50': job.status === 'pending' || job.status === 'processing',
                'text-green-400 bg-green-900/30 border-green-800/50': job.status === 'done' || job.status === 'completed',
                'text-red-400 bg-red-900/30 border-red-800/50': job.status === 'failed',
              }"
              class="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border"
            >
              <span class="w-1.5 h-1.5 rounded-full" :class="{
                'bg-yellow-400 animate-pulse': job.status === 'pending' || job.status === 'processing',
                'bg-green-400': job.status === 'done' || job.status === 'completed',
                'bg-red-400': job.status === 'failed',
              }"/>
              {{ statusLabel(job.status) }}
            </span>
          </div>
        </div>

        <div class="p-4 space-y-3">
          <div class="grid grid-cols-2 gap-3 text-xs">
            <div>
              <p class="text-gray-500 mb-1">任务 ID</p>
              <p class="text-gray-300 font-mono">{{ job.id }}</p>
            </div>
            <div v-if="job.render_profile">
              <p class="text-gray-500 mb-1">规格</p>
              <p class="text-gray-300 uppercase">{{ job.render_profile }}</p>
            </div>
          </div>

          <!-- Progress bar -->
          <div v-if="job.status === 'processing'" class="space-y-1.5">
            <div class="flex justify-between text-xs text-gray-500">
              <span>渲染进度</span>
              <span>{{ job.progress ?? 0 }}%</span>
            </div>
            <div class="h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                class="h-full bg-blue-500 rounded-full transition-all duration-500"
                :style="{ width: `${job.progress ?? 0}%` }"
              />
            </div>
          </div>

          <!-- Error message -->
          <div v-if="job.error_message" class="p-2.5 bg-red-900/30 border border-red-800/50 rounded-lg">
            <p class="text-xs text-red-400">{{ job.error_message }}</p>
          </div>

          <!-- Download button -->
          <div v-if="job.output_url">
            <a
              :href="job.output_url"
              target="_blank"
              class="inline-flex items-center gap-2 px-4 py-2.5 bg-green-700 hover:bg-green-600 text-white text-sm rounded-lg transition-colors"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
              下载视频
            </a>
          </div>

          <details class="group">
            <summary class="text-xs text-gray-600 cursor-pointer hover:text-gray-400 flex items-center gap-1">
              <svg class="w-3 h-3 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
              任务详情
            </summary>
            <pre class="mt-2 text-xs bg-gray-800 rounded-lg p-3 overflow-auto text-gray-600 max-h-40">{{ JSON.stringify(job, null, 2) }}</pre>
          </details>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { rendersApi, timelinesApi } from '@/api'
import type { RenderJob } from '@/types'

const route = useRoute()
const projectId = computed(() => route.params.id as string)

const format = ref('mp4')
const resolution = ref('1080p')
const loading = ref(false)
const error = ref('')
const job = ref<RenderJob | null>(null)

const resolutionOptions = [
  { value: '720p',  label: '720p' },
  { value: '1080p', label: '1080p' },
  { value: '2k',    label: '2K' },
  { value: '4k',    label: '4K' },
]

function statusLabel(s?: string) {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '渲染中',
    done: '已完成',
    completed: '已完成',
    failed: '失败',
  }
  return map[s ?? ''] ?? s ?? '未知'
}

async function doRender() {
  loading.value = true
  error.value = ''
  try {
    const tlData = await timelinesApi.getByProject(projectId.value)
    const items = tlData?.items ?? []
    if (!items.length) throw new Error('没有时间轴，请先完成分镜步骤')
    const tl = items[0]
    job.value = await rendersApi.create(projectId.value, String(tl.id), format.value, resolution.value)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '提交渲染失败'
  } finally {
    loading.value = false
  }
}
</script>
