<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="min-h-screen flex flex-col bg-slate-950">
    <header class="border-b border-primary-900/30 bg-slate-900/50 backdrop-blur-sm">
      <nav class="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
        <RouterLink
          to="/"
          class="text-xl font-semibold text-primary-300 hover:text-primary-200 transition-colors"
        >
          LangGraph NT View
        </RouterLink>
        <div class="flex gap-4">
          <RouterLink
            to="/"
            class="text-slate-400 hover:text-primary-300 transition-colors"
            active-class="text-primary-400"
          >
            Проекты
          </RouterLink>
        </div>
      </nav>
    </header>
    <main class="flex-1 mx-auto w-full max-w-6xl px-4 py-8">
      <RouterView />
    </main>
    <footer class="border-t border-primary-900/30 py-4 text-center text-sm text-slate-500">
      LangGraph NT View &middot; Тестирование систем
    </footer>
  </div>
</template>
