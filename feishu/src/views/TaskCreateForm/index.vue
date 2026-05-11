<script setup lang="ts">
/**
 * 新建 / 编辑任务：整页表单入口，负责状态、校验、保存与子区块编排。
 */
import dayjs from 'dayjs'
import { computed, nextTick, onScopeDispose, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { createFeishuTaskConfig, updateFeishuTaskConfig } from '@/lib/api'
import type { FeishuTaskConfigDetail } from '@/lib/api'

import BasicInfoSection from '@/views/TaskCreateForm/components/BasicInfoSection.vue'
import KeywordsSection from '@/views/TaskCreateForm/components/KeywordsSection.vue'
import FilterSettingsSection from '@/views/TaskCreateForm/components/FilterSettingsSection.vue'
import SourceSelectionSection from '@/views/TaskCreateForm/components/SourceSelectionSection.vue'
import DataRetentionSection from '@/views/TaskCreateForm/components/DataRetentionSection.vue'

import { dataRangeOptions, sourcePlatforms } from '@/views/TaskCreateForm/constants'
import type { SourceFieldKey, TaskCreateFormModel, TaskRunStatus } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'TaskCreateForm' })

/** 编辑态任务 id；为空则保存时走创建接口 */
const props = withDefaults(
  defineProps<{
    taskConfigId?: number | null
    /** 详情接口回显用 */
    detail?: FeishuTaskConfigDetail | null
  }>(),
  { taskConfigId: null, detail: null },
)

const emit = defineEmits<{
  back: []
  saved: [id: number]
}>()

/** 各平台采集字段多选初始化为空数组，避免 undefined */
function emptySourceFieldSelection(): Record<PlatformKey, SourceFieldKey[]> {
  return {
    xiaohongshu: [],
    weibo: [],
    douyin: [],
    gzh: [],
    shipinhao: [],
    kuaishou: [],
  }
}

/** 表单默认值工厂（重置、合并前打底） */
function initialForm(): TaskCreateFormModel {
  return {
    planName: '',
    taskType: 'scheduled',
    crawlFrequency: '5',
    effectiveAt: '',
    expireAt: '',
    authCode: '',
    keywords: [],
    excludeKeywords: [],
    heatLikeMin: 0,
    heatCommentMin: 0,
    heatFavoriteMin: 0,
    heatShareMin: 0,
    sortOrder: 'latest',
    publishTime: 'unlimited',
    videoDuration: 'all',
    dataRange: dataRangeOptions[1],
    selectedSources: [],
    sourceFieldSelection: emptySourceFieldSelection(),
    tableMode: 'existing',
    existingTableId: '',
    runStatus: 'stopped',
  }
}

/** 与 `el-form` 绑定的响应式模型 */
const form = reactive<TaskCreateFormModel>(initialForm())
/** Element Plus 表单实例，用于校验与 clearValidate */
const formRef = ref<FormInstance>()
/** 关键词输入框未完成提交的一行草稿（回车成 tag） */
const keywordDraft = ref('')
/** 排除词区域草稿，交互同 `keywordDraft` */
const excludeKeywordDraft = ref('')

/** 已勾选信源按 `sourcePlatforms` 固定顺序排列，用于下方字段区展示顺序 */
const orderedSelectedPlatforms = computed(() =>
  sourcePlatforms.filter((p) => form.selectedSources.includes(p.id)),
)

function parseFormDateTime(s: string | undefined): dayjs.Dayjs | null {
  if (!s?.trim()) return null
  const d = dayjs(s.trim())
  return d.isValid() ? d : null
}

const rules: FormRules = {
  authCode: [{ required: true, message: '请输入授权码', trigger: 'blur' }],
  effectiveAt: [
    { required: true, message: '请选择生效时间', trigger: 'change' },
    {
      validator: (_rule, value: string, callback) => {
        const d = parseFormDateTime(value)
        if (!d) {
          callback(new Error('生效时间格式不正确'))
          return
        }
        if (d.valueOf() < Date.now()) {
          callback(new Error('生效时间不能早于当前时间'))
          return
        }
        callback()
      },
      trigger: ['change', 'blur'],
    },
  ],
  expireAt: [
    { required: true, message: '请选择过期时间', trigger: 'change' },
    {
      validator: (_rule, value: string, callback) => {
        const d = parseFormDateTime(value)
        if (!d) {
          callback(new Error('过期时间格式不正确'))
          return
        }
        if (d.valueOf() < Date.now()) {
          callback(new Error('过期时间不能早于当前时间'))
          return
        }
        const eff = parseFormDateTime(form.effectiveAt)
        if (eff && d.isBefore(eff)) {
          callback(new Error('过期时间不能早于生效时间'))
          return
        }
        callback()
      },
      trigger: ['change', 'blur'],
    },
  ],
}

/** `el-collapse` 当前展开的面板 name 列表 */
const activePanels = ref<string[]>(['basic'])

/** 保存中，防止连点导致重复提示 */
const saving = ref(false)
/** 保存结果：页内顶部提示（飞书嵌入里 ElMessage 易出现在整页底部） */
const saveBanner = ref<'success' | 'error' | null>(null)
const saveErrorText = ref('')
let saveSuccessClearTimer: ReturnType<typeof setTimeout> | null = null

function clearSaveSuccessTimer() {
  if (saveSuccessClearTimer != null) {
    clearTimeout(saveSuccessClearTimer)
    saveSuccessClearTimer = null
  }
}

function showSaveSuccess() {
  clearSaveSuccessTimer()
  saveBanner.value = 'success'
  saveErrorText.value = ''
  saveSuccessClearTimer = setTimeout(() => {
    saveBanner.value = null
    saveSuccessClearTimer = null
  }, 4000)
}

function showSaveError(msg: string) {
  clearSaveSuccessTimer()
  saveBanner.value = 'error'
  saveErrorText.value = msg
}

onScopeDispose(() => {
  clearSaveSuccessTimer()
})

/** 恢复默认并清空草稿与校验态 */
function resetForm() {
  Object.assign(form, initialForm())
  keywordDraft.value = ''
  excludeKeywordDraft.value = ''
  void nextTick(() => formRef.value?.clearValidate())
}

/**
 * 将服务端 `config` 合并进表单；对 `sourceFieldSelection` 做白名单字段过滤。
 */
/** 兼容旧版 `excludeKeywords` 为整段字符串的配置 */
function normalizeExcludeKeywords(raw: unknown): string[] {
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
}

function normalizeRunStatus(raw: unknown): TaskRunStatus {
  if (raw === 'running' || raw === 'completed' || raw === 'stopped' || raw === 'failed') {
    return raw
  }
  return 'stopped'
}

function mergeConfigIntoForm(raw: Record<string, unknown>) {
  Object.assign(form, initialForm(), raw as Partial<TaskCreateFormModel>)
  form.excludeKeywords = normalizeExcludeKeywords(raw.excludeKeywords)
  form.runStatus = normalizeRunStatus(raw.runStatus)
  const sel = raw.sourceFieldSelection
  const merged = emptySourceFieldSelection()
  if (sel && typeof sel === 'object' && !Array.isArray(sel)) {
    for (const key of Object.keys(merged) as PlatformKey[]) {
      const v = (sel as Record<string, unknown>)[key]
      if (Array.isArray(v)) {
        merged[key] = v.filter(
          (x): x is SourceFieldKey => x === 'like' || x === 'comment' || x === 'share',
        )
      }
    }
  }
  form.sourceFieldSelection = merged
  form.taskType = 'scheduled'
}

watch(
  () => form.effectiveAt,
  () => {
    if (form.expireAt?.trim()) {
      void nextTick(() => formRef.value?.validateField('expireAt').catch(() => {}))
    }
  },
)

watch(
  () => [props.taskConfigId, props.detail] as const,
  ([id, d]) => {
    if (d?.config) {
      mergeConfigIntoForm(d.config)
      keywordDraft.value = ''
      excludeKeywordDraft.value = ''
      void nextTick(() => formRef.value?.clearValidate())
    } else if (id == null) {
      resetForm()
    }
  },
  { immediate: true },
)

/** 深拷贝为普通对象便于 `JSON.stringify` 提交 */
function snapshotForm(): Record<string, unknown> {
  return JSON.parse(JSON.stringify(form)) as Record<string, unknown>
}

/** 校验通过后调用创建或更新接口 */
async function saveConfig() {
  if (!formRef.value || saving.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const payload = snapshotForm()
    if (props.taskConfigId != null) {
      await updateFeishuTaskConfig(props.taskConfigId, payload)
      showSaveSuccess()
      emit('saved', props.taskConfigId)
    } else {
      const { id } = await createFeishuTaskConfig(payload)
      showSaveSuccess()
      emit('saved', id)
    }
  } catch (e) {
    showSaveError(e instanceof Error ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex min-h-0 flex-col gap-6 pb-8">
    <div class="flex items-center gap-3">
      <el-button link type="primary" @click="emit('back')">← 返回任务列表</el-button>
    </div>
    <h2 class="text-lg font-medium text-slate-800">新建任务</h2>

    <el-alert
      v-if="saveBanner === 'success'"
      type="success"
      title="配置已保存"
      show-icon
      closable
      class="save-banner sticky top-0 z-20 mb-3 max-w-3xl shadow-sm"
      @close="saveBanner = null"
    />
    <el-alert
      v-else-if="saveBanner === 'error'"
      type="error"
      :title="saveErrorText"
      show-icon
      closable
      class="save-banner sticky top-0 z-20 mb-3 max-w-3xl shadow-sm"
      @close="saveBanner = null"
    />

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="max-w-3xl">
      <el-collapse v-model="activePanels" class="task-form-collapse">
        <el-collapse-item title="基础信息" name="basic">
          <BasicInfoSection :form="form" />
        </el-collapse-item>

        <el-collapse-item title="关键词管理" name="keywords">
          <KeywordsSection
            :form="form"
            :keyword-draft="keywordDraft"
            @update:keyword-draft="keywordDraft = $event"
          />
        </el-collapse-item>

        <el-collapse-item title="过滤设置" name="filter">
          <FilterSettingsSection
            :form="form"
            :exclude-keyword-draft="excludeKeywordDraft"
            @update:exclude-keyword-draft="excludeKeywordDraft = $event"
          />
        </el-collapse-item>

        <el-collapse-item title="信源选择" name="sources">
          <SourceSelectionSection :form="form" :ordered-platforms="orderedSelectedPlatforms" />
        </el-collapse-item>

        <el-collapse-item name="retention">
          <template #title>
            <span class="retention-collapse-title inline-flex items-center gap-2 text-sm font-semibold text-slate-800">
              <svg
                class="size-4 shrink-0 text-slate-600"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.75"
                aria-hidden="true"
              >
                <path d="M6 4h9l3 3v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z" />
                <path d="M8 12h8M8 16h5" stroke-linecap="round" />
              </svg>
              数据沉淀配置
            </span>
          </template>

          <DataRetentionSection :form="form" />
        </el-collapse-item>
      </el-collapse>
    </el-form>

    <div class="flex flex-wrap gap-3 border-t border-slate-100 pt-6">
      <el-button @click="resetForm">重置</el-button>
      <el-button type="primary" :loading="saving" @click="saveConfig">保存配置</el-button>
    </div>
  </div>
</template>

<style scoped>
.save-banner :deep(.el-alert__title) {
  font-size: 0.875rem;
}

.task-form-collapse {
  border: none;
}

.task-form-collapse :deep(.el-collapse-item) {
  margin-bottom: 0.5rem;
  border: 1px solid rgb(226 232 240);
  border-radius: 0.5rem;
  overflow: hidden;
  background: #fff;
}

.task-form-collapse :deep(.el-collapse-item__header) {
  height: auto;
  min-height: 48px;
  padding: 0 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgb(30 41 59);
  background: rgb(248 250 252);
}

.task-form-collapse :deep(.el-collapse-item__wrap) {
  border-bottom: none;
}

.task-form-collapse :deep(.el-collapse-item__content) {
  padding: 1rem 1rem 1.25rem;
  padding-bottom: 1.25rem;
}
</style>
