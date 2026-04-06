<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="mb-6">
      <h2 class="text-xl font-bold text-white mb-1">时间轴</h2>
      <p class="text-gray-400 text-sm">查看自动装配的时间轴，确认无误后进行渲染导出。</p>
    </div>

    <div v-if="error" class="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm">
      {{ error }}
    </div>

    <div v-if="loading" class="text-gray-500 text-center py-20">加载时间轴...</div>

    <div v-else-if="!timeline" class="text-center py-20 text-gray-500">
      <p class="mb-4">还没有时间轴，请先确认分镜。</p>
      <RouterLink
        :to="`/projects/${projectId}/storyboard`"
        class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
      >
        前往分镜
      </RouterLink>
    </div>

    <div v-else class="space-y-4">
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="font-semibold text-white">时间轴</h3>
            <p v-if="timeline.total_duration_seconds" class="text-sm text-gray-400 mt-0.5">
              总时长：{{ timeline.total_duration_seconds }}s
            </p>
          </div>
          <StatusBadge :status="timeline.status" />
        </div>

        <!-- Visual timeline -->
        <div v-if="timeline.clips?.length" class="space-y-2 mb-6">
          <div
            v-for="clip in timeline.clips"
            :key="clip.shot_id"
            class="flex items-center gap-3"
          >
            <div class="text-xs text-gray-500 w-8 text-right">{{ clip.start_time.toFixed(1) }}s</div>
            <div
              class="h-8 rounded bg-blue-600/40 border border-blue-500/30 flex items-center px-2"
              :style="{ width: `${Math.max(60, (clip.end_time - clip.start_time) * 20)}px` }"
            >
              <span class="text-xs text-blue-300 truncate">Shot {{ clip.shot_id.slice(0, 6) }}</span>
            </div>
            <div class="text-xs text-gray-600">{{ (clip.end_time - clip.start_time).toFixed(1) }}s</div>
          </div>
        </div>

        <div class="flex justify-end">
          <RouterLink
            :to="`/projects/${projectId}/render`"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
          >
            渲染导出 →
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { timelinesApi } from '@/api'
import type { Timeline } from '@/types'
import StatusBadge from '@/components/ui/StatusBadge.vue'

const route = useRoute()
const projectId = computed(() => route.params.id as string)

const timeline = ref<Timeline | null>(null)
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  loading.value = true
  try {
    const data = await timelinesApi.getByProject(projectId.value)
    const item = Array.isArray(data) ? data[0] : data
    if (item) timeline.value = item
  } catch {
    // none yet
  } finally {
    loading.value = false
  }
})
</script>
