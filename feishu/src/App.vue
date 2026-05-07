<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import dayjs from '@/lib/dayjs'
import { useCounterStore } from '@/stores/counter'

const counter = useCounterStore()
const now = ref(dayjs().format('YYYY-MM-DD HH:mm:ss'))
let timer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  timer = setInterval(() => {
    now.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const weekday = computed(() => dayjs().format('dddd'))
</script>

<template>
  <div
    class="flex min-h-screen items-center justify-center bg-linear-to-br from-slate-100 to-indigo-100 p-6"
  >
    <el-card class="w-full max-w-md shadow-lg" shadow="hover">
      <template #header>
        <div class="flex flex-col gap-1">
          <span class="text-lg font-semibold text-slate-800">飞书 · Vue 3 · TS · Vite</span>
          <span class="text-xs text-slate-500">Element Plus · Pinia · Tailwind · dayjs · Lark Base JS SDK</span>
        </div>
      </template>
      <div class="space-y-4 text-left">
        <div class="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
          <p class="font-mono text-indigo-600">{{ now }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ weekday }}</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <el-button type="primary" @click="counter.increment">+1</el-button>
          <el-button @click="counter.reset">重置</el-button>
        </div>
        <p class="text-sm text-slate-700">
          计数：<strong>{{ counter.count }}</strong>，双倍：<strong>{{ counter.double }}</strong>
        </p>
      </div>
    </el-card>
  </div>
</template>
