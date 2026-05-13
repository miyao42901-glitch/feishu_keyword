<script setup lang="ts">
import { Calendar, Clock, Promotion } from '@element-plus/icons-vue'
import type { TaskCardModel } from '@/views/tasks/types'
import type { TaskRunStatus } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'TaskListCard' })

const props = withDefaults(
  defineProps<{
    row: TaskCardModel
    /** 主操作（停止/启动/重启）请求中 */
    primaryLoading?: boolean
  }>(),
  { primaryLoading: false },
)

const emit = defineEmits<{
  view: [row: TaskCardModel]
  edit: [row: TaskCardModel]
  primaryAction: [row: TaskCardModel]
  delete: [row: TaskCardModel]
}>()

const statusStyles: Record<
  TaskRunStatus,
  { label: string; dot: string; wrap: string; text: string }
> = {
  running: {
    label: '运行中',
    dot: 'bg-emerald-600',
    wrap: 'bg-emerald-50',
    text: 'text-emerald-800',
  },
  completed: {
    label: '已完成',
    dot: 'bg-emerald-600',
    wrap: 'bg-emerald-50',
    text: 'text-emerald-800',
  },
  stopped: {
    label: '已停止',
    dot: 'bg-amber-600',
    wrap: 'bg-amber-50',
    text: 'text-amber-800',
  },
  failed: {
    label: '失败',
    dot: 'bg-red-600',
    wrap: 'bg-red-50',
    text: 'text-red-800',
  },
}

function primaryActionLabel(status: TaskRunStatus): string {
  switch (status) {
    case 'running':
      return '停止'
    case 'completed':
      return '重启'
    case 'stopped':
      return '启动'
    case 'failed':
      return '重启'
  }
}

function onPrimary() {
  emit('primaryAction', props.row)
}
</script>

<template>
  <el-card class="task-list-card relative overflow-visible !border-slate-200/90 shadow-none">
    <div
      v-if="row.notificationCount > 0"
      class="absolute -right-1 -top-1 z-10 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[11px] font-medium text-white shadow-sm ring-2 ring-white"
    >
      {{ row.notificationCount > 99 ? '99+' : row.notificationCount }}
    </div>

    <div class="space-y-3 p-4">
      <div class="flex min-w-0 items-start justify-between gap-2 pr-1">
        <h3 class="min-w-0 flex-1 truncate text-sm font-semibold leading-snug text-slate-800">
          {{ row.name }}
        </h3>
        <span
          class="inline-flex shrink-0 items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium leading-none"
          :class="[statusStyles[row.status].wrap, statusStyles[row.status].text]"
        >
          <span
            class="h-1.5 w-1.5 shrink-0 rounded-full"
            :class="[statusStyles[row.status].dot, row.status === 'running' && 'status-dot-blink']"
          />
          {{ statusStyles[row.status].label }}
        </span>
      </div>

      <div class="flex min-w-0 flex-wrap gap-x-4 gap-y-1.5 text-[11px] leading-tight text-slate-500">
        <span class="inline-flex min-w-0 max-w-full items-center gap-1">
          <el-icon class="shrink-0 text-slate-400" :size="13">
            <Promotion />
          </el-icon>
          <span class="min-w-0 truncate">{{ row.platformsLabel }}</span>
        </span>
        <span class="inline-flex shrink-0 items-center gap-1">
          <el-icon class="text-slate-400" :size="13">
            <Clock />
          </el-icon>
          {{ row.taskTypeLabel }}
        </span>
        <span class="inline-flex shrink-0 items-center gap-1">
          <el-icon class="text-slate-400" :size="13">
            <Calendar />
          </el-icon>
          {{ row.dateLabel }}
        </span>
      </div>
    </div>

    <div class="border-t border-slate-100 px-4 py-2.5">
      <div class="flex flex-wrap items-center gap-x-1 gap-y-1 text-xs">
        <button
          type="button"
          class="cursor-pointer rounded px-2 py-1 text-blue-600 transition-colors hover:bg-blue-50 hover:text-blue-700"
          @click.stop="emit('view', row)"
        >
          查看
        </button>
        <button
          type="button"
          class="cursor-pointer rounded px-2 py-1 text-blue-600 transition-colors hover:bg-blue-50 hover:text-blue-700"
          @click.stop="emit('edit', row)"
        >
          编辑
        </button>
        <el-button
          link
          type="primary"
          class="!px-2 !py-1"
          :loading="primaryLoading"
          :disabled="primaryLoading"
          @click.stop="onPrimary"
        >
          {{ primaryActionLabel(row.status) }}
        </el-button>
        <div class="ml-auto">
          <button
            type="button"
            class="cursor-pointer rounded border border-red-200 bg-red-50 px-2.5 py-1 text-sm text-red-600 transition-colors hover:border-red-300 hover:bg-red-100"
            @click.stop="emit('delete', row)"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.task-list-card :deep(.el-card__body) {
  padding: 0;
}

/* 「运行中」状态圆点闪烁 */
.status-dot-blink {
  animation: status-dot-blink 1s ease-in-out infinite;
}

@keyframes status-dot-blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.28;
  }
}
</style>
