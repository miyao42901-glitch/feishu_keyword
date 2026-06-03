<template>
  <div class="ops-page">
    <OpsStatGrid
      :stats="[
        { label: '今日调用次数', value: data?.total ?? 0, sub: '', tone: 'neutral' },
        { label: '成功率', value: data?.successRate ?? '-', sub: '', tone: 'neutral' },
        { label: '平均响应耗时', value: data?.avgLatencyMs ? `${(data.avgLatencyMs / 1000).toFixed(2)}s` : '-', sub: '', tone: 'neutral' },
      ]"
    />

    <el-row :gutter="16" class="ops-chart-row" v-if="data && data.platformStats.length">
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="各平台调用成功率" :option="platformOption" />
      </el-col>
    </el-row>

    <el-card shadow="never" class="ops-table-card">
      <div class="ops-table-head">
        <h3>API 调用记录</h3>
        <div class="ops-table-toolbar">
          <el-select v-model="range" style="width: 100px; margin-right: 12px" @change="loadData">
            <el-option label="今日" value="day" />
            <el-option label="本周" value="week" />
            <el-option label="本月" value="month" />
          </el-select>
          <el-input v-model="keyword" placeholder="搜索请求ID..." clearable style="width: 220px" />
        </div>
      </div>
      <div class="admin-table-scroll">
        <el-table :data="pagedRows" stripe v-loading="loading">
          <el-table-column prop="requestId" label="请求ID" width="160" />
          <el-table-column prop="taskId" label="任务ID" min-width="120">
            <template #default="{ row }">
              <el-link type="primary" :underline="false">{{ row.taskId || '-' }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="platform" label="平台" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.platform" size="small" effect="plain">{{ row.platform }}</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="calledAt" label="调用时间" width="160" />
          <el-table-column prop="result" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.result === '成功' ? 'success' : 'danger'" size="small">{{ row.result }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="errorCode" label="失败码" width="120">
            <template #default="{ row }">
              <span :style="{ color: row.errorCode ? '#f53f3f' : undefined }">{{ row.errorCode || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="响应耗时" width="100">
            <template #default="{ row }">{{ row.latencyMs ? `${(row.latencyMs / 1000).toFixed(2)}s` : '-' }}</template>
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
import type { OpsChartOption } from '@/types/opsCharts'
import OpsChartCard from '@/components/ops/OpsChartCard.vue'
import OpsStatGrid from '@/components/ops/OpsStatGrid.vue'
import { useOpsEcharts } from '@/composables/useOpsEcharts'
import { fetchApiCalls, type ApiCallsData, type AnalyticsRange } from '@/api/analytics'

useOpsEcharts()

const keyword = ref('')
const page = ref(1)
const pageSize = 10
const range = ref<AnalyticsRange>('day')
const loading = ref(false)
const data = ref<ApiCallsData | null>(null)

async function loadData() {
  loading.value = true
  try {
    data.value = await fetchApiCalls(range.value)
  } finally {
    loading.value = false
  }
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

const platformOption = computed((): OpsChartOption => {
  const stats = data.value?.platformStats ?? []
  return {
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 48, right: 24, top: 40, bottom: 40 },
    xAxis: { type: 'category', data: stats.map((s) => s.platform) },
    yAxis: { type: 'value' },
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
  }
})

onMounted(() => {
  loadData()
})
</script>
