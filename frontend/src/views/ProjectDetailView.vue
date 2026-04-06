<template>
  <div class="flex h-[calc(100vh-56px)]">
    <!-- Sidebar pipeline nav -->
    <aside class="w-48 bg-gray-900 border-r border-gray-800 flex-shrink-0 flex flex-col">
      <div class="p-4 border-b border-gray-800">
        <p class="text-xs text-gray-500 mb-1">项目</p>
        <p v-if="store.current" class="text-sm text-white font-medium truncate">
          {{ store.current.name }}
        </p>
        <RouterLink to="/projects" class="text-xs text-gray-500 hover:text-gray-300 transition-colors">
          ← 所有项目
        </RouterLink>
      </div>

      <nav class="flex-1 p-3 space-y-1">
        <RouterLink
          v-for="step in pipelineSteps"
          :key="step.path"
          :to="`/projects/${projectId}/${step.path}`"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors"
          :class="isActive(step.path)
            ? 'bg-blue-600/20 text-blue-400 border border-blue-600/30'
            : 'text-gray-400 hover:text-white hover:bg-gray-800'"
        >
          <span>{{ step.icon }}</span>
          <span>{{ step.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <!-- Main content -->
    <main class="flex-1 overflow-y-auto bg-gray-950">
      <div v-if="store.loading" class="flex items-center justify-center h-full text-gray-500">
        加载中...
      </div>
      <RouterView v-else />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, RouterView, RouterLink } from 'vue-router'
import { useProjectStore } from '@/stores/projects'

const route = useRoute()
const store = useProjectStore()
const projectId = computed(() => route.params.id as string)

const pipelineSteps = [
  { path: 'brief', icon: '💡', label: 'Brief' },
  { path: 'script', icon: '📝', label: '脚本' },
  { path: 'storyboard', icon: '🎞', label: '分镜' },
  { path: 'timeline', icon: '⏱', label: '时间轴' },
  { path: 'render', icon: '🎬', label: '导出' },
]

function isActive(path: string) {
  return route.path.endsWith(`/${path}`)
}

onMounted(() => store.fetchOne(projectId.value))
</script>
