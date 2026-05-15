<script setup lang="ts">
import { ArrowLeft, ArrowRight, Plus } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { computed, onMounted, onScopeDispose, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { storeToRefs } from 'pinia'
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
import { useGlobalSettingsStore } from '@/stores/globalSettings'

const tasks = ref<TaskCardModel[]>([])
/** 列表每页条数 */
const pageSize = ref(10)
const listCurrentPage = ref(1)
const screen = ref<'list' | 'create'>('list')
const editingTaskId = ref<number | null>(null)
const taskDetail = ref<FeishuTaskConfigDetail | null>(null)

const globalSettings = useGlobalSettingsStore()
const { authCode } = storeToRefs(globalSettings)

const detailDialogVisible = ref(false)
const detailDialogLoading = ref(false)
const detailDialogPayload = ref<FeishuTaskConfigDetail | null>(null)
/** 与详情弹框底部操作区对应列表行（随列表刷新同步） */
const detailDialogRow = ref<TaskCardModel | null>(null)

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
    completed: list.filter((t) => t.status === 'completed').length,
  }
})

/** 点击统计卡片筛选列表：`all` | `running` | `completed` */
const listFilter = ref<'all' | 'running' | 'completed'>('all')

const displayedTasks = computed(() => {
  switch (listFilter.value) {
    case 'running':
      return tasks.value.filter((t) => t.status === 'running')
    case 'completed':
      return tasks.value.filter((t) => t.status === 'completed')
    default:
      return tasks.value
  }
})

/** 当前筛选下的分页切片 */
const pagedDisplayedTasks = computed(() => {
  const list = displayedTasks.value
  const start = (listCurrentPage.value - 1) * pageSize.value
  return list.slice(start, start + pageSize.value)
})

watch(
  () => displayedTasks.value.length,
  (len) => {
    const maxPage = Math.max(1, Math.ceil(len / pageSize.value))
    if (listCurrentPage.value > maxPage) listCurrentPage.value = maxPage
  },
)

const paginationTotalPages = computed(() =>
  Math.max(1, Math.ceil(displayedTasks.value.length / pageSize.value)),
)

/** 页码序列：如 1 2 3 … 10 */
function buildPaginationItems(current: number, total: number): Array<number | 'ellipsis'> {
  if (total < 1) return []
  if (total === 1) return [1]
  const edge = new Set<number>([1, total])
  const pad = 2
  for (let i = current - pad; i <= current + pad; i++) {
    if (i >= 1 && i <= total) edge.add(i)
  }
  const sorted = [...edge].sort((a, b) => a - b)
  const out: Array<number | 'ellipsis'> = []
  for (let i = 0; i < sorted.length; i++) {
    const n = sorted[i]!
    if (i > 0 && n - sorted[i - 1]! > 1) out.push('ellipsis')
    out.push(n)
  }
  return out
}

const paginationItems = computed(() =>
  buildPaginationItems(listCurrentPage.value, paginationTotalPages.value),
)

const pageSizeSelectOptions = [5, 10, 20] as const

function onPageSizeChange(s: number) {
  pageSize.value = s
  listCurrentPage.value = 1
}

const listFilterLoading = ref(false)

/** 切换统计维度时重新拉列表，保证与后端状态一致 */
async function selectListFilter(next: 'all' | 'running' | 'completed') {
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
      name: r.plan_name?.trim() || '未命名任务',
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
  if (!authCode.value.trim()) {
    tasks.value = []
    listCurrentPage.value = 1
    return
  }
  try {
    const rows = await listFeishuTaskConfigs(0, 100)
    tasks.value = mapRows(rows)
    const maxPage = Math.max(1, Math.ceil(displayedTasks.value.length / pageSize.value))
    if (listCurrentPage.value > maxPage) listCurrentPage.value = maxPage
  } catch (e) {
    const msg = e instanceof Error ? e.message : '加载任务列表失败'
    ElMessage.error(msg)
    tasks.value = []
    listCurrentPage.value = 1
  }
}

watch(authCode, () => {
  void loadTaskList()
})

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

const emit = defineEmits<{
  createModeChange: [inCreate: boolean]
}>()

watch(
  screen,
  (s) => {
    emit('createModeChange', s === 'create')
  },
  { immediate: true },
)

defineExpose({
  leaveCreateToList: onBackFromCreate,
})

/** 保存成功后回到任务列表并刷新 */
async function onSaved(_id: number) {
  await onBackFromCreate()
  showListTip('任务已添加到任务列表')
}

async function openView(row: TaskCardModel) {
  detailDialogRow.value = row
  detailDialogVisible.value = true
  detailDialogLoading.value = true
  detailDialogPayload.value = null
  try {
    detailDialogPayload.value = await getFeishuTaskConfig(row.id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载配置失败')
    detailDialogVisible.value = false
    detailDialogRow.value = null
    void markTaskAbnormal(row.id)
    await loadTaskList()
  } finally {
    detailDialogLoading.value = false
  }
}

async function openEdit(row: TaskCardModel) {
  detailDialogVisible.value = false
  detailDialogPayload.value = null
  detailDialogRow.value = null
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
      case 'running':
      case 'pending_run': {
        const wr = await patchTaskConfig(row.id, { taskPaused: true })
        await loadTaskList()
        await mergeTaskCardFromDetail(row.id, wr)
        showListTip(parseBackendDisplayStatus(wr) === 'stopped' ? '已停止' : '已保存')
        break
      }
      case 'stopped':
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
    if (detailDialogVisible.value && detailDialogRow.value?.id === row.id) {
      const next = tasks.value.find((t) => t.id === row.id)
      if (next) detailDialogRow.value = next
    }
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
    const deletedId = row.id
    await deleteFeishuTaskConfig(row.id)
    deleteDialogVisible.value = false
    showListTip('已删除')
    await loadTaskList()
    if (detailDialogVisible.value && detailDialogRow.value?.id === deletedId) {
      detailDialogVisible.value = false
      detailDialogPayload.value = null
      detailDialogRow.value = null
    }
  } catch (e) {
    deleteError.value = e instanceof Error ? e.message : '删除失败'
  } finally {
    deleteSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-0 w-full min-w-0 flex-col gap-4">
    <TaskDetailDialog
      v-model="detailDialogVisible"
      :detail="detailDialogPayload"
      :loading="detailDialogLoading"
      :row="detailDialogRow"
      :primary-loading="detailDialogRow ? isPrimaryLoadingFor(detailDialogRow.id) : false"
      @primary-action="onPrimaryAction"
      @delete="onDeleteTask"
      @edit="openEdit"
    />

    <el-dialog
      v-model="deleteDialogVisible"
      title="删除任务"
      width="90%"
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
        <div class="task-stat-row flex w-full min-w-0 gap-2">
          <button
            type="button"
            class="task-stat-card"
            :class="{ 'task-stat-card--active': listFilter === 'all' }"
            :disabled="listFilterLoading"
            @click="selectListFilter('all')"
          >
            <div class="task-stat-num task-stat-num--total">{{ taskStats.total }}</div>
            <div class="task-stat-label">总任务数</div>
          </button>
          <button
            type="button"
            class="task-stat-card"
            :class="{ 'task-stat-card--active': listFilter === 'running' }"
            :disabled="listFilterLoading"
            @click="selectListFilter('running')"
          >
            <div class="task-stat-num task-stat-num--running">{{ taskStats.running }}</div>
            <div class="task-stat-label">运行中</div>
          </button>
          <button
            type="button"
            class="task-stat-card"
            :class="{ 'task-stat-card--active': listFilter === 'completed' }"
            :disabled="listFilterLoading"
            @click="selectListFilter('completed')"
          >
            <div class="task-stat-num task-stat-num--completed">{{ taskStats.completed }}</div>
            <div class="task-stat-label">已完成</div>
          </button>
        </div>

        <button type="button" class="task-create-btn" @click="onCreateTask">
          <el-icon class="task-create-btn__icon" :size="18">
            <Plus />
          </el-icon>
          新建任务
        </button>

        <h2 class="task-list-heading">任务列表</h2>

        <div v-if="displayedTasks.length > 0" class="flex flex-col gap-3">
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
          <div class="task-pagination-bar">
            <button
              type="button"
              class="task-pagination-icon-btn"
              :disabled="listCurrentPage <= 1"
              aria-label="上一页"
              @click="listCurrentPage--"
            >
              <el-icon :size="18">
                <ArrowLeft />
              </el-icon>
            </button>
            <div class="task-pagination-pages">
              <template v-for="(item, idx) in paginationItems" :key="`pg-${idx}-${String(item)}`">
                <span v-if="item === 'ellipsis'" class="task-pagination-ellipsis">...</span>
                <button
                  v-else
                  type="button"
                  class="task-pagination-page-btn"
                  :class="{ 'task-pagination-page-btn--active': item === listCurrentPage }"
                  @click="listCurrentPage = item"
                >
                  {{ item }}
                </button>
              </template>
            </div>
            <button
              type="button"
              class="task-pagination-icon-btn"
              :disabled="listCurrentPage >= paginationTotalPages"
              aria-label="下一页"
              @click="listCurrentPage++"
            >
              <el-icon :size="18">
                <ArrowRight />
              </el-icon>
            </button>
            <el-select
              :model-value="pageSize"
              class="task-pagination-size-select"
              size="small"
              teleported
              @update:model-value="onPageSizeChange"
            >
              <el-option
                v-for="n in pageSizeSelectOptions"
                :key="n"
                :label="`${n}条/页`"
                :value="n"
              />
            </el-select>
          </div>
        </div>
        <p v-else-if="tasks.length > 0" class="py-6 text-center text-sm text-slate-400">当前筛选下暂无任务</p>
        <p v-else class="py-6 text-center text-sm text-slate-400">暂无任务</p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.task-stat-row {
  -webkit-overflow-scrolling: touch;
}

.task-stat-card {
  box-sizing: border-box;
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: auto;
  height: 94px;
  padding: 0 8px;
  margin: 0;
  border: none;
  background: #f8f9fa;
  border-radius: 0;
  cursor: pointer;
  transition: box-shadow 0.15s ease;
}

.task-stat-card:hover:not(:disabled):not(.task-stat-card--active) {
  box-shadow: inset 0 0 0 1px #e1e4e8;
}

.task-stat-card:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.task-stat-card--active {
  box-shadow: inset 0 0 0 2px #3370ff;
}

.task-stat-num {
  font-weight: 600;
  font-size: 24px;
  text-align: center;
  font-style: normal;
  text-transform: none;
  line-height: 1.2;
}

.task-stat-num--total {
  color: #2b2f36;
}

.task-stat-num--running {
  color: #3370ff;
}

.task-stat-num--completed {
  color: #34c724;
}

.task-stat-label {
  margin-top: 6px;
  font-weight: 400;
  font-size: 14px;
  color: #2b2f36;
  text-align: center;
  font-style: normal;
  text-transform: none;
  line-height: 1.2;
  white-space: nowrap;
}

.task-list-heading {
  margin: 0;
  font-weight: 500;
  font-size: 16px;
  color: #0f1114;
  text-align: left;
  font-style: normal;
  text-transform: none;
  line-height: 1.4;
}

.task-create-btn {
  box-sizing: border-box;
  display: inline-flex;
  width: 100%;
  min-width: 0;
  align-items: center;
  justify-content: center;
  height: 46px;
  padding: 0 16px;
  margin: 0;
  border: none;
  border-radius: 4px;
  background: linear-gradient(90deg, #1456f0 0%, #4014f0 100%);
  color: #ffffff;
  font-weight: 400;
  font-size: 16px;
  text-align: center;
  font-style: normal;
  line-height: 1;
  cursor: pointer;
  transition: filter 0.15s ease, box-shadow 0.15s ease;
}

.task-create-btn:hover {
  filter: brightness(1.06);
}

.task-create-btn:focus-visible {
  outline: 2px solid #4014f0;
  outline-offset: 2px;
}

.task-create-btn:active {
  filter: brightness(0.96);
}

.task-create-btn__icon {
  margin-right: 6px;
  color: #ffffff;
}

.task-pagination-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px 12px;
  padding-top: 0.5rem;
}

.task-pagination-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #646a73;
  cursor: pointer;
  transition: color 0.15s ease, background-color 0.15s ease;
}

.task-pagination-icon-btn:hover:not(:disabled) {
  color: #3370ff;
  background: rgba(51, 112, 255, 0.08);
}

.task-pagination-icon-btn:disabled {
  cursor: not-allowed;
  color: #bbbfc4;
  opacity: 0.55;
}

.task-pagination-pages {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.task-pagination-ellipsis {
  display: inline-flex;
  min-width: 1.25rem;
  align-items: center;
  justify-content: center;
  padding: 0 2px;
  font-size: 14px;
  font-weight: 500;
  color: #8f959e;
  user-select: none;
}

.task-pagination-page-btn {
  box-sizing: border-box;
  min-width: 28px;
  height: 28px;
  padding: 0 6px;
  margin: 0;
  border: 1px solid transparent;
  border-radius: 4px;
  background: #ffffff;
  color: #2b2f36;
  font-size: 14px;
  font-weight: 400;
  line-height: 1;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    color 0.15s ease,
    background-color 0.15s ease;
}

.task-pagination-page-btn:hover:not(.task-pagination-page-btn--active) {
  border-color: #dee0e3;
  background: #f8f9fa;
}

.task-pagination-page-btn--active {
  border-color: #3370ff;
  color: #3370ff;
  font-weight: 500;
}

.task-pagination-size-select {
  width: 108px;
}

.task-pagination-size-select :deep(.el-select__wrapper) {
  border-radius: 4px;
}
</style>

<style>
.delete-task-dialog.el-dialog {
  width: min(420px, calc(100vw - 24px)) !important;
  max-width: calc(100vw - 16px);
}
</style>
