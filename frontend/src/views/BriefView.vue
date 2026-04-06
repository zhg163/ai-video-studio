<template>
  <div class="h-full flex flex-col">
    <!-- Top bar -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 flex-shrink-0">
      <div>
        <h2 class="text-base font-semibold text-white">Creative Brief</h2>
        <p class="text-xs text-gray-500 mt-0.5">描述你的创意构想，AI 生成结构化摘要</p>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="isConfirmed" class="inline-flex items-center gap-1.5 text-xs text-green-400 bg-green-900/30 border border-green-800/50 px-2.5 py-1 rounded-full">
          <span class="w-1.5 h-1.5 rounded-full bg-green-400"/>
          已确认
        </span>
        <span v-else-if="brief" class="inline-flex items-center gap-1.5 text-xs text-yellow-400 bg-yellow-900/30 border border-yellow-800/50 px-2.5 py-1 rounded-full">
          <span class="w-1.5 h-1.5 rounded-full bg-yellow-400"/>
          待确认
        </span>
        <span v-if="brief" class="text-xs text-gray-600">v{{ brief.version_no }}</span>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
      <!-- Error -->
      <div v-if="error" class="p-3 bg-red-900/40 border border-red-700/60 rounded-xl text-red-300 text-sm flex items-start gap-2">
        <svg class="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856C18.448 19 19 18.296 19 17.5V6.5C19 5.704 18.448 5 17.918 5H6.082C5.552 5 5 5.704 5 6.5v11c0 .796.552 1.5 1.062 1.5z"/>
        </svg>
        {{ error }}
      </div>

      <!-- Input area (show when no brief OR editing) -->
      <div v-if="!brief || showInput" class="space-y-3">
        <div class="bg-gray-900 border border-gray-700 rounded-xl p-4 focus-within:border-blue-500 transition-colors">
          <p class="text-xs text-gray-500 mb-2 font-medium">创意描述</p>
          <textarea
            v-model="inputText"
            rows="5"
            :disabled="loading"
            placeholder="例：为我们的新产品「智能耳机 X1」制作一个30秒的社交媒体宣传视频，风格科技感强，目标用户是18-30岁的年轻人，展示降噪功能和时尚设计..."
            class="w-full bg-transparent text-sm text-gray-200 placeholder-gray-600 outline-none resize-none leading-relaxed"
          />
        </div>

        <!-- Settings row -->
        <div class="grid grid-cols-3 gap-2">
          <div class="bg-gray-900 border border-gray-800 rounded-lg p-3">
            <p class="text-xs text-gray-500 mb-1.5">视频时长</p>
            <select v-model="duration" class="w-full bg-transparent text-sm text-gray-300 outline-none">
              <option value="15">15 秒</option>
              <option value="30">30 秒</option>
              <option value="60">60 秒</option>
              <option value="90">90 秒</option>
              <option value="120">2 分钟</option>
            </select>
          </div>
          <div class="bg-gray-900 border border-gray-800 rounded-lg p-3">
            <p class="text-xs text-gray-500 mb-1.5">画幅比例</p>
            <select v-model="aspectRatio" class="w-full bg-transparent text-sm text-gray-300 outline-none">
              <option value="16:9">横屏 16:9</option>
              <option value="9:16">竖屏 9:16</option>
              <option value="1:1">方形 1:1</option>
            </select>
          </div>
          <div class="bg-gray-900 border border-gray-800 rounded-lg p-3">
            <p class="text-xs text-gray-500 mb-1.5">叙事模式</p>
            <select v-model="narrativeMode" class="w-full bg-transparent text-sm text-gray-300 outline-none">
              <option value="auto">自动</option>
              <option value="storytelling">故事驱动</option>
              <option value="product">产品展示</option>
              <option value="documentary">纪录片</option>
            </select>
          </div>
        </div>

        <div class="flex justify-end gap-2">
          <button
            v-if="brief && showInput"
            @click="showInput = false"
            class="px-4 py-2 text-sm text-gray-400 hover:text-white border border-gray-700 hover:border-gray-600 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            @click="doGenerate"
            :disabled="loading || !inputText.trim()"
            class="inline-flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
          >
            <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <span>{{ loading ? 'AI 分析中...' : 'AI 生成 Brief' }}</span>
          </button>
        </div>
      </div>

      <!-- Brief result -->
      <div v-if="brief && !showInput" class="space-y-4">
        <!-- Source quote -->
        <div class="bg-gray-900/60 border-l-2 border-blue-500/50 pl-3 py-2 pr-3 rounded-r-lg">
          <p class="text-xs text-gray-500 mb-1">原始输入</p>
          <p class="text-sm text-gray-300 italic leading-relaxed">"{{ brief.source_input?.text }}"</p>
        </div>

        <!-- Structured brief grid -->
        <div class="grid grid-cols-2 gap-3">
          <div v-if="brief.structured_brief?.theme" class="bg-gray-900 border border-gray-800 rounded-xl p-3.5">
            <p class="text-xs text-gray-500 mb-1.5 flex items-center gap-1.5">
              <span class="text-blue-400">◆</span> 主题
            </p>
            <p class="text-sm text-gray-200 leading-snug">{{ brief.structured_brief.theme }}</p>
          </div>
          <div v-if="brief.structured_brief?.tone" class="bg-gray-900 border border-gray-800 rounded-xl p-3.5">
            <p class="text-xs text-gray-500 mb-1.5 flex items-center gap-1.5">
              <span class="text-purple-400">◆</span> 基调
            </p>
            <p class="text-sm text-gray-200 leading-snug">{{ brief.structured_brief.tone }}</p>
          </div>
          <div v-if="brief.structured_brief?.target_audience" class="bg-gray-900 border border-gray-800 rounded-xl p-3.5">
            <p class="text-xs text-gray-500 mb-1.5 flex items-center gap-1.5">
              <span class="text-green-400">◆</span> 目标受众
            </p>
            <p class="text-sm text-gray-200 leading-snug">{{ brief.structured_brief.target_audience }}</p>
          </div>
          <div v-if="brief.structured_brief?.duration_seconds" class="bg-gray-900 border border-gray-800 rounded-xl p-3.5">
            <p class="text-xs text-gray-500 mb-1.5 flex items-center gap-1.5">
              <span class="text-yellow-400">◆</span> 时长
            </p>
            <p class="text-sm text-gray-200">{{ brief.structured_brief.duration_seconds }} 秒</p>
          </div>
          <div v-if="brief.structured_brief?.visual_style" class="bg-gray-900 border border-gray-800 rounded-xl p-3.5">
            <p class="text-xs text-gray-500 mb-1.5 flex items-center gap-1.5">
              <span class="text-pink-400">◆</span> 视觉风格
            </p>
            <p class="text-sm text-gray-200 leading-snug">{{ brief.structured_brief.visual_style }}</p>
          </div>
          <div v-if="brief.structured_brief?.sound_mood" class="bg-gray-900 border border-gray-800 rounded-xl p-3.5">
            <p class="text-xs text-gray-500 mb-1.5 flex items-center gap-1.5">
              <span class="text-orange-400">◆</span> 音效基调
            </p>
            <p class="text-sm text-gray-200 leading-snug">{{ brief.structured_brief.sound_mood }}</p>
          </div>
        </div>

        <!-- Key messages -->
        <div v-if="keyMessages.length" class="bg-gray-900 border border-gray-800 rounded-xl p-3.5">
          <p class="text-xs text-gray-500 mb-2.5 font-medium">核心信息</p>
          <ul class="space-y-2">
            <li v-for="(msg, i) in keyMessages" :key="i" class="flex items-start gap-2.5">
              <span class="flex-shrink-0 w-5 h-5 rounded-full bg-blue-600/20 border border-blue-600/30 flex items-center justify-center text-xs text-blue-400 mt-0.5">{{ i + 1 }}</span>
              <span class="text-sm text-gray-300 leading-snug">{{ msg }}</span>
            </li>
          </ul>
        </div>

        <!-- Extra fields -->
        <details class="group">
          <summary class="text-xs text-gray-600 cursor-pointer hover:text-gray-400 flex items-center gap-1">
            <svg class="w-3 h-3 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
            完整 Brief 数据
          </summary>
          <pre class="mt-2 text-xs bg-gray-900 border border-gray-800 rounded-lg p-3 overflow-auto text-gray-500">{{ JSON.stringify(brief.structured_brief, null, 2) }}</pre>
        </details>
      </div>
    </div>

    <!-- Action footer -->
    <div v-if="brief && !showInput" class="px-6 py-4 border-t border-gray-800 flex-shrink-0">
      <div v-if="!isConfirmed" class="flex items-center justify-between">
        <button
          @click="showInput = true"
          class="text-sm text-gray-400 hover:text-white flex items-center gap-1.5 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
          </svg>
          重新输入
        </button>
        <button
          @click="doConfirm"
          :disabled="loading"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-green-700 hover:bg-green-600 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          {{ loading ? '确认中...' : '确认 Brief，生成脚本' }}
          <svg v-if="!loading" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
          </svg>
        </button>
      </div>
      <div v-else class="flex items-center justify-between">
        <div class="flex items-center gap-2 text-green-400 text-sm">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          Brief 已确认，脚本正在生成
        </div>
        <RouterLink
          :to="`/projects/${projectId}/script`"
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          查看脚本
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
          </svg>
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
const duration = ref('30')
const aspectRatio = ref('16:9')
const narrativeMode = ref('auto')
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
      const { useProjectStore } = await import('@/stores/projects')
      const store = useProjectStore()
      isConfirmed.value = !!store.current?.current_brief_version_id
    }
  } catch { /* no brief yet */ }
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
    error.value = e instanceof Error ? e.message : '生成失败，请重试'
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
    try { await scriptsApi.generate(projectId.value, brief.value.id) } catch { /* non-fatal */ }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '确认失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
