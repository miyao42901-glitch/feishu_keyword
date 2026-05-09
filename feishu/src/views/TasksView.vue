<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import TaskCreateForm from '@/views/TaskCreateForm/index.vue'
import {
  getFeishuTaskConfig,
  listFeishuTaskConfigs,
  type FeishuTaskConfigDetail,
  type FeishuTaskConfigListItem,
} from '@/lib/api'

interface TaskRow {
  id: number
  name: string
  status: string
  updatedAt: string
}

const tasks = ref<TaskRow[]>([])
const screen = ref<'list' | 'create'>('list')
const editingTaskId = ref<number | null>(null)
const taskDetail = ref<FeishuTaskConfigDetail | null>(null)

function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('zh-CN', { hour12: false })
}

function mapRows(rows: FeishuTaskConfigListItem[]): TaskRow[] {
  return rows.map((r) => ({
    id: r.id,
    name: r.plan_name?.trim() || '未命名方案',
    status: '已保存',
    updatedAt: formatTime(r.updated_at ?? undefined),
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

async function openEdit(row: TaskRow) {
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
</script>

<template>
  <div class="flex min-h-0 flex-col gap-4">
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
      <section class="flex min-h-0 flex-col gap-3">
        <h2 class="text-base font-medium text-slate-800">任务列表</h2>
        <el-button type="primary" @click="onCreateTask">新建任务</el-button>
        <ul v-if="tasks.length > 0" class="divide-y divide-slate-100 text-sm text-slate-800">
          <li
            v-for="row in tasks"
            :key="row.id"
            class="flex cursor-pointer flex-wrap items-baseline gap-x-4 gap-y-1 py-3 transition-colors hover:bg-slate-50"
            role="button"
            tabindex="0"
            @click="openEdit(row)"
            @keydown.enter.prevent="openEdit(row)"
          >
            <span class="min-w-0 flex-1 font-medium">{{ row.name }}</span>
            <span class="shrink-0 text-slate-500">{{ row.status }}</span>
            <span class="shrink-0 text-xs text-slate-400">{{ row.updatedAt }}</span>
          </li>
        </ul>
        <p v-else class="py-6 text-center text-sm text-slate-400">暂无任务</p>
      </section>
    </template>
  </div>
</template>
