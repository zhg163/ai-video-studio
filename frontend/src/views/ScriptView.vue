<template>
  <div class="p-6 max-w-3xl mx-auto">
    <div class="mb-6">
      <h2 class="text-xl font-bold text-white mb-1">脚本</h2>
      <p class="text-gray-400 text-sm">AI 根据 Brief 自动生成分场景脚本，确认后进入分镜制作。</p>
    </div>

    <div v-if="error" class="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm">
      {{ error }}
    </div>

    <div v-if="loading" class="text-gray-500 text-center py-20">AI 正在生成脚本...</div>

    <div v-else-if="!script" class="text-center py-20 text-gray-500">
      <p class="mb-4">还没有脚本，请先完成并确认 Brief。</p>
      <RouterLink
        :to="`/projects/${projectId}/brief`"
        class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
      >
        前往 Brief
      </RouterLink>
    </div>

    <div v-else class="space-y-4">
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="font-semibold text-white">{{ script.title || '未命名脚本' }} v{{ script.version_no }}</h3>
            <p class="text-xs text-gray-500 mt-0.5">语言：{{ script.language }}</p>
          </div>
          <div>
            <span v-if="isConfirmed" class="text-xs text-green-400 bg-green-900/40 px-2 py-0.5 rounded-full">已确认</span>
            <span v-else class="text-xs text-yellow-400 bg-yellow-900/40 px-2 py-0.5 rounded-full">待确认</span>
          </div>
        </div>

        <!-- Sections / scenes -->
        <div v-if="script.sections?.length" class="space-y-3 mb-4">
          <div
            v-for="(sec, i) in script.sections"
            :key="i"
            class="bg-gray-800/60 rounded-lg p-4 border border-gray-700"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs text-blue-400 font-medium uppercase">
                Scene {{ sec.scene_number ?? (i + 1) }}
                <template v-if="sec.title"> — {{ sec.title }}</template>
              </span>
              <span v-if="sec.duration_seconds" class="text-xs text-gray-500">{{ sec.duration_seconds }}s</span>
            </div>
            <p v-if="sec.narration" class="text-sm text-gray-200 mb-2">{{ sec.narration }}</p>
            <p v-if="sec.visual_description" class="text-xs text-gray-500 italic">{{ sec.visual_description }}</p>
            <!-- Generic fallback for unknown section shape -->
            <pre v-if="!sec.narration && !sec.visual_description" class="text-xs text-gray-500 overflow-auto">{{ JSON.stringify(sec, null, 2) }}</pre>
          </div>
        </div>

        <!-- full_text fallback -->
        <div v-if="script.full_text && !script.sections?.length" class="mb-4">
          <pre class="text-sm text-gray-300 whitespace-pre-wrap">{{ script.full_text }}</pre>
        </div>

        <!-- Actions -->
        <div v-if="!isConfirmed" class="flex justify-end gap-3 pt-4 border-t border-gray-800">
          <button
            @click="doConfirm"
            :disabled="loading"
            class="px-4 py-2 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
          >
            确认脚本，生成分镜 →
          </button>
        </div>

        <div v-else class="flex items-center justify-between pt-4 border-t border-gray-800">
          <span class="text-sm text-green-400">脚本已确认</span>
          <RouterLink
            :to="`/projects/${projectId}/storyboard`"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
          >
            前往分镜 →
          </RouterLink>
        </div>
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
  } catch {
    // none yet
  } finally {
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
    try {
      await storyboardsApi.generate(projectId.value, script.value.id)
    } catch {
      // non-fatal
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed'
  } finally {
    loading.value = false
  }
}
</script>
