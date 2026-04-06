<template>
  <div class="h-full flex flex-col">
    <!-- Top bar -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 flex-shrink-0">
      <div>
        <h2 class="text-base font-semibold text-white">脚本</h2>
        <p class="text-xs text-gray-500 mt-0.5">AI 根据 Brief 生成分场景脚本</p>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="isConfirmed" class="inline-flex items-center gap-1.5 text-xs text-green-400 bg-green-900/30 border border-green-800/50 px-2.5 py-1 rounded-full">
          <span class="w-1.5 h-1.5 rounded-full bg-green-400"/>已确认
        </span>
        <span v-else-if="script" class="inline-flex items-center gap-1.5 text-xs text-yellow-400 bg-yellow-900/30 border border-yellow-800/50 px-2.5 py-1 rounded-full">
          <span class="w-1.5 h-1.5 rounded-full bg-yellow-400"/>待确认
        </span>
        <span v-if="script" class="text-xs text-gray-600">v{{ script.version_no }}</span>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-6 py-5 space-y-4 min-h-0">
      <!-- Error -->
      <div v-if="error" class="p-3 bg-red-900/40 border border-red-700/60 rounded-xl text-red-300 text-sm">{{ error }}</div>

      <!-- Loading -->
      <div v-if="loading && !script" class="flex flex-col items-center justify-center py-24 text-gray-500">
        <svg class="w-8 h-8 animate-spin text-blue-400 mb-3" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <p class="text-sm">AI 正在生成脚本...</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="!script" class="flex flex-col items-center justify-center py-24 text-center">
        <div class="w-14 h-14 rounded-2xl bg-gray-900 border border-gray-800 flex items-center justify-center text-2xl mb-4">📝</div>
        <p class="text-sm text-gray-400 mb-1">还没有脚本</p>
        <p class="text-xs text-gray-600 mb-5">请先完成并确认 Brief</p>
        <RouterLink :to="`/projects/${projectId}/brief`"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors">
          前往 Brief
        </RouterLink>
      </div>

      <!-- Script content -->
      <div v-else class="space-y-3">
        <!-- Title -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
          <p class="text-xs text-gray-500 mb-1">标题</p>
          <h3 class="text-base font-semibold text-white">{{ script.title || '未命名脚本' }}</h3>
          <p class="text-xs text-gray-600 mt-1">语言：{{ script.language }}</p>
        </div>

        <!-- Sections -->
        <div
          v-for="(sec, i) in script.sections"
          :key="i"
          class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden"
        >
          <!-- Scene header -->
          <div class="flex items-center justify-between px-4 py-2.5 bg-gray-800/40 border-b border-gray-800">
            <div class="flex items-center gap-2">
              <span class="text-xs font-mono text-blue-400 bg-blue-900/30 px-2 py-0.5 rounded">
                Scene {{ sec.scene_number ?? (i + 1) }}
              </span>
              <span v-if="sec.title" class="text-sm text-gray-300 font-medium">{{ sec.title }}</span>
            </div>
            <span v-if="sec.duration_seconds" class="text-xs text-gray-500">{{ sec.duration_seconds }}s</span>
          </div>

          <div class="p-4 space-y-3">
            <!-- Narration -->
            <div v-if="sec.narration">
              <p class="text-xs text-gray-500 mb-1.5 flex items-center gap-1.5">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/>
                </svg>
                旁白
              </p>
              <p class="text-sm text-gray-200 leading-relaxed">{{ sec.narration }}</p>
            </div>

            <!-- Visual description -->
            <div v-if="sec.visual_description">
              <p class="text-xs text-gray-500 mb-1.5 flex items-center gap-1.5">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                </svg>
                画面描述
              </p>
              <p class="text-sm text-gray-400 italic leading-relaxed">{{ sec.visual_description }}</p>
            </div>

            <!-- Fallback JSON -->
            <pre v-if="!sec.narration && !sec.visual_description"
              class="text-xs text-gray-500 overflow-auto bg-gray-800 rounded p-2">{{ JSON.stringify(sec, null, 2) }}</pre>
          </div>
        </div>

        <!-- Full text fallback -->
        <div v-if="script.full_text && !script.sections?.length"
          class="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <pre class="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">{{ script.full_text }}</pre>
        </div>
      </div>
    </div>

    <!-- Footer actions -->
    <div v-if="script" class="px-6 py-4 border-t border-gray-800 flex-shrink-0">
      <div v-if="!isConfirmed" class="flex items-center justify-end">
        <button
          @click="doConfirm"
          :disabled="loading"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-green-700 hover:bg-green-600 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          {{ loading ? '确认中...' : '确认脚本，生成分镜' }}
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
          脚本已确认，分镜正在生成
        </div>
        <RouterLink :to="`/projects/${projectId}/storyboard`"
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors">
          查看分镜
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
import { scriptsApi, storyboardsApi } from '@/api'
import type { Script } from '@/types'

const route = useRoute()
const projectId = computed(() => route.params.id as string)

const script = ref<Script | null>(null)
const loading = ref(false)
const error = ref('')
const isConfirmed = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const data = await scriptsApi.getByProject(projectId.value)
    const items = data?.items ?? []
    if (items.length > 0) {
      script.value = items[0]
      const { useProjectStore } = await import('@/stores/projects')
      const store = useProjectStore()
      isConfirmed.value = !!store.current?.current_script_version_id
    }
  } catch { /* none yet */ } finally {
    loading.value = false
  }
})

async function doConfirm() {
  if (!script.value) return
  loading.value = true
  error.value = ''
  try {
    await scriptsApi.confirm(projectId.value, script.value.id)
    isConfirmed.value = true
    try { await storyboardsApi.generate(projectId.value, script.value.id) } catch { /* non-fatal */ }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '确认失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
