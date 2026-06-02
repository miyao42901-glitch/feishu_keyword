<template>
  <div class="ops-page">
    <OpsStatGrid
      :col-sm="6"
      :stats="[
        { label: '今日推送次数', value: '856', sub: '↑ 11.2% vs 昨日', tone: 'up' },
        { label: '推送触达率', value: '93.6%', sub: '↑ 2.1% vs 上月', tone: 'up' },
        { label: '通知打开次数（本月）', value: '28', sub: '较上月 +5', tone: 'up' },
        { label: '通知关闭次数（本月）', value: '14', sub: '较上月 -8', tone: 'down' },
      ]"
    />

    <el-row :gutter="16" class="ops-chart-row">
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="推送趋势（近7天）" :option="pushTrendOption" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="通知开关趋势（近30天）" :option="notifySwitchOption" />
      </el-col>
    </el-row>

    <el-card shadow="never" class="ops-table-card">
      <div class="ops-table-head">
        <h3>推送记录</h3>
        <div class="ops-table-toolbar">
          <el-input v-model="keyword" placeholder="搜索推送ID / 任务ID..." clearable style="width: 220px" />
        </div>
      </div>
      <div class="admin-table-scroll">
        <el-table :data="pagedRows" stripe>
          <el-table-column prop="id" label="推送ID" width="90" />
          <el-table-column prop="taskId" label="任务ID" min-width="150">
            <template #default="{ row }">
              <el-link type="primary" :underline="false">{{ row.taskId }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="webhook" label="Webhook" min-width="180" show-overflow-tooltip />
          <el-table-column prop="sendTime" label="发送时间" width="160" />
          <el-table-column prop="sendResult" label="发送结果" width="90">
            <template #default="{ row }">
              <el-tag :type="row.sendResult === '成功' ? 'success' : 'danger'" size="small">{{ row.sendResult }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="callbackResult" label="回调结果" width="90">
            <template #default="{ row }">
              <el-tag :type="callbackTagType(row.callbackResult)" size="small">{{ row.callbackResult }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="newData" label="新增数据" width="90" align="right" />
          <el-table-column prop="retry" label="重试次数" width="90" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.retry > 0 ? '#ff7d00' : undefined }">{{ row.retry }}</span>
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
import { computed, ref } from 'vue'
import type { OpsChartOption } from '@/types/opsCharts'
import OpsChartCard from '@/components/ops/OpsChartCard.vue'
import OpsStatGrid from '@/components/ops/OpsStatGrid.vue'
import { useOpsEcharts } from '@/composables/useOpsEcharts'
import { PUSH_RECORDS } from '@/mock/opsMockData'

useOpsEcharts()

const keyword = ref('')
const page = ref(1)
const pageSize = 10

function callbackTagType(value: string) {
  if (value === '成功') return 'success'
  if (value === '失败') return 'danger'
  return 'warning'
}

const filteredRows = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return PUSH_RECORDS.filter((row) => {
    if (!q) return true
    return `${row.id} ${row.taskId}`.toLowerCase().includes(q)
  })
})

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})

const pushTrendOption = computed(
  (): OpsChartOption => ({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 48, right: 24, top: 40, bottom: 32 },
    xAxis: { type: 'category', data: ['5/22', '5/23', '5/24', '5/25', '5/26', '5/27', '5/28'] },
    yAxis: { type: 'value' },
    series: [
      { name: '推送总数', type: 'line', smooth: true, data: [110, 125, 105, 98, 118, 130, 140], itemStyle: { color: '#4073fa' }, areaStyle: { color: 'rgba(64,115,250,0.08)' } },
      { name: '触达成功', type: 'line', smooth: true, data: [102, 117, 98, 92, 110, 122, 131], itemStyle: { color: '#00b42a' }, areaStyle: { color: 'rgba(0,180,42,0.08)' } },
    ],
  }),
)

const notifySwitchOption = computed(
  (): OpsChartOption => ({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 48, right: 24, top: 40, bottom: 32 },
    xAxis: { type: 'category', data: ['4/29', '5/2', '5/5', '5/8', '5/11', '5/14', '5/17', '5/20', '5/23', '5/26', '5/28'] },
    yAxis: { type: 'value' },
    series: [
      { name: '开启通知', type: 'line', smooth: true, data: [3, 5, 2, 4, 3, 6, 2, 4, 3, 5, 4], itemStyle: { color: '#00b42a' }, areaStyle: { color: 'rgba(0,180,42,0.1)' } },
      { name: '关闭通知', type: 'line', smooth: true, data: [1, 2, 1, 3, 2, 1, 2, 1, 2, 1, 2], itemStyle: { color: '#f53f3f' }, areaStyle: { color: 'rgba(245,63,63,0.08)' } },
    ],
  }),
)
</script>
