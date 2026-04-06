<template>
  <span
    class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
    :class="cls"
  >
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const map: Record<string, { cls: string; label: string }> = {
  draft: { cls: 'bg-gray-700 text-gray-300', label: '草稿' },
  brief_ready: { cls: 'bg-yellow-900/60 text-yellow-300', label: 'Brief 完成' },
  script_ready: { cls: 'bg-orange-900/60 text-orange-300', label: '脚本完成' },
  storyboard_ready: { cls: 'bg-purple-900/60 text-purple-300', label: '分镜完成' },
  shots_ready: { cls: 'bg-blue-900/60 text-blue-300', label: '素材完成' },
  timeline_ready: { cls: 'bg-cyan-900/60 text-cyan-300', label: '时间轴完成' },
  rendering: { cls: 'bg-indigo-900/60 text-indigo-300', label: '渲染中' },
  completed: { cls: 'bg-green-900/60 text-green-300', label: '已完成' },
  confirmed: { cls: 'bg-green-900/60 text-green-300', label: '已确认' },
  generated: { cls: 'bg-blue-900/60 text-blue-300', label: '已生成' },
  pending: { cls: 'bg-gray-700 text-gray-400', label: '待处理' },
  failed: { cls: 'bg-red-900/60 text-red-300', label: '失败' },
}

const cls = computed(() => map[props.status]?.cls ?? 'bg-gray-700 text-gray-400')
const label = computed(() => map[props.status]?.label ?? props.status)
</script>
