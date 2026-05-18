<script setup lang="ts">
import { Clock } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { taskStatusRasterImgAttrs } from '@/views/tasks/task-status-media'
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

const platformRowIcon = {
  src: '/Frame.png',
  srcset: '/Frame@2x.png 2x',
} as const

const statusLabels: Record<TaskRunStatus, string> = {
  pending_run: '待运行',
  running: '运行中',
  completed: '已完成',
  stopped: '已停止',
  failed: '失败',
}

const statusTextModifier: Record<TaskRunStatus, string> = {
  pending_run: 'pending-run',
  running: 'running',
  completed: 'completed',
  stopped: 'stopped',
  failed: 'failed',
}

function primaryActionLabel(status: TaskRunStatus): string {
  switch (status) {
    case 'running':
      return '停止'
    case 'completed':
      return '重启'
    case 'stopped':
      return '启动'
    case 'pending_run':
      return '重试'
    case 'failed':
      return '重试'
  }
}

const showEdit = computed(() => props.row.status !== 'running')

/** 驱动「X 分钟后开始」等相对时间文案定期重算 */
const scheduleClockTick = ref(Date.now())
let scheduleClockTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  scheduleClockTimer = setInterval(() => {
    scheduleClockTick.value = Date.now()
  }, 30_000)
})

onUnmounted(() => {
  if (scheduleClockTimer) {
    clearInterval(scheduleClockTimer)
    scheduleClockTimer = null
  }
})

/** 定时/单次任务副文案（相对生效时间等） */
const scheduleSubtitle = computed(() => {
  void scheduleClockTick.value
  const row = props.row
  if (row.taskTypeLabel === '单次任务') {
    return row.dateLabel !== '—' ? `单次任务 · ${row.dateLabel}` : '单次任务'
  }
  const eff = row.effectiveAtRaw
  if (!eff?.trim()) {
    return row.dateLabel !== '—' ? `定时任务 · ${row.dateLabel}` : '定时任务'
  }
  const t = dayjs(eff.trim())
  if (!t.isValid()) {
    return `定时任务 · ${row.dateLabel}`
  }
  const now = dayjs(scheduleClockTick.value)
  if (t.isAfter(now)) {
    const mins = t.diff(now, 'minute')
    if (mins < 60) return `定时任务 · ${Math.max(1, mins)} 分钟后开始`
    const h = Math.ceil(t.diff(now, 'hour', true))
    if (h < 24) return `定时任务 · ${h} 小时后开始`
    const d = Math.ceil(t.diff(now, 'day', true))
    return `定时任务 · ${d} 天后开始`
  }
  const minsPast = now.diff(t, 'minute')
  if (minsPast < 60) return `定时任务 · ${Math.max(1, minsPast)} 分钟前`
  const hPast = Math.floor(now.diff(t, 'hour', true))
  if (hPast < 24) return `定时任务 · ${hPast} 小时前`
  const dPast = Math.floor(now.diff(t, 'day', true))
  return `定时任务 · ${dPast} 天前`
})

const showPrimaryAction = computed(() => true)

function onPrimary() {
  emit('primaryAction', props.row)
}
</script>

<template>
  <div class="task-list-card">
    <div class="space-y-2.5 p-4">
      <div class="task-list-card__title-row flex min-w-0 items-center justify-between gap-2">
        <div class="task-list-card__title-left min-w-0 flex-1">
          <span
            v-if="row.notificationCount > 0 && row.status !== 'running'"
            class="mb-1.5 inline-block rounded-md bg-sky-100 px-2 py-0.5 text-[11px] font-medium text-sky-800"
          >
            {{ row.notificationCount > 99 ? '99+' : row.notificationCount }} 条新数据
          </span>
          <h3 class="truncate text-left text-sm font-semibold leading-snug text-slate-900">
            {{ row.name }}
          </h3>
        </div>
        <div class="task-list-card__title-right shrink-0">
          <div
            class="task-status-wrap"
            :class="`task-status-wrap--${statusTextModifier[row.status]}`"
          >
            <span class="task-status-badge-icon" aria-hidden="true">
              <img
                class="task-status-badge-img"
                v-bind="taskStatusRasterImgAttrs(row.status)"
                alt=""
                decoding="async"
              />
            </span>
            <span
              class="task-status-text"
              :class="`task-status-text--${statusTextModifier[row.status]}`"
            >
              {{ statusLabels[row.status] }}
            </span>
          </div>
        </div>
      </div>

      <div
        class="task-list-card__meta-row flex min-w-0 flex-row flex-nowrap items-center justify-between gap-3 text-[12px] leading-snug text-slate-500"
      >
        <span class="task-meta-cell task-meta-cell--left">
          <span class="task-meta-icon-slot" aria-hidden="true">
            <img
              class="task-list-card__platform-icon"
              :src="platformRowIcon.src"
              :srcset="platformRowIcon.srcset"
              width="12"
              height="12"
              alt=""
              decoding="async"
            />
          </span>
          <span class="min-w-0 truncate">{{ row.platformsLabel }}</span>
        </span>
        <span class="task-meta-cell task-meta-cell--right">
          <span class="task-meta-icon-slot task-meta-icon-slot--clock" aria-hidden="true">
            <el-icon class="task-meta-clock-icon text-slate-400" :size="12">
              <Clock />
            </el-icon>
          </span>
          <span class="min-w-0 truncate">{{ scheduleSubtitle }}</span>
        </span>
      </div>
    </div>

    <div
      class="task-list-card__actions flex flex-nowrap items-center gap-2 border-t border-[#DEE0E3] px-3"
    >
      <template v-if="row.status === 'running' || row.status === 'pending_run'">
        <span
          v-if="row.status === 'running' && row.notificationCount > 0"
          class="task-running-new-count shrink-0"
        >
          {{ row.notificationCount > 99 ? '99+' : row.notificationCount }}条新数据
        </span>
        <div class="task-list-card__actions-trailing ml-auto flex shrink-0 items-center gap-2">
          <button
            type="button"
            class="task-action-btn task-action-btn--stop-neutral"
            :disabled="primaryLoading"
            @click.stop="onPrimary"
          >
            停止
          </button>
          <button
            type="button"
            class="task-action-btn task-action-btn--outline-blue"
            @click.stop="emit('view', row)"
          >
            查看
          </button>
        </div>
      </template>
      <template v-else-if="row.status === 'completed'">
        <div class="task-list-card__actions-trailing ml-auto flex shrink-0 items-center gap-2">
          <button type="button" class="task-action-completed-delete" @click.stop="emit('delete', row)">
            删除
          </button>
          <button
            type="button"
            class="task-action-btn task-action-btn--outline-blue"
            @click.stop="emit('view', row)"
          >
            查看
          </button>
          <button
            type="button"
            class="task-action-completed-restart"
            :disabled="primaryLoading"
            @click.stop="onPrimary"
          >
            重启
          </button>
        </div>
      </template>
      <template v-else>
        <div class="task-list-card__actions-trailing ml-auto flex shrink-0 flex-wrap items-center justify-end gap-2">
          <button
            type="button"
            class="rounded px-2 py-1 text-xs font-medium text-red-600 transition-colors hover:bg-red-50"
            @click.stop="emit('delete', row)"
          >
            删除
          </button>
          <button
            type="button"
            class="task-action-btn task-action-btn--outline-blue"
            @click.stop="emit('view', row)"
          >
            查看
          </button>
          <button
            v-if="showEdit"
            type="button"
            class="task-action-btn task-action-btn--outline-blue"
            @click.stop="emit('edit', row)"
          >
            编辑
          </button>
          <button
            v-if="showPrimaryAction"
            type="button"
            class="task-action-completed-restart"
            :disabled="primaryLoading"
            @click.stop="onPrimary"
          >
            {{ primaryActionLabel(row.status) }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.task-meta-cell {
  box-sizing: border-box;
  display: inline-flex;
  min-width: 0;
  align-items: center;
  gap: 6px;
  line-height: 1.25;
}

.task-meta-cell--left {
  max-width: 48%;
}

.task-meta-cell--right {
  flex: 1 1 0;
  justify-content: flex-end;
  text-align: right;
}

.task-meta-icon-slot {
  box-sizing: border-box;
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
}

.task-meta-icon-slot--clock {
  width: 14px;
  height: 14px;
}

.task-meta-clock-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  line-height: 0;
}

.task-meta-clock-icon :deep(svg) {
  display: block;
}

.task-list-card__platform-icon {
  display: block;
  width: 12px;
  height: 12px;
  object-fit: contain;
}

.task-list-card {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 100%;
  margin-left: 0;
  margin-right: 0;
  overflow: hidden;
  background: #ffffff;
  border-radius: 4px;
  border: 1px solid #dee0e3;
}

.task-list-card__actions {
  box-sizing: border-box;
  height: 60px;
  min-height: 60px;
}

.task-list-card__actions-trailing {
  flex-shrink: 0;
}

.task-running-new-count {
  box-sizing: border-box;
  display: inline-flex;
  width: 76px;
  height: 28px;
  align-items: center;
  justify-content: flex-start;
  padding: 0 6px;
  overflow: hidden;
  background: #f5f6f7;
  border-radius: 2px;
  font-weight: 500;
  font-size: 12px;
  color: #3370ff;
  text-align: left;
  font-style: normal;
  text-transform: none;
  line-height: 1.2;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.task-action-btn {
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0 12px;
  height: 28px;
  font-size: 13px;
  font-weight: 400;
  line-height: 1;
  cursor: pointer;
  transition: opacity 0.15s ease, background-color 0.15s ease;
}

.task-action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.task-action-btn--stop-neutral {
  background: #ffffff;
  border-radius: 2px;
  border: 1px solid #bbbfc4;
  color: #0f1114;
}

.task-action-btn--stop-neutral:hover:not(:disabled) {
  background: #f8f9fa;
}

.task-action-btn--outline-blue {
  width: 52px;
  min-width: 52px;
  padding: 0;
  background: #ffffff;
  border-radius: 2px;
  border: 1px solid #1f22f6;
  color: #1f22f6;
  font-weight: 500;
}

.task-action-btn--outline-blue:hover:not(:disabled) {
  background: rgba(31, 34, 246, 0.06);
}

.task-action-completed-delete {
  box-sizing: border-box;
  display: inline-flex;
  width: max-content;
  min-width: 28px;
  height: 20px;
  align-items: center;
  justify-content: flex-start;
  padding: 0;
  margin: 0;
  border: none;
  background: transparent;
  font-family: 'PingFang SC', 'PingFang SC', system-ui, -apple-system, sans-serif;
  font-weight: 400;
  font-size: 14px;
  color: #f54a45;
  text-align: left;
  font-style: normal;
  text-transform: none;
  line-height: 20px;
  cursor: pointer;
}

.task-action-completed-delete:hover {
  opacity: 0.88;
}

.task-action-completed-restart {
  box-sizing: border-box;
  display: inline-flex;
  width: 52px;
  height: 28px;
  align-items: center;
  justify-content: center;
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 2px;
  background: #1f22f6;
  color: #ffffff;
  font-size: 13px;
  font-weight: 500;
  line-height: 1;
  cursor: pointer;
  transition: opacity 0.15s ease, background-color 0.15s ease;
}

.task-action-completed-restart:hover:not(:disabled) {
  background: #1719c4;
}

.task-action-completed-restart:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.task-list-card__title-row {
  align-items: center;
}

.task-list-card__title-left {
  display: flex;
  min-width: 0;
  flex: 1 1 0;
  flex-direction: column;
  align-items: flex-start;
}

.task-list-card__title-right {
  flex-shrink: 0;
}

.task-status-wrap {
  box-sizing: border-box;
  display: inline-flex;
  width: 72px;
  height: 29px;
  min-width: 72px;
  min-height: 29px;
  max-width: 72px;
  align-items: center;
  justify-content: center;
  column-gap: 3px;
  row-gap: 0;
  padding: 0 4px;
  overflow: hidden;
  border-radius: 50px;
}

.task-status-wrap--pending-run {
  background: #ededfe;
}

.task-status-wrap--running {
  background: rgba(51, 112, 255, 0.08);
}

@keyframes task-status-running-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.task-status-wrap--running .task-status-badge-icon {
  animation: task-status-running-spin 1.1s linear infinite;
}

@media (prefers-reduced-motion: reduce) {
  .task-status-wrap--running .task-status-badge-icon {
    animation: none;
  }
}

.task-status-wrap--completed {
  background: rgba(52, 199, 36, 0.08);
}

.task-status-wrap--stopped {
  background: rgba(255, 136, 0, 0.08);
}

.task-status-wrap--failed {
  background: rgba(245, 74, 69, 0.08);
}

.task-status-badge-icon {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  transform-origin: center center;
}

.task-status-badge-img {
  display: block;
  max-width: 14px;
  max-height: 14px;
  width: auto;
  height: auto;
  margin: 0;
  object-fit: contain;
  object-position: center;
}

.task-status-text {
  display: inline-flex;
  min-width: 0;
  align-items: center;
  align-self: stretch;
  overflow: hidden;
  font-size: 11px;
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.task-status-text--pending-run {
  color: #1f22f6;
}

.task-status-text--running {
  color: #3370ff;
}

.task-status-text--completed {
  color: #34c724;
}

.task-status-text--stopped {
  color: #ff8800;
}

.task-status-text--failed {
  color: #f54a45;
}
</style>
