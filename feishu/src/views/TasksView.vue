<script setup lang="ts">
import dayjs from 'dayjs'
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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

function onSaved(id: number) {
  editingTaskId.value = id
  void loadTaskList()
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

async function onDeleteTask(row: TaskCardModel) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.name}」？删除后不可恢复。`, '删除任务', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await deleteFeishuTaskConfig(row.id)
    ElMessage.success('已删除')
    await loadTaskList()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '删除失败')
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
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="text-base font-semibold text-slate-800">任务列表</h2>
          <el-button type="primary" @click="onCreateTask">新建任务</el-button>
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
