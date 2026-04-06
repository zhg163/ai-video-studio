<template>
  <!-- Agent Chat Panel -->
  <div class="flex flex-col h-full bg-gray-900 border-l border-gray-800">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-800 flex-shrink-0">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full" :class="statusDotClass" />
        <span class="text-sm font-medium text-white">AI Agent</span>
      </div>
      <span class="text-xs text-gray-500">{{ stepLabel }}</span>
    </div>

    <!-- Messages -->
    <div ref="messagesEl" class="flex-1 overflow-y-auto px-4 py-3 space-y-4 min-h-0">
      <!-- Empty state -->
      <div v-if="!messages.length" class="flex flex-col items-center justify-center h-full text-center">
        <div class="text-4xl mb-3">🤖</div>
        <p class="text-sm text-gray-500 leading-relaxed">
          在此输入指令，Agent 将自动<br>分析并执行当前步骤。
        </p>
      </div>

      <!-- Message list -->
      <template v-for="msg in messages" :key="msg.id">
        <!-- User message -->
        <div v-if="msg.role === 'user'" class="flex justify-end">
          <div class="max-w-[85%] bg-blue-600/20 border border-blue-600/30 rounded-2xl rounded-tr-sm px-3 py-2">
            <p class="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">{{ msg.content }}</p>
          </div>
        </div>

        <!-- Assistant message -->
        <div v-else class="flex flex-col gap-2">
          <!-- Agent thought steps -->
          <div
            v-if="msg.thoughtSteps?.length"
            class="bg-gray-800/60 border border-gray-700/50 rounded-xl p-3 space-y-1.5"
          >
            <p class="text-xs text-gray-500 mb-2 font-medium">Agent 分析</p>
            <div
              v-for="step in msg.thoughtSteps"
              :key="step.id"
              class="flex items-center gap-2"
            >
              <!-- step icon -->
              <span class="flex-shrink-0 w-4 h-4 flex items-center justify-center">
                <svg v-if="step.status === 'done'" class="w-3.5 h-3.5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                </svg>
                <svg v-else-if="step.status === 'failed'" class="w-3.5 h-3.5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/>
                </svg>
                <svg v-else-if="step.status === 'running'" class="w-3.5 h-3.5 text-blue-400 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                <span v-else class="w-3 h-3 rounded-full bg-gray-600" />
              </span>
              <span
                class="text-xs"
                :class="{
                  'text-gray-300': step.status === 'done',
                  'text-red-400': step.status === 'failed',
                  'text-blue-300': step.status === 'running',
                  'text-gray-500': step.status === 'pending',
                }"
              >{{ step.label }}</span>
            </div>
          </div>

          <!-- Message bubble -->
          <div v-if="msg.content" class="max-w-[90%] bg-gray-800 border border-gray-700 rounded-2xl rounded-tl-sm px-3 py-2">
            <p class="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">{{ msg.content }}</p>
          </div>

          <!-- Typing indicator -->
          <div
            v-if="msg.agentStatus === 'thinking' || msg.agentStatus === 'generating'"
            class="flex items-center gap-1.5 px-1"
          >
            <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:0ms"/>
            <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:150ms"/>
            <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:300ms"/>
          </div>
        </div>
      </template>
    </div>

    <!-- Suggestions (quick actions) -->
    <div v-if="suggestions.length && !isAgentRunning" class="px-4 pb-2 flex flex-wrap gap-1.5">
      <button
        v-for="s in suggestions"
        :key="s"
        @click="sendMessage(s)"
        class="px-2.5 py-1 text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 rounded-full transition-colors"
      >
        {{ s }}
      </button>
    </div>

    <!-- Input -->
    <div class="px-3 pb-3 flex-shrink-0">
      <div class="flex items-end gap-2 bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 focus-within:border-blue-500 transition-colors">
        <textarea
          v-model="inputText"
          ref="inputEl"
          :disabled="isAgentRunning"
          rows="1"
          placeholder="输入指令或描述..."
          class="flex-1 bg-transparent text-sm text-gray-200 placeholder-gray-500 outline-none resize-none max-h-32 leading-5"
          @keydown.enter.exact.prevent="handleEnter"
          @input="autoResize"
        />
        <button
          @click="handleEnter"
          :disabled="!inputText.trim() || isAgentRunning"
          class="flex-shrink-0 w-7 h-7 flex items-center justify-center bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors"
        >
          <svg v-if="!isAgentRunning" class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
          <svg v-else class="w-3.5 h-3.5 text-white animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
        </button>
      </div>
      <p class="text-xs text-gray-600 mt-1 text-center">Enter 发送 · Shift+Enter 换行</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import type { ChatMessage, AgentThoughtStep, AgentStatus } from '@/types'

const props = defineProps<{
  step: string   // 'brief' | 'script' | 'storyboard' | 'timeline' | 'render'
}>()

const emit = defineEmits<{
  (e: 'action', payload: { type: string; text: string }): void
}>()

const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const inputEl = ref<HTMLTextAreaElement | null>(null)
const messagesEl = ref<HTMLDivElement | null>(null)
const isAgentRunning = ref(false)

// Step-specific labels
const stepLabels: Record<string, string> = {
  brief: 'Brief 阶段',
  script: '脚本阶段',
  storyboard: '分镜阶段',
  timeline: '时间轴',
  render: '导出阶段',
}
const stepLabel = computed(() => stepLabels[props.step] ?? props.step)

// Status dot
const agentStatus = ref<AgentStatus>('idle')
const statusDotClass = computed(() => ({
  'bg-green-400': agentStatus.value === 'idle',
  'bg-blue-400 animate-pulse': agentStatus.value === 'thinking' || agentStatus.value === 'generating',
  'bg-yellow-400 animate-pulse': agentStatus.value === 'searching',
  'bg-red-400': agentStatus.value === 'failed',
  'bg-gray-500': agentStatus.value === 'done',
}))

// Quick action suggestions per step
const suggestions = computed(() => {
  const map: Record<string, string[]> = {
    brief: ['AI 生成 Brief', '查看结构化摘要', '修改目标受众'],
    script: ['生成完整脚本', '调整场景数量', '修改旁白风格'],
    storyboard: ['生成分镜', '查看所有镜头', '修改镜头构图'],
    timeline: ['装配时间轴', '查看轨道', '调整转场'],
    render: ['开始渲染', '查看导出状态'],
  }
  return map[props.step] ?? []
})

// Thought step templates per step
function buildThoughtSteps(step: string): AgentThoughtStep[] {
  const templates: Record<string, string[]> = {
    brief: ['解析输入文本', '提取主题与基调', '分析目标受众', '生成结构化 Brief'],
    script: ['读取 Brief 内容', '规划场景结构', '生成旁白文本', '完成脚本'],
    storyboard: ['解析脚本场景', '规划镜头序列', '生成镜头描述', '分配首尾帧策略'],
    timeline: ['读取分镜数据', '计算时间节点', '装配视频轨道', '添加字幕轨道'],
    render: ['校验时间轴', '准备渲染参数', '提交渲染队列'],
  }
  return (templates[step] ?? ['处理中']).map((label, i) => ({
    id: `step-${i}`,
    label,
    status: 'pending' as const,
  }))
}

async function sendMessage(text: string) {
  if (!text.trim() || isAgentRunning.value) return
  inputText.value = ''
  autoResize()

  // Add user message
  const userMsg: ChatMessage = {
    id: `u-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: Date.now(),
  }
  messages.value.push(userMsg)
  await scrollToBottom()

  // Emit to parent (parent handles actual API calls)
  emit('action', { type: props.step, text })

  // Simulate agent thought process
  isAgentRunning.value = true
  agentStatus.value = 'thinking'

  const thoughtSteps = buildThoughtSteps(props.step)
  const assistantMsg: ChatMessage = {
    id: `a-${Date.now()}`,
    role: 'assistant',
    content: '',
    timestamp: Date.now(),
    thoughtSteps,
    agentStatus: 'thinking',
  }
  messages.value.push(assistantMsg)
  await scrollToBottom()

  // Animate thought steps
  for (let i = 0; i < thoughtSteps.length; i++) {
    await sleep(400 + Math.random() * 300)
    thoughtSteps[i].status = 'running'
    await scrollToBottom()
    await sleep(600 + Math.random() * 400)
    thoughtSteps[i].status = 'done'
    await scrollToBottom()
  }

  assistantMsg.agentStatus = 'done'
  agentStatus.value = 'idle'
  isAgentRunning.value = false
  await scrollToBottom()
}

// Expose method so parent can trigger agent with a system message
function addSystemMessage(content: string, status: AgentStatus = 'done') {
  const msg: ChatMessage = {
    id: `sys-${Date.now()}`,
    role: 'assistant',
    content,
    timestamp: Date.now(),
    agentStatus: status,
  }
  messages.value.push(msg)
  scrollToBottom()
}

function addThinkingMessage(thoughtSteps: AgentThoughtStep[]) {
  const msg: ChatMessage = {
    id: `think-${Date.now()}`,
    role: 'assistant',
    content: '',
    timestamp: Date.now(),
    thoughtSteps,
    agentStatus: 'thinking',
  }
  messages.value.push(msg)
  isAgentRunning.value = true
  agentStatus.value = 'thinking'
  scrollToBottom()
  return msg
}

function resolveThinkingMessage(msg: ChatMessage, content: string, success = true) {
  if (msg.thoughtSteps) {
    msg.thoughtSteps.forEach(s => {
      if (s.status !== 'done') s.status = success ? 'done' : 'failed'
    })
  }
  msg.content = content
  msg.agentStatus = success ? 'done' : 'failed'
  isAgentRunning.value = false
  agentStatus.value = success ? 'idle' : 'failed'
  scrollToBottom()
}

defineExpose({ addSystemMessage, addThinkingMessage, resolveThinkingMessage, buildThoughtSteps })

function handleEnter() {
  if (inputText.value.trim()) sendMessage(inputText.value.trim())
}

function autoResize() {
  const el = inputEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 128)}px`
}

async function scrollToBottom() {
  await nextTick()
  const el = messagesEl.value
  if (el) el.scrollTop = el.scrollHeight
}

function sleep(ms: number) {
  return new Promise(r => setTimeout(r, ms))
}

// Watch for step changes to show welcome
watch(() => props.step, (step) => {
  if (!messages.value.length) return
  // optionally add a step context message
}, { immediate: false })
</script>
