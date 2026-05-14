<script setup lang="ts">
import dayjs from 'dayjs'
import { computed, onMounted, onScopeDispose, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import TaskCreateForm from '@/views/TaskCreateForm/index.vue'
import { platformDisplayNames, sourcePlatforms } from '@/views/TaskCreateForm/constants'
import TaskDetailDialog from '@/views/tasks/components/TaskDetailDialog.vue'
import TaskListCard from '@/views/tasks/components/TaskListCard.vue'
import type { TaskCardModel, TaskStoppedKind } from '@/views/tasks/types'
import {
  deleteFeishuTaskConfig,
  feishuDetailToListItem,
  getFeishuTaskConfig,
  listFeishuTaskConfigs,
  parseBackendDisplayStatus,
  parseBackendStoppedKind,
  updateFeishuTaskConfig,
  type FeishuTaskConfigDetail,
  type FeishuTaskConfigListItem,
  type FeishuTaskConfigWriteResult,
} from '@/lib/api'

const tasks = ref<TaskCardModel[]>([])
/** 列表每页条数 */
const TASK_PAGE_SIZE = 5
const listCurrentPage = ref(1)
/** 「前往」页码输入草稿，需点击「确定」才翻页 */
const jumpPageDraft = ref(1)
const screen = ref<'list' | 'create'>('list')
const editingTaskId = ref<number | null>(null)
const taskDetail = ref<FeishuTaskConfigDetail | null>(null)

const detailDialogVisible = ref(false)
const detailDialogLoading = ref(false)
const detailDialogPayload = ref<FeishuTaskConfigDetail | null>(null)

/** 删除确认：不用 ElMessageBox（飞书 iframe 内易出现错位、叠字） */
const deleteDialogVisible = ref(false)
const deleteTarget = ref<TaskCardModel | null>(null)
const deleteSubmitting = ref(false)
const deleteError = ref('')

const listTip = ref<string | null>(null)
let listTipTimer: ReturnType<typeof setTimeout> | null = null

function showListTip(msg: string) {
  if (listTipTimer != null) {
    clearTimeout(listTipTimer)
    listTipTimer = null
  }
  listTip.value = msg
  listTipTimer = setTimeout(() => {
    listTip.value = null
    listTipTimer = null
  }, 3500)
}

onScopeDispose(() => {
  if (listTipTimer != null) clearTimeout(listTipTimer)
})

const primaryActionRowId = ref<number | null>(null)

function cloneConfigRecord(raw: unknown): Record<string, unknown> {
  if (raw != null && typeof raw === 'object' && !Array.isArray(raw)) {
    return JSON.parse(JSON.stringify(raw)) as Record<string, unknown>
  }
  return {}
}

async function patchTaskConfig(
  id: number,
  patch: Record<string, unknown>,
): Promise<FeishuTaskConfigWriteResult> {
  const detail = await getFeishuTaskConfig(id)
  const cfg = { ...cloneConfigRecord(detail.config), ...patch }
  return updateFeishuTaskConfig(id, cfg)
}

/** 用 POST/PUT 返回的 `display_status` 覆盖列表行（在 `loadTaskList` 之后调用） */
function applyDisplayFromWrite(id: number, wr: FeishuTaskConfigWriteResult) {
  if (typeof wr.display_status !== 'string' || !wr.display_status.trim()) return
  const idx = tasks.value.findIndex((t) => t.id === id)
  if (idx < 0) return
  const prev = tasks.value[idx]
  const status = parseBackendDisplayStatus(wr)
  const stoppedKind: TaskStoppedKind =
    status === 'stopped' ? parseBackendStoppedKind(wr) : 'neutral'
  tasks.value.splice(idx, 1, { ...prev, status, stoppedKind })
}

function isPrimaryLoadingFor(rowId: number): boolean {
  return primaryActionRowId.value === rowId
}

/** 将任务标为异常（接口失败等），供列表推导为「失败」 */
async function markTaskAbnormal(id: number) {
  try {
    const detail = await getFeishuTaskConfig(id)
    const cfg = { ...cloneConfigRecord(detail.config), taskAbnormal: true, runStatus: 'failed' }
    await updateFeishuTaskConfig(id, cfg)
  } catch {
    /* 忽略二次失败 */
  }
}

function formatPlatformsLabel(keys: string[] | null | undefined): string {
  if (!keys || keys.length === 0) return '未选择平台'
  const supported = new Set(sourcePlatforms.map((p) => p.id))
  const normalized = keys.filter((k): k is keyof typeof platformDisplayNames => k in platformDisplayNames)
  const onlySupported = normalized.filter((k) => supported.has(k))
  if (onlySupported.length >= sourcePlatforms.length && sourcePlatforms.every((p) => onlySupported.includes(p.id))) {
    return '全平台'
  }
  const labels = normalized.map((k) => platformDisplayNames[k])
  return labels.length ? labels.join('、') : '未选择平台'
}

function formatCardDate(raw: string | null | undefined): string {
  if (!raw?.trim()) return '—'
  const d = dayjs(raw)
  return d.isValid() ? d.format('YYYY-MM-DD') : raw.slice(0, 10) || '—'
}

/** 任务列表统计（与后端返回的 `display_status` 映射后一致） */
const taskStats = computed(() => {
  const list = tasks.value
  return {
    total: list.length,
    running: list.filter((t) => t.status === 'running').length,
    stopped: list.filter((t) => t.status === 'stopped' || t.status === 'pending_run').length,
  }
})

/** 点击统计卡片筛选列表：`all` | `running` | `stopped` */
const listFilter = ref<'all' | 'running' | 'stopped'>('all')

const displayedTasks = computed(() => {
  switch (listFilter.value) {
    case 'running':
      return tasks.value.filter((t) => t.status === 'running')
    case 'stopped':
      return tasks.value.filter((t) => t.status === 'stopped' || t.status === 'pending_run')
    default:
      return tasks.value
  }
})

/** 当前筛选下的分页切片 */
const pagedDisplayedTasks = computed(() => {
  const list = displayedTasks.value
  const start = (listCurrentPage.value - 1) * TASK_PAGE_SIZE
  return list.slice(start, start + TASK_PAGE_SIZE)
})

/** 当前筛选下的总页数 */
const totalPages = computed(() =>
  Math.max(1, Math.ceil(displayedTasks.value.length / TASK_PAGE_SIZE)),
)

watch(listCurrentPage, (p) => {
  jumpPageDraft.value = p
})

watch(
  () => displayedTasks.value.length,
  (len) => {
    const maxPage = Math.max(1, Math.ceil(len / TASK_PAGE_SIZE))
    if (listCurrentPage.value > maxPage) listCurrentPage.value = maxPage
  },
)

function confirmJumpPage() {
  const n = Number(jumpPageDraft.value)
  if (!Number.isFinite(n) || n < 1) {
    ElMessage.warning('请输入有效页码')
    return
  }
  const clamped = Math.min(totalPages.value, Math.max(1, Math.floor(n)))
  listCurrentPage.value = clamped
  jumpPageDraft.value = clamped
}

const listFilterLoading = ref(false)

/** 切换统计维度时重新拉列表，保证与后端状态一致 */
async function selectListFilter(next: 'all' | 'running' | 'stopped') {
  if (listFilterLoading.value) return
  listFilter.value = next
  listCurrentPage.value = 1
  listFilterLoading.value = true
  try {
    await loadTaskList()
  } finally {
    listFilterLoading.value = false
  }
}

/** 停止/启动后：优先用 PUT 返回的 `display_status` 覆盖；否则再拉详情（列表缺字段时） */
async function mergeTaskCardFromDetail(id: number, wr?: FeishuTaskConfigWriteResult) {
  if (typeof wr?.display_status === 'string' && wr.display_status.trim() !== '') {
    applyDisplayFromWrite(id, wr)
    return
  }
  try {
    const detail = await getFeishuTaskConfig(id)
    const item = feishuDetailToListItem(detail)
    const [card] = mapRows([item])
    const idx = tasks.value.findIndex((t) => t.id === id)
    if (idx >= 0) tasks.value.splice(idx, 1, card)
  } catch {
    /* 详情失败时保留仅列表刷新的结果 */
  }
}

function mapRows(rows: FeishuTaskConfigListItem[]): TaskCardModel[] {
  return rows.map((r) => {
    const effStr = r.effective_at?.trim() ? String(r.effective_at).trim() : null
    const expStr = r.expire_at?.trim() ? String(r.expire_at).trim() : null
    const o = r as Record<string, unknown>
    const status = parseBackendDisplayStatus(o)
    const rawTaskType = o.task_type ?? o.taskType
    const isRealtime = rawTaskType === 'realtime'
    const stoppedKind: TaskStoppedKind =
      status === 'stopped' ? parseBackendStoppedKind(o) : 'neutral'

    return {
      id: r.id,
      name: r.plan_name?.trim() || '未命名方案',
      platformsLabel: formatPlatformsLabel(r.platform_keys ?? undefined),
      taskTypeLabel: isRealtime ? '单次任务' : '定时任务',
      dateLabel: isRealtime ? '—' : formatCardDate(r.effective_at ?? undefined),
      status,
      notificationCount: 0,
      effectiveAtRaw: effStr,
      expireAtRaw: expStr,
      stoppedKind,
    }
  })
}

async function loadTaskList() {
  try {
    const rows = await listFeishuTaskConfigs(0, 100)
    tasks.value = mapRows(rows)
    const maxPage = Math.max(1, Math.ceil(displayedTasks.value.length / TASK_PAGE_SIZE))
    if (listCurrentPage.value > maxPage) listCurrentPage.value = maxPage
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载任务列表失败')
    tasks.value = []
    listCurrentPage.value = 1
  }
}

onMounted(() => {
  void loadTaskList()
})

function onCreateTask() {
  editingTaskId.value = null
  taskDetail.value = null
  screen.value = 'create'
}

async function onBackFromCreate() {
  screen.value = 'list'
  editingTaskId.value = null
  taskDetail.value = null
  await loadTaskList()
}

/** 保存成功后回到任务列表并刷新（与点「返回任务列表」一致） */
async function onSaved(_id: number) {
  await onBackFromCreate()
}

async function openView(row: TaskCardModel) {
  detailDialogVisible.value = true
  detailDialogLoading.value = true
  detailDialogPayload.value = null
  try {
    detailDialogPayload.value = await getFeishuTaskConfig(row.id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载配置失败')
    detailDialogVisible.value = false
    void markTaskAbnormal(row.id)
    await loadTaskList()
  } finally {
    detailDialogLoading.value = false
  }
}

async function openEdit(row: TaskCardModel) {
  editingTaskId.value = row.id
  taskDetail.value = null
  screen.value = 'create'
  try {
    taskDetail.value = await getFeishuTaskConfig(row.id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载配置失败')
    void markTaskAbnormal(row.id)
    await loadTaskList()
    screen.value = 'list'
    editingTaskId.value = null
  }
}

async function onPrimaryAction(row: TaskCardModel) {
  if (primaryActionRowId.value != null) return
  primaryActionRowId.value = row.id
  try {
    switch (row.status) {
      case 'running': {
        const wr = await patchTaskConfig(row.id, { taskPaused: true })
        await loadTaskList()
        await mergeTaskCardFromDetail(row.id, wr)
        showListTip(wr.display_status === 'stopped' ? '已停止' : '已保存')
        break
      }
      case 'stopped':
      case 'pending_run':
      case 'completed':
      case 'failed': {
        const wr = await patchTaskConfig(row.id, {
          taskPaused: false,
          taskAbnormal: false,
          runStatus: 'stopped',
        })
        await loadTaskList()
        await mergeTaskCardFromDetail(row.id, wr)
        if (wr.display_status === 'running') {
          showListTip('已启动')
        } else if (wr.display_status === 'completed') {
          showListTip('任务已过期或未在窗口内，请编辑生效/过期时间后再启动')
        } else if (wr.display_status === 'pending_run') {
          showListTip('未到生效时间，仍为待运行')
        } else if (parseBackendStoppedKind(wr) === 'before_effective') {
          showListTip('未到生效时间，仍为已停止')
        } else {
          showListTip('已提交')
        }
        break
      }
      default:
        break
    }
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '操作失败')
    void markTaskAbnormal(row.id)
    await loadTaskList()
  } finally {
    primaryActionRowId.value = null
  }
}

function onDeleteTask(row: TaskCardModel) {
  deleteError.value = ''
  deleteTarget.value = row
  deleteDialogVisible.value = true
}

function onDeleteDialogClosed() {
  deleteTarget.value = null
  deleteError.value = ''
}

async function confirmDeleteTask() {
  const row = deleteTarget.value
  if (!row || deleteSubmitting.value) return
  deleteError.value = ''
  deleteSubmitting.value = true
  try {
    await deleteFeishuTaskConfig(row.id)
    deleteDialogVisible.value = false
    showListTip('已删除')
    await loadTaskList()
  } catch (e) {
    deleteError.value = e instanceof Error ? e.message : '删除失败'
  } finally {
    deleteSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-0 flex-col gap-4">
    <TaskDetailDialog
      v-model="detailDialogVisible"
      :detail="detailDialogPayload"
      :loading="detailDialogLoading"
    />

    <el-dialog
      v-model="deleteDialogVisible"
      title="删除任务"
      width="420px"
      align-center
      append-to-body
      destroy-on-close
      :close-on-click-modal="false"
      class="delete-task-dialog"
      @closed="onDeleteDialogClosed"
    >
      <el-alert
        v-if="deleteError"
        type="error"
        :title="deleteError"
        show-icon
        closable
        class="mb-3"
        @close="deleteError = ''"
      />
      <p v-if="deleteTarget" class="m-0 text-sm leading-relaxed text-slate-600">
        确定删除「<strong class="font-medium text-slate-800">{{ deleteTarget.name }}</strong>」？删除后不可恢复。
      </p>
      <template #footer>
        <div class="flex justify-end gap-2">
          <el-button :disabled="deleteSubmitting" @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" :loading="deleteSubmitting" @click="confirmDeleteTask">删除</el-button>
        </div>
      </template>
    </el-dialog>

    <template v-if="screen === 'create'">
      <div
        v-if="editingTaskId !== null && !taskDetail"
        class="py-16 text-center text-sm text-slate-500"
      >
        加载配置…
      </div>
      <TaskCreateForm
        v-else
        :task-config-id="editingTaskId"
        :detail="taskDetail"
        @back="onBackFromCreate"
        @saved="onSaved"
      />
    </template>

    <template v-else>
      <section class="flex min-h-0 flex-col gap-4">
        <el-alert
          v-if="listTip"
          type="success"
          :title="listTip"
          show-icon
          closable
          class="sticky top-0 z-10 shadow-sm"
          @close="listTip = null"
        />
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="text-base font-semibold text-slate-800">任务列表</h2>
          <el-button type="primary" @click="onCreateTask">新建任务</el-button>
        </div>

        <div class="grid min-w-0 grid-cols-3 gap-2 sm:gap-3">
          <button
            type="button"
            class="min-w-0 rounded-lg border px-2 py-4 text-center shadow-sm transition-colors sm:px-4 sm:py-5 disabled:cursor-not-allowed disabled:opacity-60"
            :class="
              listFilter === 'running'
                ? 'border-indigo-500 bg-indigo-50/90 ring-1 ring-indigo-500/30'
                : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
            "
            :disabled="listFilterLoading"
            @click="selectListFilter('running')"
          >
            <div class="text-2xl font-bold leading-none text-[#3355FF] sm:text-3xl">{{ taskStats.running }}</div>
            <div class="mt-1.5 whitespace-nowrap text-[11px] leading-none text-slate-600 sm:text-xs">
              运行中
            </div>
          </button>
          <button
            type="button"
            class="min-w-0 rounded-lg border px-2 py-4 text-center shadow-sm transition-colors sm:px-4 sm:py-5 disabled:cursor-not-allowed disabled:opacity-60"
            :class="
              listFilter === 'stopped'
                ? 'border-indigo-500 bg-indigo-50/90 ring-1 ring-indigo-500/30'
                : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
            "
            :disabled="listFilterLoading"
            @click="selectListFilter('stopped')"
          >
            <div class="text-2xl font-bold leading-none text-[#3355FF] sm:text-3xl">{{ taskStats.stopped }}</div>
            <div class="mt-1.5 whitespace-nowrap text-[11px] leading-none text-slate-600 sm:text-xs">
              已停止
            </div>
          </button>
          <button
            type="button"
            class="min-w-0 rounded-lg border px-2 py-4 text-center shadow-sm transition-colors sm:px-4 sm:py-5 disabled:cursor-not-allowed disabled:opacity-60"
            :class="
              listFilter === 'all'
                ? 'border-indigo-500 bg-indigo-50/90 ring-1 ring-indigo-500/30'
                : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
            "
            :disabled="listFilterLoading"
            @click="selectListFilter('all')"
          >
            <div class="text-2xl font-bold leading-none text-[#3355FF] sm:text-3xl">{{ taskStats.total }}</div>
            <div class="mt-1.5 whitespace-nowrap text-[11px] leading-none text-slate-600 sm:text-xs">
              总任务数
            </div>
          </button>
        </div>

        <div v-if="displayedTasks.length > 0" class="flex flex-col gap-4">
          <TaskListCard
            v-for="row in pagedDisplayedTasks"
            :key="row.id"
            :row="row"
            :primary-loading="isPrimaryLoadingFor(row.id)"
            @view="openView"
            @edit="openEdit"
            @primary-action="onPrimaryAction"
            @delete="onDeleteTask"
          />
          <div
            class="task-page-bar mx-auto flex max-w-full flex-nowrap items-center justify-center gap-1.5 overflow-x-auto pt-2 text-xs text-slate-600"
          >
            <el-button size="small" :disabled="listCurrentPage <= 1" @click="listCurrentPage--">
              上一页
            </el-button>
            <el-button size="small" :disabled="listCurrentPage >= totalPages" @click="listCurrentPage++">
              下一页
            </el-button>
            <span class="shrink-0 pl-0.5">前往</span>
            <el-input-number
              v-model="jumpPageDraft"
              size="small"
              :min="1"
              :max="totalPages"
              :controls="false"
              class="task-page-jump-input shrink-0"
            />
            <el-button size="small" type="primary" @click="confirmJumpPage">确定</el-button>
          </div>
        </div>
        <p v-else-if="tasks.length > 0" class="py-6 text-center text-sm text-slate-400">当前筛选下暂无任务</p>
        <p v-else class="py-6 text-center text-sm text-slate-400">暂无任务</p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.task-page-jump-input {
  width: 3.75rem;
}
.task-page-jump-input :deep(.el-input__wrapper) {
  padding-left: 0.375rem;
  padding-right: 0.375rem;
}
</style>
