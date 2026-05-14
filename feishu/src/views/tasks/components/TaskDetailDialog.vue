<script setup lang="ts">
import { computed } from 'vue'
import { Document } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import type { FeishuTaskConfigDetail } from '@/lib/api'
import { DATETIME_FORMAT } from '@/views/TaskCreateForm/constants'

defineOptions({ name: 'TaskDetailDialog' })

const props = defineProps<{
  /** v-model 显示弹框 */
  modelValue: boolean
  detail: FeishuTaskConfigDetail | null
  loading: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
}>()

const cfg = computed(() => props.detail?.config ?? {})

const planName = computed(() => {
  const n = cfg.value.planName
  if (typeof n === 'string' && n.trim()) return n.trim()
  const fallback = props.detail?.plan_name
  return typeof fallback === 'string' && fallback.trim() ? fallback.trim() : '—'
})

const isRealtime = computed(() => cfg.value.taskType === 'realtime')

const taskTypeLabel = computed(() =>
  cfg.value.taskType === 'realtime' ? '单词任务' : '定时任务',
)

function formatDateTime(raw: unknown): string {
  if (raw == null) return '—'
  const s = String(raw).trim()
  if (!s) return '—'
  const d = dayjs(s)
  return d.isValid() ? d.format(DATETIME_FORMAT) : s
}

const effectiveAtLabel = computed(() => formatDateTime(cfg.value.effectiveAt))
const expireAtLabel = computed(() => formatDateTime(cfg.value.expireAt))

const keywordTags = computed(() => {
  const k = cfg.value.keywords
  if (!Array.isArray(k)) return []
  return k
    .filter((x): x is string => typeof x === 'string')
    .map((x) => x.trim())
    .filter((x) => x.length > 0)
})

/** 排除词：新版为数组；旧版为整段字符串 */
const excludeTags = computed(() => {
  const raw = cfg.value.excludeKeywords
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
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    width="480px"
    class="task-detail-dialog"
    align-center
    destroy-on-close
    :show-close="true"
    :close-on-click-modal="true"
    append-to-body
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template #header>
      <div class="flex items-center gap-2 border-b border-slate-100 pb-3">
        <el-icon class="text-slate-700" :size="20">
          <Document />
        </el-icon>
        <span class="text-base font-semibold text-slate-800">任务详情</span>
      </div>
    </template>

    <div v-if="loading" class="py-12 text-center text-sm text-slate-500">加载中…</div>

    <div v-else class="space-y-4 text-sm">
      <div>
        <div class="mb-1 text-xs text-slate-400">方案名称</div>
        <div class="font-medium text-slate-800">{{ planName }}</div>
      </div>
      <div>
        <div class="mb-1 text-xs text-slate-400">任务类型</div>
        <div class="text-slate-800">{{ taskTypeLabel }}</div>
      </div>
      <template v-if="!isRealtime">
        <div>
          <div class="mb-1 text-xs text-slate-400">开始时间</div>
          <div class="text-slate-800">{{ effectiveAtLabel }}</div>
        </div>
        <div>
          <div class="mb-1 text-xs text-slate-400">结束时间</div>
          <div class="text-slate-800">{{ expireAtLabel }}</div>
        </div>
      </template>
      <div>
        <div class="mb-1 text-xs text-slate-400">关键词</div>
        <div v-if="keywordTags.length" class="flex flex-wrap gap-2">
          <span
            v-for="(tag, i) in keywordTags"
            :key="`kw-${i}`"
            class="inline-flex rounded-md bg-sky-50 px-2.5 py-0.5 text-sm text-sky-900"
          >
            {{ tag }}
          </span>
        </div>
        <div v-else class="text-slate-500">—</div>
      </div>
      <div>
        <div class="mb-1 text-xs text-slate-400">排除词</div>
        <div v-if="excludeTags.length" class="flex flex-wrap gap-2">
          <span
            v-for="(tag, i) in excludeTags"
            :key="`ex-${i}`"
            class="inline-flex rounded-md bg-sky-50 px-2.5 py-0.5 text-sm text-sky-900"
          >
            {{ tag }}
          </span>
        </div>
        <div v-else class="text-slate-500">—</div>
      </div>
    </div>
  </el-dialog>
</template>

<style scoped>
.task-detail-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding-bottom: 0;
}
.task-detail-dialog :deep(.el-dialog__body) {
  padding-top: 1rem;
}
.task-detail-dialog :deep(.el-dialog__footer) {
  display: none;
}
</style>
