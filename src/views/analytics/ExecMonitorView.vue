<template>
  <div class="analytics-page">
    <div class="analytics-stats-grid">
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">今日执行次数</div>
        <div class="analytics-stat-value">{{ data?.total ?? 0 }}</div>
      </div>
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">执行成功率</div>
        <div class="analytics-stat-value">{{ data?.successRate ?? '-' }}</div>
      </div>
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">平均耗时</div>
        <div class="analytics-stat-value">
          {{ data?.avgDurationMs ? `${(data.avgDurationMs / 1000).toFixed(1)}s` : '-' }}
        </div>
      </div>
    </div>

    <el-card shadow="never" class="analytics-table-card">
      <template #header>
        <div class="analytics-table-head">
          <h3>执行记录</h3>
          <div class="analytics-table-toolbar">
            <el-select v-model="range" style="width: 100px; margin-right: 12px" @change="loadData">
              <el-option label="今日" value="day" />
              <el-option label="本周" value="week" />
              <el-option label="本月" value="month" />
            </el-select>
            <el-input v-model="keyword" placeholder="搜索..." clearable style="width: 200px" />
          </div>
        </div>
      </template>
      <div v-loading="loading">
        <el-table :data="pagedRows" stripe size="small" style="width: 100%">
          <el-table-column label="执行ID" width="140">
            <template #default="{ row }">
              <el-tooltip :content="row.execId" placement="top">
                <span style="font-size: 12px">{{ maskId(row.execId) }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="taskId" label="任务ID" min-width="140" />
          <el-table-column prop="taskType" label="类型" width="90">
            <template #default="{ row }">
              <el-tag :type="row.taskType === '定时任务' ? 'primary' : 'info'" size="small">
                {{ row.taskType }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="开始时间" width="150">
            <template #default="{ row }">{{ formatDateTime(row.startedAt) }}</template>
          </el-table-column>
          <el-table-column label="耗时" width="90">
            <template #default="{ row }">
              {{ row.durationMs ? `${(row.durationMs / 1000).toFixed(1)}s` : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="result" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.result === '成功' ? 'success' : 'danger'" size="small">
                {{ row.result }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="points" label="点数" width="80" align="right" />
          <el-table-column prop="collectCount" label="采集数" width="90" align="right" />
          <el-table-column prop="failReason" label="失败原因" min-width="120">
            <template #default="{ row }">
              <span :style="{ color: row.failReason ? '#f53f3f' : undefined }">
                {{ row.failReason || '-' }}
              </span>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          style="margin-top: 16px; justify-content: flex-end"
          background
          layout="total, prev, pager, next"
          :total="filteredRows.length"
          :page-size="pageSize"
          v-model:current-page="page"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchExecRuns } from '@/api/analytics'

const keyword = ref('')
const page = ref(1)
const pageSize = 10
const range = ref('day')
const loading = ref(false)
const data = ref(null)

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

function maskId(id) {
  if (!id || id.length <= 7) return id
  return `${id.slice(0, 4)}***${id.slice(-3)}`
}

function formatDateTime(iso) {
  if (!iso) return '-'
  return iso.replace('T', ' ').slice(0, 19)
}

onMounted(() => {
  loadData()
})
</script>
