<template>
  <div class="ops-page">
    <OpsStatGrid
      :stats="[
        { label: '今日执行次数', value: data?.total ?? 0, sub: '', tone: 'neutral' },
        { label: '执行成功率', value: data?.successRate ?? '-', sub: '', tone: 'neutral' },
        { label: '平均耗时', value: data?.avgDurationMs ? `${(data.avgDurationMs / 1000).toFixed(1)}s` : '-', sub: '', tone: 'neutral' },
      ]"
    />

    <el-card shadow="never" class="ops-table-card">
      <div class="ops-table-head">
        <h3>执行记录</h3>
        <div class="ops-table-toolbar">
          <el-select v-model="range" style="width: 100px; margin-right: 12px" @change="loadData">
            <el-option label="今日" value="day" />
            <el-option label="本周" value="week" />
            <el-option label="本月" value="month" />
          </el-select>
          <el-input v-model="keyword" placeholder="搜索执行ID / 任务ID..." clearable style="width: 220px" />
        </div>
      </div>
      <div class="admin-table-scroll">
        <el-table :data="pagedRows" stripe v-loading="loading">
          <el-table-column prop="execId" label="执行ID" width="120" />
          <el-table-column prop="taskId" label="任务ID" min-width="120">
            <template #default="{ row }">
              <el-link type="primary" :underline="false">{{ row.taskId }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="taskType" label="任务类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.taskType === '定时任务' ? 'primary' : 'info'" size="small">{{ row.taskType }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="startedAt" label="开始时间" width="160" />
          <el-table-column prop="endedAt" label="结束时间" width="160" />
          <el-table-column label="耗时" width="100">
            <template #default="{ row }">{{ row.durationMs ? `${(row.durationMs / 1000).toFixed(1)}s` : '-' }}</template>
          </el-table-column>
          <el-table-column prop="result" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.result === '成功' ? 'success' : 'danger'" size="small">{{ row.result }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="points" label="消耗点数" width="90" align="right" />
          <el-table-column prop="collectCount" label="采集条数" width="90" align="right" />
          <el-table-column prop="failReason" label="失败原因" min-width="120">
            <template #default="{ row }">
              <span :style="{ color: row.failReason ? '#f53f3f' : undefined }">{{ row.failReason || '-' }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination
        class="admin-pagination"
        style="margin-top: 16px; justify-content: flex-end"
        background
        layout="total, prev, pager, next"
        :total="filteredRows.length"
        :page-size="pageSize"
        v-model:current-page="page"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import OpsStatGrid from '@/components/ops/OpsStatGrid.vue'
import { fetchExecRuns, type ExecRunsData, type AnalyticsRange } from '@/api/analytics'

const keyword = ref('')
const page = ref(1)
const pageSize = 10
const range = ref<AnalyticsRange>('day')
const loading = ref(false)
const data = ref<ExecRunsData | null>(null)

async function loadData() {
  loading.value = true
  try {
    data.value = await fetchExecRuns(range.value)
  } finally {
    loading.value = false
  }
}

const filteredRows = computed(() => {
  if (!data.value) return []
  const q = keyword.value.trim().toLowerCase()
  return data.value.records.filter((row) => {
    if (!q) return true
    return `${row.execId} ${row.taskId}`.toLowerCase().includes(q)
  })
})

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})

onMounted(() => {
  loadData()
})
</script>
