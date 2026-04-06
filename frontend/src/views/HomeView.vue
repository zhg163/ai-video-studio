<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
    <h1 class="text-5xl font-bold mb-4">
      <span class="text-blue-400">AI</span> Video Studio
    </h1>
    <p class="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
      从创意到成片，AI 多智能体视频制作平台。输入一句话，自动生成完整视频脚本、分镜、配音和时间轴。
    </p>
    <div class="flex justify-center gap-4">
      <RouterLink
        to="/projects"
        class="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors"
      >
        开始创作
      </RouterLink>
    </div>

    <div class="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
      <div
        v-for="step in steps"
        :key="step.title"
        class="bg-gray-900 border border-gray-800 rounded-xl p-6"
      >
        <div class="text-3xl mb-3">{{ step.icon }}</div>
        <h3 class="font-semibold text-white mb-2">{{ step.title }}</h3>
        <p class="text-gray-400 text-sm">{{ step.desc }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

const steps = [
  {
    icon: '✍️',
    title: 'Brief → Script → Storyboard',
    desc: 'AI 自动将创意转化为专业脚本和分镜，支持确认和重新生成。',
  },
  {
    icon: '🎬',
    title: 'Shot 图片/视频生成',
    desc: '每个分镜调用 GPT Image 或 Kling 3.0 生成对应的视觉素材。',
  },
  {
    icon: '🎵',
    title: 'Timeline 装配与导出',
    desc: '自动装配时间轴，添加 TTS 配音，FFmpeg 合成成片。',
  },
]
</script>
