<template>
  <div class="flex h-[calc(100vh-56px)] overflow-hidden">
    <!-- Left sidebar: pipeline nav -->
    <aside class="w-44 bg-gray-900 border-r border-gray-800 flex-shrink-0 flex flex-col">
      <div class="p-3 border-b border-gray-800">
        <RouterLink to="/projects" class="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors mb-2">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
          所有项目
        </RouterLink>
        <p v-if="store.current" class="text-sm text-white font-medium truncate leading-tight">
          {{ store.current.name }}
        </p>
        <p v-if="store.current" class="text-xs text-gray-600 mt-0.5">
          {{ store.current.aspect_ratio ?? '16:9' }} · {{ store.current.language ?? 'zh-CN' }}
        </p>
      </div>

      <nav class="flex-1 p-2 space-y-0.5">
        <RouterLink
          v-for="step in pipelineSteps"
          :key="step.path"
          :to="`/projects/${projectId}/${step.path}`"
          class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors group"
          :class="isActive(step.path)
            ? 'bg-blue-600/20 text-blue-400 border border-blue-600/30'
            : 'text-gray-400 hover:text-white hover:bg-gray-800'"
        >
          <span class="text-base">{{ step.icon }}</span>
          <div class="flex-1 min-w-0">
            <span class="block truncate">{{ step.label }}</span>
          </div>
          <!-- Step status indicator -->
          <span
            v-if="getStepStatus(step.path) === 'done'"
            class="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0"
          />
          <span
            v-else-if="getStepStatus(step.path) === 'active'"
            class="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse flex-shrink-0"
          />
        </RouterLink>
      </nav>

      <!-- Project status -->
      <div class="p-3 border-t border-gray-800">
        <div class="text-xs text-gray-600 space-y-1">
          <div class="flex items-center justify-between">
            <span>状态</span>
            <span class="text-gray-400 capitalize">{{ store.current?.status ?? '—' }}</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- Center: main content -->
    <main class="flex-1 overflow-y-auto bg-gray-950 min-w-0">
      <div v-if="store.loading && !store.current" class="flex items-center justify-center h-full text-gray-500 text-sm">
        加载项目...
      </div>
      <RouterView v-else @agent-action="handleAgentAction" />
    </main>

    <!-- Right: Agent chat panel -->
    <aside class="w-72 flex-shrink-0 flex flex-col">
      <AgentChat
        ref="agentChatRef"
        :step="currentStep"
        @action="handleAgentAction"
      />
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, RouterView, RouterLink } from 'vue-router'
import { useProjectStore } from '@/stores/projects'
import AgentChat from '@/components/AgentChat.vue'

const route = useRoute()
const store = useProjectStore()
const projectId = computed(() => route.params.id as string)
const agentChatRef = ref<InstanceType<typeof AgentChat> | null>(null)

const pipelineSteps = [
  { path: 'brief',      icon: '💡', label: 'Brief'   },
  { path: 'script',     icon: '📝', label: '脚本'    },
  { path: 'storyboard', icon: '🎞', label: '分镜'    },
  { path: 'timeline',   icon: '⏱', label: '时间轴'  },
  { path: 'render',     icon: '🎬', label: '导出'    },
]

const currentStep = computed(() => {
  const path = route.path
  for (const s of pipelineSteps) {
    if (path.endsWith(`/${s.path}`)) return s.path
  }
  return 'brief'
})

function isActive(path: string) {
  return route.path.endsWith(`/${path}`)
}

// Determine step completion from project state
function getStepStatus(path: string): 'done' | 'active' | 'pending' {
  const p = store.current
  if (!p) return 'pending'
  if (isActive(path)) return 'active'
  const doneMap: Record<string, boolean> = {
    brief:      !!p.current_brief_version_id,
    script:     !!p.current_script_version_id,
    storyboard: !!p.current_storyboard_version_id,
    timeline:   !!p.current_timeline_version_id,
    render:     false,
  }
  return doneMap[path] ? 'done' : 'pending'
}

// Handle action events from AgentChat or child views
function handleAgentAction(payload: { type: string; text: string }) {
  // Child views can emit their own actions; parent orchestrates
  // For now, log — in future this would dispatch to an agent API
  console.log('[AgentAction]', payload)
}

// Show welcome message when step changes
watch(currentStep, (step) => {
  const welcome: Record<string, string> = {
    brief:      '请输入你的创意描述，我将帮你生成结构化 Brief。',
    script:     'Brief 已就绪，点击「生成脚本」或告诉我如何调整。',
    storyboard: '脚本已确认，我将按场景拆分每个镜头并生成分镜。',
    timeline:   '分镜确认后，我会自动装配多轨道时间轴。',
    render:     '选择输出格式和分辨率，提交渲染任务。',
  }
  if (agentChatRef.value && welcome[step]) {
    agentChatRef.value.addSystemMessage(welcome[step])
  }
}, { immediate: false })

onMounted(() => {
  store.fetchOne(projectId.value)

  // Show welcome for initial step
  setTimeout(() => {
    const welcome: Record<string, string> = {
      brief:      '请输入你的创意描述，我将帮你生成结构化 Brief。',
      script:     'Brief 已就绪，点击「生成脚本」或告诉我如何调整。',
      storyboard: '脚本已确认，我将按场景拆分每个镜头并生成分镜。',
      timeline:   '分镜确认后，我会自动装配多轨道时间轴。',
      render:     '选择输出格式和分辨率，提交渲染任务。',
    }
    const msg = welcome[currentStep.value]
    if (agentChatRef.value && msg) {
      agentChatRef.value.addSystemMessage(msg)
    }
  }, 500)
})
</script>
