<script setup lang="ts">
/**
 * 新建 / 编辑任务：整页表单入口，负责状态、校验、保存与子区块编排。
 */
import { computed, nextTick, onScopeDispose, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import {
  createFeishuTaskConfig,
  updateFeishuTaskConfig,
} from '@/lib/api'
import type { FeishuTaskConfigDetail } from '@/lib/api'
import { useGlobalSettingsStore } from '@/stores/globalSettings'
import { useAccountPointsStore } from '@/stores/accountPoints'
import { estimateTaskPointsBreakdown } from '@/lib/task-estimate-points'

import BasicInfoSection from '@/views/TaskCreateForm/components/BasicInfoSection.vue'
import FeishuNotifySection from '@/views/TaskCreateForm/components/FeishuNotifySection.vue'
import KeywordsSection from '@/views/TaskCreateForm/components/KeywordsSection.vue'
import FilterSettingsSection from '@/views/TaskCreateForm/components/FilterSettingsSection.vue'
import CrawlScheduleSection from '@/views/TaskCreateForm/components/CrawlScheduleSection.vue'
import SourceSelectionSection from '@/views/TaskCreateForm/components/SourceSelectionSection.vue'
import DataRetentionSection from '@/views/TaskCreateForm/components/DataRetentionSection.vue'
import TaskConfigConfirmDialog from '@/views/TaskCreateForm/components/TaskConfigConfirmDialog.vue'
import {
  buildTaskConfigConfirmRows,
  snapshotForPreview,
} from '@/views/TaskCreateForm/build-preview-rows'

import {
  effectiveAtFormItemRules,
  expireAtFormItemRules,
} from '@/lib/datetime-task-window'
import { dataRangeOptions, sourcePlatforms } from '@/views/TaskCreateForm/constants'
import {
  ensureSourceFieldSelectionForAllSelected,
  isSourceFieldKey,
  isSupportedSourcePlatform,
} from '@/views/TaskCreateForm/source-field-catalog'
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

function emptyPlatformStringMap(): Record<PlatformKey, string> {
  return {
    xiaohongshu: '',
    weibo: '',
    douyin: '',
    gzh: '',
    shipinhao: '',
    kuaishou: '',
  }
}

/** 表单默认值工厂（重置、合并前打底） */
function initialForm(): TaskCreateFormModel {
  return {
    planName: '',
    feishuNotifyEnabled: false,
    feishuWebhookUrl: '',
    taskType: 'scheduled',
    crawlFrequency: '5',
    effectiveAt: '',
    expireAt: '',
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
    tableMode: 'new',
    existingTableId: '',
    platformNewTableNames: emptyPlatformStringMap(),
    platformExistingTableIds: emptyPlatformStringMap(),
    runStatus: 'stopped',
    taskPaused: false,
    taskAbnormal: false,
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

const accountPoints = useAccountPointsStore()
const pointsEstimate = computed(() => estimateTaskPointsBreakdown(form))

/** 仅定时任务校验开始/结束时间；单次任务不展示时间字段 */
const rules = computed<FormRules>(() => ({
  planName: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  feishuWebhookUrl: [
    {
      validator: (_rule, value, callback) => {
        if (!form.feishuNotifyEnabled) {
          callback()
          return
        }
        if (!String(value ?? '').trim()) {
          callback(new Error('请输入飞书机器人Webhook地址'))
          return
        }
        callback()
      },
      trigger: ['blur', 'change'],
    },
  ],
  ...(form.taskType === 'scheduled'
    ? {
        effectiveAt: effectiveAtFormItemRules(),
        expireAt: expireAtFormItemRules(() => form.effectiveAt),
      }
    : {}),
}))

/** 分步向导：① 基础/平台/关键词/飞书 → ② 排除词、排序方式、发布时间、视频时长、选择条数 → ③ 采集字段与沉淀（共 3 步） */
const LAST_STEP = 2
const totalWizardSteps = LAST_STEP + 1
const currentStep = ref(0)

/** 新建首次保存后由接口返回的 id，用于再次保存走 PUT */
const internalConfigId = ref<number | null>(null)

/** 保存前确认弹框 */
const confirmVisible = ref(false)
const confirmDisplayRows = computed(() =>
  buildTaskConfigConfirmRows(snapshotForPreview(snapshotForm() as Record<string, unknown>)),
)

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

function showSaveError(msg: string) {
  clearSaveSuccessTimer()
  saveBanner.value = 'error'
  saveErrorText.value = msg
}

/** 表单校验未通过时：弹提示（优先展示首个字段的校验文案） */
function notifyFormValidationFailed(invalidFields: unknown) {
  const fallback = '请完善必填项后再保存任务'
  if (invalidFields && typeof invalidFields === 'object' && !Array.isArray(invalidFields)) {
    const record = invalidFields as Record<string, { message?: string }[] | undefined>
    for (const key of Object.keys(record)) {
      const errs = record[key]
      const first = Array.isArray(errs) ? errs[0] : undefined
      const msg = first && typeof first.message === 'string' ? first.message.trim() : ''
      if (msg) {
        ElMessage.warning(msg)
        return
      }
    }
  }
  ElMessage.warning(fallback)
}

onScopeDispose(() => {
  clearSaveSuccessTimer()
})

/** 恢复默认并清空草稿与校验态 */
function resetForm() {
  Object.assign(form, initialForm())
  keywordDraft.value = ''
  excludeKeywordDraft.value = ''
  currentStep.value = 0
  internalConfigId.value = null
  void nextTick(() => formRef.value?.clearValidate())
}

function effectiveTaskConfigId(): number | null {
  return props.taskConfigId ?? internalConfigId.value
}

function goPrevStep() {
  if (currentStep.value > 0) currentStep.value -= 1
}

function goNextStep() {
  if (currentStep.value < LAST_STEP) currentStep.value += 1
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
  if (raw === 'pending_run') return 'stopped'
  return 'stopped'
}

function coerceTaskPausedFlag(raw: Record<string, unknown>): boolean {
  for (const key of ['taskPaused', 'task_paused'] as const) {
    const v = raw[key]
    if (typeof v === 'boolean') return v
    if (typeof v === 'string') {
      const s = v.trim().toLowerCase()
      if (['true', '1', 'yes', 'on'].includes(s)) return true
      if (['false', '0', 'no', 'off', ''].includes(s)) return false
    }
    if (typeof v === 'number' && (v === 1 || v === 0)) return v === 1
  }
  return false
}

function normalizePlatformStringMap(
  raw: unknown,
  fallback: Record<PlatformKey, string>,
): Record<PlatformKey, string> {
  const base = { ...emptyPlatformStringMap(), ...fallback }
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return base
  for (const key of Object.keys(base) as PlatformKey[]) {
    const v = (raw as Record<string, unknown>)[key]
    if (typeof v === 'string') base[key] = v
  }
  return base
}

function mergeConfigIntoForm(raw: Record<string, unknown>) {
  const globalSettings = useGlobalSettingsStore()
  const savedAuth = raw.authCode
  const { authCode: _omitAuth, ...rest } = raw
  Object.assign(form, initialForm(), rest as Partial<TaskCreateFormModel>)
  if (
    typeof savedAuth === 'string' &&
    savedAuth.trim() &&
    !String(globalSettings.authCode ?? '').trim()
  ) {
    globalSettings.authCode = savedAuth.trim()
  }
  form.excludeKeywords = normalizeExcludeKeywords(raw.excludeKeywords)
  form.runStatus = normalizeRunStatus(raw.runStatus)
  form.taskPaused = coerceTaskPausedFlag(raw)
  form.taskAbnormal = typeof raw.taskAbnormal === 'boolean' ? raw.taskAbnormal : false
  const sel = raw.sourceFieldSelection
  const merged = emptySourceFieldSelection()
  if (sel && typeof sel === 'object' && !Array.isArray(sel)) {
    for (const key of Object.keys(merged) as PlatformKey[]) {
      const v = (sel as Record<string, unknown>)[key]
      if (Array.isArray(v)) {
        merged[key] = v.filter((x): x is SourceFieldKey => isSourceFieldKey(x))
      }
    }
  }
  form.sourceFieldSelection = merged
  form.selectedSources = form.selectedSources.filter((id) => isSupportedSourcePlatform(id))
  ensureSourceFieldSelectionForAllSelected(form)
  const tt = raw.taskType
  form.taskType = tt === 'realtime' ? 'realtime' : 'scheduled'
  form.feishuNotifyEnabled =
    raw.feishuNotifyEnabled === true ||
    raw.feishuNotifyEnabled === 1 ||
    String(raw.feishuNotifyEnabled ?? '')
      .trim()
      .toLowerCase() === 'true'
  form.feishuWebhookUrl =
    typeof raw.feishuWebhookUrl === 'string' ? raw.feishuWebhookUrl.trim() : ''
  form.platformNewTableNames = normalizePlatformStringMap(
    raw.platformNewTableNames,
    form.platformNewTableNames,
  )
  form.platformExistingTableIds = normalizePlatformStringMap(
    raw.platformExistingTableIds,
    form.platformExistingTableIds,
  )
}

watch(
  () => [...form.selectedSources],
  () => {
    ensureSourceFieldSelectionForAllSelected(form)
  },
  { immediate: true },
)

watch(
  () => form.taskType,
  (t) => {
    if (t === 'realtime') {
      form.effectiveAt = ''
      form.expireAt = ''
      void nextTick(() => {
        formRef.value?.clearValidate(['effectiveAt', 'expireAt'])
      })
    }
  },
)

watch(
  () => form.feishuNotifyEnabled,
  (on) => {
    if (!on) void nextTick(() => formRef.value?.clearValidate(['feishuWebhookUrl']))
  },
)

watch(
  () => [form.effectiveAt, form.taskType] as const,
  () => {
    if (form.taskType !== 'scheduled') return
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
    if (id != null) {
      internalConfigId.value = null
    }
  },
  { immediate: true },
)

/** 深拷贝为普通对象便于 `JSON.stringify` 提交；授权码来自全局配置写入 `config_json`。 */
function snapshotForm(): Record<string, unknown> {
  const globalSettings = useGlobalSettingsStore()
  const base = JSON.parse(JSON.stringify(form)) as Record<string, unknown>
  base.authCode = globalSettings.authCode
  return base
}

/** 打开保存前确认弹框（校验 API-Key 与表单） */
async function openSaveConfirm() {
  if (!formRef.value || saving.value) return
  const globalSettings = useGlobalSettingsStore()
  if (!String(globalSettings.authCode ?? '').trim()) {
    showSaveError('请先在顶部填写 API-Key（授权码）')
    return
  }
  try {
    await formRef.value.validate()
  } catch (invalidFields) {
    notifyFormValidationFailed(invalidFields)
    return
  }
  confirmVisible.value = true
}

/** 确认弹框内「开始执行」：落库并提交运行，回到任务列表 */
async function persistFromConfirmDialog() {
  if (!formRef.value || saving.value) return
  const globalSettings = useGlobalSettingsStore()
  if (!String(globalSettings.authCode ?? '').trim()) {
    showSaveError('请先在顶部填写 API-Key（授权码）')
    confirmVisible.value = false
    return
  }
  try {
    await formRef.value.validate()
  } catch (invalidFields) {
    notifyFormValidationFailed(invalidFields)
    confirmVisible.value = false
    return
  }
  saving.value = true
  try {
    const payload = snapshotForm()
    Object.assign(payload, {
      taskPaused: false,
      taskAbnormal: false,
      runStatus: 'stopped',
    })
    const existingId = effectiveTaskConfigId()
    let targetId: number
    if (existingId != null) {
      await updateFeishuTaskConfig(existingId, payload)
      targetId = existingId
    } else {
      const { id } = await createFeishuTaskConfig(payload)
      internalConfigId.value = id
      targetId = id
    }
    confirmVisible.value = false
    saveBanner.value = null
    saveErrorText.value = ''
    emit('saved', targetId)
  } catch (e) {
    showSaveError(e instanceof Error ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex min-h-0 flex-col gap-6 pb-8">
    <el-alert
      v-if="saveBanner === 'error'"
      type="error"
      :title="saveErrorText"
      show-icon
      closable
      class="save-banner sticky top-0 z-20 mb-3 max-w-3xl shadow-sm"
      @close="saveBanner = null"
    />

    <TaskConfigConfirmDialog
      v-model="confirmVisible"
      :rows="confirmDisplayRows"
      :estimated-points="pointsEstimate.total"
      :balance-points="accountPoints.currentBalancePoints"
      :confirming="saving"
      @confirm="persistFromConfirmDialog"
    />

    <div
      class="task-config-step-header flex max-w-3xl shrink-0 items-center justify-between gap-3 pt-1"
    >
      <span class="text-base font-semibold text-slate-900">任务配置</span>
      <p class="m-0 text-sm text-slate-400">
        第
        <span class="font-semibold text-blue-600 tabular-nums">{{ currentStep + 1 }}</span>
        /{{ totalWizardSteps }} 步
      </p>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      class="task-create-form max-w-3xl"
    >
      <div v-show="currentStep === 0">
        <BasicInfoSection :form="form" />
        <CrawlScheduleSection :form="form" />
        <p class="task-form-field-title mb-2 mt-6">采集平台</p>
        <SourceSelectionSection
          mode="platforms"
          :form="form"
          :ordered-platforms="orderedSelectedPlatforms"
        />
        <p class="task-form-field-title mb-2 mt-6">关键词</p>
        <KeywordsSection
          :form="form"
          :keyword-draft="keywordDraft"
          @update:keyword-draft="keywordDraft = $event"
        />
      </div>
      <div v-if="currentStep === 1" class="task-wizard-step-filters">
        <FilterSettingsSection
          :form="form"
          :exclude-keyword-draft="excludeKeywordDraft"
          @update:exclude-keyword-draft="excludeKeywordDraft = $event"
        />
      </div>
      <div v-show="currentStep === 2">
        <template v-if="orderedSelectedPlatforms.length">
          <SourceSelectionSection
            mode="fields"
            :form="form"
            :ordered-platforms="orderedSelectedPlatforms"
          />
        </template>
        <div class="mt-8" :class="{ 'mt-2': !orderedSelectedPlatforms.length }">
          <p class="task-form-field-title mb-3">采集数据写入表格</p>
          <DataRetentionSection :form="form" :ordered-platforms="orderedSelectedPlatforms" />
        </div>
        <FeishuNotifySection :form="form" class="mt-8" />
      </div>
    </el-form>

    <div class="footer-actions max-w-3xl border-t border-slate-100 pt-6">
      <div class="flex w-full gap-3">
        <template v-if="currentStep === 0">
          <el-button
            type="primary"
            class="task-footer-primary task-footer-step-btn flex-1"
            @click="goNextStep"
            >下一步</el-button
          >
        </template>
        <template v-else-if="currentStep === 1">
          <el-button class="task-footer-step-btn flex-1" @click="goPrevStep">上一步</el-button>
          <el-button
            type="primary"
            class="task-footer-primary task-footer-step-btn flex-1"
            @click="goNextStep"
            >下一步</el-button
          >
        </template>
        <template v-else>
          <el-button class="task-footer-step-btn flex-1" @click="goPrevStep">上一步</el-button>
          <el-button
            type="primary"
            class="task-footer-primary task-footer-step-btn flex-1"
            @click="openSaveConfirm"
            >保存任务</el-button
          >
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-create-form :deep(.el-form-item__content .el-select) {
  width: 100%;
}

.task-create-form :deep(.el-form-item__content .el-date-editor) {
  width: 100%;
  max-width: 100%;
}

.task-create-form :deep(.el-form-item__content .el-input) {
  width: 100%;
  max-width: 100%;
}

.footer-actions :deep(.task-footer-step-btn.el-button) {
  height: 46px;
  min-height: 46px;
  padding-top: 0;
  padding-bottom: 0;
}

.footer-actions :deep(.task-footer-primary.el-button--primary) {
  border: none;
  border-radius: 4px;
  background-color: transparent;
  background-image: linear-gradient(90deg, #1456f0 0%, #4014f0 100%);
  --el-button-bg-color: transparent;
  --el-button-border-color: transparent;
  --el-button-hover-bg-color: transparent;
  --el-button-hover-border-color: transparent;
}

.footer-actions :deep(.task-footer-primary.el-button--primary:hover),
.footer-actions :deep(.task-footer-primary.el-button--primary:focus) {
  background-image: linear-gradient(90deg, #1a5df8 0%, #4d22f5 100%);
  color: #ffffff;
}

.footer-actions :deep(.task-footer-primary.el-button--primary:active) {
  background-image: linear-gradient(90deg, #124ecf 0%, #3612d8 100%);
}

.save-banner :deep(.el-alert__title) {
  font-size: 0.875rem;
}
</style>

<style>
/* 任务配置表单：表单项 label 与独立区块标题（子组件也在此 el-form 内） */
.task-create-form.el-form .el-form-item__label {
  font-weight: 500;
  font-size: 12px;
  color: #2b2f36;
  text-align: left;
  font-style: normal;
  text-transform: none;
}

.task-create-form .task-form-field-title {
  font-weight: 500;
  font-size: 12px;
  color: #2b2f36;
  text-align: left;
  font-style: normal;
  text-transform: none;
}
</style>
