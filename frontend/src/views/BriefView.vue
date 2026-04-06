<template>
  <div class="p-6 max-w-3xl mx-auto">
    <div class="mb-6">
      <h2 class="text-xl font-bold text-white mb-1">Brief — 创意输入</h2>
      <p class="text-gray-400 text-sm">描述你想要创作的视频，AI 将自动分析并生成结构化创意摘要。</p>
    </div>

    <div v-if="error" class="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm">
      {{ error }}
    </div>

    <!-- Input area -->
    <div v-if="!brief || showInput" class="mb-6">
      <textarea
        v-model="inputText"
        rows="4"
        :disabled="loading"
        placeholder="例：为我们公司新产品「智能耳机 X1」制作一个30秒的社交媒体宣传视频，风格科技感强，目标用户是18-30岁的年轻人..."
        class="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none text-sm"
      />
      <div class="flex justify-end mt-3 gap-3">
        <button
          v-if="brief && showInput"
          @click="showInput = false"
          class="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          取消
        </button>
        <button
          @click="doGenerate"
          :disabled="loading || !inputText.trim()"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {{ loading ? 'AI 生成中...' : 'AI 生成 Brief' }}
        </button>
      </div>
    </div>

    <!-- Brief result card -->
    <div v-if="brief && !showInput" class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="font-semibold text-white">Brief v{{ brief.version_no }}</h3>
        <div class="flex items-center gap-2">
          <span v-if="isConfirmed" class="text-xs text-green-400 bg-green-900/40 px-2 py-0.5 rounded-full">已确认</span>
          <span v-else class="text-xs text-yellow-400 bg-yellow-900/40 px-2 py-0.5 rounded-full">待确认</span>
        </div>
      </div>

      <!-- Source input -->
      <div class="text-sm text-gray-400 bg-gray-800/50 rounded-lg p-3 italic">
        "{{ brief.source_input?.text }}"
      </div>

      <!-- Structured brief fields -->
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div v-if="brief.structured_brief?.theme">
          <p class="text-gray-500 mb-1">主题</p>
          <p class="text-gray-200">{{ brief.structured_brief.theme }}</p>
        </div>
        <div v-if="brief.structured_brief?.tone">
          <p class="text-gray-500 mb-1">基调</p>
          <p class="text-gray-200">{{ brief.structured_brief.tone }}</p>
        </div>
        <div v-if="brief.structured_brief?.duration_seconds">
          <p class="text-gray-500 mb-1">时长</p>
          <p class="text-gray-200">{{ brief.structured_brief.duration_seconds }} 秒</p>
        </div>
        <div v-if="brief.structured_brief?.target_audience">
          <p class="text-gray-500 mb-1">目标受众</p>
          <p class="text-gray-200">{{ brief.structured_brief.target_audience }}</p>
        </div>
      </div>

      <div v-if="keyMessages.length">
        <p class="text-gray-500 text-sm mb-2">核心信息</p>
        <ul class="space-y-1">
          <li v-for="(msg, i) in keyMessages" :key="i" class="text-sm text-gray-300 flex items-start gap-2">
            <span class="text-blue-400 mt-0.5">•</span>{{ msg }}
          </li>
        </ul>
      </div>

      <!-- Unknown fields fallback -->
      <details class="text-xs text-gray-600">
        <summary class="cursor-pointer hover:text-gray-400">完整 Brief 数据</summary>
        <pre class="mt-2 bg-gray-800 rounded p-3 overflow-auto text-gray-400">{{ JSON.stringify(brief.structured_brief, null, 2) }}</pre>
      </details>

      <!-- Actions: not confirmed -->
      <div v-if="!isConfirmed" class="flex justify-end gap-3 pt-2 border-t border-gray-800">
        <button
          @click="showInput = true"
          class="px-4 py-2 text-sm border border-gray-700 text-gray-400 hover:text-white rounded-lg transition-colors"
        >
          重新输入
        </button>
        <button
          @click="doConfirm"
          :disabled="loading"
          class="px-4 py-2 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {{ loading ? '确认中...' : '确认 Brief →' }}
        </button>
      </div>

      <!-- Confirmed -->
      <div v-else class="flex items-center justify-between pt-2 border-t border-gray-800">
        <span class="text-sm text-green-400">Brief 已确认，脚本已触发生成</span>
        <RouterLink
          :to="`/projects/${projectId}/script`"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          查看脚本 →
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { briefsApi, scriptsApi } from '@/api'
import type { Brief } from '@/types'

const route = useRoute()
const projectId = computed(() => route.params.id as string)

const brief = ref<Brief | null>(null)
const inputText = ref('')
const loading = ref(false)
const error = ref('')
const showInput = ref(false)
const isConfirmed = ref(false)

const keyMessages = computed(() => {
  const km = brief.value?.structured_brief?.key_messages
  return Array.isArray(km) ? km : []
})

onMounted(async () => {
  try {
    const data = await briefsApi.getByProject(projectId.value)
    const items = data?.items ?? []
    if (items.length > 0) {
      brief.value = items[0]
      inputText.value = items[0].source_input?.text ?? ''
      // Check if project has confirmed this brief
      const { useProjectStore } = await import('@/stores/projects')
      const store = useProjectStore()
      isConfirmed.value = !!store.current?.current_brief_version_id
    }
  } catch {
    // no brief yet
  }
})

async function doGenerate() {
  if (!inputText.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    brief.value = await briefsApi.generate(projectId.value, inputText.value)
    isConfirmed.value = false
    showInput.value = false
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to generate brief'
  } finally {
    loading.value = false
  }
}

async function doConfirm() {
  if (!brief.value) return
  loading.value = true
  error.value = ''
  try {
    await briefsApi.confirm(projectId.value, brief.value.id)
    isConfirmed.value = true
    // Auto-trigger script generation
    try {
      await scriptsApi.generate(projectId.value, brief.value.id)
    } catch {
      // Script generation failure is non-fatal at this step
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to confirm'
  } finally {
    loading.value = false
  }
}
</script>
