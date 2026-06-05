<template>
  <div class="analytics-page">
    <div class="analytics-stats-grid">
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">今日调用次数</div>
        <div class="analytics-stat-value">{{ data?.total ?? 0 }}</div>
      </div>
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">成功率</div>
        <div class="analytics-stat-value">{{ data?.successRate ?? '-' }}</div>
      </div>
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">平均响应耗时</div>
        <div class="analytics-stat-value">
          {{ data?.avgLatencyMs ? `${(data.avgLatencyMs / 1000).toFixed(2)}s` : '-' }}
        </div>
      </div>
    </div>

    <el-card v-if="data?.platformStats?.length" shadow="never" class="analytics-chart-card" style="margin-bottom: 16px">
      <template #header>各平台调用成功率</template>
      <div ref="platformChartEl" style="height: 280px" />
    </el-card>

    <el-card shadow="never" class="analytics-table-card">
      <template #header>
        <div class="analytics-table-head">
          <h3>API 调用记录</h3>
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
          <el-table-column prop="requestId" label="请求ID" width="130" />
          <el-table-column prop="taskId" label="任务ID" min-width="140" />
          <el-table-column prop="platform" label="平台" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.platform" size="small" effect="plain">{{ row.platform }}</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="calledAt" label="调用时间" width="150" />
          <el-table-column prop="result" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.result === '成功' ? 'success' : 'danger'" size="small">
                {{ row.result }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="errorCode" label="失败码" width="100">
            <template #default="{ row }">
              <span :style="{ color: row.errorCode ? '#f53f3f' : undefined }">
                {{ row.errorCode || '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="响应耗时" width="100">
            <template #default="{ row }">
              {{ row.latencyMs ? `${(row.latencyMs / 1000).toFixed(2)}s` : '-' }}
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
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { fetchApiCalls } from '@/api/analytics'

const keyword = ref('')
const page = ref(1)
const pageSize = 10
const range = ref('day')
const loading = ref(false)
const data = ref(null)
const platformChartEl = ref(null)
let platformChart = null

async function loadData() {
  loading.value = true
  try {
    data.value = await fetchApiCalls(range.value)
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

function renderChart() {
  const stats = data.value?.platformStats
  if (!stats || !platformChartEl.value || !window.echarts) return

  if (!platformChart) {
    platformChart = window.echarts.init(platformChartEl.value)
  }

  platformChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0, textStyle: { fontSize: 11 } },
    grid: { left: 44, right: 20, top: 36, bottom: 36 },
    xAxis: {
      type: 'category',
      data: stats.map((s) => s.platform),
      axisLabel: { fontSize: 10 },
    },
    yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
    series: [
      {
        name: '成功',
        type: 'bar',
        stack: 'total',
        data: stats.map((s) => s.success),
        itemStyle: { color: '#00b42a' },
      },
      {
        name: '失败',
        type: 'bar',
        stack: 'total',
        data: stats.map((s) => s.total - s.success),
        itemStyle: { color: '#f53f3f' },
      },
    ],
  })
}

const filteredRows = computed(() => {
  if (!data.value) return []
  const q = keyword.value.trim().toLowerCase()
  return data.value.records.filter((row) => !q || row.requestId.toLowerCase().includes(q))
})

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})

onMounted(() => {
  loadData()
})

onBeforeUnmount(() => {
  platformChart?.dispose()
})
</script>
