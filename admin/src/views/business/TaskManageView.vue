<template>
  <div class="ops-page">
    <OpsStatGrid
      :col-sm="6"
      :stats="[
        { label: '任务总数', value: statsData.total, sub: '', tone: 'up' },
        { label: '运行中', value: statsData.running, sub: `占比 ${runningPct}`, tone: 'muted' },
        { label: '已停止', value: statsData.stopped, sub: `占比 ${stoppedPct}`, tone: 'muted' },
        { label: '已完成', value: statsData.completed, sub: `占比 ${completedPct}`, tone: 'muted' },
      ]"
    />

    <el-card shadow="never" class="ops-table-card" style="margin-top: 16px">
      <div class="ops-table-head">
        <h3>任务列表</h3>
        <div class="ops-table-toolbar">
          <el-input
            v-model="keyword"
            placeholder="搜索任务ID / 用户ID / 关键词..."
            clearable
            style="width: 280px"
            @change="handleSearch"
          />
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="-"
            start-placeholder="创建起"
            end-placeholder="创建止"
            value-format="YYYY-MM-DD"
            @change="handleSearch"
          />
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 120px" @change="handleSearch">
            <el-option label="待执行" value="pending" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="success" />
            <el-option label="已失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </div>
      </div>
      <div v-loading="loading" class="admin-table-scroll">
        <el-table :data="tableData" stripe>
          <el-table-column prop="id" label="任务ID" width="100">
            <template #default="{ row }">
              <el-link type="primary" :underline="false">{{ row.id }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="taskName" label="任务名称" min-width="150" show-overflow-tooltip />
          <el-table-column prop="userId" label="用户ID" width="120" show-overflow-tooltip />
          <el-table-column label="关键词" min-width="180">
            <template #default="{ row }">
              <div class="ops-tag-gap">
                <el-tag v-for="(k, idx) in row.keywords.slice(0, 3)" :key="idx" size="small" effect="plain">
                  {{ k }}
                </el-tag>
                <span v-if="row.keywords.length > 3" style="color: #909399; font-size: 12px">
                  +{{ row.keywords.length - 3 }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="平台" width="100">
            <template #default="{ row }">
              <el-tag size="small" type="info" effect="plain">{{ row.platform || '-' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="采集进度" width="110">
            <template #default="{ row }">
              <span style="color: #67c23a">{{ row.successCount }}</span>
              <span style="color: #909399"> / </span>
              <span style="color: #f56c6c">{{ row.failedCount }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="intervalMinutes" label="频率(分钟)" width="100" align="center" />
          <el-table-column prop="createdAt" label="创建时间" width="110">
            <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
          </el-table-column>
          <el-table-column prop="nextRunAt" label="下次执行" width="110">
            <template #default="{ row }">{{ formatDateTime(row.nextRunAt) || '-' }}</template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination
        class="admin-pagination"
        style="margin-top: 16px; justify-content: flex-end"
        background
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import OpsStatGrid from '@/components/ops/OpsStatGrid.vue'
import { fetchAdminTasks, type AdminTasksData } from '@/api/analytics'

const loading = ref(false)
const keyword = ref('')
const dateRange = ref<[string, string] | null>(null)
const statusFilter = ref('')
const page = ref(1)
const pageSize = 20

const tasksData = ref<AdminTasksData>({
  total: 0,
  page: 1,
  limit: 20,
  records: [],
  stats: {
    total: 0,
    running: 0,
    stopped: 0,
    completed: 0,
  },
})

const tableData = computed(() => tasksData.value.records)
const total = computed(() => tasksData.value.total)
const statsData = computed(() => tasksData.value.stats)

const runningPct = computed(() => {
  const t = statsData.value.total
  return t > 0 ? `占比 ${((statsData.value.running / t) * 100).toFixed(1)}%` : '占比 0%'
})

const stoppedPct = computed(() => {
  const t = statsData.value.total
  return t > 0 ? `占比 ${((statsData.value.stopped / t) * 100).toFixed(1)}%` : '占比 0%'
})

const completedPct = computed(() => {
  const t = statsData.value.total
  return t > 0 ? `占比 ${((statsData.value.completed / t) * 100).toFixed(1)}%` : '占比 0%'
})

function statusTagType(status: string) {
  if (status === '运行中' || status === '待执行') return 'success'
  if (status === '已完成') return 'info'
  if (status === '已失败') return 'danger'
  return 'warning'
}

function formatDateTime(iso: string): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch {
    return ''
  }
}

async function loadTasks() {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      limit: pageSize,
    }
    if (keyword.value.trim()) {
      params.keyword = keyword.value.trim()
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.created_start = dateRange.value[0]
      params.created_end = dateRange.value[1]
    }
    tasksData.value = await fetchAdminTasks(params)
  } catch (err) {
    console.error('Failed to load tasks:', err)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadTasks()
}

function handlePageChange(newPage: number) {
  page.value = newPage
  loadTasks()
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.ops-page {
  padding: 16px;
}
.ops-table-card {
  margin-top: 16px;
}
.ops-table-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.ops-table-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.ops-table-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}
.ops-tag-gap {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
.admin-table-scroll {
  min-height: 400px;
}
</style>
