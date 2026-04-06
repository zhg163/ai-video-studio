<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-10">
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-bold text-white">项目列表</h1>
      <button
        @click="showCreate = true"
        class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
      >
        + 新建项目
      </button>
    </div>

    <!-- Create Dialog -->
    <div
      v-if="showCreate"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
      @click.self="showCreate = false"
    >
      <div class="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold text-white mb-4">新建项目</h2>
        <form @submit.prevent="handleCreate">
          <div class="mb-4">
            <label class="block text-sm text-gray-400 mb-1">项目名称 *</label>
            <input
              v-model="form.name"
              type="text"
              required
              placeholder="例：产品发布宣传片"
              class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div class="mb-6">
            <label class="block text-sm text-gray-400 mb-1">描述（可选）</label>
            <textarea
              v-model="form.description"
              rows="3"
              placeholder="项目简介..."
              class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
            />
          </div>
          <div class="flex justify-end gap-3">
            <button
              type="button"
              @click="showCreate = false"
              class="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="store.loading"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {{ store.loading ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="store.error"
      class="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm"
    >
      {{ store.error }}
    </div>

    <!-- Loading -->
    <div v-if="store.loading && !store.projects.length" class="text-gray-500 text-center py-20">
      加载中...
    </div>

    <!-- Empty -->
    <div
      v-else-if="!store.projects.length"
      class="text-center py-20 text-gray-500"
    >
      <div class="text-5xl mb-4">🎬</div>
      <p>还没有项目，点击「新建项目」开始创作</p>
    </div>

    <!-- Project grid -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <RouterLink
        v-for="project in store.projects"
        :key="project.id"
        :to="`/projects/${project.id}/brief`"
        class="block bg-gray-900 border border-gray-800 hover:border-gray-600 rounded-xl p-5 transition-colors group"
      >
        <div class="flex items-start justify-between mb-3">
          <h3 class="font-semibold text-white group-hover:text-blue-400 transition-colors truncate">
            {{ project.name }}
          </h3>
          <StatusBadge :status="project.status" />
        </div>
        <p v-if="project.description" class="text-gray-400 text-sm line-clamp-2 mb-3">
          {{ project.description }}
        </p>
        <p class="text-xs text-gray-600">
          {{ formatDate(project.created_at) }}
        </p>
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useProjectStore } from '@/stores/projects'
import StatusBadge from '@/components/ui/StatusBadge.vue'

const store = useProjectStore()
const router = useRouter()
const showCreate = ref(false)
const form = ref({ name: '', description: '' })

onMounted(() => store.fetchAll())

async function handleCreate() {
  try {
    const p = await store.create(form.value.name, form.value.description || undefined)
    showCreate.value = false
    form.value = { name: '', description: '' }
    router.push(`/projects/${p.id}/brief`)
  } catch {
    // error is shown via store.error
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
</script>
