<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <!-- Top nav -->
    <nav class="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-40">
      <div class="max-w-screen-2xl mx-auto px-4 sm:px-6">
        <div class="flex items-center justify-between h-14">
          <!-- Logo -->
          <RouterLink to="/" class="flex items-center gap-2.5 font-bold text-white">
            <div class="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center text-sm">▶</div>
            <span>AI Video Studio</span>
          </RouterLink>

          <!-- Nav links -->
          <div class="flex items-center gap-6">
            <RouterLink
              to="/projects"
              class="text-sm transition-colors"
              :class="$route.path.startsWith('/projects')
                ? 'text-white'
                : 'text-gray-400 hover:text-white'"
            >
              项目
            </RouterLink>
          </div>
        </div>
      </div>
    </nav>

    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { RouterView, RouterLink, useRoute } from 'vue-router'
const $route = useRoute()
</script>
