<template>
  <div class="ops-page">
    <OpsStatGrid
      :stats="[
        { label: '今日执行次数', value: '3,842', sub: '↑ 5.2% vs 昨日', tone: 'up' },
        { label: '执行成功率', value: '96.8%', sub: '↑ 1.2% vs 上月', tone: 'up' },
        { label: '平均耗时', value: '2.3s', sub: '↑ 0.2s vs 上月', tone: 'down' },
      ]"
    />

    <OpsChartCard title="执行趋势（近7天）" :option="trendOption" />

    <el-row :gutter="16" class="ops-chart-row">
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="执行失败原因分布（近30天）" :option="failReasonOption" />
      </el-col>
    </el-row>

    <el-card shadow="never" class="ops-table-card">
      <div class="ops-table-head">
        <h3>执行记录</h3>
        <div class="ops-table-toolbar">
          <el-input v-model="keyword" placeholder="搜索执行ID / 任务ID..." clearable style="width: 220px" />
        </div>
      </div>
      <div class="admin-table-scroll">
        <el-table :data="pagedRows" stripe>
          <el-table-column prop="id" label="执行ID" width="100" />
          <el-table-column prop="taskId" label="任务ID" min-width="150">
            <template #default="{ row }">
              <el-link type="primary" :underline="false">{{ row.taskId }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="taskType" label="任务类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.taskType === '定时任务' ? 'primary' : 'info'" size="small">{{ row.taskType }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="第几次执行" width="110">
            <template #default="{ row }">{{ row.taskType === '定时任务' ? row.execCount : '-' }}</template>
          </el-table-column>
          <el-table-column prop="start" label="开始时间" width="160" />
          <el-table-column prop="end" label="结束时间" width="160" />
          <el-table-column prop="duration" label="耗时" width="80" />
          <el-table-column prop="result" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.result === '成功' ? 'success' : 'danger'" size="small">{{ row.result }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="points" label="消耗点数" width="90" align="right" />
          <el-table-column prop="count" label="采集条数" width="90" align="right" />
          <el-table-column prop="failReason" label="失败原因" min-width="120">
            <template #default="{ row }">
              <span :style="{ color: row.failReason !== '-' ? '#f53f3f' : undefined }">{{ row.failReason }}</span>
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
import { EXEC_RECORDS } from '@/mock/opsMockData'

useOpsEcharts()

const keyword = ref('')
const page = ref(1)
const pageSize = 10

const filteredRows = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return EXEC_RECORDS.filter((row) => {
    if (!q) return true
    return `${row.id} ${row.taskId}`.toLowerCase().includes(q)
  })
})

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})

const trendOption = computed(
  (): OpsChartOption => ({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 48, right: 24, top: 40, bottom: 32 },
    xAxis: { type: 'category', data: ['5/22', '5/23', '5/24', '5/25', '5/26', '5/27', '5/28'] },
    yAxis: { type: 'value' },
    series: [
      { name: '成功', type: 'bar', stack: 'total', data: [502, 530, 493, 480, 515, 542, 562], itemStyle: { color: '#00b42a' }, barMaxWidth: 28 },
      { name: '失败', type: 'bar', stack: 'total', data: [18, 18, 17, 15, 15, 18, 18], itemStyle: { color: '#f53f3f' }, barMaxWidth: 28 },
    ],
  }),
)

const failReasonOption = computed(
  (): OpsChartOption => ({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, type: 'scroll' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '65%'],
        data: [
          { name: 'API限流', value: 32 },
          { name: '网络超时', value: 25 },
          { name: '平台返回异常', value: 18 },
          { name: '任务已停止', value: 12 },
          { name: '账号权限异常', value: 8 },
          { name: '数据解析失败', value: 5 },
        ],
        color: ['#f53f3f', '#ff7d00', '#ffb700', '#4073fa', '#9ca3af', '#d1d5db'],
      },
    ],
  }),
)
</script>
