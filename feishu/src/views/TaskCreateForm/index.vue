<script setup lang="ts">
/**
 * 新建 / 编辑任务：整页表单入口，负责状态、校验、保存与子区块编排。
 */
import { computed, nextTick, onScopeDispose, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import {
  createFeishuTaskConfig,
  getFeishuTaskConfig,
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
import TaskConfigPreviewDialog from '@/views/TaskCreateForm/components/TaskConfigPreviewDialog.vue'
import TaskConfigConfirmDialog from '@/views/TaskCreateForm/components/TaskConfigConfirmDialog.vue'
import {
  buildTaskConfigConfirmRows,
  buildTaskConfigPreviewRows,
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
    tableMode: 'existing',
    existingTableId: '',
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

/** 仅定时任务校验开始/结束时间；单词任务不展示时间字段 */
const rules = computed<FormRules>(() => ({
  planName: [{ required: true, message: '请输入方案名称', trigger: 'blur' }],
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

/** 分步向导：基础设置 → 过滤设置 → 采集配置 */
const LAST_STEP = 2
const currentStep = ref(0)
const stepTitles = ['基础设置', '过滤设置', '采集配置'] as const

/** 新建首次保存后由接口返回的 id，用于再次保存走 PUT */
const internalConfigId = ref<number | null>(null)

/** 保存前确认弹框 */
const confirmVisible = ref(false)
const confirmDisplayRows = computed(() =>
  buildTaskConfigConfirmRows(snapshotForPreview(snapshotForm() as Record<string, unknown>)),
)

/** 保存成功后的预览弹框 */
const previewVisible = ref(false)
const previewRows = ref<{ label: string; value: string }[]>([])
const savedTaskIdForPreview = ref<number | null>(null)
const previewExecuting = ref(false)

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

/** 与后端 `task_paused_from_config` 一致，避免库存非严格 bool 时表单误判为未暂停 */
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
  } catch {
    return
  }
  confirmVisible.value = true
}

/** 确认弹框内「开始执行」：落库后打开预览弹框（是否立即分配任务） */
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
  } catch {
    return
  }
  saving.value = true
  try {
    const payload = snapshotForm()
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
    savedTaskIdForPreview.value = targetId
    previewRows.value = buildTaskConfigPreviewRows(snapshotForPreview(payload as Record<string, unknown>))
    confirmVisible.value = false
    showSaveSuccess()
    previewVisible.value = true
  } catch (e) {
    showSaveError(e instanceof Error ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}

/** 与任务列表「启动」一致：解除暂停并清除异常标记，由服务端推导运行态 */
async function executeFromPreview() {
  const id = savedTaskIdForPreview.value
  if (id == null || previewExecuting.value) return
  previewExecuting.value = true
  try {
    const detail = await getFeishuTaskConfig(id)
    const cfg = JSON.parse(JSON.stringify(detail.config)) as Record<string, unknown>
    Object.assign(cfg, {
      taskPaused: false,
      taskAbnormal: false,
      runStatus: 'stopped',
    })
    await updateFeishuTaskConfig(id, cfg)
    ElMessage.success('已开始分配任务')
    previewVisible.value = false
    emit('saved', id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '启动失败')
  } finally {
    previewExecuting.value = false
  }
}

function leavePreviewWithoutExecute() {
  const id = savedTaskIdForPreview.value
  previewVisible.value = false
  if (id != null) emit('saved', id)
}

function onBackRequested() {
  if (confirmVisible.value) confirmVisible.value = false
  if (previewVisible.value) previewVisible.value = false
  emit('back')
}
</script>

<template>
  <div class="flex min-h-0 flex-col gap-6 pb-8">
    <div class="flex items-center gap-3">
      <el-button link type="primary" @click="onBackRequested">← 返回任务列表</el-button>
    </div>

    <el-alert
      v-if="saveBanner === 'success'"
      type="success"
      title="配置已保存，请预览后选择是否立即执行"
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

    <TaskConfigConfirmDialog
      v-model="confirmVisible"
      :rows="confirmDisplayRows"
      :estimated-points="pointsEstimate.total"
      :balance-points="accountPoints.currentBalancePoints"
      :confirming="saving"
      @confirm="persistFromConfirmDialog"
    />

    <TaskConfigPreviewDialog
      v-model="previewVisible"
      :rows="previewRows"
      :executing="previewExecuting"
      @execute="executeFromPreview"
      @leave="leavePreviewWithoutExecute"
    />

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="max-w-3xl">
      <el-steps
        :active="currentStep"
        finish-status="success"
        align-center
        class="task-create-steps mb-6"
      >
        <el-step v-for="(t, i) in stepTitles" :key="i" :title="t" />
      </el-steps>

      <div v-show="currentStep === 0">
        <BasicInfoSection :form="form" />
        <p class="mb-2 mt-6 text-sm font-medium text-slate-800">采集平台</p>
        <SourceSelectionSection
          mode="platforms"
          :form="form"
          :ordered-platforms="orderedSelectedPlatforms"
        />
        <p class="mb-2 mt-6 text-sm font-medium text-slate-800">关键词</p>
        <KeywordsSection
          :form="form"
          :keyword-draft="keywordDraft"
          @update:keyword-draft="keywordDraft = $event"
        />
        <FeishuNotifySection :form="form" />
      </div>
      <div v-show="currentStep === 1">
        <FilterSettingsSection
          :form="form"
          :exclude-keyword-draft="excludeKeywordDraft"
          @update:exclude-keyword-draft="excludeKeywordDraft = $event"
        />
      </div>
      <div v-show="currentStep === 2">
        <CrawlScheduleSection :form="form" />
        <p class="mb-2 mt-2 text-sm font-medium text-slate-800">采集字段</p>
        <SourceSelectionSection
          mode="fields"
          :form="form"
          :ordered-platforms="orderedSelectedPlatforms"
        />
        <div class="mt-8">
          <DataRetentionSection :form="form" />
        </div>
      </div>
    </el-form>

    <div class="footer-actions max-w-3xl border-t border-slate-100 pt-6">
      <div
        class="mb-3 flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800"
      >
        <span>
          预估消耗：<span class="font-medium text-[#3355FF]">~{{ pointsEstimate.total }}条</span>
        </span>
        <span>当前余额: {{ accountPoints.currentBalancePoints }}点</span>
      </div>
      <div class="flex w-full gap-3">
        <template v-if="currentStep === 0">
          <el-button type="primary" class="flex-1" @click="goNextStep">下一步</el-button>
        </template>
        <template v-else-if="currentStep === 1">
          <el-button class="flex-1" @click="goPrevStep">上一步</el-button>
          <el-button type="primary" class="flex-1" @click="goNextStep">下一步</el-button>
        </template>
        <template v-else>
          <el-button class="flex-1" @click="goPrevStep">上一步</el-button>
          <el-button type="primary" class="flex-1" @click="openSaveConfirm">保存配置</el-button>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.save-banner :deep(.el-alert__title) {
  font-size: 0.875rem;
}

/* 飞书窄容器内避免步骤标题换行：略缩字号 + 单行 */
.task-create-steps :deep(.el-step__title) {
  font-size: 0.6875rem;
  line-height: 1.2;
  white-space: nowrap;
  margin-top: 0.25rem;
  padding: 0 0.125rem;
}

.task-create-steps :deep(.el-step__head) {
  margin-right: 0;
}

.task-create-steps :deep(.el-step__line) {
  margin: 0 0.125rem;
}

.task-create-steps :deep(.el-step__icon) {
  width: 1.375rem;
  height: 1.375rem;
  font-size: 0.6875rem;
}

.task-create-steps :deep(.el-step__icon-inner) {
  font-size: 0.6875rem;
  font-weight: 600;
}
</style>
