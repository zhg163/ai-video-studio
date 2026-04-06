<template>
  <div class="p-6 max-w-3xl mx-auto">
    <div class="mb-6">
      <h2 class="text-xl font-bold text-white mb-1">渲染导出</h2>
      <p class="text-gray-400 text-sm">将时间轴合成为完整视频文件。</p>
    </div>

    <div v-if="error" class="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm">
      {{ error }}
    </div>

    <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm text-gray-400 mb-1">输出格式</label>
          <select
            v-model="format"
            class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
          >
            <option value="mp4">MP4 (H.264)</option>
            <option value="webm">WebM (VP9)</option>
          </select>
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1">分辨率</label>
          <select
            v-model="resolution"
            class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
          >
            <option value="1080p">1080p (1920×1080)</option>
            <option value="720p">720p (1280×720)</option>
            <option value="2k">2K (2560×1440)</option>
            <option value="4k">4K (3840×2160)</option>
          </select>
        </div>
      </div>

      <button
        @click="doRender"
        :disabled="loading"
        class="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
      >
        {{ loading ? '提交渲染任务...' : '开始渲染' }}
      </button>

      <div
        v-if="job"
        class="mt-4 p-4 bg-gray-800 rounded-lg space-y-2"
      >
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-300">渲染任务</span>
          <span class="text-xs text-gray-400">{{ job.status }}</span>
        </div>
        <p class="text-xs text-gray-500 font-mono">ID: {{ job.id }}</p>
        <div v-if="job.output_url" class="pt-2">
          <a
            :href="job.output_url"
            target="_blank"
            class="inline-flex items-center gap-2 px-4 py-2 bg-green-700 hover:bg-green-600 text-white text-sm rounded-lg transition-colors"
          >
            下载视频
          </a>
        </div>
        <details class="text-xs text-gray-600">
          <summary class="cursor-pointer hover:text-gray-400">任务详情</summary>
          <pre class="mt-2 bg-gray-900 rounded p-2 overflow-auto text-gray-400">{{ JSON.stringify(job, null, 2) }}</pre>
        </details>
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
    error.value = e instanceof Error ? e.message : 'Failed to start render'
  } finally {
    loading.value = false
  }
}
</script>
