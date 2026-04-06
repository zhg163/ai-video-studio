<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="mb-6">
      <h2 class="text-xl font-bold text-white mb-1">分镜</h2>
      <p class="text-gray-400 text-sm">AI 根据脚本生成每个镜头的分镜描述，确认后可生成图片/视频素材。</p>
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
        <StatusBadge :status="storyboard.status" />
        <span class="text-sm text-gray-400">{{ storyboard.shots?.length ?? 0 }} 个镜头</span>
      </div>

      <!-- Shot grid -->
      <div
        v-if="storyboard.shots?.length"
        class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6"
      >
        <div
          v-for="shot in storyboard.shots"
          :key="shot.shot_number"
          class="bg-gray-900 border border-gray-800 rounded-xl p-4"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs text-blue-400 font-medium">
              Shot {{ shot.shot_number }} / Scene {{ shot.scene_number }}
            </span>
            <span class="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">
              {{ shot.shot_type }}
            </span>
          </div>
          <p class="text-sm text-gray-200 mb-1">{{ shot.action }}</p>
          <p class="text-xs text-gray-500">{{ shot.composition }}</p>
          <div v-if="shot.dialogue" class="mt-2 text-xs text-yellow-300 italic">
            "{{ shot.dialogue }}"
          </div>
          <div class="mt-2 text-xs text-gray-600">{{ shot.duration_seconds }}s</div>
        </div>
      </div>

      <!-- Actions -->
      <div v-if="storyboard.status !== 'confirmed'" class="flex justify-end gap-3">
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
import StatusBadge from '@/components/ui/StatusBadge.vue'

const route = useRoute()
const projectId = computed(() => route.params.id as string)

const storyboard = ref<Storyboard | null>(null)
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  loading.value = true
  try {
    const data = await storyboardsApi.getByProject(projectId.value)
    const item = Array.isArray(data) ? data[0] : data
    if (item) storyboard.value = item
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
    await storyboardsApi.confirm(storyboard.value.id)
    storyboard.value = await storyboardsApi.get(storyboard.value.id)
    // Auto-assemble timeline
    await timelinesApi.assemble(projectId.value)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed'
  } finally {
    loading.value = false
  }
}
</script>
