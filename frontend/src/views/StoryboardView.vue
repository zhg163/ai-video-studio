<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="mb-6">
      <h2 class="text-xl font-bold text-white mb-1">分镜</h2>
      <p class="text-gray-400 text-sm">AI 根据脚本生成每个镜头的分镜描述，确认后可装配时间轴。</p>
    </div>

    <div v-if="error" class="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm">
      {{ error }}
    </div>

    <div v-if="loading" class="text-gray-500 text-center py-20">AI 正在生成分镜...</div>

    <div v-else-if="!storyboard" class="text-center py-20 text-gray-500">
      <p class="mb-4">还没有分镜，请先确认脚本。</p>
      <RouterLink
        :to="`/projects/${projectId}/script`"
        class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
      >
        前往脚本
      </RouterLink>
    </div>

    <div v-else>
      <div class="flex items-center justify-between mb-4">
        <div>
          <span v-if="isConfirmed" class="text-xs text-green-400 bg-green-900/40 px-2 py-0.5 rounded-full">已确认</span>
          <span v-else class="text-xs text-yellow-400 bg-yellow-900/40 px-2 py-0.5 rounded-full">待确认</span>
        </div>
        <span class="text-sm text-gray-400">{{ totalShots }} 个镜头 · v{{ storyboard.version_no }}</span>
      </div>

      <!-- Scenes and shots -->
      <div v-if="storyboard.scenes?.length" class="space-y-4 mb-6">
        <div
          v-for="scene in storyboard.scenes"
          :key="scene.scene_id ?? scene.scene_number"
          class="bg-gray-900 border border-gray-800 rounded-xl p-4"
        >
          <h4 class="text-sm font-medium text-blue-400 mb-3">
            Scene {{ scene.scene_number }}
            <template v-if="scene.title"> — {{ scene.title }}</template>
          </h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div
              v-for="shot in scene.shots"
              :key="shot.shot_id ?? shot.shot_number"
              class="bg-gray-800/60 rounded-lg p-3 border border-gray-700"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs text-gray-400">Shot {{ shot.shot_number }}</span>
                <span v-if="shot.shot_type" class="text-xs text-gray-600 bg-gray-700 px-2 py-0.5 rounded">
                  {{ shot.shot_type }}
                </span>
              </div>
              <p v-if="shot.action" class="text-sm text-gray-200 mb-1">{{ shot.action }}</p>
              <p v-if="shot.composition" class="text-xs text-gray-500">{{ shot.composition }}</p>
              <div v-if="shot.dialogue" class="mt-1 text-xs text-yellow-300 italic">"{{ shot.dialogue }}"</div>
              <div v-if="shot.duration_seconds" class="mt-1 text-xs text-gray-600">{{ shot.duration_seconds }}s</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div v-if="!isConfirmed" class="flex justify-end gap-3">
        <button
          @click="doConfirm"
          :disabled="loading"
          class="px-4 py-2 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
        >
          确认分镜，装配时间轴 →
        </button>
      </div>

      <div v-else class="flex items-center justify-between">
        <span class="text-sm text-green-400">分镜已确认</span>
        <RouterLink
          :to="`/projects/${projectId}/timeline`"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          前往时间轴 →
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
  } catch {
    // none yet
  } finally {
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
    try {
      await timelinesApi.assemble(projectId.value, storyboard.value.id)
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
