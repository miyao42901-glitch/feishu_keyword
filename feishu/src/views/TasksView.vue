<script setup lang="ts">
import dayjs from 'dayjs'
import { computed, onMounted, onScopeDispose, ref } from 'vue'
import { ElMessage } from 'element-plus'
import TaskCreateForm from '@/views/TaskCreateForm/index.vue'
import { sourcePlatforms } from '@/views/TaskCreateForm/constants'
import TaskDetailDialog from '@/views/tasks/components/TaskDetailDialog.vue'
import TaskListCard from '@/views/tasks/components/TaskListCard.vue'
import type { TaskCardModel } from '@/views/tasks/types'
import type { TaskRunStatus } from '@/views/TaskCreateForm/types'
import {
  deleteFeishuTaskConfig,
  getFeishuTaskConfig,
  listFeishuTaskConfigs,
  type FeishuTaskConfigDetail,
  type FeishuTaskConfigListItem,
} from '@/lib/api'

const tasks = ref<TaskCardModel[]>([])
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

/** 列表项 `run_status`（源自 config.runStatus）；缺省为已停止 */
function parseListRunStatus(raw: string | null | undefined): TaskRunStatus {
  if (raw === 'running' || raw === 'completed' || raw === 'stopped' || raw === 'failed') {
    return raw
  }
  return 'stopped'
}

function formatPlatformsLabel(keys: string[] | null | undefined): string {
  if (!keys || keys.length === 0) return '未选择平台'
  if (keys.length >= sourcePlatforms.length) return '全平台'
  const labels = keys
    .map((k) => sourcePlatforms.find((p) => p.id === k)?.label)
    .filter(Boolean) as string[]
  return labels.length ? labels.join('、') : '未选择平台'
}

function formatCardDate(raw: string | null | undefined): string {
  if (!raw?.trim()) return '—'
  const d = dayjs(raw)
  return d.isValid() ? d.format('YYYY-MM-DD') : raw.slice(0, 10) || '—'
}

/** 任务列表统计（与卡片 `status` 一致，来自接口 `run_status`） */
const taskStats = computed(() => {
  const list = tasks.value
  return {
    total: list.length,
    running: list.filter((t) => t.status === 'running').length,
    completed: list.filter((t) => t.status === 'completed').length,
  }
})

function mapRows(rows: FeishuTaskConfigListItem[]): TaskCardModel[] {
  return rows.map((r) => ({
    id: r.id,
    name: r.plan_name?.trim() || '未命名方案',
    platformsLabel: formatPlatformsLabel(r.platform_keys ?? undefined),
    taskTypeLabel: r.task_type === 'realtime' ? '实时任务' : '定时任务',
    dateLabel: formatCardDate(r.effective_at ?? undefined),
    status: parseListRunStatus(r.run_status ?? undefined),
    notificationCount: 0,
  }))
}

async function loadTaskList() {
  try {
    const rows = await listFeishuTaskConfigs(0, 100)
    tasks.value = mapRows(rows)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载任务列表失败')
    tasks.value = []
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
    screen.value = 'list'
    editingTaskId.value = null
  }
}

function onPrimaryAction(_row: TaskCardModel) {}

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
          <div
            class="min-w-0 rounded-lg border border-slate-200 bg-white px-2 py-4 text-center shadow-sm sm:px-4 sm:py-5"
          >
            <div class="text-2xl font-bold leading-none text-[#3355FF] sm:text-3xl">{{ taskStats.total }}</div>
            <div class="mt-1.5 truncate text-xs text-slate-600 sm:mt-2 sm:text-sm">总任务数</div>
          </div>
          <div
            class="min-w-0 rounded-lg border border-slate-200 bg-white px-2 py-4 text-center shadow-sm sm:px-4 sm:py-5"
          >
            <div class="text-2xl font-bold leading-none text-[#3355FF] sm:text-3xl">{{ taskStats.running }}</div>
            <div class="mt-1.5 truncate text-xs text-slate-600 sm:mt-2 sm:text-sm">运行中</div>
          </div>
          <div
            class="min-w-0 rounded-lg border border-slate-200 bg-white px-2 py-4 text-center shadow-sm sm:px-4 sm:py-5"
          >
            <div class="text-2xl font-bold leading-none text-[#3355FF] sm:text-3xl">{{ taskStats.completed }}</div>
            <div class="mt-1.5 truncate text-xs text-slate-600 sm:mt-2 sm:text-sm">已完成</div>
          </div>
        </div>

        <div v-if="tasks.length > 0" class="flex flex-col gap-4">
          <TaskListCard
            v-for="row in tasks"
            :key="row.id"
            :row="row"
            @view="openView"
            @edit="openEdit"
            @primary-action="onPrimaryAction"
            @delete="onDeleteTask"
          />
        </div>
        <p v-else class="py-6 text-center text-sm text-slate-400">暂无任务</p>
      </section>
    </template>
  </div>
</template>
