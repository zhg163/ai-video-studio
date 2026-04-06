<template>
  <div class="min-h-[calc(100vh-56px)] flex flex-col items-center justify-center px-4 text-center">
    <!-- Hero -->
    <div class="max-w-2xl mx-auto mb-16">
      <h1 class="text-4xl sm:text-5xl font-bold text-white leading-tight mb-4">
        在 <span class="text-blue-400">AI Video Studio</span>，<br>
        每个人都是自己创意的导演
      </h1>
      <p class="text-lg text-gray-400 mb-10">
        与 AI 协作，创作你的精彩视频 — 从一个想法到完整成片
      </p>

      <RouterLink
        to="/projects"
        class="inline-flex items-center gap-2 px-8 py-3.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-colors text-base"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        即刻创作
      </RouterLink>
    </div>

    <!-- Pipeline steps -->
    <div class="max-w-4xl w-full mx-auto">
      <p class="text-xs text-gray-600 uppercase tracking-widest mb-6">创作流水线</p>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
        <div
          v-for="(step, i) in pipeline"
          :key="step.label"
          class="relative bg-gray-900 border border-gray-800 rounded-xl p-4 text-left"
        >
          <!-- Connector arrow -->
          <div v-if="i < pipeline.length - 1"
            class="hidden md:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-gray-700 text-lg">›</div>
          <div class="text-2xl mb-2">{{ step.icon }}</div>
          <p class="text-sm font-medium text-white mb-1">{{ step.label }}</p>
          <p class="text-xs text-gray-500 leading-snug">{{ step.desc }}</p>
        </div>
      </div>
    </div>

    <!-- Feature highlights -->
    <div class="max-w-3xl w-full mx-auto mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div v-for="feat in features" :key="feat.title"
        class="bg-gray-900/50 border border-gray-800 rounded-xl p-4 text-left">
        <div class="text-xl mb-2">{{ feat.icon }}</div>
        <p class="text-sm font-medium text-white mb-1">{{ feat.title }}</p>
        <p class="text-xs text-gray-500 leading-snug">{{ feat.desc }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

const pipeline = [
  { icon: '💡', label: 'Brief',   desc: '输入创意，AI 结构化分析' },
  { icon: '📝', label: '脚本',    desc: '分场景完整剧本生成' },
  { icon: '🎞', label: '分镜',    desc: '镜头序列 + 首尾帧策略' },
  { icon: '⏱', label: '时间轴',  desc: '多轨道自动装配' },
  { icon: '🎬', label: '成片导出', desc: 'MP4/WebM 高清导出' },
]

const features = [
  {
    icon: '🤖',
    title: 'AI Agent 驱动',
    desc: '每个阶段有专属 Agent 分析、规划、执行，全程可干预',
  },
  {
    icon: '🔄',
    title: '局部重算',
    desc: '任意镜头独立重新生成，不影响其他内容',
  },
  {
    icon: '🎨',
    title: '首尾帧连贯',
    desc: '前一镜头尾帧作为后一镜头首帧，保证视觉连续性',
  },
]
</script>
