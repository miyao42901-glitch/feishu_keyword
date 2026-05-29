<script setup lang="ts">
/**
 * 新建 / 编辑任务：整页表单入口，负责状态、校验、保存与子区块编排。
 */
import { computed, nextTick, onScopeDispose, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import {
  persistCollectionRefsToLocal,
  saveTaskConfigSnapshot,
} from '@/lib/feishu-async-task-config'
import { clearGlobalBitableAppendDedup } from '@/lib/feishu-bitable-append-feed'
import { syncSinglePlatformCollectionToBitable } from '@/lib/feishu-bitable-task-sync'
import { isLocalDraftTaskId } from '@/lib/feishu-task-config-local'
import { buildCollectionFetchContext } from '@/lib/collection-context'
import {
  applyCollectionResultToConfig,
  buildAsyncTaskEditRequest,
  canEditAsyncScheduleFields,
  editAsyncTask,
  isRealtimeTaskConfig,
  runRealtimeSyncSearchFromConfig,
  submitCollectionFromConfig,
} from '@/lib/async-task-api'
import type { FeishuTaskConfigDetail } from '@/lib/task-config-types'
import { useGlobalSettingsStore } from '@/stores/globalSettings'
import { useAccountPointsStore } from '@/stores/accountPoints'
import { refreshYddmUserBalance } from '@/lib/refresh-yddm-balance'
import {
  estimatePointsFromItemsByPlatform,
  estimateTaskPointsBreakdown,
} from '@/lib/task-estimate-points'
import {
  KEYWORD_COUNT_EXCEEDED_HINT,
  KEYWORD_MAX_COUNT,
  truncateKeyword,
} from '@/lib/keyword-limits'
import { isSyncCollectionPlatform } from '@/lib/sync-collection-platforms'

import BasicInfoSection from '@/views/TaskCreateForm/components/BasicInfoSection.vue'
import FeishuNotifySection from '@/views/TaskCreateForm/components/FeishuNotifySection.vue'
import KeywordsSection from '@/views/TaskCreateForm/components/KeywordsSection.vue'
import FilterSettingsSection from '@/views/TaskCreateForm/components/FilterSettingsSection.vue'
import CrawlScheduleSection from '@/views/TaskCreateForm/components/CrawlScheduleSection.vue'
import SourceSelectionSection from '@/views/TaskCreateForm/components/SourceSelectionSection.vue'
import DataRetentionSection from '@/views/TaskCreateForm/components/DataRetentionSection.vue'
import CustomerServiceQrDialog from '@/components/CustomerServiceQrDialog.vue'
import TaskConfigConfirmDialog from '@/views/TaskCreateForm/components/TaskConfigConfirmDialog.vue'
import { isPointsInsufficient, POINTS_INSUFFICIENT_MSG } from '@/lib/insufficient-balance'
import {
  buildTaskConfigConfirmRows,
  snapshotForPreview,
} from '@/views/TaskCreateForm/build-preview-rows'

import {
  effectiveAtFormItemRules,
  expireAtFormItemRules,
} from '@/lib/datetime-task-window'
import {
  dataRangeOptions,
  DEFAULT_CRAWL_FREQUENCY,
  platformDisplayNames,
  sourcePlatforms,
  TASK_NAME_MAX_LEN,
} from '@/views/TaskCreateForm/constants'
import {
  ensureSourceFieldSelectionForAllSelected,
  ensureSourceFieldSelectionInConfig,
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
    /** 编辑态：YDDM 列表卡片状态（决定调度字段是否可改） */
    editTaskStatus?: TaskRunStatus | null
  }>(),
  { taskConfigId: null, detail: null, editTaskStatus: null },
)

const emit = defineEmits<{
  back: []
  /** 第三参 `isRealtime`：单次任务已在弹框内 search-page 执行，列表页勿再调任务列表接口 */
  saved: [id: number, isEdit: boolean, isRealtime?: boolean]
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
    crawlFrequency: DEFAULT_CRAWL_FREQUENCY,
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

const isEditMode = computed(() => effectiveTaskConfigId() != null)

/** 非 pending 的编辑态：调度字段只读（名称仍可改） */
const scheduleFieldsLocked = computed(
  () => isEditMode.value && !canEditAsyncScheduleFields(props.editTaskStatus),
)

/** 仅定时任务校验开始/结束时间；单次任务不展示时间字段 */
const rules = computed<FormRules>(() => ({
  planName: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    {
      max: TASK_NAME_MAX_LEN,
      message: `任务名称不能超过 ${TASK_NAME_MAX_LEN} 个字符`,
      trigger: 'blur',
    },
  ],
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

/** 分步向导：① 基础/平台/关键词 → ② 排除词、排序、时间、条数 → ③ 采集字段、沉淀与飞书通知（定时，共 3 步） */
const LAST_STEP = 2
const totalWizardSteps = LAST_STEP + 1
const currentStep = ref(0)

/** 新建首次保存后由接口返回的 id，用于再次保存走 PUT */
const internalConfigId = ref<number | null>(null)

/** 保存前确认弹框 */
const confirmVisible = ref(false)
/** 积分不足时展示客服二维码 */
const customerServiceQrVisible = ref(false)
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

function isBalanceInsufficientForEstimate(): boolean {
  return isPointsInsufficient(
    pointsEstimate.value.total,
    accountPoints.currentBalancePoints,
  )
}

/** 预估消耗超过余额：关闭确认弹层、页内提示并弹出客服二维码 */
function handleInsufficientBalance() {
  confirmVisible.value = false
  showSaveError(POINTS_INSUFFICIENT_MSG)
  customerServiceQrVisible.value = true
}

const PLATFORM_REQUIRED_MSG = '请至少选择一个采集平台'

/** 至少勾选一个采集平台；失败时用页内横幅提示（避免被确认弹层遮挡） */
function ensurePlatformsSelected(): boolean {
  const hasPlatform = form.selectedSources.some((id) => isSupportedSourcePlatform(id))
  if (hasPlatform) return true
  confirmVisible.value = false
  showSaveError(PLATFORM_REQUIRED_MSG)
  if (currentStep.value !== 0) currentStep.value = 0
  return false
}

/** 关键词必填：合并草稿后检查，与表格名称等业务校验一致 */
function ensureKeywordsFilled(): boolean {
  flushKeywordDraftsToForm()
  if (form.keywords.length > KEYWORD_MAX_COUNT) {
    ElMessage.warning(KEYWORD_COUNT_EXCEEDED_HINT)
    return false
  }
  if (form.keywords.length > 0) return true
  ElMessage.warning('请至少添加一个关键词')
  return false
}

/** 保存前校验：单次任务不校验开始/结束时间与飞书通知 */
async function validateFormForSave(): Promise<void> {
  if (!formRef.value) return
  if (form.taskType === 'realtime') {
    formRef.value.clearValidate(['effectiveAt', 'expireAt', 'crawlFrequency', 'feishuWebhookUrl'])
    await formRef.value.validateField('planName')
    return
  }
  await formRef.value.validate()
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

async function goNextStep() {
  if (currentStep.value >= LAST_STEP) return
  if (currentStep.value === 0) {
    if (!ensureKeywordsFilled()) return
    if (!ensurePlatformsSelected()) return
    if (formRef.value) {
      const fields: string[] = ['planName']
      if (form.taskType === 'scheduled') {
        fields.push('crawlFrequency', 'effectiveAt', 'expireAt')
      }
      try {
        await formRef.value.validateField(fields)
      } catch (invalidFields) {
        notifyFormValidationFailed(invalidFields)
        return
      }
    }
  }
  currentStep.value += 1
}

/**
 * 将服务端 `config` 合并进表单；对 `sourceFieldSelection` 做白名单字段过滤。
 */
/** 兼容旧版 `excludeKeywords` 为整段字符串的配置 */
function normalizeKeywords(raw: unknown): string[] {
  if (!Array.isArray(raw)) return []
  const seen = new Set<string>()
  const out: string[] = []
  for (const item of raw) {
    if (typeof item !== 'string') continue
    const { value } = truncateKeyword(item)
    if (!value || seen.has(value)) continue
    seen.add(value)
    out.push(value)
  }
  return out.slice(0, KEYWORD_MAX_COUNT)
}

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
  form.keywords = normalizeKeywords(raw.keywords ?? form.keywords)
  const keywordSet = new Set(form.keywords)
  form.excludeKeywords = normalizeExcludeKeywords(raw.excludeKeywords).filter(
    (ex) => !keywordSet.has(ex),
  )
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
      form.feishuNotifyEnabled = false
      form.feishuWebhookUrl = ''
      void nextTick(() => {
        formRef.value?.clearValidate(['effectiveAt', 'expireAt', 'feishuWebhookUrl'])
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
/** 将输入框未按回车提交的草稿合并进表单数组 */
function flushKeywordDraftsToForm() {
  const { value: kw } = truncateKeyword(keywordDraft.value)
  if (kw && !form.keywords.includes(kw) && form.keywords.length < KEYWORD_MAX_COUNT) {
    form.keywords.push(kw)
  }
  keywordDraft.value = ''

  const ex = excludeKeywordDraft.value.trim()
  if (ex && !form.excludeKeywords.includes(ex) && !form.keywords.includes(ex)) {
    form.excludeKeywords.push(ex)
  }
  excludeKeywordDraft.value = ''
}

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
  if (!ensureKeywordsFilled()) return
  if (!ensurePlatformsSelected()) return
  try {
    await validateFormForSave()
  } catch (invalidFields) {
    notifyFormValidationFailed(invalidFields)
    return
  }
  if (form.tableMode === 'new') {
    for (const p of orderedSelectedPlatforms.value) {
      if (!form.platformNewTableNames[p.id]?.trim()) {
        showSaveError(`请填写${p.label}的目标表格名称（高级配置）`)
        return
      }
    }
  }
  await refreshYddmUserBalance()
  if (isBalanceInsufficientForEstimate()) {
    handleInsufficientBalance()
    return
  }
  confirmVisible.value = true
}

/** 确认弹框：定时任务落库并提交 YDDM；单次任务立即 search-page 采集并写表（不调任务列表接口） */
async function executeRealtimeFromConfirm(
  taskId: number,
  payload: Record<string, unknown>,
  ctx: Awaited<ReturnType<typeof buildCollectionFetchContext>>,
): Promise<void> {
  const taskName =
    String(payload.planName ?? payload.plan_name ?? '').trim() || '未命名任务'
  clearGlobalBitableAppendDedup()

  const createdTableNames = new Set<string>()
  let totalWritten = 0
  let totalRowCount = 0
  const platformWriteErrors: string[] = []

  const collection = await runRealtimeSyncSearchFromConfig(payload, ctx, {
    taskId,
    async onPlatformCollected(platform, items) {
      if (!isSyncCollectionPlatform(platform)) return
      const label = platformDisplayNames[platform] ?? platform
      try {
        const bitable = await syncSinglePlatformCollectionToBitable({
          taskId,
          taskName,
          config: payload,
          syncCtx: ctx,
          platform,
          items,
        })
        totalWritten += bitable.written
        totalRowCount += bitable.rowCount
        for (const name of bitable.createdTables) createdTableNames.add(name)
        if (bitable.written > 0) {
          ElMessage.success(`${label}：已写入 ${bitable.written} 条 → ${bitable.createdTables.join('、')}`)
        } else if (items.length > 0) {
          ElMessage.warning(
            `${label}：采集 ${items.length} 条，写入 0 条（请在飞书多维表格内打开插件，并检查采集字段配置）`,
          )
        } else if (bitable.createdTables.length) {
          ElMessage.info(`${label}：已新建「${bitable.createdTables.join('、')}」，本次无数据`)
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : '写入失败'
        platformWriteErrors.push(`${label}：${msg}`)
        ElMessage.error(`${label} 写入飞书表格失败：${msg}`)
      }
    },
  })

  applyCollectionResultToConfig(payload, {
    mode: 'sync',
    itemCount: collection.itemCount,
    itemsByPlatform: collection.itemsByPlatform,
    pointsConsumed: estimatePointsFromItemsByPlatform(collection.itemsByPlatform),
    emptyPlatformHints: collection.emptyPlatformHints,
  })
  saveTaskConfigSnapshot(taskId, payload)

  if (collection.emptyPlatformHints?.length && collection.itemCount === 0) {
    ElMessage.warning(collection.emptyPlatformHints.join('；'))
    return
  }
  if (collection.emptyPlatformHints?.length) {
    ElMessage.warning(`部分平台无数据：${collection.emptyPlatformHints.join('；')}`)
  }

  const tableHint = createdTableNames.size
    ? `左侧数据表：${[...createdTableNames].join('、')}`
    : ''
  if (platformWriteErrors.length && totalWritten === 0) {
    return
  }
  if (createdTableNames.size && totalWritten > 0) {
    ElMessage.success(`全部完成，共写入 ${totalWritten} 条。${tableHint}`)
  } else if (createdTableNames.size) {
    ElMessage.warning(
      `已新建 ${[...createdTableNames].join('、')}，但共写入 0 条（解析 ${totalRowCount} 条）。请在左侧点击表名查看。`,
    )
  } else if (collection.itemCount === 0) {
    ElMessage.warning('采集结果为空，未写入多维表格')
  }
}

async function persistFromConfirmDialog() {
  if (!formRef.value || saving.value) return
  if (isBalanceInsufficientForEstimate()) {
    handleInsufficientBalance()
    return
  }
  const globalSettings = useGlobalSettingsStore()
  if (!String(globalSettings.authCode ?? '').trim()) {
    showSaveError('请先在顶部填写 API-Key（授权码）')
    confirmVisible.value = false
    return
  }
  if (!ensureKeywordsFilled()) {
    confirmVisible.value = false
    return
  }
  if (!ensurePlatformsSelected()) return
  try {
    await validateFormForSave()
  } catch (invalidFields) {
    notifyFormValidationFailed(invalidFields)
    confirmVisible.value = false
    return
  }
  saving.value = true
  try {
    const payload = snapshotForm()
    if (form.taskType === 'realtime') {
      payload.taskType = 'realtime'
      payload.task_type = 'realtime'
      payload.effectiveAt = ''
      payload.expireAt = ''
      payload.feishuNotifyEnabled = false
      payload.feishuWebhookUrl = ''
      delete payload.task_start_time
      delete payload.task_end_time
    }
    Object.assign(payload, {
      taskPaused: false,
      taskAbnormal: false,
    })
    payload.selectedSources = [...form.selectedSources]
    payload.platformNewTableNames = { ...form.platformNewTableNames }
    ensureSourceFieldSelectionInConfig(payload)

    const existingId = effectiveTaskConfigId()
    const ctx = await buildCollectionFetchContext()
    let targetId: number
    let savedAsRealtime = false
    if (isRealtimeTaskConfig(payload)) {
      const draftId =
        existingId != null && (isLocalDraftTaskId(existingId) || form.taskType === 'realtime')
          ? existingId
          : Date.now()
      saveTaskConfigSnapshot(draftId, payload)
      internalConfigId.value = draftId
      targetId = draftId
      await executeRealtimeFromConfirm(draftId, payload, ctx)
      savedAsRealtime = true
    } else if (existingId != null && !isLocalDraftTaskId(existingId)) {
      const editBody = buildAsyncTaskEditRequest(existingId, payload, {
        allowScheduleFields:
          form.taskType === 'scheduled' && canEditAsyncScheduleFields(props.editTaskStatus),
      })
      await editAsyncTask(ctx, editBody)
      saveTaskConfigSnapshot(existingId, payload)
      targetId = existingId
    } else {
      const collection = await submitCollectionFromConfig(payload, ctx)
      if (collection.mode !== 'async' || !collection.refs.length) {
        throw new Error('提交定时任务失败：未返回 YDDM 任务 ID')
      }
      applyCollectionResultToConfig(payload, collection)
      const primaryId = Number(collection.refs[0]!.taskId)
      if (!Number.isFinite(primaryId) || primaryId <= 0 || isLocalDraftTaskId(primaryId)) {
        throw new Error('提交定时任务失败：任务 ID 无效')
      }
      persistCollectionRefsToLocal(primaryId, payload, {
        draftId: existingId != null && isLocalDraftTaskId(existingId) ? existingId : undefined,
      })
      internalConfigId.value = primaryId
      targetId = primaryId
    }

    confirmVisible.value = false
    saveBanner.value = null
    saveErrorText.value = ''
    emit('saved', targetId, existingId != null, savedAsRealtime)
  } catch (e) {
    confirmVisible.value = false
    const msg = e instanceof Error ? e.message : '保存任务失败'
    if (msg === PLATFORM_REQUIRED_MSG && currentStep.value !== 0) {
      currentStep.value = 0
    }
    showSaveError(msg)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex min-h-0 w-full min-w-0 flex-col gap-6 pb-8">
    <el-alert
      v-if="saveBanner === 'error'"
      type="error"
      :title="saveErrorText"
      show-icon
      closable
      class="save-banner sticky top-0 z-[2100] mb-3 w-full min-w-0 shadow-sm"
      @close="saveBanner = null"
    />

    <CustomerServiceQrDialog v-model="customerServiceQrVisible" />

    <TaskConfigConfirmDialog
      v-model="confirmVisible"
      :rows="confirmDisplayRows"
      :estimated-points="pointsEstimate.total"
      :scheduled-execution-rounds="
        form.taskType === 'scheduled' ? pointsEstimate.scheduledExecutionRounds : undefined
      "
      :balance-points="accountPoints.currentBalancePoints"
      :confirming="saving"
      :is-realtime-task="form.taskType === 'realtime'"
      @confirm="persistFromConfirmDialog"
      @recharge="handleInsufficientBalance"
    />

    <div
      class="task-config-step-header flex w-full min-w-0 shrink-0 items-center justify-between gap-3 pt-1"
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
      class="task-create-form w-full min-w-0"
    >
      <div v-show="currentStep === 0">
        <BasicInfoSection :form="form" />
        <CrawlScheduleSection :form="form" :schedule-locked="scheduleFieldsLocked" />
        <p class="task-form-field-title mb-2 mt-6">
          采集平台<span class="task-form-field-required" aria-hidden="true">*</span>
        </p>
        <SourceSelectionSection
          mode="platforms"
          :form="form"
          :ordered-platforms="orderedSelectedPlatforms"
        />
        <p class="task-form-field-title mb-2 mt-6">
          关键词监控<span class="task-form-field-required" aria-hidden="true">*</span>
        </p>
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
          :schedule-locked="scheduleFieldsLocked"
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
        <FeishuNotifySection v-if="form.taskType === 'scheduled'" :form="form" class="mt-8" />
      </div>
    </el-form>

    <div class="footer-actions w-full min-w-0 border-t border-slate-100 pt-6">
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
            >{{ form.taskType === 'realtime' ? '立即执行' : '开始执行' }}</el-button
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

.task-create-form .task-form-field-optional {
  margin-left: 4px;
  font-weight: 400;
  color: #86909c;
}

.task-create-form .task-form-field-required {
  margin-left: 4px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1;
  color: #f54a45;
}
</style>
