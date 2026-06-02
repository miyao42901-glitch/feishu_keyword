<template>
  <div class="ops-page">
    <OpsStatGrid
      :stats="[
        { label: '今日调用次数', value: '12,486', sub: '↑ 3.1% vs 昨日', tone: 'up' },
        { label: '成功率', value: '99.1%', sub: '↑ 0.3% vs 上月', tone: 'up' },
        { label: '平均响应耗时', value: '1.8s', sub: '↑ 0.1s vs 上月', tone: 'down' },
      ]"
    />

    <el-row :gutter="16" class="ops-chart-row">
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="各平台调用成功率" :option="platformOption" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <OpsChartCard title="错误码分布（近30天）" :option="errorCodeOption" />
      </el-col>
    </el-row>

    <el-card shadow="never" class="ops-table-card">
      <div class="ops-table-head">
        <h3>API 调用记录</h3>
        <div class="ops-table-toolbar">
          <el-input v-model="keyword" placeholder="搜索 API 请求ID..." clearable style="width: 220px" />
        </div>
      </div>
      <div class="admin-table-scroll">
        <el-table :data="pagedRows" stripe>
          <el-table-column prop="id" label="请求ID" width="100" />
          <el-table-column prop="taskId" label="任务ID" min-width="150">
            <template #default="{ row }">
              <el-link type="primary" :underline="false">{{ row.taskId }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="platform" label="平台" width="120">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ row.platform }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="time" label="调用时间" width="160" />
          <el-table-column prop="result" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="row.result === '成功' ? 'success' : 'danger'" size="small">{{ row.result }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="code" label="失败码" width="100">
            <template #default="{ row }">
              <span :style="{ color: row.code !== '-' ? '#f53f3f' : undefined }">{{ row.code }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="latency" label="响应耗时" width="100" />
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
import { API_RECORDS } from '@/mock/opsMockData'

useOpsEcharts()

const keyword = ref('')
const page = ref(1)
const pageSize = 10

const filteredRows = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return API_RECORDS.filter((row) => !q || row.id.toLowerCase().includes(q))
})

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})

const platformOption = computed(
  (): OpsChartOption => ({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 48, right: 24, top: 40, bottom: 40 },
    xAxis: { type: 'category', data: ['微博', '抖音', '百度', '知乎', '小红书', '微信公众号', '政府网'] },
    yAxis: { type: 'value' },
    series: [
      { name: '成功', type: 'bar', stack: 'total', data: [3168, 2772, 2079, 1485, 1188, 960, 698], itemStyle: { color: '#00b42a' } },
      { name: '失败', type: 'bar', stack: 'total', data: [32, 28, 21, 15, 12, 20, 8], itemStyle: { color: '#f53f3f' } },
    ],
  }),
)

const errorCodeOption = computed(
  (): OpsChartOption => ({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, type: 'scroll' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '65%'],
        data: [
          { name: 'E40301 (权限不足)', value: 35 },
          { name: 'E40401 (资源不存在)', value: 28 },
          { name: 'E50001 (服务异常)', value: 18 },
          { name: 'E42901 (频率限制)', value: 12 },
          { name: '其他', value: 7 },
        ],
        color: ['#f53f3f', '#ff7d00', '#4073fa', '#ffb700', '#9ca3af'],
      },
    ],
  }),
)
</script>
