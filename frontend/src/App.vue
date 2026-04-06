<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <nav class="border-b border-gray-800 bg-gray-900">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-14">
          <RouterLink to="/" class="flex items-center gap-2 font-bold text-white text-lg">
            <span class="text-blue-400">AI</span> Video Studio
          </RouterLink>
          <RouterLink
            to="/projects"
            class="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Projects
          </RouterLink>
        </div>
      </div>
    </nav>
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
</script>
