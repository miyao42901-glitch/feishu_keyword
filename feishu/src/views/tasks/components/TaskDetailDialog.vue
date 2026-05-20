<script setup lang="ts">
import { computed } from 'vue'
import dayjs from 'dayjs'
import type { FeishuTaskConfigDetail } from '@/lib/api'
import { platformDisplayNames, sourcePlatforms, DATETIME_FORMAT } from '@/views/TaskCreateForm/constants'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import type { TaskCardModel } from '@/views/tasks/types'
import {
  canTaskAction,
  taskPrimaryActionKind,
  taskPrimaryActionLabel,
} from '@/views/tasks/task-action-matrix'

defineOptions({ name: 'TaskDetailDialog' })

const props = withDefaults(
  defineProps<{
    /** v-model 显示弹框 */
    modelValue: boolean
    detail: FeishuTaskConfigDetail | null
    loading: boolean
    /** 与底部操作对应列表行；无则隐藏底部操作 */
    row?: TaskCardModel | null
    /** 主操作请求中 */
    primaryLoading?: boolean
  }>(),
  { row: null, primaryLoading: false },
)

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  primaryAction: [row: TaskCardModel]
  delete: [row: TaskCardModel]
  edit: [row: TaskCardModel]
}>()

const cfg = computed(() => (props.detail?.config ?? {}) as Record<string, unknown>)

const planName = computed(() => {
  const n = cfg.value.planName
  if (typeof n === 'string' && n.trim()) return n.trim()
  const fallback = props.detail?.plan_name
  return typeof fallback === 'string' && fallback.trim() ? fallback.trim() : '—'
})

const taskTypeLabel = computed(() => {
  const tt = cfg.value.taskType ?? cfg.value.task_type
  return tt === 'realtime' ? '单次任务' : '定时任务'
})

function formatDateTime(raw: unknown): string {
  if (raw == null) return '—'
  const s = String(raw).trim()
  if (!s) return '—'
  const d = dayjs(s)
  return d.isValid() ? d.format(DATETIME_FORMAT) : s
}

const effectiveAtLabel = computed(() =>
  formatDateTime(cfg.value.effectiveAt ?? cfg.value.effective_at),
)
const expireAtLabel = computed(() => formatDateTime(cfg.value.expireAt ?? cfg.value.expire_at))

const selectedSources = computed((): string[] => {
  const raw = cfg.value.selectedSources ?? cfg.value.selected_sources
  if (!Array.isArray(raw)) return []
  return raw
    .filter((x): x is string => typeof x === 'string')
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
})

const platformsLabel = computed(() => {
  const keys = selectedSources.value
  if (!keys.length) return '未选择平台'
  const supported = new Set(sourcePlatforms.map((p) => p.id))
  const normalized = keys.filter((k): k is PlatformKey => k in platformDisplayNames)
  const onlySupported = normalized.filter((k) => supported.has(k))
  if (
    onlySupported.length >= sourcePlatforms.length &&
    sourcePlatforms.every((p) => onlySupported.includes(p.id))
  ) {
    return '全平台'
  }
  const labels = normalized.map((k) => platformDisplayNames[k])
  return labels.length ? labels.join('、') : '未选择平台'
})

const keywordTags = computed(() => {
  const k = cfg.value.keywords
  if (!Array.isArray(k)) return []
  return k
    .filter((x): x is string => typeof x === 'string')
    .map((x) => x.trim())
    .filter((x) => x.length > 0)
})

const excludeTags = computed(() => {
  const raw = cfg.value.excludeKeywords ?? cfg.value.exclude_keywords
  if (Array.isArray(raw)) {
    return raw
      .filter((x): x is string => typeof x === 'string')
      .map((s) => s.trim())
      .filter((x) => x.length > 0)
  }
  if (typeof raw === 'string' && raw.trim()) {
    return raw
      .split(/[\n,，、]+/)
      .map((s) => s.trim())
      .filter(Boolean)
  }
  return []
})

const showFooterActions = computed(() => !props.loading && props.row != null)

const rowStatus = computed(() => props.row?.status)

const showEdit = computed(() => rowStatus.value != null && canTaskAction(rowStatus.value, 'edit'))
const showDelete = computed(() => rowStatus.value != null && canTaskAction(rowStatus.value, 'delete'))
const showStop = computed(() => rowStatus.value != null && canTaskAction(rowStatus.value, 'stop'))
const showRetry = computed(() => rowStatus.value != null && canTaskAction(rowStatus.value, 'retry'))
const primaryKind = computed(() =>
  rowStatus.value != null ? taskPrimaryActionKind(rowStatus.value) : null,
)

function emitPrimary() {
  const r = props.row
  if (r) emit('primaryAction', r)
}

function emitDelete() {
  const r = props.row
  if (r) emit('delete', r)
}

function emitEdit() {
  const r = props.row
  if (r) emit('edit', r)
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="任务详情"
    width="92%"
    class="task-detail-dialog"
    align-center
    destroy-on-close
    :show-close="true"
    :close-on-click-modal="true"
    append-to-body
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="loading" class="task-detail-loading">加载中…</div>
    <div v-else class="task-detail-body">
      <div class="task-detail-item">
        <div class="task-detail-label">任务名称</div>
        <div class="task-detail-value">{{ planName }}</div>
      </div>
      <div class="task-detail-item">
        <div class="task-detail-label">任务类型</div>
        <div class="task-detail-value">{{ taskTypeLabel }}</div>
      </div>
      <div class="task-detail-item">
        <div class="task-detail-label">采集平台</div>
        <div class="task-detail-value">{{ platformsLabel }}</div>
      </div>
      <div class="task-detail-item">
        <div class="task-detail-label">监控关键词</div>
        <div v-if="keywordTags.length" class="task-detail-tags">
          <span v-for="(tag, i) in keywordTags" :key="`kw-${i}`" class="task-detail-tag">{{ tag }}</span>
        </div>
        <div v-else class="task-detail-value">—</div>
      </div>
      <div class="task-detail-item">
        <div class="task-detail-label">排除词</div>
        <div v-if="excludeTags.length" class="task-detail-tags">
          <span v-for="(tag, i) in excludeTags" :key="`ex-${i}`" class="task-detail-tag">{{ tag }}</span>
        </div>
        <div v-else class="task-detail-value">—</div>
      </div>
      <div class="task-detail-item">
        <div class="task-detail-label">任务开始时间</div>
        <div class="task-detail-value">{{ effectiveAtLabel }}</div>
      </div>
      <div class="task-detail-item task-detail-item--last">
        <div class="task-detail-label">任务结束时间</div>
        <div class="task-detail-value">{{ expireAtLabel }}</div>
      </div>
    </div>

    <template v-if="showFooterActions && row" #footer>
      <div class="task-detail-footer">
        <span
          v-if="row.status === 'running' && row.notificationCount > 0"
          class="task-detail-footer__new-count shrink-0"
        >
          {{ row.notificationCount > 99 ? '99+' : row.notificationCount }}条新数据
        </span>
        <div class="task-detail-footer__trailing ml-auto flex shrink-0 flex-wrap items-center justify-end gap-2">
          <button v-if="showDelete" type="button" class="tdf-completed-delete" @click="emitDelete">
            删除
          </button>
          <button v-if="showEdit" type="button" class="tdf-btn tdf-btn--outline-blue" @click="emitEdit">
            编辑
          </button>
          <button
            v-if="showStop"
            type="button"
            class="tdf-btn tdf-btn--stop-neutral"
            :disabled="primaryLoading"
            @click="emitPrimary"
          >
            停止
          </button>
          <button
            v-if="showRetry && primaryKind"
            type="button"
            class="tdf-btn tdf-btn--restart"
            :disabled="primaryLoading"
            @click="emitPrimary"
          >
            {{ taskPrimaryActionLabel(primaryKind) }}
          </button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.task-detail-loading {
  display: flex;
  min-height: 200px;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #646a73;
}

.task-detail-body {
  display: flex;
  flex-direction: column;
}

.task-detail-item {
  margin-bottom: 24px;
}

.task-detail-item--last {
  margin-bottom: 0;
}

.task-detail-label {
  margin-bottom: 8px;
  font-weight: 400;
  font-size: 12px;
  color: #646a73;
  text-align: left;
  font-style: normal;
}

.task-detail-value {
  font-weight: 400;
  font-size: 14px;
  color: #0f1114;
  text-align: left;
  font-style: normal;
  line-height: 1.5;
  word-break: break-word;
}

.task-detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.task-detail-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  background: #eff0f1;
  border-radius: 2px;
  font-weight: 400;
  font-size: 14px;
  color: #0f1114;
  text-align: left;
  font-style: normal;
  line-height: 1.4;
}

.task-detail-footer {
  box-sizing: border-box;
  display: flex;
  min-height: 52px;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
}

.task-detail-footer__trailing {
  flex-shrink: 0;
}

.task-detail-footer__new-count {
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
  line-height: 1.2;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.tdf-btn {
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

.tdf-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.tdf-btn--stop-neutral {
  background: #ffffff;
  border-radius: 2px;
  border: 1px solid #bbbfc4;
  color: #0f1114;
}

.tdf-btn--stop-neutral:hover:not(:disabled) {
  background: #f8f9fa;
}

.tdf-completed-delete {
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
  font-weight: 400;
  font-size: 14px;
  color: #f54a45;
  line-height: 20px;
  cursor: pointer;
}

.tdf-completed-delete:hover {
  opacity: 0.88;
}

.tdf-else-delete {
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  background: transparent;
  font-size: 12px;
  font-weight: 500;
  color: #f54a45;
  line-height: 1;
  cursor: pointer;
}

.tdf-else-delete:hover {
  background: rgba(245, 74, 69, 0.08);
}

.tdf-btn--outline-blue {
  width: 52px;
  min-width: 52px;
  height: 28px;
  padding: 0;
  border: 1px solid #1f22f6;
  border-radius: 2px;
  background: #ffffff;
  color: #1f22f6;
  font-size: 13px;
  font-weight: 500;
}

.tdf-btn--outline-blue:hover:not(:disabled) {
  background: rgba(31, 34, 246, 0.06);
}

.tdf-btn--restart {
  width: 52px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 2px;
  background: #1f22f6;
  color: #ffffff;
  font-size: 13px;
  font-weight: 500;
}

.tdf-btn--restart:hover:not(:disabled) {
  background: #1719c4;
}
</style>

<style>
.task-detail-dialog.el-dialog {
  width: min(420px, calc(100vw - 24px)) !important;
  max-width: calc(100vw - 16px);
  height: 695px;
  max-height: min(695px, calc(100vh - 48px));
  display: flex;
  flex-direction: column;
  margin: auto !important;
  overflow: hidden;
  border-radius: 8px;
  background: #ffffff;
}

.task-detail-dialog .el-dialog__header {
  flex-shrink: 0;
  padding: 16px 20px 0;
  margin: 0;
}

.task-detail-dialog .el-dialog__title {
  font-size: 16px;
  font-weight: 600;
  color: #0f1114;
}

.task-detail-dialog .el-dialog__body {
  flex: 1 1 auto;
  min-height: 0;
  padding: 16px 20px 12px;
  overflow-x: hidden;
  overflow-y: auto;
  background: #ffffff;
}

.task-detail-dialog .el-dialog__headerbtn {
  top: 12px;
  right: 12px;
}

.task-detail-dialog .el-dialog__footer {
  flex-shrink: 0;
  padding: 0;
  margin: 0;
  border-top: 1px solid #dee0e3;
  background: #ffffff;
}
</style>
