<template>
  <div class="p-6 max-w-3xl mx-auto">
    <div class="mb-6">
      <h2 class="text-xl font-bold text-white mb-1">Brief — 创意输入</h2>
      <p class="text-gray-400 text-sm">描述你想要创作的视频，AI 将自动分析并生成结构化创意摘要。</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm">
      {{ error }}
    </div>

    <!-- Input area (no brief yet or can regenerate) -->
    <div v-if="!brief || brief.status !== 'confirmed'" class="mb-6">
      <textarea
        v-model="rawInput"
        rows="4"
        :disabled="loading"
        placeholder="例：为我们公司新产品「智能耳机 X1」制作一个30秒的社交媒体宣传视频，风格科技感强，目标用户是18-30岁的年轻人..."
        class="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none text-sm"
      />
      <div class="flex justify-end mt-3 gap-3">
        <button
          v-if="brief"
          @click="doRegenerate"
          :disabled="loading"
          class="px-4 py-2 text-sm border border-gray-600 hover:border-gray-400 text-gray-300 hover:text-white rounded-lg transition-colors disabled:opacity-50"
        >
          重新生成
        </button>
        <button
          @click="doGenerate"
          :disabled="loading || !rawInput.trim()"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {{ loading ? '生成中...' : brief ? '重新生成' : 'AI 生成 Brief' }}
        </button>
      </div>
    </div>

    <!-- Brief result card -->
    <div v-if="brief" class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="font-semibold text-white">Brief 摘要</h3>
        <StatusBadge :status="brief.status" />
      </div>

      <div class="grid grid-cols-2 gap-4 text-sm">
        <div v-if="brief.theme">
          <p class="text-gray-500 mb-1">主题</p>
          <p class="text-gray-200">{{ brief.theme }}</p>
        </div>
        <div v-if="brief.tone">
          <p class="text-gray-500 mb-1">基调</p>
          <p class="text-gray-200">{{ brief.tone }}</p>
        </div>
        <div v-if="brief.duration_seconds">
          <p class="text-gray-500 mb-1">时长</p>
          <p class="text-gray-200">{{ brief.duration_seconds }} 秒</p>
        </div>
        <div v-if="brief.target_audience">
          <p class="text-gray-500 mb-1">目标受众</p>
          <p class="text-gray-200">{{ brief.target_audience }}</p>
        </div>
      </div>

      <div v-if="brief.key_messages?.length">
        <p class="text-gray-500 text-sm mb-2">核心信息</p>
        <ul class="space-y-1">
          <li
            v-for="(msg, i) in brief.key_messages"
            :key="i"
            class="text-sm text-gray-300 flex items-start gap-2"
          >
            <span class="text-blue-400 mt-0.5">•</span>{{ msg }}
          </li>
        </ul>
      </div>

      <!-- Confirm / Edit button -->
      <div v-if="brief.status !== 'confirmed'" class="flex justify-end gap-3 pt-2 border-t border-gray-800">
        <button
          @click="showInput = !showInput"
          class="px-4 py-2 text-sm border border-gray-700 text-gray-400 hover:text-white rounded-lg transition-colors"
        >
          修改输入
        </button>
        <button
          @click="doConfirm"
          :disabled="loading"
          class="px-4 py-2 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {{ loading ? '确认中...' : '确认 Brief，生成脚本 →' }}
        </button>
      </div>

      <!-- Confirmed state: go to script -->
      <div v-else class="flex items-center justify-between pt-2 border-t border-gray-800">
        <span class="text-sm text-green-400">Brief 已确认</span>
        <RouterLink
          :to="`/projects/${projectId}/script`"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          前往脚本 →
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
import StatusBadge from '@/components/ui/StatusBadge.vue'

const route = useRoute()
const projectId = computed(() => route.params.id as string)

const brief = ref<Brief | null>(null)
const rawInput = ref('')
const loading = ref(false)
const error = ref('')
const showInput = ref(false)

onMounted(async () => {
  try {
    const data = await briefsApi.getByProject(projectId.value)
    // API returns list or single item
    const item = Array.isArray(data) ? data[0] : data
    if (item) {
      brief.value = item
      rawInput.value = item.raw_input || ''
    }
  } catch {
    // no brief yet, that's ok
  }
})

async function doGenerate() {
  if (!rawInput.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    brief.value = await briefsApi.generate(projectId.value, rawInput.value)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to generate brief'
  } finally {
    loading.value = false
  }
}

async function doRegenerate() {
  if (!brief.value) return
  loading.value = true
  error.value = ''
  try {
    brief.value = await briefsApi.regenerate(brief.value.id)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to regenerate'
  } finally {
    loading.value = false
  }
}

async function doConfirm() {
  if (!brief.value) return
  loading.value = true
  error.value = ''
  try {
    await briefsApi.confirm(brief.value.id)
    // Refresh brief
    brief.value = await briefsApi.get(brief.value.id)
    // Auto-trigger script generation
    await scriptsApi.generate(projectId.value, brief.value.id)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to confirm'
  } finally {
    loading.value = false
  }
}
</script>
