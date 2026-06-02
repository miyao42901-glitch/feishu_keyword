<template>
  <div class="ops-page">
    <OpsStatGrid
      :col-sm="6"
      :stats="[
        { label: '任务总数', value: '1,247', sub: '本月新增 186', tone: 'up' },
        { label: '运行中', value: '623', sub: '占比 49.9%', tone: 'muted' },
        { label: '已停止', value: '438', sub: '占比 35.1%', tone: 'muted' },
        { label: '已完成', value: '186', sub: '占比 14.9%', tone: 'muted' },
      ]"
    />

    <el-row :gutter="16" class="ops-chart-row">
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="任务类型偏好（本月）" :option="typePieOption" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="任务类型创建趋势（近6个月）" :option="typeTrendOption" />
      </el-col>
    </el-row>

    <el-card shadow="never" class="ops-table-card">
      <div class="ops-table-head">
        <h3>任务列表</h3>
        <div class="ops-table-toolbar">
          <el-input v-model="keyword" placeholder="搜索任务ID / 关键词..." clearable style="width: 220px" />
          <el-date-picker v-model="dateRange" type="daterange" range-separator="-" start-placeholder="创建起" end-placeholder="创建止" value-format="YYYY-MM-DD" />
        </div>
      </div>
      <div class="admin-table-scroll">
        <el-table :data="pagedRows" stripe>
          <el-table-column prop="id" label="任务ID" min-width="150">
            <template #default="{ row }">
              <el-link type="primary" :underline="false">{{ row.id }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="taskType" label="任务类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.taskType === '定时任务' ? 'primary' : 'info'" size="small">{{ row.taskType }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="user" label="创建用户" width="90" />
          <el-table-column label="关键词" min-width="180">
            <template #default="{ row }">
              <div class="ops-tag-gap">
                <el-tag v-for="k in row.keywords" :key="k" size="small" effect="plain">{{ k }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="信源平台" min-width="180">
            <template #default="{ row }">
              <div class="ops-tag-gap">
                <el-tag v-for="p in row.platforms" :key="p" size="small" type="info" effect="plain">{{ p }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="notify" label="通知" width="70">
            <template #default="{ row }">
              <el-tag :type="row.notify === '开' ? 'success' : 'danger'" size="small">{{ row.notify }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created" label="创建时间" width="110" />
          <el-table-column prop="lastExec" label="最近执行" width="150" />
          <el-table-column prop="points" label="累计消耗点数" width="120" align="right">
            <template #default="{ row }">{{ row.points.toLocaleString() }}</template>
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
import { TASKS } from '@/mock/opsMockData'

useOpsEcharts()

const keyword = ref('')
const dateRange = ref<[string, string] | null>(null)
const page = ref(1)
const pageSize = 10

function statusTagType(status: string) {
  if (status === '运行中') return 'success'
  if (status === '已完成') return 'info'
  return 'warning'
}

const filteredRows = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return TASKS.filter((row) => {
    if (!q) return true
    const blob = [row.id, row.user, ...row.keywords].join(' ').toLowerCase()
    return blob.includes(q)
  })
})

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})

const typePieOption = computed(
  (): OpsChartOption => ({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{ type: 'pie', radius: ['45%', '70%'], data: [{ name: '定时任务', value: 1061 }, { name: '单次任务', value: 186 }], color: ['#4073fa', '#9ca3af'] }],
  }),
)

const typeTrendOption = computed(
  (): OpsChartOption => ({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 48, right: 24, top: 40, bottom: 32 },
    xAxis: { type: 'category', data: ['12月', '1月', '2月', '3月', '4月', '5月'] },
    yAxis: { type: 'value', name: '新增任务数' },
    series: [
      { name: '定时任务', type: 'bar', data: [38, 45, 52, 48, 61, 58], itemStyle: { color: '#4073fa' }, barMaxWidth: 20 },
      { name: '单次任务', type: 'bar', data: [12, 18, 22, 25, 28, 31], itemStyle: { color: '#9ca3af' }, barMaxWidth: 20 },
    ],
  }),
)
</script>
