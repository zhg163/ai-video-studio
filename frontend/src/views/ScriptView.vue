<template>
  <div class="p-6 max-w-3xl mx-auto">
    <div class="mb-6">
      <h2 class="text-xl font-bold text-white mb-1">脚本</h2>
      <p class="text-gray-400 text-sm">AI 根据 Brief 自动生成分场景脚本，你可以确认后进入分镜制作。</p>
    </div>

    <div v-if="error" class="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm">
      {{ error }}
    </div>

    <div v-if="loading" class="text-gray-500 text-center py-20">
      AI 正在生成脚本...
    </div>

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
            <h3 class="font-semibold text-white">{{ script.title || '未命名脚本' }}</h3>
            <p v-if="script.total_duration_seconds" class="text-sm text-gray-400 mt-0.5">
              总时长：{{ script.total_duration_seconds }} 秒
            </p>
          </div>
          <StatusBadge :status="script.status" />
        </div>

        <!-- Scenes -->
        <div v-if="script.scenes?.length" class="space-y-3">
          <div
            v-for="scene in script.scenes"
            :key="scene.scene_number"
            class="bg-gray-800/60 rounded-lg p-4 border border-gray-700"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs text-blue-400 font-medium uppercase">
                Scene {{ scene.scene_number }} — {{ scene.title }}
              </span>
              <span class="text-xs text-gray-500">{{ scene.duration_seconds }}s</span>
            </div>
            <p class="text-sm text-gray-200 mb-2">{{ scene.narration }}</p>
            <p class="text-xs text-gray-500 italic">{{ scene.visual_description }}</p>
          </div>
        </div>

        <!-- Actions -->
        <div v-if="script.status !== 'confirmed'" class="flex justify-end gap-3 pt-4 border-t border-gray-800 mt-4">
          <button
            @click="doRegenerate"
            :disabled="loading"
            class="px-4 py-2 text-sm border border-gray-700 text-gray-400 hover:text-white rounded-lg transition-colors disabled:opacity-50"
          >
            重新生成
          </button>
          <button
            @click="doConfirm"
            :disabled="loading"
            class="px-4 py-2 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
          >
            确认脚本，生成分镜 →
          </button>
        </div>

        <div v-else class="flex items-center justify-between pt-4 border-t border-gray-800 mt-4">
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
import StatusBadge from '@/components/ui/StatusBadge.vue'

const route = useRoute()
const projectId = computed(() => route.params.id as string)

const script = ref<Script | null>(null)
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  loading.value = true
  try {
    // Try to fetch latest script for project (backend returns list or single)
    const data = await scriptsApi.getByProject(projectId.value)
    const item = Array.isArray(data) ? data[0] : data
    if (item) script.value = item
  } catch {
    // none yet
  } finally {
    loading.value = false
  }
})

async function doRegenerate() {
  if (!script.value) return
  loading.value = true
  error.value = ''
  try {
    script.value = await scriptsApi.regenerate(script.value.id)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed'
  } finally {
    loading.value = false
  }
}

async function doConfirm() {
  if (!script.value) return
  loading.value = true
  error.value = ''
  try {
    await scriptsApi.confirm(script.value.id)
    script.value = await scriptsApi.get(script.value.id)
    // Auto-trigger storyboard generation
    await storyboardsApi.generate(projectId.value, script.value.id)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed'
  } finally {
    loading.value = false
  }
}
</script>
